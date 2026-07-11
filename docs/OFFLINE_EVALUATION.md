# Offline Anomaly Evaluation

The velocity-spike detector was evaluated using deterministic synthetic simulator data. Ground truth comes only from `is_injected_anomaly`; it is not a real-world fraud label.

## Overall metrics

| Precision | Recall | False-positive rate |
| ---: | ---: | ---: |
| 100.00% | 100.00% | 0.00% |

## Scenario results

| Scenario | Windows | TP | FP | FN | TN |
| --- | ---: | ---: | ---: | ---: | ---: |
| normal_traffic | 10 | 0 | 0 | 0 | 10 |
| eid_spike | 10 | 0 | 0 | 0 | 10 |
| injected_anomaly | 10 | 10 | 0 | 0 | 0 |

Eid spike safeguard: **passed** — legitimate Eid demand windows were not flagged as injected anomalies.

Limitation: this is an offline synthetic evaluation of one velocity detector. It demonstrates reproducibility and false-positive handling, not production fraud-detection performance.
