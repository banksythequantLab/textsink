# TextSink — Submission Plan (deadline Fri Jul 11, 12:00 PM ET)
_Updated 2026-07-08. Full context in HANDOFF.md._

## TODAY — Wed Jul 8 (unblock + real output)
- [ ] Create/join lablab team (REQUIRED for submission; one AMD GPU pod per team). Do first — registration issues need lead time.
- [ ] Gather 3-5 real clips (30s-2min, varied: dialogue, action, product/tech, outdoor).
- [ ] Wake gemma4cap deployment (expect ~3-5 min cold start) and run: python run.py --input <clips-folder>
- [ ] Review captions.json for accuracy + tone; re-run weak styles; keep best 2 clips' outputs.
- [ ] Run eval/run_eval.py self-eval on real outputs; note scores for the deck.

## THU Jul 9 (assets + repo)
- [ ] Paste genuine captions into slide 6 of TextSink_Track2.pptx (replace "OPEN 24/7" sample); re-export PDF.
- [ ] Update demo_script.md with the real clip/captions.
- [ ] Record 2-3 min demo per script — real terminal run on screen. If cold start hurts pacing, warm the deployment first, cut the wait, caption "~4 min cold start (scale-to-zero)".
- [ ] Push to public GitHub as `textsink` (verify .env NOT in history; .env.example present).
- [ ] Put real repo URL on closing deck slide + README; re-export deck PDF.
- [ ] (Optional) docker build -t textsink . && mock-mode smoke test in container.

## FRI Jul 10-11 AM (submit — don't wait for the deadline)
- [ ] Assemble submission on lablab: repo URL, demo video, deck PDF, cover.png, description.
- [ ] Submit Thu night or Fri morning; verify it shows as received.
- [ ] After confirmation: PATCH .../deployments/gemma4cap:scale {"replicaCount":0}

## Risks
- lablab team/registration friction → do today.
- Cold start eats demo time → warm before recording.
- Secret leak on GitHub push → check history before making public; rotate key if leaked.
- Fireworks credits (~$56) fine for a few runs; don't leave deployment min>0.
