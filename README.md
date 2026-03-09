# 杭州智慧文旅 · 行程规划平台

基于多智能体的智慧文化旅行管理平台，前端 + 后端完整实现。

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: React + TypeScript + Vite + React Router

## 本地运行

### 1. 后端

```bash
cd smart_tourism_backend
uvicorn app.main:app --reload
```

后端默认运行在：<http://127.0.0.1:8000>  
API 文档：<http://127.0.0.1:8000/docs>

### 2. 前端

```bash
cd smart_tourism_frontend
npm install
npm run dev
```

前端默认运行在：<http://localhost:5173>

### 3. 使用说明

1. 打开 http://localhost:5173
2. 在首页填写开始/结束日期、预算档位、兴趣偏好
3. 点击「一键生成行程」，系统会调用行程规划智能体生成个性化行程
4. 生成后自动跳转到行程详情页
5. 可从「查看我的行程」进入历史行程列表，点击任意行程查看详情

---

## 开发进度记录

### 2026-03-08 (今天)

**已完成：**

1. **启动服务** - 启动了后端和前端服务进行测试

2. **天气API修复** - 修复了高德天气API的参数问题
   - 问题：`extensions=forecast` 应改为 `extensions=all`
   - 效果：现在可以正确获取明天及后天的天气预报

3. **POI过滤逻辑修复** - 修复了POI过滤后为空导致的报错问题
   - 问题：过滤条件太严格时返回空列表导致系统报错
   - 修复：当没有匹配的POI时返回所有POI而不是报错

4. **日期时间格式解析** - 修复了WeatherAgent中的日期解析错误

5. **天气数据返回** - 修复了weather_info中forecast数组为空的问题
   - 确保后端返回完整的天气预报数据给前端

6. **前端显示** - 改进了天气信息的显示效果

7. **行程详情页天气显示** - 修复了从My Trips进入行程详情时天气数据消失的问题
   - 原因：天气数据没有保存到数据库，每次获取详情时需要重新从API获取
   - 修复：修改了`itinerary_service.py`中的`get_by_id`方法，确保每次都重新获取最新的天气数据

8. **天气数据中文化** - 将天气数据显示从中文改为英文
   - 添加了`WEATHER_MAP`天气类型映射（中→英）
   - 添加了`WIND_DIRECTION_MAP`风向映射
   - 添加了`_translate_aqi()` AQI翻译方法
   - 修复了模拟数据也使用英文

9. **Save Profile功能改进** - 改进了用户保存画像后的反馈体验
   - 修复了前端消息显示的动画效果
   - 添加了成功/错误图标的视觉反馈
   - 后端日志显示功能正常工作

10. **用户画像个性化推荐** - 实现了完整的用户画像到行程推荐的流程

    **问题描述：**
    - 用户设置偏好后保存到数据库，但生成行程时没有使用这些偏好信息

    **实现方案：**
    - **UserProfileAgent** 分析用户输入的兴趣、预算、体能等信息，生成多维度用户画像
    - **ItineraryPlannerAgent** 将用户画像信息传递给行程规划服务
    - **ItineraryService** 新增个性化推荐参数：
      - `_sort_pois_by_profile()`: 根据用户文化偏好进行POI排序
      - `_calculate_daily_pois_count()`: 根据旅行风格和体能计算每日景点数量
      - `_calculate_max_daily_hours()`: 根据体能计算每日最大游玩时间

    **数据流程：**
    ```
    用户设置偏好 → Save Profile → 存入数据库
                                    ↓
    生成行程时 → 读取用户画像 → UserProfileAgent 分析
                                    ↓
                            ItineraryPlannerAgent
                                    ↓
                    ItineraryService.generate_itinerary()
                                    ↓
            个性化排序 + 每日景点数量调整 → 生成行程
    ```

11. **LLM API Key处理** - 修复了无效API Key导致的服务崩溃问题
    - 修改了`LLMService`，当没有有效API Key时会优雅降级
    - 清空了`.env`中的占位符API Key

12. **编码问题修复** - 修复了Windows环境下的中文编码错误
    - 移除了orchestrator.py中的中文字符

**待解决：**

1. ~~**天气预报范围问题**~~ - 已解决：通过重试逻辑和模拟数据fallback
   - ~~高德天气API只返回3天预报，当行程日期超出范围时无法显示对应天气~~
   - ~~需要优化：将完整的天气预报列表返回给前端，让前端根据行程日期显示对应的天气~~

2. ~~**日期对齐问题**~~ - 已解决：WeatherAgent中添加了日期对齐逻辑

---

## 项目结构

```
smart_tourism_backend/
├── app/
│   ├── agents/          # 智能体模块
│   │   ├── orchestrator.py
│   │   ├── itinerary_planner_agent.py
│   │   ├── weather_agent.py
│   │   ├── culture_agent.py
│   │   └── user_profile_agent.py
│   ├── api/             # API路由
│   ├── models/          # 数据模型
│   ├── schemas/         # Pydantic模型
│   ├── services/        # 业务逻辑
│   └── main.py          # 入口文件

smart_tourism_frontend/
├── src/
│   ├── pages/           # 页面组件
│   │   ├── Home.tsx
│   │   ├── ItineraryDetail.tsx
│   │   └── ItineraryList.tsx
│   ├── App.tsx
│   └── main.tsx
```

---

## API配置

需要在 `.env` 文件中配置以下API：

- **高德地图API**: POI搜索、天气查询 - ✅ 已配置
- **和风天气API**: 天气数据 - ✅ 已配置
- **LLM (GLM)**: 用户画像分析、行程优化 - ⚠️ 未配置（可选）
- **Neo4j**: 知识图谱 - ⚠️ 未运行（可选）
- **Milvus**: 向量数据库 - ⚠️ 未运行（可选）

**注意：** 
- LLM、Neo4j、Milvus 为可选服务，不影响核心功能运行
- 如需启用LLM功能，请在 `.env` 中填入有效的 API Key

## 核心功能模块

### 智能体 (Agents)

- **UserProfileAgent**: 用户画像分析 - ✅ 完成
- **EnhancedUserProfileAgent**: 增强版画像（LLM+知识图谱）- ✅ 完成（可选LLM）
- **ItineraryPlannerAgent**: 行程规划 - ✅ 完成
- **CultureAgent**: 文化内涵丰富 - ✅ 完成
- **WeatherAgent**: 天气因素考虑 - ✅ 完成
- **Orchestrator**: 智能体编排协调 - ✅ 完成

### 个性化推荐流程

```
1. 用户在"My Profile"中设置偏好（兴趣、预算、旅行风格、体能等）
2. 点击"Save Profile"保存到数据库
3. 生成行程时，系统读取用户画像
4. UserProfileAgent 分析用户偏好，生成多维度画像
5. ItineraryPlannerAgent 根据画像进行个性化推荐：
   - 根据文化偏好排序POI
   - 根据体能调整每日景点数量
   - 根据旅行风格调整游玩时间
6. 生成个性化行程
```

## 启动命令

```bash
# 后端
cd smart_tourism_backend
uvicorn app.main:app --reload --port 8000

# 前端
cd smart_tourism_frontend
npm run dev
```

访问 http://localhost:5173 使用应用。
