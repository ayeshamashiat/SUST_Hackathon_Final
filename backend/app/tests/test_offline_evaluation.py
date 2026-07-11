from app.evaluation.offline import evaluate


def test_eid_spike_is_not_counted_as_an_injected_anomaly():
    report = evaluate(runs_per_scenario=2)
    assert report["eid_spike_not_flagged"] is True
    assert report["by_scenario"]["eid_spike"]["false_positive"] == 0
    assert report["overall"]["recall"] == 1.0
