"""
User Profile Agent - Analyze user preferences and generate user profile
"""
import json
from typing import Dict, List, Any, Optional
from .vector_service import get_vector_service
from src.db import save_user_profile, get_user_profile


class UserProfileAgent:
    """
    User Profile Agent - Analyze user preferences and generate user profile vector

    Responsibilities:
    1. Collect and update user multi-dimensional information
    2. Generate dynamic user profile vectors (stored in Milvus)
    3. Provide personalized insights for itinerary planning
    """

    INTEREST_TAXONOMY = {
        "culture": {
            "tags": ["museum", "art", "history", "heritage", "traditional", "folklore"],
            "weight": 0.8
        },
        "food": {
            "tags": ["local cuisine", "night market", "restaurants", "street food", "foodie"],
            "weight": 0.9
        },
        "nature": {
            "tags": ["park", "wetland", "mountain", "garden", "lake", "hiking", "scenery"],
            "weight": 0.7
        },
        "religion": {
            "tags": ["temple", "church", "shrine", "Buddhism", "Taoism", "meditation"],
            "weight": 0.6
        },
        "entertainment": {
            "tags": ["show", "theme park", "nightlife", "performance"],
            "weight": 0.8
        },
        "shopping": {
            "tags": ["market", "street", "mall", "souvenirs", "shopping"],
            "weight": 0.5
        },
        "photography": {
            "tags": ["photo", "sunset", "landscape", "portrait"],
            "weight": 0.7
        },
        "sports": {
            "tags": ["hiking", "cycling", "running", "swimming", "adventure"],
            "weight": 0.8
        },
        "wellness": {
            "tags": ["spa", "hot spring", "yoga", "relaxation", "health"],
            "weight": 0.6
        }
    }

    BUDGET_PROFILES = {
        "low": {"max_price_level": 1, "label": "Budget", "accommodation": "hostel", "dining": "street food"},
        "medium": {"max_price_level": 2, "label": "Comfort", "accommodation": "hotel", "dining": "local restaurants"},
        "high": {"max_price_level": 3, "label": "Luxury", "accommodation": "luxury hotel", "dining": "fine dining"}
    }

    FITNESS_PROFILES = {
        "low": {"max_daily_walk_hours": 2, "max_daily_steps": 5000, "label": "Light", "avoid_stairs": True},
        "medium": {"max_daily_walk_hours": 4, "max_daily_steps": 10000, "label": "Moderate", "avoid_stairs": False},
        "high": {"max_daily_walk_hours": 6, "max_daily_steps": 15000, "label": "Active", "avoid_stairs": False}
    }

    def __init__(self):
        pass

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comprehensive user profile analysis
        """
        user_id = context.get("user_id", 1)
        
        # Extract profile parameters
        interests = context.get("interests", [])
        budget_level = context.get("budget_level", "medium")
        travel_style = context.get("travel_style", "balanced")
        group_type = context.get("group_type", "solo")
        fitness_level = context.get("fitness_level", "medium")
        age_group = context.get("age_group", "adult")
        has_children = context.get("has_children", False)
        price_sensitivity = context.get("price_sensitivity", 0.5)

        # Build profile
        profile = self._build_profile(
            interests=interests,
            budget_level=budget_level,
            travel_style=travel_style,
            group_type=group_type,
            fitness_level=fitness_level,
            age_group=age_group,
            has_children=has_children,
            price_sensitivity=price_sensitivity
        )

        # Save to Milvus
        try:
            vector_service = get_vector_service()
            if vector_service.is_connected():
                vector_service.upsert_profile(user_id, profile)
                profile["vector_stored"] = True
        except Exception as e:
            print(f"Warning: Failed to save vector: {e}")
            profile["vector_stored"] = False

        # Save to MySQL
        try:
            await save_user_profile(user_id, profile)
            profile["mysql_stored"] = True
            print(f"User profile saved to MySQL for user_id: {user_id}")
        except Exception as e:
            print(f"Warning: Failed to save profile to MySQL: {e}")
            profile["mysql_stored"] = False

        # Pass profile to context
        context["user_profile"] = profile
        context["refined_interests"] = profile.get("refined_interests", interests)
        context["budget_info"] = profile.get("budget_info", {})
        context["fitness_info"] = profile.get("fitness_info", {})
        context["cultural_preferences"] = profile.get("cultural_preferences", {})
        context["preferred_categories"] = profile.get("preferred_categories", [])

        return context

    def _build_profile(
        self,
        interests: List[str],
        budget_level: str,
        travel_style: str,
        group_type: str,
        fitness_level: str = "medium",
        age_group: str = "adult",
        has_children: bool = False,
        price_sensitivity: float = 0.5,
    ) -> Dict[str, Any]:
        """Build comprehensive user profile"""
        
        # Process interests
        interest_result = self._process_interests(interests)
        
        # Process budget
        budget_result = self._process_budget(budget_level, price_sensitivity, group_type)
        
        # Process fitness
        fitness_result = self._process_fitness(fitness_level, age_group, has_children)
        
        # Process cultural preferences
        cultural_result = self._process_cultural_preferences(interests, interest_result)
        
        # Calculate pace
        pace = self._calculate_pace(travel_style, fitness_level)
        
        # Map to POI categories
        poi_categories = self._map_to_poi_categories(interest_result)

        return {
            "user_id": None,
            "interests": interests,
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
            "pace_preference": pace,
            "group_type": group_type,
            "preferred_categories": poi_categories,
        }

    def _process_interests(self, interests: List[str]) -> Dict[str, Any]:
        """Process interests with taxonomy"""
        if not interests:
            return {"primary": [], "expanded_tags": [], "categories": [], "scores": {}}
        
        primary = []
        expanded_tags = []
        categories = set()
        scores = {}
        
        for interest in interests:
            interest_lower = interest.lower()
            primary.append(interest_lower)
            
            if interest_lower in self.INTEREST_TAXONOMY:
                info = self.INTEREST_TAXONOMY[interest_lower]
                expanded_tags.extend(info["tags"])
                scores[interest_lower] = info["weight"]
            else:
                expanded_tags.append(interest_lower)
                scores[interest_lower] = 0.5
        
        return {
            "primary": primary,
            "expanded_tags": list(set(expanded_tags)),
            "categories": list(categories),
            "scores": scores,
        }

    def _process_budget(
        self,
        budget_level: str,
        price_sensitivity: float,
        group_type: str,
    ) -> Dict[str, Any]:
        """Process budget profile"""
        base = self.BUDGET_PROFILES.get(budget_level.lower(), self.BUDGET_PROFILES["medium"]).copy()
        
        if price_sensitivity > 0.7:
            base = self.BUDGET_PROFILES["low"].copy()
        elif price_sensitivity < 0.3:
            base = self.BUDGET_PROFILES["high"].copy()
        
        if group_type == "family":
            base["dining_budget"] = "family restaurant"
        elif group_type == "solo":
            base["dining_budget"] = "solo-friendly"
        
        base["price_sensitivity"] = price_sensitivity
        return base

    def _process_fitness(
        self,
        fitness_level: str,
        age_group: str,
        has_children: bool,
    ) -> Dict[str, Any]:
        """Process fitness profile"""
        base = self.FITNESS_PROFILES.get(fitness_level.lower(), self.FITNESS_PROFILES["medium"]).copy()
        
        if age_group == "senior":
            base["max_daily_walk_hours"] = max(1, base["max_daily_walk_hours"] - 1)
            base["max_daily_steps"] = int(base["max_daily_steps"] * 0.7)
            base["needs_rest_stops"] = True
        elif age_group == "youth":
            base["max_daily_walk_hours"] = min(8, base["max_daily_walk_hours"] + 1)
        
        if has_children:
            base["needs_child_friendly"] = True
            base["needs_rest_stops"] = True
        
        return base

    def _process_cultural_preferences(
        self,
        interests: List[str],
        interest_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze cultural preferences"""
        preferences = {}
        
        interest_to_cultural = {
            "culture": ["history", "art", "tradition"],
            "food": ["food_culture"],
            "nature": ["nature"],
            "religion": ["religion"],
            "entertainment": ["nightlife"],
            "photography": ["nature", "art"],
            "sports": ["nature"],
            "wellness": ["nature", "tradition"],
        }

        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in interest_to_cultural:
                for dim in interest_to_cultural[interest_lower]:
                    preferences[dim] = 0.7

        for dim in ["history", "art", "tradition", "modern", "religion", "nature", "food_culture", "nightlife"]:
            if dim not in preferences:
                preferences[dim] = 0.3

        return dict(sorted(preferences.items(), key=lambda x: x[1], reverse=True))

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
        return "balanced"

    def _map_to_poi_categories(self, interest_result: Dict[str, Any]) -> List[str]:
        """Map preferences to POI categories"""
        categories = set(interest_result.get("categories", []))
        
        scores = interest_result.get("scores", {})
        for interest, score in scores.items():
            if score > 0.6:
                if interest == "culture":
                    categories.add("historical")
                elif interest == "food":
                    categories.add("food")
                elif interest == "nature":
                    categories.add("nature")
                elif interest == "religion":
                    categories.add("religion")
                elif interest == "photography":
                    categories.add("scenic")
        
        return list(categories)
