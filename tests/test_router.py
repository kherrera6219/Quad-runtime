from quad.router import route_query


def test_router_activates_quad_for_architecture_implementation_tradeoff():
    decision = route_query("Design and build a runtime architecture with tradeoffs for implementation.")

    assert decision.mode == "quad"
    assert "architecture_or_design" in decision.activation_reasons
    assert "implementation_guidance" in decision.activation_reasons


def test_router_keeps_simple_question_normal():
    decision = route_query("What is YAML?")

    assert decision.mode == "normal"
    assert decision.output_profile == "quick"
