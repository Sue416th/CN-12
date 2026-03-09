from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Basic
    PROJECT_NAME: str = "Smart Cultural Tourism Platform"
    ENV: str = "dev"

    # Database (默认使用 SQLite，便于本地开发，无需额外安装数据库)
    DATABASE_URL: str = "sqlite:///./tourism.db"

    # Vector DB (Milvus)
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530

    # ==================== LLM Configuration ====================
    # LLM Provider: glm, openai, qwen
    LLM_PROVIDER: str = "glm"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "glm-4"
    LLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"

    # ==================== Knowledge Graph (Neo4j) ====================
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # 外部API配置
    # 和风天气API (https://dev.qweather.com/)
    QWEATHER_API_KEY: str = ""
    QWEATHER_API_HOST: str = "https://devapi.qweather.com"

    # 高德地图API (https://lbs.amap.com/)
    AMAP_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    class Config:
        env_file = ".env"


settings = Settings()

