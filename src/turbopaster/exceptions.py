from collections.abc import Sequence


class ApplicationError(Exception):
    """Base class for actionable application errors."""


class FileAccessError(ApplicationError):
    """A file or directory could not be accessed."""


class InvalidYamlSyntaxError(ApplicationError):
    """A YAML document could not be parsed."""


class InvalidYamlStructureError(ApplicationError):
    """A YAML document does not have the required structure."""


class InvalidHotkeyError(ApplicationError):
    """A hotkey does not match the supported syntax."""


class InvalidExtraPathError(ApplicationError):
    """An extra snippet path is invalid."""


class DuplicateSnippetError(ApplicationError):
    """A snippet name is defined more than once."""


class _ProblemAggregate(ApplicationError):
    label = "Validation failed"

    def __init__(self, problems: Sequence[ApplicationError]) -> None:
        self.problems = tuple(problems)
        details = "\n".join(f"  - {problem}" for problem in self.problems)
        super().__init__(f"{self.label}:\n{details}")


class ConfigurationError(_ProblemAggregate):
    """Configuration validation found one or more problems."""

    label = "Invalid configuration"


class SnippetLoadError(_ProblemAggregate):
    """Snippet validation found one or more problems."""

    label = "Snippet validation failed"
