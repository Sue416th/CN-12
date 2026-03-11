"""
Test script to verify Milvus profile saving - simplified
"""
from src.agents.vector_service import get_vector_service


def test_save_profile():
    print("=== Testing Milvus Profile Save ===\n")

    # Test profile data
    test_profile = {
        "user_id": 999,
        "interests": ["culture", "food", "nature"],
        "budget_level": "medium",
        "travel_style": "balanced",
        "group_type": "solo",
        "fitness_level": "medium",
        "age_group": "adult",
        "has_children": False,
        "price_sensitivity": 0.5,
        "refined_interests": ["history", "local cuisine", "hiking"],
        "cultural_preferences": {"cuisine": "local", "arts": "traditional"},
    }

    # Get vector service
    vector_service = get_vector_service()

    # Connect
    print("Connecting to Milvus...")
    connected = vector_service.connect()
    print(f"Connected: {connected}")

    # Save profile
    print("\nSaving profile to Milvus...")
    result = vector_service.upsert_profile(999, test_profile)
    print(f"Upsert result: {result}")

    # Check if data exists
    print("\nChecking if data was saved...")
    try:
        from pymilvus import Collection
        collection = Collection("user_profiles")
        collection.load()

        from pymilvus import utility
        expr = "user_id == 999"
        results = collection.query(
            expr=expr,
            output_fields=["user_id", "interests", "budget_level", "travel_style", "fitness_level"]
        )

        print(f"\nQuery results: {results}")

        if results:
            print("\n✓ Profile saved to Milvus successfully!")
        else:
            print("\n✗ No data found in Milvus!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_save_profile()
