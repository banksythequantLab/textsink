# Harness simulation — full hidden-set-sized dress rehearsal

`results_15clips.json` is the output of running the exact harness
contract (`main.py`, `tasks.json` with all 15 official
`amd-hackathon-clips` bucket URLs) end-to-end on the all-Gemma path:

- **15 tasks in 199 seconds** — roughly one-third of the ~10-minute
  harness budget (`run.log` has per-task timing).
- **Every caption filled, zero refusal text** — the refusal filter +
  sane-scene gate + three-tier ladder make an empty caption structurally
  impossible. One task's primary grounding failed all retries during
  this run and was recovered by the ladder mid-flight, as designed.
- Best-of-3 self-judged drafting enabled (the shipped configuration).

Companion artifact: `submission/fallback_verification/` shows the same
contract surviving a forced foreign-key run on the serverless path.
