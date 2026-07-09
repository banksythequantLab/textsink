# SUBMIT.md — Friday morning runbook (deadline 12:00 PM ET)

Work top to bottom. Target: submitted and verified by 11:00 AM ET.

## 1. Pin the GPU (~9:30 AM)
```powershell
cd B:\amd-track2-captioner
$k = (Get-Content .env | ?{$_ -match '^FIREWORKS_API_KEY='}) -replace '^FIREWORKS_API_KEY=',''
Invoke-RestMethod -Method Patch -Uri 'https://api.fireworks.ai/v1/accounts/banksythequant/deployments/gemma4cap?updateMask=min_replica_count' -Headers @{Authorization="Bearer $k";'Content-Type'='application/json'} -Body '{"minReplicaCount":1}'
```
Verify ready (~5 min): readyReplicaCount = 1.

## 2. Final sanity run (optional, 5 min)
```powershell
$env:INPUT_PATH='B:\amd-track2-captioner\test_input\tasks.json'
$env:OUTPUT_PATH='B:\amd-track2-captioner\final_check.json'
python -u main.py
```
Expect: "probe: Gemma deployment reachable - all-Gemma run", 3 tasks, ~60-100s.

## 3. Upload the demo video
- File: B:\amd-track2-captioner\demo_kit\TextSink_demo_roughcut.mp4 (or final)
- Upload to lablab's video field (or YouTube unlisted + link, per form).

## 4. Fill the lablab form
Everything is paste-ready in submission\lablab_copy.md:
- Title, short description, long description (includes the 18-4 stat)
- Tags: Gemma, Fireworks AI, AMD Developer Cloud, Docker, FFmpeg, Python
- GitHub: https://github.com/banksythequantLab/textsink
- Slides: submission\TextSink_Track2.pdf
- Cover: submission\cover.png
- Application URL: https://banksythequantlab.github.io/textsink/
  (verify it loads first!)

## 5. Submit + verify
- Click submit BEFORE 11:30 AM ET. Screenshot the confirmation.
- Verify the submission appears on the hackathon submissions page.

## 6. After confirmed
- Leave gemma4cap pinned for a few hours if credits allow (graders may run
  same-day), then:
```powershell
Invoke-RestMethod -Method Patch -Uri 'https://api.fireworks.ai/v1/accounts/banksythequant/deployments/gemma4cap?updateMask=min_replica_count' -Headers @{Authorization="Bearer $k";'Content-Type'='application/json'} -Body '{"minReplicaCount":0}'
```

## Open items (do tonight if possible)
- [ ] GHCR image push — needs Derek once: `gh auth refresh -h github.com -s write:packages`
      then tell Claude to retry the push.
- [ ] Ask in hackathon Discord: does the Track 2 harness inject its own
      FIREWORKS_API_KEY, or use the team's? (Decides how much the pin matters.)
- [ ] Verify GitHub Pages is live: https://banksythequantlab.github.io/textsink/
