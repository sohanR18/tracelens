# TraceLens

**Evidence-first AI incident investigation.** Rank competing root causes from structured log events, inspect source citations, and test how removing observations changes the result.

## Run

Requires Python 3.10+. No packages, account, API key, or network access required.

```sh
python3 server.py
```

Open http://127.0.0.1:8080. Load the synthetic sample, click **Run investigation**, and click a hypothesis to inspect its evidence. Exclude `database` and rerun to explore sensitivity. Import a JSON array for your own investigation. Export saves the full result as JSON.

```json
[
  {"time":"14:03:12", "service":"database", "severity":"error", "message":"Connection pool exhausted; too many connections"},
  {"time":"14:03:25", "service":"api", "severity":"error", "message":"Request failed waiting for database"}
]
```

Known service names: `database`, `api`, `cache`, `worker`, `upstream`, `gateway`. Unknown names work as observations but have no dependency edges. Timestamps are displayed in input order; no automatic time alignment is performed.

## What makes it useful

Most incident demos return a paragraph of generated advice. TraceLens exposes competing hypotheses, immutable per-investigation event citations, dependency coverage, and sensitivity tests. The UI supports a complete investigate–challenge–export workflow. Everything runs locally.

## Architecture

Browser → loopback HTTP API → event validation → Bayesian classifier → evidence aggregation → dependency coverage → ranked investigation + citations.

- `engine.py`: five-class multinomial Naive Bayes classifier with Laplace smoothing, trained on explicit domain phrases. Unknown tokens are ignored. Each event is scored independently.
- Evidence with class relevance > 0.27 is retained. Distinct messages contribute a saturating top-three aggregate, so repeated identical logs cannot inflate rankings.
- Ranking = 0.85 × text support + 0.15 × downstream dependency coverage. Graph-only hypotheses receive zero support. Scores are ranking signals, **not confidence probabilities**.
- A top score ≤ 0.45 returns `insufficient evidence`. This is a heuristic abstention rule, not a calibrated detector.
- Observation removal reruns the same pipeline. It is a sensitivity test, **not a causal intervention on an actual system**.
- `server.py`: standard-library server bound to loopback; bounded input, validation, cross-origin POST rejection, fixed asset routes.
- `static/`: responsive dashboard with safe text rendering, event import, hypothesis filtering, and export.

The supplied dependency graph is fixed. This prototype does not discover topology, parse raw log files, train embeddings, call an LLM, or execute remediation. It is intended for local trusted use; authentication and production hardening are outside the current scope.

## Verify

```sh
python3 -m unittest -v
python3 evaluate.py
```

The evaluation contains ten hand-authored synthetic holdout messages with vocabulary overlapping the training phrases. It checks basic behavior, not generalization to real incidents. Tests cover root-cause ranking, abstention, duplicate resilience, evidence removal, citation stability, and invalid input.

## Two-minute demo

1. Load the sample and investigate. A recent deployment is present, while database evidence should lead the ranking.
2. Click the database hypothesis; inspect the source observations and verification action.
3. Remove database observations and rerun. Explain why sensitivity is useful and why it cannot establish causality.
4. Restore all observations, import your own events, and export the report.
5. Show the tests and explain the limitations of the synthetic evaluation.

## Resume wording

Use this only after running the project and understanding the implementation:

> Built TraceLens, a local AI incident-investigation application combining Bayesian log classification, dependency-graph analysis, cited evidence, and observation-removal sensitivity tests; implemented an interactive dashboard, JSON API, and reproducible evaluation suite.

Do not claim reduced downtime, real-world accuracy, or production deployment without measuring those outcomes.

## Strong next milestones

1. Collect labeled incidents with permission; split by incident and service to prevent leakage. Measure macro-F1, top-k recall, abstention coverage, and calibration against a keyword baseline.
2. Make topology configurable and evaluate graph ablations.
3. Add semantic retrieval and compare against this baseline before increasing complexity.
4. Add an optional grounded LLM explanation layer that must cite retrieved event IDs, with unsupported-claim checks.
5. Add trace ingestion, durable investigation storage, and authentication before deployment.

## License

MIT. See LICENSE.
