# 🎙️ VoiceTrace AI

> **Voice-powered AI Business Assistant** — Speak your day, get insights instantly.

Built with WhisperX · Groq · LangGraph · Qdrant · SentenceTransformers · Streamlit

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────────────────────┐
│  Streamlit UI   │────▶│  FastAPI Backend                                     │
│  (Port 8501)    │◀────│  (Port 8000)                                         │
└─────────────────┘     │                                                      │
                        │  ┌─────────────────────────────────────────────────┐  │
                        │  │          LangGraph Pipeline                     │  │
                        │  │                                                 │  │
                        │  │  transcribe ─▶ guardrail ─▶ sanitize           │  │
                        │  │       │            │            │               │  │
                        │  │       ▼            ▼            ▼               │  │
                        │  │   WhisperX    LlamaGuard    PII Redact         │  │
                        │  │                   │                             │  │
                        │  │            [UNSAFE? → END]                     │  │
                        │  │                   │                             │  │
                        │  │                   ▼                             │  │
                        │  │  extract ─▶ memory_analysis ─▶ router          │  │
                        │  │     │            │               │              │  │
                        │  │     ▼            ▼          ┌────┴────┐         │  │
                        │  │   Groq       Groq(small)    │         │         │  │
                        │  │                          Important  Routine     │  │
                        │  │                             │         │         │  │
                        │  │                             ▼         │         │  │
                        │  │                      long_term_mem    │         │  │
                        │  │                     (embed+Qdrant)    │         │  │
                        │  │                             │         │         │  │
                        │  │                             └────┬────┘         │  │
                        │  │                                  ▼              │  │
                        │  │                            retrieval            │  │
                        │  │                          (Qdrant RAG)           │  │
                        │  │                                  │              │  │
                        │  │                                  ▼              │  │
                        │  │                            decision             │  │
                        │  │                         (Groq response)         │  │
                        │  └─────────────────────────────────────────────────┘  │
                        └──────────────────────────────────────────────────────┘
                                      │                    │
                        ┌─────────────┘                    └─────────────┐
                        ▼                                                ▼
                ┌───────────────┐                              ┌───────────────┐
                │    SQLite     │                              │    Qdrant     │
                │ (Short-term)  │                              │ (Long-term)   │
                └───────────────┘                              │  Port 6333    │
                                                               └───────────────┘
