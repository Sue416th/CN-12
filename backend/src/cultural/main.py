from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.cultural.agents.culture_agent import CulturalInterpretationAgent
import json

app = FastAPI(title="Cultural Interpretation Agent API", version="1.0.0")

# 添加 CORS 中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:5173", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = CulturalInterpretationAgent()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


class ChatWithImagesResponse(BaseModel):
    answer: str
    images: list
    keywords: str


@app.get("/")
async def root():
    return {"message": "Cultural Interpretation Agent API"}


@app.post("/api/cultural/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Cultural chat endpoint (non-streaming)"""
    try:
        answer = agent.chat(request.message)
        return ChatResponse(answer=answer)
    except Exception as e:
        import traceback
        print(f"Error in chat: {e}")
        print(traceback.format_exc())
        raise


@app.post("/api/cultural/chat/stream")
async def chat_stream(request: ChatRequest):
    """Cultural chat endpoint (streaming)"""
    def generate():
        for chunk in agent.chat_stream(request.message):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/cultural/chat/images", response_model=ChatWithImagesResponse)
async def chat_with_images(request: ChatRequest):
    """Cultural chat endpoint with images"""
    try:
        result = agent.chat_with_images(request.message)
        return ChatWithImagesResponse(
            answer=result["answer"],
            images=result["images"],
            keywords=result["keywords"]
        )
    except Exception as e:
        import traceback
        print(f"Error in chat_with_images: {e}")
        print(traceback.format_exc())
        raise
