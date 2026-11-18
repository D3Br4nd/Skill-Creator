# Comparing a skill with the same agent working unaided

Use a paired evaluation to answer a practical question: does loading the skill improve the result for this task? A structural validator checks the package. A behavioral evaluation checks outputs produced in actual agent sessions.

## Before either run

1. Draft three realistic prompts covering a typical request, a paraphrase and an edge case. Supply the same task policy and input files to both conditions. For a complex workflow, reserve inputs the skill author has not seen.
2. Write observable scoring criteria and expected results before seeing either answer. A criterion can check a numeric total, an omitted decision, a file that opens correctly or a policy constraint. For subjective work, define examples of a passing result and score anonymous outputs where practical.
3. Keep the answer key, assertions and previous outputs outside both workers' context. Expose only the prompt and raw inputs to the baseline. The assisted worker also receives the installable skill and its runtime resources. Keep bundled evals out of its context. Use an isolated workspace when automatic discovery would load the skill into the baseline.

## Run and score

- Use fresh independent sessions for each prompt and condition. Match the host, model, settings, tools and input bytes within each pair. Ordinary tools available to the baseline remain available to the assisted worker.
- Save the actual outputs, including failures. Score both with the same criteria. Compare by case and criterion. Record gains, ties and regressions, and inspect any material errors even if the overall score improves. When the user requests a machine-readable format, score direct parsing separately from content recovered by stripping wrappers. If a shared fixture or permission fails, fix the setup for both conditions and retain the original attempt.
- For a multi-agent target, repeat at least one matched pair on a second host when available and authorized. Record each host and model separately. A second session on the same host is a repeat. An interpreter or validator run tests a different property.
- A tie on a small sample supports a statement about that sample. Claim speed, cost or consistency improvements only when measured under comparable conditions. Label revised skills and reruns separately. Use fresh cases before drawing a broader conclusion.
- When a runner, permission or credential is unavailable, finish the feasible checks and record the exact missing run. Keep comparison results separate from trigger-query checks.

## Record the outcome

In the generated README or a linked local report, give the prompt IDs, input and answer-key locations, host/model if known, number of runs, scores by condition, and one concrete example explaining the result. Provide a way to inspect or replay the scoring. Store sensitive run outputs locally according to the user's sharing requirements.