```

---

## 📁 Project Structure

```
VoiceTrace-AI/
│
├── backend/
│   ├── main.py              # FastAPI app with /process, /health endpoints
│   ├── graph.py             # LangGraph pipeline orchestrator
│   ├── config.py            # Centralized configuration
│   ├── models.py            # Pydantic models & PipelineState
│   ├── requirements.txt     # Backend Python dependencies
│   ├── Dockerfile           # CUDA-enabled backend image
│   ├── nodes/               # LangGraph pipeline nodes
│   │   ├── __init__.py
│   │   ├── transcribe.py    # WhisperX transcription
│   │   ├── guardrail.py     # LlamaGuard safety check
│   │   ├── sanitize.py      # PII redaction
│   │   ├── extract.py       # Groq entity extraction
│   │   ├── memory_analysis.py # Memory importance classifier
│   │   ├── memory_router.py # Conditional routing
│   │   ├── long_term_memory.py # Qdrant storage
│   │   ├── retrieval.py     # RAG retrieval
│   │   └── decision.py      # Final response generation
│   └── services/            # Core services
│       ├── __init__.py
│       ├── transcription.py # WhisperX wrapper
│       ├── groq_llm.py      # Groq API (safety, extraction, memory, response)
│       ├── embedding.py     # SentenceTransformer (multilingual-e5-large)
│       ├── qdrant_memory.py # Qdrant client
│       └── sqlite_memory.py # SQLite short-term storage
│
├── frontend/
│   ├── app.py               # Streamlit UI
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml       # Full orchestration
├── .env.example             # Environment template
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** installed
- **NVIDIA GPU** with drivers (or CPU fallback)
- **NVIDIA Container Toolkit** (for GPU passthrough to Docker)
- **Groq API Key** — [Get one free at console.groq.com](https://console.groq.com)

### 1. Clone & Configure

```bash
cd VoiceTrace-AI

# Create your environment file
cp .env.example .env

# Edit .env and set your Groq API key
# GROQ_API_KEY=gsk_your_key_here
```

### 2. Launch with Docker Compose

```bash
# Build and start all services
docker compose up --build

# Or run in background
docker compose up --build -d
```

### 3. Access the App

| Service    | URL                          |
|------------|------------------------------|
| Streamlit  | http://localhost:8501         |
| FastAPI    | http://localhost:8000         |
| API Docs   | http://localhost:8000/docs    |
| Qdrant     | http://localhost:6333/dashboard |

### 4. Test It

1. Open http://localhost:8501
2. Upload a `.wav` or `.mp3` audio file (max 3 minutes)
3. Click **"🚀 Process Audio"**
4. View: Transcript → Extracted Data → Memory Decision → Past Memories → AI Response

---

## 🧪 Example Test Flow

### Sample Audio Content (record this or use a TTS tool):

> "Today was a good day at the shop. I sold 15 kilos of tomatoes at 40 rupees per kilo
> and 8 kilos of onions at 30 rupees per kilo. I also bought new weighing scales for
> 2000 rupees. My total expenses for rent this month were 5000 rupees. Overall I'm
> happy with the business but worried about rising vegetable prices."

### Expected Output:

- **Transcript**: Full text from the audio
- **Extracted Data**:
  ```json
  {
    "items_sold": [
      {"item": "tomatoes", "quantity": 15, "price": 40},
      {"item": "onions", "quantity": 8, "price": 30}
    ],
    "expenses": [
      {"description": "weighing scales", "amount": 2000},
      {"description": "rent", "amount": 5000}
    ],
    "total_earnings": 840,
    "total_expenses": 7000,
    "net_profit": -6160,
    "sentiment": "mixed",
    "key_topics": ["vegetable sales", "expenses", "price concerns"]
  }
  ```
- **Memory**: ⭐ Important (first day's data, concerns about pricing)
- **AI Response**: Summary + insights + recommendations

---

## 🔧 Development (Without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install git+https://github.com/m-bain/whisperx.git

# Start Qdrant
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Run the backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run app.py
```

---

## ⚡ Performance Notes

- **WhisperX**: First run downloads model (~1.5 GB for `medium`). Subsequent runs use cache.
- **SentenceTransformers**: First run downloads `multilingual-e5-large` (~2.2 GB). Cached after.
- **Groq API**: Sub-second response times for all LLM calls.
- **Target**: < 15 seconds total processing for a 1-minute audio clip.

---

## 🔑 Environment Variables

| Variable              | Default          | Description                     |
|-----------------------|------------------|---------------------------------|
| `GROQ_API_KEY`        | (required)       | Groq API key                    |
| `QDRANT_HOST`         | `localhost`      | Qdrant server host              |
| `QDRANT_PORT`         | `6333`           | Qdrant server port              |
| `WHISPERX_MODEL`      | `medium`         | WhisperX model size             |
| `WHISPERX_DEVICE`     | `cuda`           | `cuda` or `cpu`                 |
| `WHISPERX_COMPUTE_TYPE`| `float16`       | `float16`, `int8`, or `float32` |
| `BACKEND_URL`         | `http://localhost:8000` | Backend URL (for Streamlit) |

---

## 🛡️ Safety

- **LlamaGuard 3** (via Groq) filters every transcript before processing
- **PII Redaction**: Phone numbers, emails, credit cards, and SSNs are masked
- Unsafe content stops the pipeline immediately

---

## 📝 License

MIT — Built for hackathon excellence 🏆
