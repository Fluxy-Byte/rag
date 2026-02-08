# RAG Local + Google ADK + Chroma

Pipeline RAG local (ingestão de PDFs/TXTs), embeddings SentenceTransformers, base vetorial Chroma (local ou remota) e agente ADK com ferramenta `local_rag` citando fontes.

## Estrutura
- `src/`
  - `settings.py` — configurações (paths, modelo, top_k, modelo LLM, etc.).
  - `chroma_setup.py` — cliente Chroma local (persistente) ou remoto (`CHROMA_HOST`).
  - `chunker.py` — leitura PDF/TXT e chunking com overlap.
  - `rag.py` — ingestão e busca no Chroma.
  - `cli.py` — ingestão, busca manual e watcher.
  - `watcher.py` — monitora `data/raw` e reindexa automaticamente.
  - `adk_app.py` — tool `local_rag`, runner ADK, gera respostas.
  - `server.py` — FastAPI em `/query`, `/ingest`, `/debug/search`.
- `scripts/patch_chromadb.py` — hotfix compatibilidade chromadb + pydantic v2 (aplicado no build).
- `docker-compose.yml` — sobe `chroma` + `api`.
- `Dockerfile` — imagem da API.

## Requisitos
- Python 3.10+
- Docker (para usar compose)
- Chave OpenAI (`OPENAI_API_KEY`)

## Ambiente local
```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

Baixar modelo de embedding (já fizemos, mas caso precise):
```bash
.\.venv\Scripts\python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2').save('models/all-MiniLM-L6-v2')"
```

## Variáveis (.env)
Veja `.env.example` e copie para `.env`:
```bash
cp .env.example .env
```

## Ingestão / teste manual
```bash
.\.venv\Scripts\python -m src.cli ingest --reset   # carrega data/raw
.\.venv\Scripts\python -m src.cli search "pergunta"
```

Watcher automático:
```bash
.\.venv\Scripts\python -m src.cli watch
```

## Servidor FastAPI
```bash
$env:PORT="3000"; $env:HOST="0.0.0.0"
.\.venv\Scripts\python -m src.server
```
Consulta:
```bash
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"ping","user_id":"alice"}'
```
`user_id` vira o `session_id` se não enviado, isolando contexto por usuário.

## Chroma remoto (VPS)
- Suba um servidor Chroma (ex: `chromadb serve --host 0.0.0.0 --port 8000`).
- Defina `CHROMA_HOST=http://<ip-vps>:8000` no `.env`.
- A ingestão e buscas passam a usar o Chroma remoto.

## Docker / Compose
Build e subir tudo (API + Chroma):
```bash
docker compose up -d --build
```
Portas:
- API: 3000
- Chroma: 8000 (exposta para debug, pode restringir se quiser)

Volumes:
- `chroma_data` (vetor) persiste no Docker.
- `./data` e `./models` montados na API.

## Endpoints
- `POST /query` `{ question, user_id, session_id?, top_k? }`
- `POST /ingest` `{ reset?, chunk_size?, overlap?, source_dir? }` (assíncrono via background)
- `POST /debug/search` `{ question, top_k? }` (retorna matches brutos)
- `GET /health`

## Notas
- Patch do chromadb é aplicado no build (`scripts/patch_chromadb.py`). Se reinstalar chromadb localmente, rode o script.
- Prompt do agente cita fontes no formato `[fonte: arquivo#chunk]`; se não achar evidência, responde que não encontrou.

## Troubleshooting
- Porta ocupada: `netstat -ano | findstr :3000` e `taskkill /PID <pid> /F`.
- 401/403 OpenAI: verifique `OPENAI_API_KEY` (sem prefixo `Bearer`).
- Chroma remoto indisponível: cheque `CHROMA_HOST` e latência da VPS.
