from careroute.tools import lookup_symptoms, score_urgency, suggest_appointment


def test_lookup_symptoms_matches_and_unmatched():
    result = lookup_symptoms(symptoms=["Headache", "glowing skin"])
    assert "headache" in result["matches"]
    assert result["matches"]["headache"]["possible_causes"]
    assert result["matches"]["headache"]["red_flags"]
    assert result["unmatched"] == ["glowing skin"]


def test_score_urgency_levels():
    assert score_urgency(red_flags=["stiff neck"], duration_days=1, severity=3)["urgency"] == "emergency"
    assert score_urgency(red_flags=[], duration_days=1, severity=8)["urgency"] == "urgent"
    assert score_urgency(red_flags=[], duration_days=10, severity=2)["urgency"] == "routine"
    assert score_urgency(red_flags=[], duration_days=1, severity=2)["urgency"] == "self_care"


def test_suggest_appointment_is_stubbed():
    result = suggest_appointment(urgency="routine")
    assert "Thursday" in result["slot"]
    assert "DEMO STUB" in result["note"]
