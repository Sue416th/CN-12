from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent
from app.services.itinerary_service import ItineraryService


class ItineraryPlannerAgent(BaseAgent):
    """
    使用 ItineraryService 执行行程生成和持久化的 Agent。
    """

    def __init__(self):
        super().__init__(name="itinerary_planner")

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        db = context["db"]

        # 从 context 中获取约束条件
        constraints = context.get("constraints", {})
        start_date_str = constraints.get("start_date")
        end_date_str = constraints.get("end_date")
        budget_level = constraints.get("budget_level", "medium")
        interests: List[str] = constraints.get("interests", [])
        user_id = context.get("user_id")
        city = context.get("city", "Hangzhou")

        # Convert date strings to datetime objects
        from datetime import datetime
        start_date = None
        end_date = None

        if start_date_str:
            try:
                if isinstance(start_date_str, str):
                    # Handle ISO format: "2026-03-10T09:00:00"
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                else:
                    start_date = start_date_str
            except:
                start_date = None

        if end_date_str:
            try:
                if isinstance(end_date_str, str):
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                else:
                    end_date = end_date_str
            except:
                end_date = None

        # 如果日期解析失败，使用默认值
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date

        # 获取精化的兴趣标签（由 UserProfileAgent 生成）
        refined_interests = context.get("refined_interests", interests)

        # 获取用户画像信息用于个性化推荐
        travel_style = context.get("travel_style", "balanced")
        group_type = context.get("group_type", "solo")

        # 从 profile_info 获取详细的画像信息
        profile_info = context.get("profile_info", {})
        fitness_level = profile_info.get("fitness_info", {}).get("label", "medium")
        # 将标签转换为标准值
        fitness_map = {"Light": "low", "Moderate": "medium", "Active": "high"}
        fitness_level = fitness_map.get(fitness_level, "medium")

        cultural_preferences = profile_info.get("cultural_preferences", {})
        preferred_categories = profile_info.get("preferred_categories", [])

        # 验证必要参数
        if not start_date:
            context["error"] = "缺少开始日期"
            context["error_stage"] = "itinerary_planner"
            return context

        if not end_date:
            end_date = start_date

        try:
            service = ItineraryService(db)
            itinerary_dict = service.generate_itinerary(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                budget_level=budget_level,
                interests=refined_interests,
                city=city,
                # 传递个性化推荐参数
                travel_style=travel_style,
                fitness_level=fitness_level,
                group_type=group_type,
                cultural_preferences=cultural_preferences,
                preferred_categories=preferred_categories,
            )

            # 检查是否有错误
            if isinstance(itinerary_dict, dict) and itinerary_dict.get("error"):
                context["error"] = itinerary_dict["error"]
                context["error_stage"] = "itinerary_planner"
                return context

            context["itinerary"] = itinerary_dict
            return context

        except Exception as e:
            import traceback
            context["error"] = f"行程规划失败: {str(e)}"
            context["error_detail"] = traceback.format_exc()
            context["error_stage"] = "itinerary_planner"
            return context
