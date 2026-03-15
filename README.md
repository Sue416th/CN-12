# Trailmark 项目启动指南

## 启动顺序

### 第一步：启动 Docker Desktop 和 Milvus

```powershell
# 启动 Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 等待 Docker 启动完成后，运行：
docker start milvus-etcd milvus-minio milvus attu
```

### 第二步：启动后端基础服务 (Express)

```powershell
cd backend
npm run dev
```
后端运行在：`http://127.0.0.1:3001`

### 第三步：启动 Python 后端服务

#### 启动文化解读服务 (run_cultural.py)
```powershell
cd backend
python run_cultural.py
```
服务运行在：`http://localhost:8000`

#### 启动行程规划服务 (run_trip.py)
```powershell
cd backend
python run_trip.py
```
服务运行在：`http://localhost:3204`

### 第四步：启动前端服务

```powershell
cd frontend
npm run dev
```
前端运行在：`http://localhost:8080`

---

## 服务端口对照表

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端主页 | http://localhost:8080 | React + Vite + Tailwind |
| 后端 API (Express) | http://127.0.0.1:3001 | 认证服务 |
| 文化解读服务 | http://localhost:8000 | FastAPI - 文化解读Agent |
| 行程规划服务 | http://localhost:3204 | FastAPI - 行程规划Agent |
| Milvus | http://localhost:19530 | 向量数据库 |
| Attu (Milvus 可视化) | http://localhost:18000 | Milvus 管理界面 |
| Milvus MinIO | http://localhost:9000 | 对象存储 |

---

## Docker 容器说明

项目使用 Docker Compose 管理以下服务：

- **milvus**: 向量数据库服务
- **milvus-etcd**: etcd 分布式存储
- **milvus-minio**: MinIO 对象存储
- **attu**: Milvus 可视化管理界面

---

## 快速启动命令汇总

```powershell
# 1. 启动 Docker Desktop 后，执行：
docker start milvus-etcd milvus-minio milvus attu

# 2. 启动后端 Express 服务
cd backend; npm run dev

# 3. 启动文化解读服务
cd backend; python run_cultural.py

# 4. 启动行程规划服务
cd backend; python run_trip.py

# 5. 启动前端
cd frontend; npm run dev
```

---

## 访问地址

- 前端页面：http://localhost:8080
- Attu 管理界面：http://localhost:18000
