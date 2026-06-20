from __future__ import annotations

from pathlib import Path
from typing import Any

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


class QuadConfigError(ValueError):
    """Raised when QUAD YAML is missing or malformed."""


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


def return_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = load_yaml(path)
    validate_required_sections(config)
    return config
