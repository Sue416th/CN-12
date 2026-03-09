from typing import Any, Dict, List
import asyncio

from app.agents.user_profile_agent import UserProfileAgent
from app.agents.enhanced_user_profile_agent import EnhancedUserProfileAgent
from app.agents.culture_agent import CultureAgent
from app.agents.weather_agent import WeatherAgent
from app.agents.itinerary_planner_agent import ItineraryPlannerAgent
from app.services.agent_monitor import get_monitor


class AgentOrchestrator:
    """
    Agent编排器 - 协调多个Agent完成复杂的行程规划任务
    流程：
    1. UserProfileAgent - 分析用户偏好 (支持增强版)
    2. ItineraryPlannerAgent - 生成基础行程
    3. CultureAgent - 丰富文化内涵
    4. WeatherAgent - 考虑天气因素
    
    支持两种用户画像Agent:
    - UserProfileAgent: 基础版 (基于规则)
    - EnhancedUserProfileAgent: 增强版 (LLM + 知识图谱)
    """

    def __init__(self, use_enhanced_profile: bool = True):
        """
        初始化编排器
        
        Args:
            use_enhanced_profile: 是否使用增强版用户画像Agent (默认True)
        """
        # 根据配置选择使用基础版或增强版用户画像Agent
        if use_enhanced_profile:
            self.user_profile_agent = EnhancedUserProfileAgent()
            print("Using Enhanced User Profile Agent (LLM + Knowledge Graph)")
        else:
            self.user_profile_agent = UserProfileAgent()
            print("Using Basic User Profile Agent")
        
        self.itinerary_planner_agent = ItineraryPlannerAgent()
        self.culture_agent = CultureAgent()
        self.weather_agent = WeatherAgent()
        self.monitor = get_monitor()
        
        # 标记是否使用增强版
        self.use_enhanced_profile = use_enhanced_profile

    async def run_pre_trip_flow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行完整的行程规划流程
        """
        # 记录总流程开始
        flow_start_time = self.monitor.record_start("pre_trip_flow") if self.monitor else None

        try:
            # 1. UserProfileAgent
            exec_id = self.monitor.record_start("user_profile") if self.monitor else None
            try:
                context = await self.user_profile_agent.run(context)
                if self.monitor:
                    self.monitor.record_end("user_profile", exec_id, success=True)
            except Exception as e:
                if self.monitor:
                    self.monitor.record_end("user_profile", exec_id, success=False, error=str(e))
                raise

            # 2. ItineraryPlannerAgent
            exec_id = self.monitor.record_start("itinerary_planner") if self.monitor else None
            try:
                context = await self.itinerary_planner_agent.run(context)
                if self.monitor:
                    self.monitor.record_end("itinerary_planner", exec_id, success=True)
            except Exception as e:
                if self.monitor:
                    self.monitor.record_end("itinerary_planner", exec_id, success=False, error=str(e))
                raise

            # 将行程的开始日期传递给后续Agent
            itinerary = context.get("itinerary", {})
            if "start_date" in itinerary:
                context["start_date"] = itinerary["start_date"]
            elif "items" in itinerary and itinerary["items"]:
                # 从第一个行程项获取开始日期
                first_item = itinerary["items"][0]
                if first_item.get("start_time"):
                    context["start_date"] = str(first_item["start_time"])[:10]

            # 将完整的用户画像信息传递给后续Agent
            if "user_profile" in context:
                profile = context["user_profile"]
                context["profile_info"] = {
                    "budget_info": profile.get("budget_info", {}),
                    "fitness_info": profile.get("fitness_info", {}),
                    "cultural_preferences": profile.get("cultural_preferences", {}),
                    "preferred_categories": profile.get("preferred_categories", []),
                    "profile_scores": profile.get("profile_scores", {}),
                }

            # 3. CultureAgent
            exec_id = self.monitor.record_start("culture") if self.monitor else None
            try:
                context = await self.culture_agent.run(context)
                if self.monitor:
                    self.monitor.record_end("culture", exec_id, success=True)
            except Exception as e:
                if self.monitor:
                    self.monitor.record_end("culture", exec_id, success=False, error=str(e))
                raise

            # 4. WeatherAgent
            exec_id = self.monitor.record_start("weather") if self.monitor else None
            try:
                context = await self.weather_agent.run(context)
                if self.monitor:
                    self.monitor.record_end("weather", exec_id, success=True)
            except Exception as e:
                if self.monitor:
                    self.monitor.record_end("weather", exec_id, success=False, error=str(e))
                raise

            # 记录总流程完成
            if self.monitor and flow_start_time:
                self.monitor.record_end("pre_trip_flow", flow_start_time, success=True)

            return context

        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            context["error"] = str(e)
            context["error_detail"] = error_detail
            context["error_stage"] = "unknown"
            
            # 记录流程失败
            if self.monitor and flow_start_time:
                self.monitor.record_end("pre_trip_flow", flow_start_time, success=False, error=str(e))
            
            return context

    async def generate_itinerary(
        self,
        db: Any,
        user_id: int,
        city: str,
        start_date,
        end_date,
        interests: List[str],
        budget_level: str = "medium",
        travel_style: str = "balanced",
        group_type: str = "solo",
    ) -> Dict[str, Any]:
        """
        生成完整行程的入口方法
        """
        context = {
            "db": db,
            "user_id": user_id,
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "interests": interests,
            "budget_level": budget_level,
            "travel_style": travel_style,
            "group_type": group_type,
        }

        result = await self.run_pre_trip_flow(context)

        return result.get("itinerary", {})

    def get_agent_status(self) -> Dict[str, str]:
        """获取各Agent状态"""
        return {
            "user_profile": "active",
            "itinerary_planner": "active",
            "culture": "active",
            "weather": "active",
            "enhanced_mode": self.use_enhanced_profile,
        }

    async def get_user_profile_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取用户画像详细信息 (增强版)
        
        返回:
        - 用户画像数据
        - LLM生成的描述 (如果有)
        - 知识图谱统计 (如果有)
        """
        result = {}
        
        # 获取基础画像
        if "user_profile" in context:
            result["profile"] = context["user_profile"]
        
        # 获取LLM描述
        if "profile_description" in context:
            result["description"] = context["profile_description"]
        
        # 获取知识图谱统计
        if self.use_enhanced_profile:
            try:
                from app.services.knowledge_graph_service import get_kg_service
                kg = get_kg_service()
                user_id = context.get("user_id")
                if user_id:
                    result["kg_stats"] = kg.get_user_stats(user_id)
            except Exception as e:
                result["kg_stats_error"] = str(e)
        
        return result

    async def analyze_feedback(
        self,
        user_id: int,
        feedback: str,
        current_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        分析用户反馈并更新画像 (仅增强版)
        
        Args:
            user_id: 用户ID
            feedback: 用户反馈文本
            current_profile: 当前用户画像
        
        Returns:
            建议的画像调整
        """
        if not self.use_enhanced_profile:
            return {"error": "增强版Agent未启用"}
        
        try:
            return await self.user_profile_agent.analyze_feedback(
                user_id=user_id,
                feedback=feedback,
                current_profile=current_profile,
            )
        except Exception as e:
            return {"error": str(e)}
