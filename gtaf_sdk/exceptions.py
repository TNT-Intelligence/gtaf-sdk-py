class GTAFSDKError(Exception):
    """Base exception for gtaf-sdk-py."""


class InvalidDRCError(GTAFSDKError):
    """Raised when the DRC file cannot be used for reference resolution."""


class ArtifactNotFoundError(GTAFSDKError):
    """Raised when a referenced artifact file does not exist."""


class InvalidJSONError(GTAFSDKError):
    """Raised when a required JSON file cannot be parsed."""


class InvalidArtifactError(GTAFSDKError):
    """Raised when an artifact file contents are invalid."""


class DuplicateArtifactIDError(GTAFSDKError):
    """Raised when the same artifact id is referenced across categories."""


class ActionNormalizationError(GTAFSDKError):
    """Raised when action normalization is configured to fail on unknown input."""
