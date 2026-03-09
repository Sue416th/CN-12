from typing import Any, Dict, List, Optional
from app.agents.base_agent import BaseAgent
from app.services.user_profile_service import UserProfileService
from app.services.vector_service import get_vector_service


class UserProfileAgent(BaseAgent):
    """
    User Profile Agent - Analyze user preferences and generate user profile vector
    
    Responsibilities:
    1. Collect and update user multi-dimensional information:
       - Interests: travel preferences, hobbies, activity types
       - Budget: price sensitivity, spending habits, value consciousness
       - Fitness: physical ability, energy level, mobility considerations
       - Cultural preferences: historical, artistic, traditional, modern
    
    2. Generate dynamic user profile vectors
    3. Analyze user behavior to improve recommendations
    4. Provide personalized insights for itinerary planning

    This is the starting point for all personalized services.
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
        super().__init__(name="user_profile")

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comprehensive user profile analysis across all dimensions
        """
        db = context.get("db")
        user_id = context.get("user_id", 1)
        
        # Extract all profile dimensions from context
        raw_interests = context.get("interests", [])
        budget_level = context.get("budget_level", "medium")
        travel_style = context.get("travel_style", "balanced")
        group_type = context.get("group_type", "solo")
        fitness_level = context.get("fitness_level", "medium")
        
        # Extended context parameters (if provided)
        age_group = context.get("age_group", "adult")  # youth, adult, senior
        has_children = context.get("has_children", False)
        price_sensitivity = context.get("price_sensitivity", 0.5)  # 0-1 scale

        # Build comprehensive profile
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

        # If database is available, save/update profile and analyze history
        if db:
            profile_service = UserProfileService(db)

            # Get existing profile for learning
            existing_profile = profile_service.get_profile(user_id)

            # Merge with existing profile data (learning from history)
            if existing_profile:
                profile = self._merge_profiles(existing_profile, profile)

            # Save to database
            db_data = self._extract_db_fields(profile)
            profile_service.update_profile(user_id, db_data)
            profile["_db_data"] = db_data

            # Save profile vector to Milvus
            try:
                vector_service = get_vector_service()
                if vector_service.is_connected():
                    vector_id = vector_service.upsert_profile(user_id, profile)
                    if vector_id:
                        profile["profile_vector_id"] = vector_id
                        db_data["profile_vector_id"] = vector_id
                        profile_service.update_profile(user_id, {"profile_vector_id": vector_id})
            except Exception as e:
                print(f"Warning: Failed to save vector: {e}")

            # Analyze behavior history to improve profile
            behavior_analysis = profile_service.analyze_preferences(user_id)
            if behavior_analysis:
                profile = self._enrich_from_behavior(profile, behavior_analysis)

            # Update statistics
            profile_service.update_stats(user_id)

        # Pass profile to context for downstream agents
        context["user_profile"] = profile
        context["refined_interests"] = profile.get("refined_interests", raw_interests)
        
        # Add specific context for itinerary planner
        context["budget_info"] = profile.get("budget_info", {})
        context["fitness_info"] = profile.get("fitness_info", {})
        context["cultural_preferences"] = profile.get("cultural_preferences", {})
        context["preferred_categories"] = profile.get("preferred_categories", [])

        return context

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
        
        # 1. Process interests with detailed taxonomy
        interest_result = self._analyze_interests(raw_interests)
        
        # 2. Analyze budget with price sensitivity
        budget_result = self._analyze_budget(budget_level, price_sensitivity, group_type)
        
        # 3. Assess fitness level considering various factors
        fitness_result = self._analyze_fitness(fitness_level, age_group, has_children, group_type)
        
        # 4. Determine cultural preferences
        cultural_result = self._analyze_cultural_preferences(raw_interests, interest_result)
        
        # 5. Determine travel pace
        pace_preference = self._calculate_pace(travel_style, fitness_level)
        
        # 6. Map to POI categories
        poi_categories = self._map_to_poi_categories(interest_result, cultural_result)

        # Combine all results
        profile = {
            "user_id": None,
            
            # Interest dimension
            "interests": raw_interests,
            "interest_details": interest_result,
            "refined_interests": interest_result.get("expanded_tags", []),
            
            # Budget dimension
            "budget_level": budget_level,
            "budget_info": budget_result,
            "price_sensitivity": price_sensitivity,
            
            # Fitness dimension
            "fitness_level": fitness_level,
            "fitness_info": fitness_result,
            "age_group": age_group,
            "has_children": has_children,
            
            # Cultural dimension
            "cultural_preferences": cultural_result,
            
            # Travel style
            "travel_style": travel_style,
            "pace_preference": pace_preference,
            "group_type": group_type,
            
            # POI mapping
            "preferred_categories": poi_categories,
            "tags": raw_interests,
            
            # Composite scores
            "profile_scores": self._calculate_profile_scores(
                interest_result, budget_result, fitness_result, cultural_result
            ),
        }
        
        # Add DB-compatible subset
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
            
            # Look up in taxonomy
            if interest_lower in self.INTEREST_TAXONOMY:
                info = self.INTEREST_TAXONOMY[interest_lower]
                expanded_tags.extend(info["tags"])
                categories.update(info["poi_categories"])
                scores[interest_lower] = info["weight"]
            else:
                # Generic expansion
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
        
        # Adjust based on price sensitivity
        # High sensitivity (closer to 1) pushes towards lower budget
        adjusted_level = budget_level.lower()
        if price_sensitivity > 0.7:
            adjusted_level = "low"
        elif price_sensitivity < 0.3:
            adjusted_level = "high"
        
        if adjusted_level != budget_level.lower():
            base_profile = self.BUDGET_PROFILES.get(adjusted_level, base_profile).copy()
            base_profile["adjusted"] = True
            base_profile["original"] = budget_level
        
        # Group size adjustments
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
        """Detailed fitness analysis considering multiple factors"""
        base_profile = self.FITNESS_PROFILES.get(
            fitness_level.lower(),
            self.FITNESS_PROFILES["medium"]
        ).copy()
        
        # Adjust for age group
        if age_group == "senior":
            base_profile["max_daily_walk_hours"] = max(1, base_profile["max_daily_walk_hours"] - 1)
            base_profile["max_daily_steps"] = int(base_profile["max_daily_steps"] * 0.7)
            base_profile["needs_rest_stops"] = True
            base_profile["avoid_stairs"] = True
            base_profile["age_adjusted"] = True
        elif age_group == "youth":
            base_profile["max_daily_walk_hours"] = min(8, base_profile["max_daily_walk_hours"] + 1)
            base_profile["max_daily_steps"] = int(base_profile["max_daily_steps"] * 1.2)
        
        # Adjust for children
        if has_children or group_type == "family":
            base_profile["needs_child_friendly"] = True
            base_profile["needs_rest_stops"] = True
            base_profile["prefer_vehicle"] = True
            base_profile["max_daily_walk_hours"] = max(1, base_profile["max_daily_walk_hours"] - 1)
        
        # Calculate energy score (0-1)
        base_profile["energy_score"] = (
            base_profile["max_daily_walk_hours"] / 6
        )  # Normalized to high level
        
        return base_profile

    def _analyze_cultural_preferences(
        self,
        raw_interests: List[str],
        interest_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze cultural preference dimensions"""
        preferences = {}

        # Map interests to cultural dimensions
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

        # Ensure all dimensions have values (default to 0.3)
        for dim in self.CULTURAL_DIMENSIONS:
            if dim not in preferences:
                preferences[dim] = 0.3

        # Sort by weight - keep simple dict for database compatibility
        sorted_prefs = dict(sorted(preferences.items(), key=lambda x: x[1], reverse=True))

        # Return simple dict for DB storage (just the scores)
        # The detailed structure is available in memory only
        return sorted_prefs

    def _calculate_pace(self, travel_style: str, fitness_level: str) -> str:
        """Calculate travel pace based on style and fitness"""
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
        
        # Add categories based on cultural preferences
        cultural_dims = cultural_result.get("dimensions", {})
        if cultural_dims.get("history", 0) > 0.6:
            categories.add("historical")
        if cultural_dims.get("art", 0) > 0.6:
            categories.add("art")
        if cultural_dims.get("nature", 0) > 0.6:
            categories.add("nature")
        if cultural_dims.get("food_culture", 0) > 0.6:
            categories.add("food")
        if cultural_dims.get("religion", 0) > 0.6:
            categories.add("religion")
            
        return list(categories)

    def _calculate_profile_scores(
        self,
        interest_result: Dict[str, Any],
        budget_result: Dict[str, Any],
        fitness_result: Dict[str, Any],
        cultural_result: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate composite profile scores for matching"""
        scores = {}
        
        # Culture seeker score
        culture_score = cultural_result.get("dimensions", {}).get("history", 0.3) + \
                       cultural_result.get("dimensions", {}).get("art", 0.3)
        scores["culture_seeker"] = min(1.0, culture_score)
        
        # Nature lover score
        scores["nature_lover"] = cultural_result.get("dimensions", {}).get("nature", 0.3)
        
        # Foodie score
        scores["foodie"] = cultural_result.get("dimensions", {}).get("food_culture", 0.3)
        
        # Adventure seeker score
        scores["adventure_seeker"] = fitness_result.get("energy_score", 0.5)
        
        # Luxury traveler score
        budget_level = budget_result.get("label", "Comfort")
        scores["luxury_traveler"] = 0.3 if budget_level == "Budget" else \
                                    0.7 if budget_level == "Luxury" else 0.5
        
        # Family-friendly score
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
        
        # Update scores based on actual behavior
        if "behavior_counts" in behavior_analysis:
            counts = behavior_analysis["behavior_counts"]
            
            # Increase score for frequently visited categories
            visit_count = counts.get("visit", 0)
            if visit_count > 5:
                profile["profile_scores"]["frequent_traveler"] = min(1.0, visit_count / 10)
        
        return profile

    def _merge_profiles(self, existing: Any, new_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge existing profile with new profile data (learning from history)
        """
        merged = new_profile.copy()
        
        # Ensure user_id is set
        merged["user_id"] = existing.user_id
        
        # Get existing _db_data
        existing_db_data = new_profile.get("_db_data", {})
        merged_db_data = existing_db_data.copy()
        
        # 1. Merge interests (cumulative learning)
        existing_interests = existing.interests or []
        new_interests = new_profile.get("interests", [])
        merged_db_data["interests"] = list(set(existing_interests + new_interests))
        merged["interests"] = merged_db_data["interests"]
        
        # Update interest details
        if hasattr(existing, 'cultural_preferences') and existing.cultural_preferences:
            existing_cultural = existing.cultural_preferences
            new_cultural = new_profile.get("cultural_preferences", {})
            if new_cultural and "dimensions" in new_cultural:
                merged_dims = new_cultural["dimensions"]
                for dim, score in existing_cultural.items():
                    if isinstance(score, dict) and "dimensions" in score:
                        for d, s in score["dimensions"].items():
                            if d in merged_dims:
                                merged_dims[d] = (merged_dims[d] + s) / 2
                new_profile["cultural_preferences"]["dimensions"] = merged_dims
        
        # 2. Keep existing cultural preferences
        if not new_profile.get("cultural_preferences") and existing.cultural_preferences:
            merged["cultural_preferences"] = existing.cultural_preferences
            merged_db_data["cultural_preferences"] = existing.cultural_preferences
        
        # 3. Keep existing preferred categories
        if not new_profile.get("preferred_categories") and existing.preferred_categories:
            merged["preferred_categories"] = existing.preferred_categories
            merged_db_data["preferred_categories"] = existing.preferred_categories
        
        # 4. Merge tags
        existing_tags = existing.tags or []
        new_tags = new_profile.get("tags", [])
        merged_db_data["tags"] = list(set(existing_tags + new_tags))
        merged["tags"] = merged_db_data["tags"]
        
        merged["_db_data"] = merged_db_data
        return merged
