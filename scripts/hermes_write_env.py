from pathlib import Path
import os

example = Path('.env.example').read_text(errors='ignore').splitlines()
out = []
for line in example:
    stripped = line.strip()
    if not stripped or stripped.startswith('#') or '=' not in line:
        out.append(line)
        continue
    key = line.split('=', 1)[0]
    if key == 'VECTOR_STORE_TYPE':
        out.append('VECTOR_STORE_TYPE=qdrant')
    elif key == 'QDRANT_URL':
        out.append('QDRANT_URL=http://localhost:6333')
    elif key == 'QDRANT_API_KEY':
        out.append(f"QDRANT_API_KEY={os.getenv('QDRANT_API_KEY', '')}")
    elif key == 'EMBEDDING_SERVICE':
        out.append('EMBEDDING_SERVICE=openai')
    elif key == 'EMBEDDING_MODEL':
        out.append(f"EMBEDDING_MODEL={os.getenv('EMBEDDING_MODEL') or 'text-embedding-3-small'}")
    else:
        out.append(f"{key}={os.getenv(key, '')}")
out.append('QDRANT_HOST=localhost')
out.append('QDRANT_PORT=6333')
Path('.env').write_text('\n'.join(out) + '\n')
print('rewrote .env from sourced zsh environment')
for k in [
    'ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL',
    'OPENAI_API_KEY','OPENAI_BASE_URL','ARK_API_KEY','ARK_BASE_URL',
    'EMBEDDING_API_KEY','EMBEDDING_BASE_URL','EMBEDDING_MODEL','QDRANT_API_KEY'
]:
    print(f"{k}={'SET' if os.getenv(k) else 'EMPTY'}")
