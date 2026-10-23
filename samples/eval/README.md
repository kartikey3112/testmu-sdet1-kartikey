# Classifier evaluation

Real runs of `scripts/eval_classifier.py` with `openai/gpt-oss-120b` on Groq, prompt
`classifier.v1`, temperature 0. The numbers are exactly what the runs produced.

**[`20261022T200611Z/eval-report.md`](20261022T200611Z/eval-report.md): 53/55 = 0.964 overall.**

| Scenario | Faults | Scored | Correct |
|---|---|---|---|
| real_bug | the 3 `BUG_*` faults | 4 | 4 |
| environment_issue | the 3 `ENV_*` faults | 37 | 37 |
| flaky | the 2 `FLAKY_*` faults | 5 | 4 |
| mixed | 3 bugs + 2 flaky + `ENV_HEALTH_FAILING` | 9 | 8 |
| clean / health_only control | none / health failing only | 0 failing tests | — |

## How to read these numbers

- **The environment scenario dominates.** `ENV_DB_UNAVAILABLE` fails all 37 tests with 5xx
  and connection errors, which are easy to classify. **Without it: 16/18 = 0.889.**
- **Both misses are the same test (DASH-005), and a single run can't settle either one:**
  - *flaky → real_bug:* the latency fault delayed the pass-rate widget on all 3 attempts, so
    every attempt failed identically. That is indistinguishable from a real bug without
    history across runs.
  - *real_bug → flaky:* in the mixed run the same widget had the pass-rate bug and the
    latency fault, so attempts failed with different messages ("loading", then the wrong
    value), which reads as flaky.
- **Small samples.** It's one run per scenario, and the flaky faults are random, so a rerun
  gives different failing tests and possibly different numbers.
- **The trap held.** In the mixed scenario `/health` was down the whole time, yet no bug or
  flaky test was labelled `environment_issue`.

## Superseded attempts (kept on purpose, see `superseded/`)

- `flaky.classification.quota-failed.json`: the first flaky classification. One chunk was
  refused by Groq's daily token limit, so its test was never classified (decision D23). The
  flaky scenario was re-classified from the same test run once the quota refilled.
- `mixed.classification.before-json-fix.*`: the first mixed run. Groq's JSON mode rejected
  one chunk (HTTP 400 `json_validate_failed`) and the client didn't retry, so 4 tests were
  `unclassified`. After the fix (decision D25) the mixed scenario was run again; that run is
  the one scored. On the classified tests of the earlier run, one flaky test (LOGIN-010) was
  labelled `environment_issue`, the only time the failing-health-check trap caught the model.

## Cost

Measured from the API's `usage` fields: the environment scenario took 16 requests and about
91k tokens; the others took 2–3 requests each. A complete evaluation doesn't fit in one day
of Groq's free tier (200k tokens per day) together with test generation.
