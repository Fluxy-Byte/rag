# RAG Local + Google ADK + Chroma

Stack: FastAPI + Google ADK (LiteLLM/OpenAI) + SentenceTransformers (all-MiniLM-L6-v2) + Chroma (persistente local ou servidor remoto na VPS).

## Destaques
- Ingestão de PDFs/TXTs com chunking configurável (tamanho e overlap) salvo em Chroma persistente.
- Suporta Chroma local (`./chroma`) ou remoto via `CHROMA_HOST` (ex.: VPS exposta em 8000).
- Contexto por usuário: o campo `user_id` vira `session_id` padrão, isolando histórico de cada usuário.
- Tool ADK `local_rag` cita a fonte no formato `[arquivo#chunk]` em cada resposta.
- Watcher opcional reindexa automaticamente novos arquivos em `data/raw`.

## Estrutura
- `src/settings.py` — configurações gerais (paths, top_k, modelo, porta, etc.).
- `src/chroma_setup.py` — client Chroma persistente local ou HTTP se `CHROMA_HOST` estiver definido.
- `src/chunker.py` — leitura de PDF/TXT e divisão em chunks com overlap.
- `src/rag.py` — ingestão/busca no Chroma.
- `src/cli.py` — CLI para ingestir, buscar e rodar watcher.
- `src/watcher.py` — monitora `data/raw` e dispara reindexação.
- `src/adk_app.py` — monta agente ADK e tool `local_rag`.
- `src/server.py` — FastAPI com endpoints `/query`, `/ingest`, `/debug/search`, `/health`.
- `scripts/patch_chromadb.py` — hotfix aplicado no build Docker para chromadb + pydantic.
- `docker-compose.yml` — serviços `chroma` e `api`.

## Pré-requisitos
- Python 3.10+
- Docker (para usar compose)
- `OPENAI_API_KEY` válido (sem prefixo `Bearer`).

## Setup local rápido
```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
# opcional: baixar o modelo de embedding (já salvo em models/)
.\.venv\Scripts\python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2').save('models/all-MiniLM-L6-v2')"
# configure .env
cp .env.example .env
```

## Ingestão e busca manual
```bash
.\.venv\Scripts\python -m src.cli ingest --reset   # lê data/raw e recria a coleção
.\.venv\Scripts\python -m src.cli search "pergunta"
# watcher (reindexa quando chega arquivo novo em data/raw)
.\.venv\Scripts\python -m src.cli watch
```

## Servidor FastAPI
```bash
$env:PORT="3000"; $env:HOST="0.0.0.0"
.\.venv\Scripts\python -m src.server
```
Exemplo de requisição mantendo contexto por usuário:
```bash
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"ping","user_id":"alice"}'
```
Se `session_id` não for enviado, ele assume o `user_id` para separar sessões.

## Chroma remoto (VPS)
1. Na VPS, suba só o serviço do Chroma:
```bash
docker compose up -d chroma
```
(ou `chromadb serve --host 0.0.0.0 --port 8000` se preferir).
2. Abra a porta 8000 na VPS.
3. No cliente/API, defina `CHROMA_HOST=http://<ip-vps>:8000` no `.env`.
4. Rode ingestão e servidor normalmente; tudo passa a usar o vetor remoto.

## Docker / Compose (API + Chroma juntos)
```bash
docker compose up -d --build
```
Portas padrão: API 3000, Chroma 8000. Volumes: `chroma_data` (vetores), `./data`, `./models` montados na API.

## Endpoints
- `POST /query` `{ question, user_id, session_id?, top_k? }`
- `POST /ingest` `{ reset?, chunk_size?, overlap?, source_dir? }`
- `POST /debug/search` `{ question, top_k? }`
- `GET /health`

## Troubleshooting
- Porta em uso: `netstat -ano | findstr :3000` e `taskkill /PID <pid> /F`.
- 401/403 OpenAI: verifique `OPENAI_API_KEY` (sem `Bearer`).
- Chroma remoto lento/offline: confira `CHROMA_HOST` e latência da VPS.
- Se reinstalar chromadb localmente, rode `python scripts/patch_chromadb.py`.
