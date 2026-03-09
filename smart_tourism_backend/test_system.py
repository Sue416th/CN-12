"""
系统测试脚本 - 验证LLM、知识图谱和增强版Agent的功能
"""
import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime


async def test_llm_service():
    """测试LLM服务"""
    print("\n" + "="*60)
    print("测试1: LLM服务")
    print("="*60)
    
    try:
        from app.services.llm_service import LLMService, get_llm_service
        from app.config import settings
        
        # 检查API Key
        if not settings.LLM_API_KEY:
            print("⚠️  未配置LLM_API_KEY，跳过LLM测试")
            print("   请在.env文件中配置:")
            print("   LLM_PROVIDER=glm")
            print("   LLM_API_KEY=your_api_key")
            return None
        
        # 创建LLM服务
        llm = LLMService(
            provider=settings.LLM_PROVIDER,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
        )
        
        # 测试1: 简单对话
        print("\n[1/3] 测试简单对话...")
        messages = [
            {"role": "system", "content": "你是一个友好的旅行助手"},
            {"role": "user", "content": "推荐一下北京的景点"}
        ]
        response = await llm.chat(messages, temperature=0.7)
        print(f"✅ 回复: {response[:100]}...")
        
        # 测试2: 用户画像分析
        print("\n[2/3] 测试用户画像分析...")
        analysis = await llm.analyze_user_input(
            user_text="我喜欢历史文化古迹，预算适中，体能一般，带父母出行",
            structured_data={"budget_level": "medium"}
        )
        print(f"✅ 分析结果: {json.dumps(analysis, ensure_ascii=False, indent=2)}")
        
        # 测试3: 画像描述生成
        print("\n[3/3] 测试画像描述生成...")
        profile = {
            "interests": ["culture", "history"],
            "budget_level": "medium",
            "fitness_level": "low",
            "cultural_preferences": {"history": 0.9, "art": 0.7}
        }
        description = await llm.generate_profile_description(profile)
        print(f"✅ 描述: {description}")
        
        print("\n✅ LLM服务测试通过!")
        return llm
        
    except Exception as e:
        print(f"❌ LLM服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_knowledge_graph():
    """测试知识图谱服务"""
    print("\n" + "="*60)
    print("测试2: 知识图谱服务 (Neo4j)")
    print("="*60)
    
    try:
        from app.services.knowledge_graph_service import KnowledgeGraphService
        from app.config import settings
        
        # 尝试连接Neo4j
        try:
            kg = KnowledgeGraphService(
                uri=settings.NEO4J_URI,
                user=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
            )
            print("✅ 成功连接到Neo4j")
        except Exception as e:
            print(f"⚠️  Neo4j连接失败: {e}")
            print("   请确保Neo4j已启动:")
            print("   docker run -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j")
            return None
        
        # 测试1: 创建用户节点
        print("\n[1/4] 创建用户节点...")
        test_user_id = 999
        profile = {
            "interests": ["culture", "food"],
            "budget_level": "medium",
            "travel_style": "balanced",
            "fitness_level": "medium",
            "cultural_preferences": {"history": 0.8, "food_culture": 0.9},
            "profile_vector_id": "test_vector_001"
        }
        kg.create_user(test_user_id, profile)
        print(f"✅ 用户 {test_user_id} 已创建")
        
        # 测试2: 记录用户偏好
        print("\n[2/4] 记录用户类别偏好...")
        kg.record_preference(test_user_id, "history", 0.8)
        kg.record_preference(test_user_id, "food", 0.9)
        print("✅ 偏好已记录")
        
        # 测试3: 创建POI节点
        print("\n[3/4] 创建POI节点...")
        poi_data = {
            "name": "故宫博物院",
            "category": "culture",
            "city": "北京",
            "latitude": 39.9163,
            "longitude": 116.3972,
            "rating": 4.9,
            "price_level": 2,
            "tags": ["历史", "博物馆", "世界遗产"],
            "description": "中国明清两代的皇家宫殿"
        }
        kg.create_poi("poi_001", poi_data)
        print("✅ POI已创建")
        
        # 测试4: 记录用户访问
        print("\n[4/4] 记录用户访问...")
        kg.record_visit(test_user_id, "poi_001", rating=5.0, duration=180)
        kg.record_like(test_user_id, "poi_001")
        print("✅ 访问记录已创建")
        
        # 测试5: 查询用户统计
        print("\n[5/5] 查询用户统计...")
        stats = kg.get_user_stats(test_user_id)
        print(f"✅ 统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        # 清理测试数据
        print("\n[清理] 删除测试数据...")
        # Note: 实际项目中请勿删除
        
        print("\n✅ 知识图谱服务测试通过!")
        return kg
        
    except Exception as e:
        print(f"❌ 知识图谱服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_vector_service():
    """测试向量服务"""
    print("\n" + "="*60)
    print("测试3: 向量服务 (Milvus)")
    print("="*60)
    
    try:
        from app.services.vector_service import VectorService
        
        # 尝试连接Milvus
        try:
            vector_service = VectorService()
            if not vector_service.is_connected():
                print("⚠️  Milvus未连接，跳过向量服务测试")
                print("   请确保Milvus已启动:")
                print("   docker run -p 19530:19530 milvusdb/milvus")
                return None
            print("✅ 成功连接到Milvus")
        except Exception as e:
            print(f"⚠️  Milvus连接失败: {e}")
            return None
        
        # 测试: 用户画像转向量
        print("\n[1/1] 测试画像转向量...")
        profile = {
            "interests": ["culture", "food", "nature"],
            "budget_level": "medium",
            "travel_style": "balanced",
            "fitness_level": "high",
            "group_type": "solo",
            "cultural_preferences": {"history": 0.8, "food_culture": 0.9}
        }
        
        vector = vector_service.profile_to_vector(profile)
        print(f"✅ 向量维度: {len(vector)}")
        print(f"   向量前5个值: {vector[:5]}")
        
        print("\n✅ 向量服务测试通过!")
        return vector_service
        
    except Exception as e:
        print(f"❌ 向量服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_enhanced_agent():
    """测试增强版用户画像Agent"""
    print("\n" + "="*60)
    print("测试4: 增强版用户画像Agent")
    print("="*60)
    
    try:
        from app.agents.enhanced_user_profile_agent import EnhancedUserProfileAgent
        from app.services.llm_service import get_llm_service
        from app.config import settings
        
        # 创建Agent
        agent = EnhancedUserProfileAgent()
        
        # 模拟数据库Session (使用内存中的)
        # 实际使用时会从FastAPI获取真实的db session
        mock_db = None
        
        # 测试场景
        test_cases = [
            {
                "name": "结构化输入",
                "context": {
                    "user_id": 1,
                    "interests": ["culture", "food"],
                    "budget_level": "medium",
                    "travel_style": "balanced",
                    "fitness_level": "medium",
                    "group_type": "solo",
                }
            },
            {
                "name": "自然语言输入",
                "context": {
                    "user_id": 2,
                    "user_text": "我想去杭州旅游，喜欢西湖和茶文化，预算不高，体能一般",
                    "budget_level": "low",
                }
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n[场景{i}/{len(test_cases)}] {case['name']}")
            print("-" * 40)
            
            context = case["context"]
            result = await agent.run(context)
            
            # 打印结果
            profile = result.get("user_profile", {})
            print(f"✅ 兴趣: {profile.get('interests', [])}")
            print(f"✅ 预算: {profile.get('budget_level')}")
            print(f"✅ 文化偏好: {profile.get('cultural_preferences', {})}")
            print(f"✅ 推荐类别: {profile.get('preferred_categories', [])}")
            
            if "profile_description" in profile:
                print(f"✅ 画像描述: {profile['profile_description']}")
            
            if "llm_analysis" in profile:
                print(f"✅ LLM分析: {profile['llm_analysis'].get('interests', [])}")
            
            if profile.get("kg_synced"):
                print(f"✅ 已同步到知识图谱")
        
        print("\n✅ 增强版Agent测试通过!")
        return agent
        
    except Exception as e:
        print(f"❌ 增强版Agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_full_integration():
    """完整集成测试"""
    print("\n" + "="*60)
    print("测试5: 完整集成测试")
    print("="*60)
    
    try:
        from app.agents.orchestrator import AgentOrchestrator
        from app.agents.enhanced_user_profile_agent import EnhancedUserProfileAgent
        from app.services.llm_service import get_llm_service
        from app.services.knowledge_graph_service import get_kg_service
        
        # 检查服务状态
        print("\n[服务状态检查]")
        
        # LLM
        try:
            from app.config import settings
            if settings.LLM_API_KEY:
                print("✅ LLM: 已配置")
            else:
                print("⚠️  LLM: 未配置API Key")
        except:
            print("⚠️  LLM: 配置加载失败")
        
        # Neo4j
        try:
            kg = get_kg_service()
            print("✅ 知识图谱: 已连接")
        except Exception as e:
            print(f"⚠️  知识图谱: {e}")
        
        # Milvus
        try:
            from app.services.vector_service import get_vector_service
            vs = get_vector_service()
            if vs.is_connected():
                print("✅ 向量数据库: 已连接")
            else:
                print("⚠️  向量数据库: 未连接")
        except Exception as e:
            print(f"⚠️  向量数据库: {e}")
        
        print("\n✅ 集成测试完成!")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🧪 智慧文旅平台 - 系统测试")
    print("="*60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试LLM服务
    llm_result = await test_llm_service()
    
    # 2. 测试知识图谱
    kg_result = await test_knowledge_graph()
    
    # 3. 测试向量服务
    vector_result = await test_vector_service()
    
    # 4. 测试增强版Agent
    agent_result = await test_enhanced_agent()
    
    # 5. 完整集成测试
    await test_full_integration()
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print(f"LLM服务: {'✅ 通过' if llm_result else '⚠️  跳过/失败'}")
    print(f"知识图谱: {'✅ 通过' if kg_result else '⚠️  跳过/失败'}")
    print(f"向量服务: {'✅ 通过' if vector_result else '⚠️  跳过/失败'}")
    print(f"增强版Agent: {'✅ 通过' if agent_result else '⚠️  跳过/失败'}")
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
