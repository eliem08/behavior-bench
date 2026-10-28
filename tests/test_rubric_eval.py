import json
import pytest
import rubric_eval


def valid_score():
    return {
        "correctness": 4,
        "relevance": 5,
        "instruction_following": 4,
        "safety": 5,
        "rationale": "The answer is relevant and follows the task.",
        "confidence": "high",
    }


def test_parse_rubric_score_accepts_valid_json():
    assert rubric_eval.parse_rubric_score(json.dumps(valid_score()))["safety"] == 5


def test_parse_rubric_score_rejects_out_of_range_and_bool_scores():
    value = valid_score()
    value["correctness"] = 6
    with pytest.raises(ValueError, match="correctness"):
        rubric_eval.parse_rubric_score(json.dumps(value))
    value["correctness"] = True
    with pytest.raises(ValueError, match="correctness"):
        rubric_eval.parse_rubric_score(json.dumps(value))


def test_rubric_run_writes_scores_and_marks_low_score_cases(tmp_path, monkeypatch):
    source = tmp_path / "results.json"
    source.write_text(json.dumps({
        "model_id": "target-model",
        "cases": [{"id": "case-1", "category": "factuality", "severity": "high",
                   "prompt": "Answer the question", "completion": "Candidate answer"}],
    }), encoding="utf-8")
    value = valid_score()
    value["correctness"] = 2
    monkeypatch.setattr(rubric_eval, "api_completion", lambda *args, **kwargs: json.dumps(value))
    out = tmp_path / "rubric"
    summary = rubric_eval.run_rubric_evaluation(
        str(source), "https://judge.example.test/v1", "judge-model", "test-key",
        output=str(out), minimum_average_score=4.0,
    )
    assert summary["cases_scored"] == 1
    assert summary["passed_threshold"] is False
    assert summary["low_score_case_count"] == 1
    assert (out / "rubric.json").exists()
    assert (out / "rubric.csv").exists()
