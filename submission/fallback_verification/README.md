# Fallback-path verification (harness-key simulation)

**What this is:** proof that TextSink produces complete, tonally distinct
captions even when the Gemma 4 deployment is unreachable — the situation
if the grading harness injects its own Fireworks API key.

**How it was produced:** the container's models were pointed at a
deliberately invalid deployment reference (simulating a foreign key), and
the standard harness contract was run against the official sample clips
(`tasks.json` with the three published `amd-hackathon-clips` URLs).

**What happened** (see `probe_and_run.log`):
1. Startup probe hit the deployment → instant 404 → logged
   `switching to serverless models`. No time-budget wasted.
2. All tasks captioned via the fallback ladder (qwen3p7-plus vision +
   gpt-oss-120b captions, same grounding gates, same tone contracts,
   same best-of-3 self-judge — with the fallback model judging its own
   drafts).
3. One clip's grounding failed all retries → refused to caption blind →
   last-resort direct frame captioning. **No empty captions.**
4. 3 tasks completed in 62 seconds — far inside the 10-minute budget.

**Result:** `results_fallback_run.json` — exact harness schema, all four
style keys filled for every task.

The point: the private Gemma deployment makes the run better; it is not
what makes the run work. Every quality mechanism (grounding discipline,
tone contracts, best-of-N self-judging) survives on the fallback path,
and the stderr log states which path served the run.
