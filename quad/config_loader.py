from __future__ import annotations

from pathlib import Path
from typing import Any

from quad.errors import QuadConfigError

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only on missing dependency
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "quad_engine_v2_2.yaml"

REQUIRED_SECTIONS = (
    "version",
    "activation_policy",
    "evidence_policy",
    "tool_policy",
    "role_policy",
    "output_profiles",
    "failure_modes",
)


def load_yaml(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    if yaml is None:
        raise QuadConfigError("PyYAML is required. Install dependencies with `pip install -r requirements.txt`.") from YAML_IMPORT_ERROR

    config_path = Path(path)
    if not config_path.exists():
        raise QuadConfigError(f"QUAD config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)

    if not isinstance(loaded, dict):
        raise QuadConfigError("QUAD config must parse to a mapping.")
    return loaded


def validate_required_sections(config: dict[str, Any]) -> None:
    engine = config.get("quad_engine")
    if not isinstance(engine, dict):
        raise QuadConfigError("Missing required top-level `quad_engine` section.")

    missing = [section for section in REQUIRED_SECTIONS if section not in engine]
    if missing:
        raise QuadConfigError(f"Missing required QUAD section(s): {', '.join(missing)}")

    _require_non_empty_string(engine, "version", "quad_engine")
    _require_mapping(engine, "activation_policy", "quad_engine")
    _require_mapping(engine, "evidence_policy", "quad_engine")
    _require_mapping(engine, "tool_policy", "quad_engine")
    _require_mapping(engine, "role_policy", "quad_engine")
    _validate_output_profiles(engine)
    _validate_failure_modes(engine)


def _require_mapping(parent: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise QuadConfigError(f"`{context}.{key}` must be a mapping.")
    return value


def _require_non_empty_string(parent: dict[str, Any], key: str, context: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise QuadConfigError(f"`{context}.{key}` must be a non-empty string.")
    return value


def _validate_output_profiles(engine: dict[str, Any]) -> None:
    profiles = _require_mapping(engine, "output_profiles", "quad_engine")
    for profile in ("quick", "standard", "deep"):
        profile_config = _require_mapping(profiles, profile, "quad_engine.output_profiles")
        visible_sections = profile_config.get("visible_sections")
        if not isinstance(visible_sections, list) or not all(isinstance(section, str) for section in visible_sections):
            raise QuadConfigError(
                f"`quad_engine.output_profiles.{profile}.visible_sections` must be a list of strings."
            )


def _validate_failure_modes(engine: dict[str, Any]) -> None:
    failure_modes = _require_mapping(engine, "failure_modes", "quad_engine")
    avoid = _require_mapping(failure_modes, "avoid", "quad_engine.failure_modes")
    required_modes = {
        "fake_panel",
        "mushy_compromise",
        "overformalization",
        "fake_disagreement",
        "unsupported_authority",
        "stale_fact_confidence",
        "visible_chain_of_thought",
    }
    missing = sorted(required_modes.difference(avoid))
    if missing:
        raise QuadConfigError(f"Missing required failure mode(s): {', '.join(missing)}")


def return_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = load_yaml(path)
    validate_required_sections(config)
    return config
