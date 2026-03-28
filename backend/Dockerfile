FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kolkata
# Hybrid mode switch: "api" = use Groq/OpenAI, "local" = local models (future)
ENV MODEL_MODE=api

WORKDIR /app

# System deps — ffmpeg for audio duration validation via pydub, nothing else heavy
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps — changes occasionally; copied before app code to use Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --timeout 120 --retries 3 -r requirements.txt

# App code — changes constantly, always last
COPY . .
RUN mkdir -p /app/uploads

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]