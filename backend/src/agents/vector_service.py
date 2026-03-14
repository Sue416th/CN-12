"""
Milvus Vector Service - User Profile Vector Storage
"""
import json
import numpy as np
from typing import Dict, List, Optional, Any
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility


class VectorService:
    def __init__(self):
        self.host = "localhost"
        self.port = 19530
        self.collection_name = "user_profiles"
        self.connected = False
        self.collection = None

    def connect(self) -> bool:
        """Connect to Milvus"""
        try:
            if not connections.has_connection("default"):
                connections.connect(host=self.host, port=self.port)

            self.connected = True
            print(f"Connected to Milvus at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            self.connected = False
            return False

    def is_connected(self) -> bool:
        """Check if connected to Milvus"""
        if not self.connected:
            return self.connect()
        return True

    def create_collection_if_not_exists(self) -> bool:
        """Create collection if not exists"""
        try:
            if not self.is_connected():
                return False

            # Check if collection exists
            if utility.has_collection(self.collection_name):
                # Collection exists, just load it
                self.collection = Collection(self.collection_name)
                self.collection.load()
                print(f"Collection '{self.collection_name}' loaded successfully")
                return True

            # Create new collection
            fields = [
                FieldSchema(name="user_id", dtype=DataType.INT64, is_primary=True, description="User ID"),
                FieldSchema(name="interests", dtype=DataType.VARCHAR, max_length=2000, description="User interests as JSON string"),
                FieldSchema(name="budget_level", dtype=DataType.VARCHAR, max_length=50, description="Budget level: low/medium/high"),
                FieldSchema(name="travel_style", dtype=DataType.VARCHAR, max_length=50, description="Travel style: relaxed/balanced/intensive"),
                FieldSchema(name="group_type", dtype=DataType.VARCHAR, max_length=50, description="Group type: solo/couple/family/group"),
                FieldSchema(name="fitness_level", dtype=DataType.VARCHAR, max_length=50, description="Fitness level: low/medium/high"),
                FieldSchema(name="age_group", dtype=DataType.VARCHAR, max_length=50, description="Age group: youth/adult/senior"),
                FieldSchema(name="has_children", dtype=DataType.VARCHAR, max_length=10, description="Has children: true/false"),
                FieldSchema(name="price_sensitivity", dtype=DataType.FLOAT, description="Price sensitivity 0-1"),
                FieldSchema(name="refined_interests", dtype=DataType.VARCHAR, max_length=2000, description="Refined interests as JSON string"),
                FieldSchema(name="cultural_preferences", dtype=DataType.VARCHAR, max_length=2000, description="Cultural preferences as JSON string"),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128, description="Profile embedding vector"),
            ]

            schema = CollectionSchema(fields, description="User profile vectors for trip recommendation")
            self.collection = Collection(self.collection_name, schema)

            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 128}
            }
            self.collection.create_index(field_name="embedding", index_params=index_params)
            self.collection.load()
            print(f"Collection '{self.collection_name}' created successfully")
            return True
        except Exception as e:
            print(f"Failed to create collection: {e}")
            return False

    def upsert_profile(self, user_id: int, profile: Dict[str, Any]) -> Optional[str]:
        """Save user profile vector to Milvus"""
        try:
            if not self.create_collection_if_not_exists():
                return None

            # Generate embedding from profile (simplified)
            embedding = self._generate_profile_embedding(profile)

            # Convert has_children to string
            has_children_str = "true" if profile.get("has_children", False) else "false"

            entities = [
                [user_id],
                [json.dumps(profile.get("interests", []))],
                [profile.get("budget_level", "medium")],
                [profile.get("travel_style", "balanced")],
                [profile.get("group_type", "solo")],
                [profile.get("fitness_level", "medium")],
                [profile.get("age_group", "adult")],
                [has_children_str],
                [float(profile.get("price_sensitivity", 0.5))],
                [json.dumps(profile.get("refined_interests", []))],
                [json.dumps(profile.get("cultural_preferences", {}))],
                [embedding.tolist()],
            ]

            # Delete existing profile first (upsert behavior)
            try:
                self.collection.delete(f"user_id == {user_id}")
                self.collection.flush()
            except Exception:
                pass  # Ignore if no existing record

            self.collection.insert(entities)
            self.collection.flush()
            print(f"User profile saved to Milvus for user_id: {user_id}")
            return str(user_id)
        except Exception as e:
            print(f"Failed to upsert profile: {e}")
            return None

    def search_similar(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict]:
        """Search similar profiles"""
        try:
            if not self.is_connected():
                return []

            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["user_id", "interests", "budget_level", "fitness_level",
                               "travel_style", "group_type", "age_group", "has_children",
                               "price_sensitivity", "refined_interests", "cultural_preferences"]
            )

            similar_profiles = []
            for hit in results[0]:
                similar_profiles.append({
                    "user_id": hit.entity.get("user_id"),
                    "interests": json.loads(hit.entity.get("interests", "[]")),
                    "budget_level": hit.entity.get("budget_level"),
                    "fitness_level": hit.entity.get("fitness_level"),
                    "travel_style": hit.entity.get("travel_style"),
                    "group_type": hit.entity.get("group_type"),
                    "age_group": hit.entity.get("age_group"),
                    "has_children": hit.entity.get("has_children"),
                    "price_sensitivity": hit.entity.get("price_sensitivity"),
                    "refined_interests": json.loads(hit.entity.get("refined_interests", "[]")),
                    "cultural_preferences": json.loads(hit.entity.get("cultural_preferences", "{}")),
                    "distance": hit.distance
                })
            return similar_profiles
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def _generate_profile_embedding(self, profile: Dict[str, Any]) -> np.ndarray:
        """Generate embedding vector from profile"""
        # Create a deterministic embedding based on profile attributes
        interests = profile.get("interests", [])
        budget = profile.get("budget_level", "medium")
        fitness = profile.get("fitness_level", "medium")
        travel_style = profile.get("travel_style", "balanced")
        group_type = profile.get("group_type", "solo")
        age_group = profile.get("age_group", "adult")
        price_sensitivity = profile.get("price_sensitivity", 0.5)

        # Create a unique seed from all profile attributes
        seed = hash(
            str(interests) + budget + fitness + travel_style +
            group_type + age_group + str(price_sensitivity)
        ) % (2**31)
        np.random.seed(seed)
        embedding = np.random.randn(128)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype(np.float32)

    def search_by_context(self, context: Dict[str, Any], top_k: int = 5) -> List[Dict]:
        """
        Search similar user profiles based on context (interests, budget, etc.)
        This enables personalized recommendations by finding users with similar preferences

        Args:
            context: Dictionary containing user preferences like interests, budget_level, etc.
            top_k: Number of similar profiles to return

        Returns:
            List of similar user profiles with their preferences
        """
        # Build a profile from context
        profile = {
            "interests": context.get("interests", []),
            "budget_level": context.get("budget_level", "medium"),
            "fitness_level": context.get("fitness_level", "medium"),
            "travel_style": context.get("travel_style", "balanced"),
            "group_type": context.get("group_type", "solo"),
            "age_group": context.get("age_group", "adult"),
            "price_sensitivity": context.get("price_sensitivity", 0.5),
        }

        # Generate embedding from the context profile
        query_embedding = self._generate_profile_embedding(profile)

        # Search similar profiles
        return self.search_similar(query_embedding, top_k=top_k)

    def get_personalized_recommendations(self, context: Dict[str, Any], top_k: int = 5) -> Dict[str, Any]:
        """
        Get personalized recommendations based on similar users' preferences

        This method:
        1. Finds users with similar profiles
        2. Extracts their preferences (interests, budget, etc.)
        3. Returns aggregated recommendations

        Args:
            context: Current user's preferences
            top_k: Number of similar users to consider

        Returns:
            Dictionary with aggregated recommendations from similar users
        """
        similar_users = self.search_by_context(context, top_k)

        if not similar_users:
            return {
                "has_recommendations": False,
                "message": "No similar users found, using default recommendations",
                "similar_users_count": 0,
            }

        # Aggregate preferences from similar users
        aggregated = {
            "interests": [],
            "budget_level_counts": {},
            "fitness_level_counts": {},
            "travel_style_counts": {},
            "refined_interests": [],
            "cultural_preferences": {},
        }

        for user in similar_users:
            # Collect interests
            interests = user.get("interests", [])
            if isinstance(interests, str):
                import json
                interests = json.loads(interests)
            aggregated["interests"].extend(interests)

            # Count budget levels
            budget = user.get("budget_level", "medium")
            aggregated["budget_level_counts"][budget] = aggregated["budget_level_counts"].get(budget, 0) + 1

            # Count fitness levels
            fitness = user.get("fitness_level", "medium")
            aggregated["fitness_level_counts"][fitness] = aggregated["fitness_level_counts"].get(fitness, 0) + 1

            # Count travel styles
            style = user.get("travel_style", "balanced")
            aggregated["travel_style_counts"][style] = aggregated["travel_style_counts"].get(style, 0) + 1

            # Collect refined interests
            refined = user.get("refined_interests", [])
            if isinstance(refined, str):
                import json
                refined = json.loads(refined)
            aggregated["refined_interests"].extend(refined)

            # Aggregate cultural preferences
            cultural = user.get("cultural_preferences", {})
            if isinstance(cultural, str):
                import json
                cultural = json.loads(cultural)
            for k, v in cultural.items():
                aggregated["cultural_preferences"][k] = aggregated["cultural_preferences"].get(k, 0) + v

        # Calculate most common values
        from collections import Counter

        # Most common interests (top 10)
        interest_counts = Counter(aggregated["interests"])
        top_interests = [item[0] for item in interest_counts.most_common(10)]

        # Most common budget level
        if aggregated["budget_level_counts"]:
            recommended_budget = max(aggregated["budget_level_counts"].items(), key=lambda x: x[1])[0]
        else:
            recommended_budget = context.get("budget_level", "medium")

        # Most common fitness level
        if aggregated["fitness_level_counts"]:
            recommended_fitness = max(aggregated["fitness_level_counts"].items(), key=lambda x: x[1])[0]
        else:
            recommended_fitness = context.get("fitness_level", "medium")

        # Most common travel style
        if aggregated["travel_style_counts"]:
            recommended_style = max(aggregated["travel_style_counts"].items(), key=lambda x: x[1])[0]
        else:
            recommended_style = context.get("travel_style", "balanced")

        # Average cultural preferences
        num_users = len(similar_users)
        avg_cultural = {k: v / num_users for k, v in aggregated["cultural_preferences"].items()}

        # Top refined interests
        refined_counts = Counter(aggregated["refined_interests"])
        top_refined_interests = [item[0] for item in refined_counts.most_common(15)]

        return {
            "has_recommendations": True,
            "similar_users_count": num_users,
            "similar_users": similar_users,
            "recommended": {
                "interests": top_interests,
                "budget_level": recommended_budget,
                "fitness_level": recommended_fitness,
                "travel_style": recommended_style,
                "refined_interests": top_refined_interests,
                "cultural_preferences": avg_cultural,
            },
            "raw_aggregated": aggregated,
        }


# Global instance
_vector_service = None

def get_vector_service() -> VectorService:
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
