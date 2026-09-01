from scripts.summarize_walk_forward import summarize


def test_summary_reports_fold_win_rate_and_deltas():
    records = [{
        "symbol": "TEST",
        "folds": [
            {"model_balanced_accuracy": 0.6, "baseline_balanced_accuracy": 0.5, "model_macro_f1": 0.5, "baseline_macro_f1": 0.4},
            {"model_balanced_accuracy": 0.4, "baseline_balanced_accuracy": 0.5, "model_macro_f1": 0.3, "baseline_macro_f1": 0.4},
        ],
    }]
    result = summarize(records)["TEST"]
    assert result["folds"] == 2
    assert result["fold_win_rate_balanced_accuracy"] == 0.5
    assert result["mean_balanced_accuracy_delta"] == 0.0
    assert result["median_macro_f1_delta"] == 0.0
