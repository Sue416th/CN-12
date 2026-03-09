"""
Enhanced User Profile Agent - 集成LLM和知识图谱的增强版用户画像Agent
"""
from typing import Any, Dict, List, Optional
from app.agents.base_agent import BaseAgent
from app.services.user_profile_service import UserProfileService
from app.services.vector_service import get_vector_service
from app.services.llm_service import get_llm_service
from app.services.knowledge_graph_service import get_kg_service


class EnhancedUserProfileAgent(BaseAgent):
    """
    Enhanced User Profile Agent - LLM-powered + Knowledge Graph
    
    职责：
    1. 收集和更新用户多维度信息（兴趣、预算、体能、文化偏好）
    2. 使用LLM进行自然语言理解和生成
    3. 使用知识图谱存储用户-POI关系
    4. 生成动态用户画像向量
    5. 提供个性化洞察和建议
    
    这是所有个性化服务的起点。
    """
    
    # Interest categories and their sub-tags
    INTEREST_TAXONOMY = {
        "culture": {
            "tags": ["museum", "art", "history", "heritage", "traditional", "folklore"],
            "poi_categories": ["culture", "museum", "historical"],
            "weight": 0.8
        },
        "food": {
            "tags": ["local cuisine", "night market", "restaurants", "street food", "foodie", "gourmet"],
            "poi_categories": ["food", "restaurant", "market"],
            "weight": 0.9
        },
        "nature": {
            "tags": ["park", "wetland", "mountain", "garden", "lake", "hiking", "scenery"],
            "poi_categories": ["nature", "park", "wetland"],
            "weight": 0.7
        },
        "religion": {
            "tags": ["temple", "church", "shrine", "Buddhism", "Taoism", "meditation"],
            "poi_categories": ["religion", "temple"],
            "weight": 0.6
        },
        "entertainment": {
            "tags": ["show", "theme park", "nightlife", "performance", "entertainment"],
            "poi_categories": ["entertainment", "theme park"],
            "weight": 0.8
        },
        "shopping": {
            "tags": ["market", "street", "mall", "souvenirs", "shopping", "bargaining"],
            "poi_categories": ["shopping", "market"],
            "weight": 0.5
        },
        "photography": {
            "tags": ["photo", "sunset", "landscape", "portrait", "instagram"],
            "poi_categories": ["scenic", "viewpoint"],
            "weight": 0.7
        },
        "sports": {
            "tags": ["hiking", "cycling", "running", "swimming", "adventure"],
            "poi_categories": ["sports", "adventure"],
            "weight": 0.8
        },
        "wellness": {
            "tags": ["spa", "hot spring", "yoga", "relaxation", "health"],
            "poi_categories": ["wellness", "spa"],
            "weight": 0.6
        }
    }
    
    # Budget profiles with detailed settings
    BUDGET_PROFILES = {
        "low": {
            "max_price_level": 1,
            "label": "Budget",
            "preferences": ["free", "cheap", "value"],
            "accommodation_type": "hostel",
            "dining_budget": "street food",
            "transport_preference": "public transit",
        },
        "medium": {
            "max_price_level": 2,
            "label": "Comfort",
            "preferences": ["balanced", "reasonable"],
            "accommodation_type": "hotel",
            "dining_budget": "local restaurants",
            "transport_preference": "mix",
        },
        "high": {
            "max_price_level": 3,
            "label": "Luxury",
            "preferences": ["premium", "exclusive", "VIP"],
            "accommodation_type": "luxury hotel",
            "dining_budget": "fine dining",
            "transport_preference": "private",
        }
    }
    
    # Fitness/physical ability profiles
    FITNESS_PROFILES = {
        "low": {
            "max_daily_walk_hours": 2,
            "max_daily_steps": 5000,
            "label": "Light",
            "prefers_sitting": True,
            "needs_rest_stops": True,
            "avoid_stairs": True,
            "prefer_vehicle": True,
        },
        "medium": {
            "max_daily_walk_hours": 4,
            "max_daily_steps": 10000,
            "label": "Moderate",
            "prefers_sitting": False,
            "needs_rest_stops": False,
            "avoid_stairs": False,
            "prefer_vehicle": False,
        },
        "high": {
            "max_daily_walk_hours": 6,
            "max_daily_steps": 15000,
            "label": "Active",
            "prefers_sitting": False,
            "needs_rest_stops": False,
            "avoid_stairs": False,
            "prefer_vehicle": False,
            "seeks_challenge": True,
        }
    }
    
    # Cultural preference dimensions
    CULTURAL_DIMENSIONS = {
        "history": {"weight": 0.8, "description": "Historical sites, ancient civilization"},
        "art": {"weight": 0.7, "description": "Art museums, galleries, creative spaces"},
        "tradition": {"weight": 0.8, "description": "Traditional crafts, local customs"},
        "modern": {"weight": 0.6, "description": "Modern architecture, contemporary culture"},
        "religion": {"weight": 0.5, "description": "Religious sites, spiritual experiences"},
        "nature": {"weight": 0.9, "description": "Natural landscapes, ecological sites"},
        "food_culture": {"weight": 0.9, "description": "Culinary traditions, local cuisine"},
        "nightlife": {"weight": 0.5, "description": "Evening entertainment, nightlife"},
    }
    
    def __init__(self):
        super().__init__(name="enhanced_user_profile")
        self.llm_service = None
        self.kg_service = None
        self.vector_service = None
        self._init_services()
    
    def _init_services(self):
        """Initialize optional services"""
        try:
            self.vector_service = get_vector_service()
        except Exception as e:
            print(f"Warning: Vector service not available: {e}")
        
        try:
            self.kg_service = get_kg_service()
        except Exception as e:
            print(f"Warning: Knowledge graph service not available: {e}")
        
        try:
            self.llm_service = get_llm_service()
        except Exception as e:
            print(f"Warning: LLM service not available: {e}")
    
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comprehensive user profile analysis with LLM and Knowledge Graph
        """
        db = context.get("db")
        user_id = context.get("user_id", 1)
        
        # Step 1: Extract basic profile dimensions from context
        raw_interests = context.get("interests", [])
        budget_level = context.get("budget_level", "medium")
        travel_style = context.get("travel_style", "balanced")
        group_type = context.get("group_type", "solo")
        fitness_level = context.get("fitness_level", "medium")
        
        # Extended context parameters
        age_group = context.get("age_group", "adult")
        has_children = context.get("has_children", False)
        price_sensitivity = context.get("price_sensitivity", 0.5)
        
        # Natural language input (if any)
        user_text = context.get("user_text", "")
        
        # Step 2: Use LLM to analyze natural language input if provided
        llm_analysis = None
        if user_text and self.llm_service:
            try:
                structured_data = {
                    "budget_level": budget_level,
                    "travel_style": travel_style,
                    "fitness_level": fitness_level,
                }
                llm_analysis = await self.llm_service.analyze_user_input(user_text, structured_data)
                
                # Merge LLM analysis with explicit inputs
                raw_interests = llm_analysis.get("interests", raw_interests)
                budget_level = llm_analysis.get("budget_level", budget_level)
                travel_style = llm_analysis.get("travel_style", travel_style)
                fitness_level = llm_analysis.get("fitness_level", fitness_level)
                
                context["llm_analysis"] = llm_analysis
            except Exception as e:
                print(f"Warning: LLM analysis failed: {e}")
        
        # Step 3: Build comprehensive profile using rules
        profile = self._build_comprehensive_profile(
            raw_interests=raw_interests,
            budget_level=budget_level,
            travel_style=travel_style,
            group_type=group_type,
            fitness_level=fitness_level,
            age_group=age_group,
            has_children=has_children,
            price_sensitivity=price_sensitivity,
        )
        
        # Add LLM analysis to profile if available
        if llm_analysis:
            profile["llm_analysis"] = llm_analysis
            # Generate profile description using LLM
            try:
                profile_description = await self.llm_service.generate_profile_description(profile)
                profile["profile_description"] = profile_description
            except Exception as e:
                print(f"Warning: Failed to generate profile description: {e}")
        
        # Step 4: Database operations
        if db:
            profile_service = UserProfileService(db)
            existing_profile = profile_service.get_profile(user_id)
            
            if existing_profile:
                profile = self._merge_profiles(existing_profile, profile)
            
            db_data = self._extract_db_fields(profile)
            profile_service.update_profile(user_id, db_data)
            profile["_db_data"] = db_data
        
        # Step 5: Save to Knowledge Graph
        if self.kg_service:
            try:
                profile["user_id"] = user_id
                self.kg_service.create_user(user_id, profile)
                
                for category in profile.get("preferred_categories", []):
                    strength = profile.get("interest_details", {}).get("scores", {}).get(category, 0.5)
                    self.kg_service.record_preference(user_id, category, strength)
                
                profile["kg_synced"] = True
            except Exception as e:
                print(f"Warning: Failed to sync to knowledge graph: {e}")
        
        # Step 6: Save vector to Milvus
        if self.vector_service and self.vector_service.is_connected():
            try:
                vector_id = self.vector_service.upsert_profile(user_id, profile)
                if vector_id:
                    profile["profile_vector_id"] = vector_id
                    if db:
                        profile_service.update_profile(user_id, {"profile_vector_id": vector_id})
            except Exception as e:
                print(f"Warning: Failed to save vector: {e}")
        
        # Step 7: Analyze behavior history
        if db:
            profile_service = UserProfileService(db)
            behavior_analysis = profile_service.analyze_preferences(user_id)
            if behavior_analysis:
                profile = self._enrich_from_behavior(profile, behavior_analysis)
            profile_service.update_stats(user_id)
        
        # Pass profile to context
        context["user_profile"] = profile
        context["refined_interests"] = profile.get("refined_interests", raw_interests)
        context["budget_info"] = profile.get("budget_info", {})
        context["fitness_info"] = profile.get("fitness_info", {})
        context["cultural_preferences"] = profile.get("cultural_preferences", {})
        context["preferred_categories"] = profile.get("preferred_categories", [])
        
        if "profile_description" in profile:
            context["profile_description"] = profile["profile_description"]
        
        return context
    
    async def analyze_feedback(
        self,
        user_id: int,
        feedback: str,
        current_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze user feedback and recommend profile adjustments using LLM"""
        if not self.llm_service:
            return {"suggested_changes": {}, "confidence": 0.0}
        
        try:
            result = await self.llm_service.recommend_profile_adjustments(current_profile, feedback)
            
            if self.kg_service and result.get("confidence", 0) > 0.7:
                suggested = result.get("suggested_changes", {})
                if suggested.get("interests"):
                    for interest in suggested["interests"]:
                        self.kg_service.record_preference(user_id, interest, 0.8)
                if suggested.get("cultural_preferences"):
                    for cat, strength in suggested["cultural_preferences"].items():
                        self.kg_service.record_preference(user_id, cat, strength)
            
            return result
        except Exception as e:
            print(f"Warning: Feedback analysis failed: {e}")
            return {"suggested_changes": {}, "confidence": 0.0, "error": str(e)}
    
    def _extract_db_fields(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only DB-compatible fields"""
        db_fields = [
            "interests", "budget_level", "travel_style", "group_type",
            "fitness_level", "cultural_preferences", "preferred_categories", "tags"
        ]
        return {k: v for k, v in profile.items() if k in db_fields}
    
    def _build_comprehensive_profile(
        self,
        raw_interests: List[str],
        budget_level: str,
        travel_style: str,
        group_type: str,
        fitness_level: str = "medium",
        age_group: str = "adult",
        has_children: bool = False,
        price_sensitivity: float = 0.5,
    ) -> Dict[str, Any]:
        """Build comprehensive multi-dimensional user profile"""
        
        interest_result = self._analyze_interests(raw_interests)
        budget_result = self._analyze_budget(budget_level, price_sensitivity, group_type)
        fitness_result = self._analyze_fitness(fitness_level, age_group, has_children, group_type)
        cultural_result = self._analyze_cultural_preferences(raw_interests, interest_result)
        pace_preference = self._calculate_pace(travel_style, fitness_level)
        poi_categories = self._map_to_poi_categories(interest_result, cultural_result)
        
        profile = {
            "user_id": None,
            "interests": raw_interests,
            "interest_details": interest_result,
            "refined_interests": interest_result.get("expanded_tags", []),
            "budget_level": budget_level,
            "budget_info": budget_result,
            "price_sensitivity": price_sensitivity,
            "fitness_level": fitness_level,
            "fitness_info": fitness_result,
            "age_group": age_group,
            "has_children": has_children,
            "cultural_preferences": cultural_result,
            "travel_style": travel_style,
            "pace_preference": pace_preference,
            "group_type": group_type,
            "preferred_categories": poi_categories,
            "tags": raw_interests,
            "profile_scores": self._calculate_profile_scores(
                interest_result, budget_result, fitness_result, cultural_result
            ),
        }
        
        profile["_db_data"] = self._extract_db_fields(profile)
        
        return profile
    
    def _analyze_interests(self, raw_interests: List[str]) -> Dict[str, Any]:
        """Detailed interest analysis with taxonomy"""
        if not raw_interests:
            return {"primary": [], "expanded_tags": [], "categories": [], "scores": {}}
        
        primary_interests = []
        expanded_tags = []
        categories = set()
        scores = {}
        
        for interest in raw_interests:
            interest_lower = interest.lower()
            primary_interests.append(interest_lower)
            
            if interest_lower in self.INTEREST_TAXONOMY:
                info = self.INTEREST_TAXONOMY[interest_lower]
                expanded_tags.extend(info["tags"])
                categories.update(info["poi_categories"])
                scores[interest_lower] = info["weight"]
            else:
                expanded_tags.append(interest_lower)
                scores[interest_lower] = 0.5
        
        return {
            "primary": primary_interests,
            "expanded_tags": list(set(expanded_tags)),
            "categories": list(categories),
            "scores": scores,
        }
    
    def _analyze_budget(
        self,
        budget_level: str,
        price_sensitivity: float,
        group_type: str,
    ) -> Dict[str, Any]:
        """Detailed budget analysis"""
        base_profile = self.BUDGET_PROFILES.get(
            budget_level.lower(), 
            self.BUDGET_PROFILES["medium"]
        ).copy()
        
        adjusted_level = budget_level.lower()
        if price_sensitivity > 0.7:
            adjusted_level = "low"
        elif price_sensitivity < 0.3:
            adjusted_level = "high"
        
        if adjusted_level != budget_level.lower():
            base_profile = self.BUDGET_PROFILES.get(adjusted_level, base_profile).copy()
            base_profile["adjusted"] = True
            base_profile["original"] = budget_level
        
        if group_type == "family":
            base_profile["dining_budget"] = "family restaurant"
            base_profile["group_discount"] = True
        elif group_type == "solo":
            base_profile["dining_budget"] = "solo-friendly"
        
        base_profile["price_sensitivity"] = price_sensitivity
        return base_profile
    
    def _analyze_fitness(
        self,
        fitness_level: str,
        age_group: str,
        has_children: bool,
        group_type: str,
    ) -> Dict[str, Any]:
        """Detailed fitness analysis"""
        base_profile = self.FITNESS_PROFILES.get(
            fitness_level.lower(),
            self.FITNESS_PROFILES["medium"]
        ).copy()
        
        if age_group == "senior":
            base_profile["max_daily_walk_hours"] = max(1, base_profile["max_daily_walk_hours"] - 1)
            base_profile["max_daily_steps"] = int(base_profile["max_daily_steps"] * 0.7)
            base_profile["needs_rest_stops"] = True
            base_profile["avoid_stairs"] = True
            base_profile["age_adjusted"] = True
        elif age_group == "youth":
            base_profile["max_daily_walk_hours"] = min(8, base_profile["max_daily_walk_hours"] + 1)
            base_profile["max_daily_steps"] = int(base_profile["max_daily_steps"] * 1.2)
        
        if has_children or group_type == "family":
            base_profile["needs_child_friendly"] = True
            base_profile["needs_rest_stops"] = True
            base_profile["prefer_vehicle"] = True
            base_profile["max_daily_walk_hours"] = max(1, base_profile["max_daily_walk_hours"] - 1)
        
        base_profile["energy_score"] = base_profile["max_daily_walk_hours"] / 6
        
        return base_profile
    
    def _analyze_cultural_preferences(
        self,
        raw_interests: List[str],
        interest_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze cultural preference dimensions"""
        preferences = {}
        
        interest_to_cultural = {
            "culture": ["history", "art", "tradition", "modern"],
            "food": ["food_culture"],
            "nature": ["nature"],
            "religion": ["religion"],
            "entertainment": ["nightlife", "modern"],
            "photography": ["nature", "art"],
            "sports": ["nature"],
            "wellness": ["nature", "tradition"],
        }
        
        for interest in raw_interests:
            interest_lower = interest.lower()
            if interest_lower in interest_to_cultural:
                for cultural_dim in interest_to_cultural[interest_lower]:
                    if cultural_dim in self.CULTURAL_DIMENSIONS:
                        base_weight = self.CULTURAL_DIMENSIONS[cultural_dim]["weight"]
                        preferences[cultural_dim] = base_weight
        
        for dim in self.CULTURAL_DIMENSIONS:
            if dim not in preferences:
                preferences[dim] = 0.3
        
        sorted_prefs = dict(sorted(preferences.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_prefs
    
    def _calculate_pace(self, travel_style: str, fitness_level: str) -> str:
        """Calculate travel pace"""
        if travel_style == "relaxed":
            return "relaxed"
        elif travel_style == "intensive":
            return "intensive"
        elif fitness_level == "low":
            return "relaxed"
        elif fitness_level == "high":
            return "intensive"
        else:
            return "balanced"
    
    def _map_to_poi_categories(
        self,
        interest_result: Dict[str, Any],
        cultural_result: Dict[str, Any],
    ) -> List[str]:
        """Map preferences to POI categories"""
        categories = set(interest_result.get("categories", []))
        
        if cultural_result.get("history", 0) > 0.6:
            categories.add("historical")
        if cultural_result.get("art", 0) > 0.6:
            categories.add("art")
        if cultural_result.get("nature", 0) > 0.6:
            categories.add("nature")
        if cultural_result.get("food_culture", 0) > 0.6:
            categories.add("food")
        if cultural_result.get("religion", 0) > 0.6:
            categories.add("religion")
            
        return list(categories)
    
    def _calculate_profile_scores(
        self,
        interest_result: Dict[str, Any],
        budget_result: Dict[str, Any],
        fitness_result: Dict[str, Any],
        cultural_result: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate composite profile scores"""
        scores = {}
        
        culture_score = cultural_result.get("history", 0.3) + cultural_result.get("art", 0.3)
        scores["culture_seeker"] = min(1.0, culture_score)
        
        scores["nature_lover"] = cultural_result.get("nature", 0.3)
        scores["foodie"] = cultural_result.get("food_culture", 0.3)
        scores["adventure_seeker"] = fitness_result.get("energy_score", 0.5)
        
        budget_level = budget_result.get("label", "Comfort")
        scores["luxury_traveler"] = 0.3 if budget_level == "Budget" else 0.7 if budget_level == "Luxury" else 0.5
        
        scores["family_friendly"] = 0.8 if budget_result.get("needs_child_friendly") else 0.3
        
        return scores
    
    def _enrich_from_behavior(
        self,
        profile: Dict[str, Any],
        behavior_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Enrich profile based on historical behavior"""
        if not behavior_analysis:
            return profile
        
        if "behavior_counts" in behavior_analysis:
            counts = behavior_analysis["behavior_counts"]
            visit_count = counts.get("visit", 0)
            if visit_count > 5:
                profile["profile_scores"]["frequent_traveler"] = min(1.0, visit_count / 10)
        
        return profile
    
    def _merge_profiles(self, existing: Any, new_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Merge existing profile with new profile data"""
        merged = new_profile.copy()
        
        merged["user_id"] = existing.user_id
        
        existing_db_data = new_profile.get("_db_data", {})
        merged_db_data = existing_db_data.copy()
        
        existing_interests = existing.interests or []
        new_interests = new_profile.get("interests", [])
        merged_db_data["interests"] = list(set(existing_interests + new_interests))
        merged["interests"] = merged_db_data["interests"]
        
        if not new_profile.get("cultural_preferences") and existing.cultural_preferences:
            merged["cultural_preferences"] = existing.cultural_preferences
            merged_db_data["cultural_preferences"] = existing.cultural_preferences
        
        if not new_profile.get("preferred_categories") and existing.preferred_categories:
            merged["preferred_categories"] = existing.preferred_categories
            merged_db_data["preferred_categories"] = existing.preferred_categories
        
        existing_tags = existing.tags or []
        new_tags = new_profile.get("tags", [])
        merged_db_data["tags"] = list(set(existing_tags + new_tags))
        merged["tags"] = merged_db_data["tags"]
        
        merged["_db_data"] = merged_db_data
        return merged
