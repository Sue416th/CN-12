from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.user_profile import UserBehavior


class RecommendationOptimizer:
    """
    基于用户行为反馈优化推荐算法
    分析用户历史行为，调整POI推荐权重
    """

    def __init__(self, db: Session):
        self.db = db

    def get_poi_scores(
        self,
        user_id: int,
        category_scores: Dict[str, float] = None,
    ) -> Dict[int, float]:
        """
        基于用户行为计算POI推荐分数
        返回 {poi_id: score}
        """
        # 初始化类别权重（如果未提供）
        if category_scores is None:
            category_scores = {
                "culture": 1.0,
                "nature": 1.0,
                "food": 1.0,
                "religion": 1.0,
                "entertainment": 1.0,
                "shopping": 1.0,
            }

        # 获取用户最近的行为
        behaviors = (
            self.db.query(UserBehavior)
            .filter(UserBehavior.user_id == user_id)
            .order_by(UserBehavior.created_at.desc())
            .limit(100)
            .all()
        )

        if not behaviors:
            return {}  # 没有历史行为，返回空

        # 分析用户偏好
        poi_visit_count = {}  # poi_id -> visit count
        category_visit_count = {}  # category -> count
        rating_sum = {}  # poi_id -> sum of ratings

        for behavior in behaviors:
            poi_id = behavior.poi_id
            if poi_id:
                if poi_id not in poi_visit_count:
                    poi_visit_count[poi_id] = 0
                poi_visit_count[poi_id] += 1

            # 记录评分
            if behavior.rating:
                if poi_id not in rating_sum:
                    rating_sum[poi_id] = []
                rating_sum[poi_id].append(behavior.rating)

            # 分析extra_data中的类别
            extra = behavior.extra_data or {}
            category = extra.get("poi_category")
            if category:
                if category not in category_visit_count:
                    category_visit_count[category] = 0
                category_visit_count[category] += 1

        # 计算加权分数
        # 1. 基于访问次数：访问过的POI权重降低（避免重复推荐）
        visit_decay = 0.8  # 每次访问后权重衰减
        poi_scores = {}
        for poi_id, count in poi_visit_count.items():
            poi_scores[poi_id] = visit_decay ** count

        # 2. 基于评分：高评分POI增加权重
        for poi_id, ratings in rating_sum.items():
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                # 将评分转换为权重（4.5分以上增加权重，3分以下降低）
                rating_weight = 1.0 + (avg_rating - 3.0) * 0.2
                if poi_id in poi_scores:
                    poi_scores[poi_id] *= rating_weight

        # 3. 基于类别偏好：调整类别分数
        total_category_visits = sum(category_visit_count.values()) if category_visit_count else 1
        for category, count in category_visit_count.items():
            category_weight = count / total_category_visits
            if category in category_scores:
                category_scores[category] *= (1.0 + category_weight)

        return {
            "poi_scores": poi_scores,
            "category_scores": category_scores,
            "category_visit_count": category_visit_count,
        }

    def get_boosted_categories(
        self,
        user_id: int,
    ) -> List[str]:
        """
        获取应该提升权重的类别
        """
        scores = self.get_poi_scores(user_id)
        category_scores = scores.get("category_scores", {})

        # 返回权重高于平均值的类别
        avg_score = sum(category_scores.values()) / len(category_scores) if category_scores else 1.0
        boosted = [
            cat for cat, score in category_scores.items()
            if score > avg_score * 1.2
        ]
        return boosted

    def get_avoid_pois(
        self,
        user_id: int,
    ) -> List[int]:
        """
        获取应该避免推荐的POI（用户已访问过很多次或不喜欢的）
        """
        scores = self.get_poi_scores(user_id)
        poi_scores = scores.get("poi_scores", {})

        # 访问超过3次的POI应该降低优先级
        avoid = [poi_id for poi_id, score in poi_scores.items() if score < 0.5]
        return avoid
