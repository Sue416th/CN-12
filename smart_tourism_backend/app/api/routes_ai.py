"""
LLM和知识图谱相关的API路由
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.agents.enhanced_user_profile_agent import EnhancedUserProfileAgent
from app.services.llm_service import get_llm_service
from app.services.knowledge_graph_service import get_kg_service
from app.services.vector_service import get_vector_service


router = APIRouter()


# ==================== Request Models ====================

class UserProfileCreateRequest(BaseModel):
    """创建用户画像请求"""
    user_id: int
    interests: List[str] = []
    budget_level: str = "medium"
    travel_style: str = "balanced"
    fitness_level: str = "medium"
    group_type: str = "solo"
    user_text: Optional[str] = None  # 自然语言输入
    age_group: str = "adult"
    has_children: bool = False
    price_sensitivity: float = 0.5


class FeedbackRequest(BaseModel):
    """用户反馈请求"""
    user_id: int
    feedback: str
    current_profile: dict


class POICreateRequest(BaseModel):
    """创建POI请求"""
    poi_id: str
    name: str
    category: str
    city: str
    latitude: float
    longitude: float
    rating: float = 0.0
    price_level: int = 0
    tags: List[str] = []
    description: str = ""


class UserVisitRequest(BaseModel):
    """记录用户访问请求"""
    user_id: int
    poi_id: str
    rating: Optional[float] = None
    duration: Optional[int] = None


class SimilarUsersRequest(BaseModel):
    """查找相似用户请求"""
    user_id: int
    limit: int = 5


# ==================== User Profile APIs ====================

@router.post("/profile/create")
async def create_user_profile(
    request: UserProfileCreateRequest,
    db: Session = Depends(get_db)
):
    """
    创建用户画像
    
    支持结构化输入和自然语言输入:
    - 结构化: interests, budget_level, travel_style等
    - 自然语言: user_text (如: "我喜欢历史文化，预算适中")
    """
    try:
        agent = EnhancedUserProfileAgent()
        
        context = {
            "db": db,
            "user_id": request.user_id,
            "interests": request.interests,
            "budget_level": request.budget_level,
            "travel_style": request.travel_style,
            "fitness_level": request.fitness_level,
            "group_type": request.group_type,
            "age_group": request.age_group,
            "has_children": request.has_children,
            "price_sensitivity": request.price_sensitivity,
        }
        
        # 添加自然语言输入
        if request.user_text:
            context["user_text"] = request.user_text
        
        result = await agent.run(context)
        
        profile = result.get("user_profile", {})
        
        return {
            "success": True,
            "user_id": request.user_id,
            "profile": {
                "interests": profile.get("interests", []),
                "budget_level": profile.get("budget_level"),
                "fitness_level": profile.get("fitness_level"),
                "cultural_preferences": profile.get("cultural_preferences", {}),
                "preferred_categories": profile.get("preferred_categories", []),
                "profile_scores": profile.get("profile_scores", {}),
            },
            "description": profile.get("profile_description"),
            "llm_analysis": profile.get("llm_analysis"),
            "kg_synced": profile.get("kg_synced", False),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/feedback")
async def analyze_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """分析用户反馈并推荐画像调整"""
    try:
        agent = EnhancedUserProfileAgent()
        
        result = await agent.analyze_feedback(
            user_id=request.user_id,
            feedback=request.feedback,
            current_profile=request.current_profile,
        )
        
        return {
            "success": True,
            "analysis": result,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户画像"""
    try:
        # 从数据库获取
        from app.services.user_profile_service import UserProfileService
        profile_service = UserProfileService(db)
        db_profile = profile_service.get_profile(user_id)
        
        if not db_profile:
            raise HTTPException(status_code=404, detail="用户画像不存在")
        
        # 从知识图谱获取统计
        kg_stats = None
        try:
            kg = get_kg_service()
            kg_stats = kg.get_user_stats(user_id)
        except:
            pass
        
        return {
            "success": True,
            "user_id": user_id,
            "profile": {
                "interests": db_profile.interests or [],
                "budget_level": db_profile.budget_level,
                "travel_style": db_profile.travel_style,
                "fitness_level": db_profile.fitness_level,
                "cultural_preferences": db_profile.cultural_preferences or {},
                "preferred_categories": db_profile.preferred_categories or [],
            },
            "kg_stats": kg_stats,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LLM APIs ====================

@router.post("/llm/chat")
async def chat_with_llm(
    messages: List[dict],
    temperature: float = 0.7,
    max_tokens: int = 2000
):
    """与LLM对话"""
    try:
        llm = get_llm_service()
        response = await llm.chat(messages, temperature, max_tokens)
        
        return {
            "success": True,
            "response": response,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/analyze")
async def analyze_user_input(
    user_text: str,
    structured_data: Optional[dict] = None
):
    """使用LLM分析用户输入"""
    try:
        llm = get_llm_service()
        analysis = await llm.analyze_user_input(user_text, structured_data)
        
        return {
            "success": True,
            "analysis": analysis,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/embed")
async def generate_embedding(text: str):
    """生成文本嵌入向量"""
    try:
        llm = get_llm_service()
        embedding = await llm.generate_embedding(text)
        
        return {
            "success": True,
            "embedding": embedding,
            "dimension": len(embedding),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Knowledge Graph APIs ====================

@router.post("/kg/poi/create")
async def create_poi(request: POICreateRequest):
    """创建POI节点"""
    try:
        kg = get_kg_service()
        
        poi_data = {
            "name": request.name,
            "category": request.category,
            "city": request.city,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "rating": request.rating,
            "price_level": request.price_level,
            "tags": request.tags,
            "description": request.description,
        }
        
        kg.create_poi(request.poi_id, poi_data)
        
        return {
            "success": True,
            "poi_id": request.poi_id,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/user/visit")
async def record_visit(request: UserVisitRequest):
    """记录用户访问"""
    try:
        kg = get_kg_service()
        kg.record_visit(
            user_id=request.user_id,
            poi_id=request.poi_id,
            rating=request.rating,
            duration=request.duration,
        )
        
        return {
            "success": True,
            "message": "访问记录已创建",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/user/like")
async def record_like(
    user_id: int,
    poi_id: str
):
    """记录用户点赞"""
    try:
        kg = get_kg_service()
        kg.record_like(user_id, poi_id)
        
        return {
            "success": True,
            "message": "点赞记录已创建",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/user/{user_id}/stats")
async def get_user_kg_stats(user_id: int):
    """获取用户在知识图谱中的统计信息"""
    try:
        kg = get_kg_service()
        stats = kg.get_user_stats(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "stats": stats,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/user/{user_id}/history")
async def get_user_poi_history(
    user_id: int,
    limit: int = 50
):
    """获取用户的POI访问历史"""
    try:
        kg = get_kg_service()
        history = kg.get_user_poi_history(user_id, limit)
        
        return {
            "success": True,
            "user_id": user_id,
            "history": history,
            "count": len(history),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kg/similar-users")
async def find_similar_users(request: SimilarUsersRequest):
    """查找相似用户"""
    try:
        kg = get_kg_service()
        similar = kg.get_similar_users(request.user_id, request.limit)
        
        return {
            "success": True,
            "user_id": request.user_id,
            "similar_users": similar,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kg/recommendations/{user_id}")
async def get_recommendations(
    user_id: int,
    limit: int = 10
):
    """基于知识图谱获取POI推荐"""
    try:
        kg = get_kg_service()
        recommendations = kg.get_recommended_pois(user_id, limit)
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendations": recommendations,
            "count": len(recommendations),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Vector Similarity APIs ====================

@router.get("/vector/search/{user_id}")
async def search_similar_users(
    user_id: int,
    limit: int = 5
):
    """基于向量相似度查找相似用户"""
    try:
        # 获取当前用户画像
        from app.services.user_profile_service import UserProfileService
        from app.db.session import SessionLocal
        
        db = SessionLocal()
        try:
            profile_service = UserProfileService(db)
            db_profile = profile_service.get_profile(user_id)
            
            if not db_profile:
                raise HTTPException(status_code=404, detail="用户画像不存在")
            
            profile_dict = {
                "interests": db_profile.interests or [],
                "budget_level": db_profile.budget_level,
                "travel_style": db_profile.travel_style,
                "fitness_level": db_profile.fitness_level,
                "group_type": db_profile.group_type,
            }
        finally:
            db.close()
        
        # 搜索相似用户
        vector_service = get_vector_service()
        if not vector_service.is_connected():
            raise HTTPException(status_code=503, detail="向量数据库未连接")
        
        similar = vector_service.search_similar_users(profile_dict, limit)
        
        return {
            "success": True,
            "user_id": user_id,
            "similar_users": similar,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== System Status APIs ====================

@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    status = {
        "llm": False,
        "knowledge_graph": False,
        "vector_db": False,
    }
    
    # 检查LLM
    try:
        from app.config import settings
        if settings.LLM_API_KEY:
            status["llm"] = True
            status["llm_provider"] = settings.LLM_PROVIDER
    except:
        pass
    
    # 检查知识图谱
    try:
        kg = get_kg_service()
        status["knowledge_graph"] = True
    except:
        pass
    
    # 检查向量数据库
    try:
        vs = get_vector_service()
        status["vector_db"] = vs.is_connected()
    except:
        pass
    
    return {
        "success": True,
        "status": status,
    }
