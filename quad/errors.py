"""Typed exceptions for QUAD Runtime integration boundaries."""


class QuadError(Exception):
    """Base class for all QUAD Runtime errors."""


class QuadConfigError(QuadError, ValueError):
    """Raised when QUAD configuration is missing, malformed, or incompatible."""


class QuadRoutingError(QuadError, ValueError):
    """Raised when routing inputs or decisions are invalid."""


class QuadPromptError(QuadError, ValueError):
    """Raised when prompt construction fails."""


class QuadModelError(QuadError, RuntimeError):
    """Raised when a model provider cannot produce a valid generation."""


class QuadToolGroundingError(QuadError, RuntimeError):
    """Raised when tool-grounding preparation fails."""


class QuadAuditLogError(QuadError, RuntimeError):
    """Raised when audit log persistence fails."""
