from quad.config_loader import return_config


def test_loads_required_quad_config():
    config = return_config()
    engine = config["quad_engine"]

    assert engine["version"] == "2.2"
    assert "activation_policy" in engine
    assert "failure_modes" in engine
