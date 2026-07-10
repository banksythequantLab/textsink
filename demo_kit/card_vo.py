import requests

REF = r"B:\freeclone-backend\derek-voice.wav"
LINES = {
    "vo_open": ("TextSink. Four voices. One truth. Built on Gemma four and "
                "Fireworks AI, for the AMD Developer Hackathon."),
    "vo_end": ("TextSink. Thanks to AMD, Fireworks AI, Google DeepMind's "
               "Gemma, and lablab dot AI. Find us on GitHub."),
}
for name, text in LINES.items():
    with open(REF, "rb") as f:
        r = requests.post("http://johnson:8300/api/clone",
                          files={"prompt_audio": ("ref.wav", f, "audio/wav")},
                          data={"text": text, "lang": "en"}, timeout=900)
    assert r.status_code == 200 and len(r.content) > 2000, r.text[:200]
    open(f"{name}.wav", "wb").write(r.content)
    print(name, "ok", len(r.content) // 1024, "KB", flush=True)
