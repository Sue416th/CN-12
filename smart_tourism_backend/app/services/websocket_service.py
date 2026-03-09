"""
WebSocket Service - Real-time profile updates and notifications
WebSocket服务 - 实时推送用户画像更新和通知
"""
from typing import Dict, Any, Set, Optional, Callable
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket Connection Manager
    
    管理WebSocket连接，支持：
    - 用户画像实时更新推送
    - 行程规划进度通知
    - 个性化推荐推送
    """
    
    def __init__(self):
        # All active connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # User ID to WebSocket mapping
        self.user_connections: Dict[WebSocket, int] = {}
        # Event callbacks
        self.event_handlers: Dict[str, Callable] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.user_connections[websocket] = user_id
        
        logger.info(f"User {user_id} connected via WebSocket. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a user"""
        user_id = self.user_connections.pop(websocket, None)
        
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            logger.info(f"User {user_id} disconnected. Remaining: {len(self.active_connections.get(user_id, set()))}")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """Send message to specific user"""
        if user_id not in self.active_connections:
            return
        
        message["timestamp"] = datetime.now().isoformat()
        message_str = json.dumps(message, ensure_ascii=False)
        
        # Send to all connections for this user
        disconnected = set()
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected users"""
        message["timestamp"] = datetime.now().isoformat()
        message_str = json.dumps(message, ensure_ascii=False)
        
        # Collect all connections
        all_connections = []
        for user_id, connections in self.active_connections.items():
            all_connections.extend(connections)
        
        # Send to all
        disconnected = set()
        for websocket in all_connections:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_connected_users(self) -> Set[int]:
        """Get all connected user IDs"""
        return set(self.active_connections.keys())
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if user is connected"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Global connection manager instance
manager = ConnectionManager()


# ==================== Profile Update Events ====================

class ProfileUpdateBroadcaster:
    """
    Broadcast user profile updates to relevant components
    """
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
    
    async def broadcast_profile_update(
        self,
        user_id: int,
        profile_data: Dict[str, Any],
        update_type: str = "full_update",
    ):
        """
        Broadcast profile update to user
        
        Args:
            user_id: User ID
            profile_data: Updated profile data
            update_type: Type of update (full_update, preference_change, score_change)
        """
        message = {
            "type": "profile_update",
            "update_type": update_type,
            "data": profile_data,
        }
        
        await self.manager.send_personal_message(message, user_id)
    
    async def broadcast_recommendation(
        self,
        user_id: int,
        recommendations: list,
        reason: str = "",
    ):
        """Broadcast new recommendations to user"""
        message = {
            "type": "recommendations",
            "data": {
                "recommendations": recommendations,
                "reason": reason,
                "count": len(recommendations),
            }
        }
        
        await self.manager.send_personal_message(message, user_id)
    
    async def broadcast_progress(
        self,
        user_id: int,
        agent_name: str,
        progress: float,
        status: str = "processing",
        message: str = "",
    ):
        """Broadcast agent processing progress"""
        message = {
            "type": "agent_progress",
            "data": {
                "agent": agent_name,
                "progress": progress,
                "status": status,
                "message": message,
            }
        }
        
        await self.manager.send_personal_message(message, user_id)
    
    async def broadcast_itinerary_update(
        self,
        user_id: int,
        itinerary_data: Dict[str, Any],
        update_type: str = "generated",
    ):
        """Broadcast itinerary update"""
        message = {
            "type": "itinerary_update",
            "update_type": update_type,
            "data": itinerary_data,
        }
        
        await self.manager.send_personal_message(message, user_id)


# Global broadcaster instance
profile_broadcaster = ProfileUpdateBroadcaster(manager)


# ==================== WebSocket Endpoint ====================

async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time communication
    
    Usage:
        wscat -c ws://localhost:8000/ws/{user_id}
    
    Message format:
        {"type": "ping"}
        {"type": "get_profile"}
        {"type": "feedback", "content": "..."}
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type", "unknown")
            
            if msg_type == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                }))
            
            elif msg_type == "get_profile":
                # Fetch current profile and send
                # This would typically query the database
                await websocket.send_text(json.dumps({
                    "type": "profile_data",
                    "data": {"user_id": user_id},
                }))
            
            elif msg_type == "feedback":
                # Handle user feedback
                feedback_content = message.get("content", "")
                logger.info(f"Received feedback from user {user_id}: {feedback_content}")
                
                await websocket.send_text(json.dumps({
                    "type": "feedback_received",
                    "message": "Thank you for your feedback!",
                }))
            
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"User {user_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket)


# ==================== Helper Functions ====================

async def notify_profile_generated(user_id: int, profile: Dict[str, Any]):
    """Notify user that their profile has been generated"""
    await profile_broadcaster.broadcast_profile_update(
        user_id=user_id,
        profile_data=profile,
        update_type="generated",
    )


async def notify_similar_users_found(user_id: int, similar_users: list):
    """Notify user about similar users (for social features)"""
    message = {
        "type": "similar_users",
        "data": {
            "users": similar_users,
            "count": len(similar_users),
        }
    }
    await manager.send_personal_message(message, user_id)


async def notify_achievement_unlocked(user_id: int, achievement: Dict[str, Any]):
    """Notify user about unlocked achievements"""
    message = {
        "type": "achievement",
        "data": achievement,
    }
    await manager.send_personal_message(message, user_id)
