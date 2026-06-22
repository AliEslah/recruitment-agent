from __future__ import annotations


class RecruitmentAgentError(Exception):
    """Base exception for expected application errors."""


class DomainError(RecruitmentAgentError):
    """Raised when recruitment domain invariants are violated."""
