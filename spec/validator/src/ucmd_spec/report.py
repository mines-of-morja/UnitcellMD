"""Validation results with the stable error codes of the spec."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Issue:
    """One finding. Codes starting with ``E_`` are errors, ``W_`` are warnings."""

    code: str
    message: str
    location: str = ""

    @property
    def is_error(self) -> bool:
        return self.code.startswith("E_")


@dataclass
class Report:
    """Outcome of validating one target (package directory or file)."""

    target: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.is_error for issue in self.issues)

    @property
    def error(self) -> Issue | None:
        """The first (and, by the spec's stop-at-first-error rule, only) error."""
        return next((issue for issue in self.issues if issue.is_error), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "ok": self.ok,
            "issues": [
                {"code": i.code, "message": i.message, "location": i.location} for i in self.issues
            ],
        }


class Invalid(Exception):
    """Raised inside validators to stop at the first error."""

    def __init__(self, code: str, message: str, location: str = "") -> None:
        super().__init__(f"{code}: {message}")
        self.issue = Issue(code, message, location)
