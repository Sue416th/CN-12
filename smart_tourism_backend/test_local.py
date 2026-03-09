"""
Simple functionality test - no external services required
"""
import asyncio
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_imports():
    """Test module imports"""
    print("\n" + "="*60)
    print("TEST 1: Module Import Test")
    print("="*60)
    
    try:
        from app.services.llm_service import LLMService
        print("[OK] llm_service imported")
        
        from app.services.knowledge_graph_service import KnowledgeGraphService
        print("[OK] knowledge_graph_service imported")
        
        from app.services.websocket_service import manager
        print("[OK] websocket_service imported")
        
        from app.services.training_data_collector import TrainingDataCollector
        print("[OK] training_data_collector imported")
        
        from app.agents.enhanced_user_profile_agent import EnhancedUserProfileAgent
        print("[OK] enhanced_user_profile_agent imported")
        
        from app.agents.orchestrator import AgentOrchestrator
        print("[OK] orchestrator imported")
        
        from app.config import settings
        print("[OK] config imported")
        print(f"   LLM_PROVIDER: {settings.LLM_PROVIDER}")
        print(f"   NEO4J_URI: {settings.NEO4J_URI}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_creation():
    """Test Agent creation"""
    print("\n" + "="*60)
    print("TEST 2: Agent Creation Test")
    print("="*60)
    
    try:
        from app.agents.enhanced_user_profile_agent import EnhancedUserProfileAgent
        from app.agents.orchestrator import AgentOrchestrator
        
        agent = EnhancedUserProfileAgent()
        print("[OK] EnhancedUserProfileAgent created")
        
        orchestrator = AgentOrchestrator(use_enhanced_profile=True)
        print("[OK] AgentOrchestrator created")
        print(f"   Enhanced mode: {orchestrator.use_enhanced_profile}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_profile_generation():
    """Test profile generation (without external services)"""
    print("\n" + "="*60)
    print("TEST 3: User Profile Generation Test")
    print("="*60)
    
    try:
        from app.agents.enhanced_user_profile_agent import EnhancedUserProfileAgent
        
        agent = EnhancedUserProfileAgent()
        
        # Test case 1: Structured input
        print("\n[Case 1] Structured input")
        context = {
            "user_id": 1,
            "interests": ["culture", "food"],
            "budget_level": "medium",
            "travel_style": "balanced",
            "fitness_level": "medium",
            "group_type": "solo",
        }
        
        result = await agent.run(context)
        profile = result.get("user_profile", {})
        
        print(f"   Interests: {profile.get('interests')}")
        print(f"   Budget: {profile.get('budget_level')}")
        print(f"   Cultural prefs: {profile.get('cultural_preferences')}")
        print(f"   Categories: {profile.get('preferred_categories')}")
        print("[OK] Profile generation successful")
        
        # Test case 2: With natural language input
        print("\n[Case 2] Natural language input")
        context2 = {
            "user_id": 2,
            "user_text": "I like historical cultural sites, medium budget, average fitness",
            "budget_level": "medium",
        }
        
        result2 = await agent.run(context2)
        profile2 = result2.get("user_profile", {})
        
        print(f"   Interests: {profile2.get('interests')}")
        print(f"   Budget: {profile2.get('budget_level')}")
        print("[OK] Natural language processing successful")
        
        return True
    except Exception as e:
        print(f"[FAIL] Profile generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_vector_conversion():
    """Test vector conversion"""
    print("\n" + "="*60)
    print("TEST 4: Vector Conversion Test")
    print("="*60)
    
    try:
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        profile = {
            "interests": ["culture", "food", "nature"],
            "budget_level": "medium",
            "travel_style": "balanced",
            "fitness_level": "high",
            "group_type": "solo",
            "cultural_preferences": {"history": 0.8, "food_culture": 0.9}
        }
        
        vector = vector_service.profile_to_vector(profile)
        
        print(f"   Vector dimension: {len(vector)}")
        print(f"   First 5 values: {[round(v, 4) for v in vector[:5]]}")
        print("[OK] Vector conversion successful")
        
        return True
    except Exception as e:
        print(f"[FAIL] Vector conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_training_data_collector():
    """Test training data collector"""
    print("\n" + "="*60)
    print("TEST 5: Training Data Collector Test")
    print("="*60)
    
    try:
        from app.services.training_data_collector import TrainingDataCollector
        
        temp_dir = tempfile.mkdtemp()
        collector = TrainingDataCollector(output_dir=temp_dir)
        
        collector.collect_user_profile_data(
            user_id=1,
            user_input={"interests": ["culture"]},
            generated_profile={
                "interests": ["culture", "history"],
                "budget_level": "medium"
            }
        )
        print("[OK] Data collection successful")
        
        stats = collector.get_statistics()
        print(f"   Stats: {stats}")
        
        shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        print(f"[FAIL] Training data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("Smart Tourism Platform - Local Functionality Test")
    print("="*60)
    
    import_ok = await test_imports()
    
    if not import_ok:
        print("\n[FAIL] Import test failed, stopping")
        return
    
    agent_ok = await test_agent_creation()
    profile_ok = await test_profile_generation()
    vector_ok = await test_vector_conversion()
    collector_ok = await test_training_data_collector()
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Module Import: {'PASS' if import_ok else 'FAIL'}")
    print(f"Agent Creation: {'PASS' if agent_ok else 'FAIL'}")
    print(f"Profile Generation: {'PASS' if profile_ok else 'FAIL'}")
    print(f"Vector Conversion: {'PASS' if vector_ok else 'FAIL'}")
    print(f"Data Collection: {'PASS' if collector_ok else 'FAIL'}")
    print("\n" + "="*60)
    print("\nNOTE: Full test requires:")
    print("   - LLM API (GLM/OpenAI)")
    print("   - Neo4j database")
    print("   - Milvus database")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
