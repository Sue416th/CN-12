"""
Script to create Milvus collection for user profiles
Run this script to initialize the Milvus collection
"""
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility


def create_user_profile_collection():
    collection_name = "user_profiles"

    # Connect to Milvus
    print("Connecting to Milvus...")
    connections.connect(host="localhost", port=19530)
    print("Connected to Milvus")

    # Check if collection already exists
    if utility.has_collection(collection_name):
        print(f"Collection '{collection_name}' already exists. Dropping it...")
        utility.drop_collection(collection_name)

    # Define schema
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

    schema = CollectionSchema(
        fields=fields,
        description="User profile vectors for trip recommendation"
    )

    # Create collection
    collection = Collection(name=collection_name, schema=schema)
    print(f"Collection '{collection_name}' created")

    # Create index
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    print("Index created")

    # Load collection
    collection.load()
    print(f"Collection '{collection_name}' loaded and ready")

    # Show collection info
    print("\n--- Collection Info ---")
    print(f"Name: {collection_name}")
    print(f"Fields: {[f.name for f in fields]}")
    print(f"Primary key: user_id")
    print(f"Vector dimension: 128")

    connections.disconnect("default")
    print("\nDone! Milvus collection is ready.")


if __name__ == "__main__":
    create_user_profile_collection()
