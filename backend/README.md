# Auth Backend (MySQL)

This backend provides registration/login APIs for the frontend app.

## 1) Setup MySQL schema

Run `schema.sql` in your MySQL client:

```sql
SOURCE path/to/backend/schema.sql;
```

## 2) Configure environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

## 3) Install and run

```bash
npm install
npm run dev
```

Server starts at `http://localhost:3001`.

## API

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me` (Bearer token required)
- `PUT /api/auth/profile` (Bearer token required)
- `PUT /api/auth/password` (Bearer token required)

---

# 文化解读智能体 API

提供文化景点的智能问答服务。

## 启动方式

```bash
cd backend
python run_cultural.py
```

服务启动后访问 `http://localhost:8000`

## API 接口

- `GET /` - 根路径，返回 API 状态
- `POST /api/cultural/chat` - 非流式聊天接口
- `POST /api/cultural/chat/stream` - 流式聊天接口
- `POST /api/cultural/chat/images` - 带图片的聊天接口

## 请求示例

```bash
curl -X POST http://localhost:8000/api/cultural/chat/images \
  -H "Content-Type: application/json" \
  -d '{"message": "请介绍一下西湖"}'
```
