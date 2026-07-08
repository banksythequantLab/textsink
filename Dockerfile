FROM python:3.11-slim

# ffmpeg + ffprobe are required for frame sampling.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Primary: Gemma 4 (26B MoE) does BOTH vision grounding and all four styles
# via our dedicated Fireworks deployment. If the deployment is unreachable
# under the grader's key, main.py automatically cuts over to serverless
# models per-task so no task ever scores zero (see main.py).
ENV VISION_MODEL="accounts/fireworks/models/gemma-4-26b-a4b-it#accounts/banksythequant/deployments/gemma4cap" \
    CAPTION_MODEL="accounts/fireworks/models/gemma-4-26b-a4b-it#accounts/banksythequant/deployments/gemma4cap" \
    REASONING_EFFORT=none \
    SCENE_MAX_TOKENS=3000 \
    TRANSCRIBE_BACKEND=none

# Track 2 judging-harness contract:
#   reads  /input/tasks.json   -> writes /output/results.json
# FIREWORKS_API_KEY is provided at `docker run -e ...` time - never baked.
ENTRYPOINT ["python", "main.py"]
