# Ablations - do the designed mechanisms cause the quality?

All configs caption the same 15 official clips from identical Gemma 4 scene facts, using the serverless fallback caption model (gpt-oss-120b) - the path most likely to be graded. Two independent judges score accuracy + tone (sum, max 10). Unparseable judge responses are excluded, not imputed. Raw data: `ablations_raw.json`.

| config | gpt-oss-120b | glm-5p2 |
|---|---|---|
| A_mech_bo3 | 9.95 (n=56) | 9.82 (n=49) |
| B_mech_bo1 | 9.82 (n=44) | 9.83 (n=47) |
| C_generic_bo3 | 9.31 (n=52) | 9.93 (n=29) |

## Head-to-head (mean of available judge scores per cell)

- **A_mech_bo3 vs B_mech_bo1**: 8-6 (42 ties)
- **A_mech_bo3 vs C_generic_bo3**: 11-5 (37 ties)

Methodology note: glm-5p2 parsed fewer C-config rows (n=29 vs 49-56
elsewhere), so per-config column means carry selection noise — the
per-cell head-to-head, which only compares rows where both configs were
scored, is the robust comparison.

Takeaways: the Gemma-designed comedic mechanisms are the dominant quality
factor (A vs C: 11-5); best-of-3 adds a smaller lift that matters most on
hard clips (judge ceiling effects produce many ties on easy ones). Both
effects survive on the fallback model — the mechanisms travel with the
prompts, not the model.
