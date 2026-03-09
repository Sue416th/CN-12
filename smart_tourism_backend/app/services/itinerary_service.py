import math
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.itinerary import Itinerary, ItineraryItem
from app.models.poi import POI
from app.services.poi_service import POIService
from app.services.recommendation_optimizer import RecommendationOptimizer


class ItineraryService:
    """
    智能行程规划服务
    1. 基于用户偏好和约束进行POI筛选
    2. 考虑距离、时间、评分等多维度优化
    3. 生成科学合理的每日行程
    """

    TIME_SLOTS = [
        {"name": "morning", "start": (9, 0), "end": (12, 0), "duration": 180},
        {"name": "lunch", "start": (12, 0), "end": (14, 0), "duration": 120},
        {"name": "afternoon", "start": (14, 0), "end": (17, 0), "duration": 180},
        {"name": "dinner", "start": (18, 0), "end": (20, 0), "duration": 120},
        {"name": "evening", "start": (20, 0), "end": (21, 30), "duration": 90},
    ]

    def __init__(self, db: Session):
        self.db = db
        self.poi_service = POIService(db)

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点之间的直线距离（公里）"""
        R = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _get_pois_for_city(self, city: str) -> List[POI]:
        """获取城市POI，自动初始化示例数据"""
        pois = self.poi_service.get_by_city(city)
        if not pois:
            pois = self.poi_service._ensure_sample_pois()
            pois = [p for p in pois if p.city == city]
        return pois

    def _filter_pois_by_interests(
        self, pois: List[POI], interests: List[str], strict: bool = False
    ) -> List[POI]:
        """根据兴趣筛选POI"""
        if not interests:
            return pois

        normalized_interests = [i.lower().strip() for i in interests]
        category_map = {
            # 中文关键词
            "文化": "culture", "历史": "culture", "博物馆": "culture", "古迹": "culture", "园林": "culture",
            "自然": "nature", "湿地": "nature", "公园": "nature", "山": "nature", "湖": "nature",
            "美食": "food", "小吃": "food", "餐厅": "food",
            "宗教": "religion", "寺庙": "religion", "教堂": "religion",
            "娱乐": "entertainment", "演出": "entertainment", "主题公园": "entertainment",
            "购物": "shopping", "逛街": "shopping",
            # 英文关键词
            "culture": "culture", "history": "culture", "museum": "culture", "heritage": "culture",
            "nature": "nature", "park": "nature", "mountain": "nature", "lake": "nature",
            "food": "food", "restaurant": "food", "cuisine": "food",
            "religion": "religion", "temple": "religion", "church": "religion",
            "entertainment": "entertainment", "show": "entertainment", "theme park": "entertainment",
            "shopping": "shopping",
        }

        matched_pois = []
        for poi in pois:
            categories = [poi.category or "", poi.sub_category or ""]
            tags = [t.lower() for t in (poi.tags or [])]

            for interest in normalized_interests:
                if interest in category_map:
                    target_cat = category_map[interest]
                    if target_cat in categories:
                        matched_pois.append(poi)
                        break
                else:
                    if any(interest in c.lower() for c in categories if c):
                        matched_pois.append(poi)
                        break
                    if any(interest in t for t in tags):
                        matched_pois.append(poi)
                        break

        if not matched_pois and strict:
            return pois
        return matched_pois if matched_pois else pois

    def _filter_pois_by_budget(
        self, pois: List[POI], budget_level: str
    ) -> List[POI]:
        """根据预算筛选POI"""
        budget_map = {"low": 1, "medium": 2, "high": 3}
        max_price = budget_map.get(budget_level.lower(), 2)

        if budget_level.lower() == "low":
            return [p for p in pois if p.price_level in [0, 1]]
        elif budget_level.lower() == "high":
            return pois
        else:
            return [p for p in pois if p.price_level <= max_price]

    def _sort_pois_by_rating(self, pois: List[POI]) -> List[POI]:
        """按评分排序"""
        return sorted(pois, key=lambda x: (x.rating or 0, x.review_count or 0), reverse=True)

    def _sort_pois_by_profile(
        self,
        pois: List[POI],
        cultural_preferences: Dict[str, float],
        preferred_categories: List[str],
    ) -> List[POI]:
        """
        根据用户画像进行个性化POI排序
        
        - 优先用户偏好类别的POI
        - 考虑文化偏好维度
        - 综合评分和偏好权重
        """
        if not cultural_preferences and not preferred_categories:
            return self._sort_pois_by_rating(pois)

        def get_profile_score(poi: POI) -> float:
            score = 0.0

            # 1. 基础评分 (0-5)
            base_rating = poi.rating or 0

            # 2. 类别偏好分数 (0-1)
            category_score = 0.0
            poi_category = poi.category or ""

            # 检查是否在用户偏好的类别中
            if preferred_categories:
                for cat in preferred_categories:
                    if cat.lower() in poi_category.lower():
                        category_score = 1.0
                        break

            # 3. 文化偏好分数 (0-1)
            cultural_score = 0.0
            poi_tags = [t.lower() for t in (poi.tags or [])]

            # 文化偏好映射到POI标签
            cultural_to_tags = {
                "history": ["history", "historical", "ancient", "heritage"],
                "art": ["art", "museum", "gallery", "exhibition"],
                "tradition": ["traditional", "folk", "craft"],
                "modern": ["modern", "contemporary", "architecture"],
                "nature": ["nature", "park", "garden", "lake", "mountain"],
                "food_culture": ["food", "restaurant", "cuisine", "market"],
                "religion": ["temple", "church", "shrine", "religious"],
                "nightlife": ["night", "bar", "entertainment"],
            }

            for cultural_dim, weight in cultural_preferences.items():
                tags = cultural_to_tags.get(cultural_dim, [])
                if any(tag in poi_tags for tag in tags):
                    cultural_score += weight

            # 综合分数：评分 * 0.3 + 类别匹配 * 0.4 + 文化匹配 * 0.3
            final_score = (
                base_rating * 0.3 +
                category_score * 0.4 +
                min(cultural_score, 1.0) * 0.3
            )

            # 添加随机因子避免完全相同的排序
            import random
            final_score += random.uniform(0, 0.1)

            return final_score

        return sorted(pois, key=get_profile_score, reverse=True)

    def _calculate_daily_pois_count(
        self,
        travel_style: str,
        fitness_level: str,
        group_type: str,
    ) -> int:
        """
        根据用户旅行风格和体能计算每日景点数量
        """
        base_count = 4  # 默认每天4个景点

        # 旅行风格调整
        if travel_style == "relaxed":
            base_count -= 1
        elif travel_style == "intensive":
            base_count += 1

        # 体能调整
        if fitness_level == "low":
            base_count -= 1
        elif fitness_level == "high":
            base_count += 1

        # 团队类型调整
        if group_type == "family":
            base_count -= 1  # 家庭游通常节奏较慢
        elif group_type == "solo":
            base_count += 0  # 独自旅行可以更灵活

        return max(2, min(base_count, 6))  # 限制在2-6个之间

    def _calculate_max_daily_hours(
        self,
        fitness_level: str,
        group_type: str,
    ) -> float:
        """
        根据用户体能和团队类型计算每日最大游玩时间（小时）
        """
        base_hours = 8.0  # 默认8小时

        # 体能调整
        if fitness_level == "low":
            base_hours = 5.0
        elif fitness_level == "medium":
            base_hours = 7.0
        elif fitness_level == "high":
            base_hours = 10.0

        # 团队类型调整
        if group_type == "family":
            base_hours = min(base_hours, 6.0)  # 家庭游通常更轻松
        elif group_type == "couple":
            base_hours += 1.0  # 情侣游可以更浪漫悠闲

        return base_hours

    def _sort_pois_by_feedback(
        self,
        pois: List[POI],
        user_id: int,
    ) -> List[POI]:
        """
        基于用户行为反馈排序POI
        - 增加用户喜欢的类别的POI权重
        - 降低用户已访问过很多次的POI权重
        """
        try:
            optimizer = RecommendationOptimizer(self.db)
            feedback_data = optimizer.get_poi_scores(user_id)
            poi_scores = feedback_data.get("poi_scores", {})
            category_scores = feedback_data.get("category_scores", {})

            def get_feedback_score(poi: POI) -> float:
                score = 1.0

                # 1. POI访问历史分数
                if poi.id in poi_scores:
                    score *= poi_scores[poi.id]

                # 2. 类别偏好分数
                if poi.category and poi.category in category_scores:
                    score *= category_scores[poi.category]

                return score

            return sorted(pois, key=get_feedback_score, reverse=True)
        except Exception as e:
            # 如果反馈服务出错，回退到评分排序
            print(f"Warning: Feedback sorting failed: {e}")
            return self._sort_pois_by_rating(pois)

    def _sort_pois_by_distance(
        self, pois: List[POI], center_lat: float, center_lon: float
    ) -> List[POI]:
        """按距离排序"""
        def get_distance(poi):
            if poi.latitude and poi.longitude:
                return self._haversine_distance(
                    center_lat, center_lon, poi.latitude, poi.longitude
                )
            return float('inf')
        return sorted(pois, key=get_distance)

    def _select_daily_pois(
        self,
        available_pois: List[POI],
        day_index: int,
        prefer_nearby: bool = False,
        center_lat: float = None,
        center_lon: float = None,
        max_pois: int = 4,
    ) -> List[POI]:
        """为每一天选择POI，确保多样性"""
        if not available_pois:
            return []

        # 限制每天的POI数量
        max_pois = max(1, min(max_pois, 8))

        selected = []
        categories_used = set()

        for poi in available_pois:
            if len(selected) >= max_pois:
                break

            category = poi.category
            if category not in categories_used or len(selected) < 2:
                selected.append(poi)
                categories_used.add(category)

        remaining = [p for p in available_pois if p not in selected]
        while len(selected) < max_pois and remaining:
            remaining.sort(key=lambda x: x.rating or 0, reverse=True)
            next_poi = remaining.pop(0)
            if next_poi.category not in categories_used or len(selected) < max_pois - 1:
                selected.append(next_poi)
                if len(selected) <= max_pois - 1:
                    categories_used.add(next_poi.category)

        return selected[:max_pois]

    def _optimize_daily_order(
        self, pois: List[POI], start_lat: float, start_lon: float
    ) -> List[POI]:
        """优化每日行程顺序（贪心最近邻）"""
        if not pois:
            return pois
        if len(pois) == 1:
            return pois

        ordered = []
        current_lat = start_lat
        current_lon = start_lon
        remaining = pois.copy()

        while remaining:
            nearest = min(remaining, key=lambda p: (
                float('inf') if not (p.latitude and p.longitude)
                else self._haversine_distance(current_lat, current_lon, p.latitude, p.longitude)
            ))
            ordered.append(nearest)
            remaining.remove(nearest)
            if nearest.latitude and nearest.longitude:
                current_lat = nearest.latitude
                current_lon = nearest.longitude

        return ordered

    def _assign_time_slots(
        self, pois: List[POI], base_date: datetime
    ) -> List[Dict[str, Any]]:
        """为POI分配时间槽"""
        if not pois:
            return []

        assignments = []
        time_slots = [
            ("morning", 9, 12),
            ("lunch", 12, 14),
            ("afternoon", 14, 17),
            ("dinner", 18, 20),
            ("evening", 20, 21),
        ]

        used_categories = set()
        food_pois = [p for p in pois if p.category == "food"]
        non_food_pois = [p for p in pois if p.category != "food"]

        for idx, poi in enumerate(pois):
            if poi.category == "food" or not non_food_pois:
                if food_pois:
                    food_poi = food_pois.pop(0)
                    slot_idx = 1 if idx < 2 else 3
                    start_h, end_h = time_slots[slot_idx][1], time_slots[slot_idx][2]
                    assignments.append({
                        "poi": food_poi,
                        "start_hour": start_h,
                        "end_hour": end_h,
                    })
                    continue

            if idx < len(time_slots):
                slot_name, start_h, end_h = time_slots[idx]
            else:
                slot_name, start_h, end_h = "evening", 20, 21

            duration = poi.estimated_duration or 120
            end_h = min(start_h + duration // 60, 22)

            assignments.append({
                "poi": poi,
                "start_hour": start_h,
                "end_hour": end_h,
            })

        return assignments

    def generate_itinerary(
        self,
        *,
        user_id: int,
        start_date,
        end_date,
        budget_level: str = "medium",
        interests: List[str] = [],
        city: str = "Hangzhou",
        # 个性化推荐参数
        travel_style: str = "balanced",
        fitness_level: str = "medium",
        group_type: str = "solo",
        cultural_preferences: Dict[str, float] = None,
        preferred_categories: List[str] = None,
    ) -> Dict[str, Any]:
        """生成智能行程"""
        if not start_date or not end_date:
            end_date = start_date or end_date

        days = 1
        if start_date and end_date and end_date > start_date:
            days = (end_date.date() - start_date.date()).days + 1

        # 初始化个性化参数
        if cultural_preferences is None:
            cultural_preferences = {}
        if preferred_categories is None:
            preferred_categories = []

        pois = self._get_pois_for_city(city)
        pois = self._filter_pois_by_interests(pois, interests)
        pois = self._filter_pois_by_budget(pois, budget_level)

        # 使用个性化推荐排序（优先使用用户画像数据）
        if cultural_preferences or preferred_categories:
            pois = self._sort_pois_by_profile(pois, cultural_preferences, preferred_categories)
        elif user_id:
            # 如果有用户历史行为，使用反馈优化排序
            try:
                optimizer = RecommendationOptimizer(self.db)
                feedback_data = optimizer.get_poi_scores(user_id)
                if feedback_data.get("poi_scores") or feedback_data.get("category_scores"):
                    pois = self._sort_pois_by_feedback(pois, user_id)
                else:
                    pois = self._sort_pois_by_rating(pois)
            except Exception:
                pois = self._sort_pois_by_rating(pois)
        else:
            pois = self._sort_pois_by_rating(pois)

        # 如果过滤后没有符合条件的POI，返回所有POI
        if not pois:
            pois = self.poi_service.get_by_city(city)
            if not pois:
                pois = self.poi_service._ensure_sample_pois()
            pois = self._sort_pois_by_rating(pois)

        # 确保 pois 不为空
        if not pois:
            return {"error": f"无法获取景点数据", "items": []}

        first_poi = pois[0]
        center_lat = first_poi.latitude if first_poi.latitude else 30.0
        center_lon = first_poi.longitude if first_poi.longitude else 120.0

        itinerary = Itinerary(user_id=user_id, name=f"{city} {days}-Day Smart Trip", city=city)
        self.db.add(itinerary)
        self.db.flush()
        itinerary_id = itinerary.id

        planned_items: List[Tuple[ItineraryItem, POI]] = []
        day_pois_list = []

        # 根据用户体能和旅行风格调整行程安排
        max_daily_pois = self._calculate_daily_pois_count(travel_style, fitness_level, group_type)
        max_daily_hours = self._calculate_max_daily_hours(fitness_level, group_type)

        for day_index in range(days):
            day_base = start_date + timedelta(days=day_index)

            if day_index == 0:
                daily_pois = self._select_daily_pois(pois, day_index, prefer_nearby=True, max_pois=max_daily_pois)
            else:
                if day_pois_list:
                    last_poi = day_pois_list[-1][-1]
                    center_lat = last_poi.latitude or center_lat
                    center_lon = last_poi.longitude or center_lon

                remaining_pois = [p for p in pois if p not in [item for sublist in day_pois_list for item in sublist]]
                daily_pois = self._select_daily_pois(remaining_pois, day_index, max_pois=max_daily_pois) if remaining_pois else []

            daily_pois = self._optimize_daily_order(daily_pois, center_lat, center_lon)
            day_pois_list.append(daily_pois)

            assignments = self._assign_time_slots(daily_pois, day_base)

            for assignment in assignments:
                poi = assignment["poi"]
                start_h = assignment["start_hour"]
                end_h = assignment["end_hour"]

                start_time = day_base.replace(hour=start_h, minute=0, second=0, microsecond=0)
                end_time = day_base.replace(hour=end_h, minute=0, second=0, microsecond=0)

                note = poi.highlight or f"建议游玩{poi.estimated_duration or 120}分钟"

                item = ItineraryItem(
                    itinerary_id=itinerary_id,
                    poi_id=poi.id,
                    start_time=start_time,
                    end_time=end_time,
                    note=note,
                )
                self.db.add(item)
                planned_items.append((item, poi))

        self.db.commit()
        self.db.refresh(itinerary)

        return {
            "itinerary_id": itinerary_id,
            "user_id": itinerary.user_id,
            "name": itinerary.name,
            "city": city,
            "days": days,
            "budget_level": budget_level,
            "interests": interests,
            "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
            "items": [
                {
                    "poi_id": item.poi_id,
                    "poi_name": poi.name,
                    "category": poi.category,
                    "rating": poi.rating or 0,
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                    "note": item.note,
                }
                for (item, poi) in planned_items
            ],
        }

    def optimize_itinerary(self, itinerary_id: int) -> Dict[str, Any]:
        """优化现有行程"""
        itinerary = self.db.query(Itinerary).filter(Itinerary.id == itinerary_id).first()
        if not itinerary:
            return {"error": "行程不存在"}

        items = list(itinerary.items)
        if not items:
            return {"error": "行程为空"}

        pois = [self.db.query(POI).filter(POI.id == item.poi_id).first() for item in items]
        pois = [p for p in pois if p and p.latitude and p.longitude]

        if len(pois) < 2:
            return {"error": "POI数据不足以优化"}

        start_lat = pois[0].latitude if pois else None
        start_lon = pois[0].longitude if pois else None
        if start_lat is None or start_lon is None:
            return {"error": "POI坐标数据缺失，无法优化"}

        optimized_order = self._optimize_daily_order(pois, start_lat, start_lon)

        reordered_items = []
        for idx, poi in enumerate(optimized_order):
            original_item = next((item for item in items if item.poi_id == poi.id), None)
            if original_item:
                original_item.start_time = items[0].start_time + timedelta(hours=idx * 2)
                original_item.end_time = items[0].start_time + timedelta(hours=idx * 2 + 2)
                reordered_items.append(original_item)

        self.db.commit()
        self.db.refresh(itinerary)

        return {
            "message": "行程已优化",
            "itinerary_id": itinerary_id,
            "city": itinerary.city,
            "items": [
                {
                    "poi_id": item.poi_id,
                    "poi_name": next((p.name for p in optimized_order if p.id == item.poi_id), ""),
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                }
                for item in reordered_items
            ],
        }

    def list_by_user(self, user_id: int, limit: int = 20) -> list:
        """获取用户的行程列表"""
        rows = (
            self.db.query(Itinerary)
            .filter(Itinerary.user_id == user_id)
            .order_by(Itinerary.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "name": r.name,
                "city": r.city,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    def delete_itinerary(self, itinerary_id: int, user_id: int) -> bool:
        """删除行程"""
        itinerary = (
            self.db.query(Itinerary)
            .filter(Itinerary.id == itinerary_id, Itinerary.user_id == user_id)
            .first()
        )
        if not itinerary:
            return False
        self.db.delete(itinerary)
        self.db.commit()
        return True

    def get_by_id(self, itinerary_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """获取行程详情"""
        from app.agents.culture_agent import CULTURE_INFO

        q = self.db.query(Itinerary).filter(Itinerary.id == itinerary_id)
        if user_id is not None:
            q = q.filter(Itinerary.user_id == user_id)
        itinerary = q.first()
        if not itinerary:
            return None

        pois = {
            p.id: p
            for p in self.db.query(POI)
            .filter(POI.id.in_([i.poi_id for i in itinerary.items]))
            .all()
        }

        items = []
        first_item_start_time = None
        for item in itinerary.items:
            poi = pois.get(item.poi_id)
            poi_name = poi.name if poi else ""
            culture_info = CULTURE_INFO.get(poi_name, {}) if poi_name else {}

            item_data = {
                "poi_id": item.poi_id,
                "poi_name": poi_name,
                "category": poi.category if poi else "",
                "rating": poi.rating if poi else 0,
                "address": poi.address if poi else "",
                "start_time": item.start_time,
                "end_time": item.end_time,
                "note": item.note,
                "culture_info": culture_info if culture_info else None,
            }

            # Add location data if available
            if poi and poi.latitude and poi.longitude:
                item_data["location"] = {
                    "lat": poi.latitude,
                    "lng": poi.longitude,
                }

            items.append(item_data)

            # 获取行程开始日期
            if first_item_start_time is None and item.start_time:
                first_item_start_time = item.start_time

        # 实时获取天气数据 - 每次都重新获取最新的天气
        weather_info = {}
        weather_advice = []
        try:
            import asyncio
            from datetime import datetime, timedelta

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 获取7天预报 - 过滤乱码或无效城市名
            city_raw = itinerary.city or ""
            city = city_raw if city_raw and len(city_raw.strip()) > 1 and not city_raw.startswith("??") else "Hangzhou"

            weather_data = loop.run_until_complete(weather_api.get_weather(city, days=7))

            # 强制确保返回数据包含forecast
            if "forecast" not in weather_data:
                weather_data["forecast"] = []

            weather_info = weather_data

            # 生成天气建议（基于实际日期的天气预报）
            today = datetime.now().date()
            start_date = None

            if first_item_start_time:
                if isinstance(first_item_start_time, str):
                    try:
                        start_date = datetime.strptime(first_item_start_time[:19], "%Y-%m-%d %H:%M:%S").date()
                    except:
                        start_date = today
                else:
                    start_date = first_item_start_time.date() if hasattr(first_item_start_time, 'date') else today

            # 根据行程第一天的天气生成建议
            if start_date and weather_data.get("forecast"):
                day_diff = (start_date - today).days
                if 0 <= day_diff < len(weather_data["forecast"]):
                    today_weather = weather_data["forecast"][day_diff]
                else:
                    today_weather = weather_data.get("today", {})
            else:
                today_weather = weather_data.get("today", {})
            temp = today_weather.get("temp", 20)
            weather_type = today_weather.get("weather", "Sunny")

            advice = []
            if temp < 10:
                advice.append("Temperature is low, please bring warm clothing")
            elif temp > 28:
                advice.append("Temperature is high, please stay cool")

            if "雨" in weather_type:
                advice.append("Rain expected, please bring umbrella. Consider indoor activities.")
            elif "雪" in weather_type:
                advice.append("Snow expected, please watch for slippery roads")

            aqi = today_weather.get("aqi", "良")
            if aqi == "优" or aqi == "Good" or aqi == "Excellent":
                advice.append("Excellent air quality, great for outdoor activities")
            elif "污染" in str(aqi) or aqi in ["轻度污染", "中度污染", "重度污染"]:
                advice.append(f"Air quality: {aqi}, recommend wearing mask")

            if not advice:
                advice.append("Good weather, perfect for travel")

            weather_advice = advice
        except Exception as e:
            import traceback
            print(f"获取天气失败: {e}")
            traceback.print_exc()

        return {
            "itinerary_id": itinerary.id,
            "user_id": itinerary.user_id,
            "name": itinerary.name,
            "city": itinerary.city,
            "weather_info": weather_info,
            "weather_advice": weather_advice,
            "items": items,
        }
