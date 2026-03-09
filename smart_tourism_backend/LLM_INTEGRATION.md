# LLM多智能体系统集成指南

## 系统架构

本系统实现了基于LLM（大型语言模型）和知识图谱的多智能体用户画像系统。

## 技术栈

### 1. LLM（大型语言模型）
- **支持**: GLM-4, GPT-4, GPT-3.5-Turbo, Qwen
- **功能**: 自然语言理解、用户画像分析、描述生成

### 2. 知识图谱 (Neo4j)
- **功能**: 用户-POI关系存储、偏好挖掘、相似用户发现

### 3. 向量数据库 (Milvus)
- **功能**: 用户画像向量存储、相似用户检索

### 4. WebSocket
- **功能**: 实时推送、在线状态感知

---

## 快速开始

### 1. 环境配置

复制 `.env.example` 到 `.env` 并配置:

```bash
# LLM配置
LLM_PROVIDER=glm
LLM_API_KEY=your_api_key

# Neo4j配置  
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 2. 启动外部服务

```bash
# 启动Neo4j
docker run -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j

# 启动Milvus
docker run -p 19530:19530 milvusdb/milvus
```

### 3. 启动应用

```bash
cd smart_tourism_backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## API文档

启动后访问: http://localhost:8000/docs

### 用户画像API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/ai/profile/create` | POST | 创建用户画像（支持自然语言）|
| `/api/v1/ai/profile/{user_id}` | GET | 获取用户画像 |
| `/api/v1/ai/profile/feedback` | POST | 分析用户反馈 |

### LLM API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/ai/llm/chat` | POST | 与LLM对话 |
| `/api/v1/ai/llm/analyze` | POST | 分析用户输入 |
| `/api/v1/ai/llm/embed` | POST | 生成文本嵌入 |

### 知识图谱API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/ai/kg/poi/create` | POST | 创建POI节点 |
| `/api/v1/ai/kg/user/visit` | POST | 记录用户访问 |
| `/api/v1/ai/kg/user/{user_id}/stats` | GET | 获取用户统计 |
| `/api/v1/ai/kg/recommendations/{user_id}` | GET | 获取POI推荐 |
| `/api/v1/ai/kg/similar-users` | POST | 查找相似用户 |

### WebSocket

| 接口 | 说明 |
|------|------|
| `WS /ws/{user_id}` | WebSocket连接 |

### 系统状态

| 接口 | 说明 |
|------|------|
| `/api/v1/ai/status` | 获取系统状态 |
| `/api/v1/ws/status` | 获取WebSocket状态 |

---

## 测试

运行测试脚本:

```bash
cd smart_tourism_backend
python test_system.py
```

---

## 训练数据收集

系统自动收集训练数据，存储在 `training_data/agent_training_data.jsonl`。

统计收集的数据:

```python
from app.services.training_data_collector import get_training_collector

collector = get_training_collector()
stats = collector.get_statistics()
print(stats)
```

---

## 毕业设计亮点

1. **LLM集成**: GLM-4/ChatGPT自然语言理解与生成
2. **多智能体系统**: Agent编排器协调多个Agent
3. **知识图谱**: Neo4j存储用户-POI关系
4. **向量检索**: Milvus用户画像相似度匹配
5. **实时通信**: WebSocket推送更新
6. **数据收集**: 自动收集训练样本
