from pathlib import Path
import os


def clean(value: str | None, default: str = "") -> str:
    if value is None:
        return default
    value = value.replace("\r", "").replace("\n", "").strip()
    return value if value else default


def getenv_any(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return clean(value)
    return default


lines = [
    f"ANTHROPIC_API_KEY={getenv_any('ANTHROPIC_API_KEY')}",
    f"ANTHROPIC_AUTH_TOKEN={getenv_any('ANTHROPIC_AUTH_TOKEN')}",
    f"ANTHROPIC_BASE_URL={getenv_any('ANTHROPIC_BASE_URL')}",
    f"OPENAI_API_KEY={getenv_any('OPENAI_API_KEY')}",
    f"OPENAI_BASE_URL={getenv_any('OPENAI_BASE_URL')}",
    f"ARK_API_KEY={getenv_any('ARK_API_KEY')}",
    f"ARK_BASE_URL={getenv_any('ARK_BASE_URL', default='https://ark.cn-beijing.volces.com/api/v3/chat/completions')}",
    f"ARK_MODEL={getenv_any('ARK_MODEL', default='doubao-seed-2-0-mini-260215')}",
    f"ARK_TIMEOUT={getenv_any('ARK_TIMEOUT', default='120')}",
    f"ARK_REASONING_EFFORT={getenv_any('ARK_REASONING_EFFORT', default='medium')}",
    "EMBEDDING_SERVICE=openai",
    f"EMBEDDING_API_KEY={getenv_any('EMBEDDING_API_KEY', 'OPENAI_API_KEY')}",
    f"EMBEDDING_BASE_URL={getenv_any('EMBEDDING_BASE_URL', 'OPENAI_BASE_URL')}",
    f"EMBEDDING_MODEL={getenv_any('EMBEDDING_MODEL', default='text-embedding-3-small')}",
    "EMBEDDING_MODEL_PATH=./.models/bge-small-zh-v1.5",
    "EMBEDDING_USE_GPU=true",
    "VECTOR_STORE_TYPE=qdrant",
    "QDRANT_URL=http://localhost:6333",
    f"QDRANT_API_KEY={getenv_any('QDRANT_API_KEY')}",
    "QDRANT_HOST=localhost",
    "QDRANT_PORT=6333",
    "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000",
    "DISABLE_AUTO_DAEMON=0",
    "LOG_LEVEL=INFO",
    "LOG_FILE=logs/aitext.log",
]

Path('.env').write_text("\n".join(lines) + "\n", encoding='utf-8')
print('WROTE_MINIMAL_ENV')
