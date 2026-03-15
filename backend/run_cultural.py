import os
import sys
from pathlib import Path

# 确保 backend 目录在 Python 路径中
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.cultural.main:app", host="0.0.0.0", port=8000, reload=True)
