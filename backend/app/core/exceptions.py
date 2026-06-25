"""
PAIOS Exception Hierarchy.

Every layer raises typed exceptions that propagate upward.
The global error handler in presentation layer maps them to HTTP responses.

Hierarchy:
    PAIOSException
    ├── DomainException
    │   ├── EntityNotFoundError
    │   ├── DuplicateEntityError
    │   ├── ValidationError
    │   └── BusinessRuleViolationError
    ├── InfrastructureException
    │   ├── DatabaseError
    │   ├── AIModelError
    │   ├── BrowserAutomationError
    │   └── ExternalServiceError
    ├── AuthenticationError
    └── AuthorizationError
"""

from __future__ import annotations


class PAIOSException(Exception):
    """Root exception for the entire PAIOS application."""

    def __init__(self, message: str, *, code: str = "PAIOS_ERROR", details: dict | None = None) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ── Domain Exceptions ──────────────────────────────────────────────────────


class DomainException(PAIOSException):
    """Base for all domain-layer errors (business logic violations)."""

    def __init__(self, message: str, *, code: str = "DOMAIN_ERROR", details: dict | None = None) -> None:
        super().__init__(message, code=code, details=details)


class EntityNotFoundError(DomainException):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"{entity_type} with id '{entity_id}' not found",
            code="ENTITY_NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class DuplicateEntityError(DomainException):
    """Raised when attempting to create an entity that already exists."""

    def __init__(self, entity_type: str, *, field: str = "id", value: str = "") -> None:
        super().__init__(
            f"{entity_type} with {field}='{value}' already exists",
            code="DUPLICATE_ENTITY",
            details={"entity_type": entity_type, "field": field, "value": value},
        )


class DomainValidationError(DomainException):
    """Raised when domain validation rules are violated."""

    def __init__(self, message: str, *, field: str = "", details: dict | None = None) -> None:
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
        )


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated (e.g., applying to an expired job)."""

    def __init__(self, rule: str, message: str = "") -> None:
        super().__init__(
            message or f"Business rule violated: {rule}",
            code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule},
        )


# ── Infrastructure Exceptions ─────────────────────────────────────────────


class InfrastructureException(PAIOSException):
    """Base for all infrastructure-layer errors."""

    def __init__(self, message: str, *, code: str = "INFRA_ERROR", details: dict | None = None) -> None:
        super().__init__(message, code=code, details=details)


class DatabaseError(InfrastructureException):
    """Raised on database connection or query failures."""

    def __init__(self, message: str = "Database operation failed", *, details: dict | None = None) -> None:
        super().__init__(message, code="DATABASE_ERROR", details=details)


class AIModelError(InfrastructureException):
    """Raised when the AI model (Ollama/Groq) fails to respond."""

    def __init__(
        self,
        message: str = "AI model inference failed",
        *,
        model: str = "",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            message,
            code="AI_MODEL_ERROR",
            details={"model": model, **(details or {})},
        )


class BrowserAutomationError(InfrastructureException):
    """Raised on Playwright browser automation failures."""

    def __init__(self, message: str = "Browser automation failed", *, details: dict | None = None) -> None:
        super().__init__(message, code="BROWSER_ERROR", details=details)


class ExternalServiceError(InfrastructureException):
    """Raised when an external HTTP service call fails."""

    def __init__(
        self,
        service_name: str,
        message: str = "",
        *,
        status_code: int | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            message or f"External service '{service_name}' failed",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name, "status_code": status_code, **(details or {})},
        )


# ── Auth Exceptions ────────────────────────────────────────────────────────


class AuthenticationError(PAIOSException):
    """Raised on authentication failures (bad credentials, expired token)."""

    def __init__(self, message: str = "Authentication failed", *, details: dict | None = None) -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR", details=details)


class AuthorizationError(PAIOSException):
    """Raised when the user lacks permission for the requested action."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        *,
        required_role: str = "",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            message,
            code="AUTHORIZATION_ERROR",
            details={"required_role": required_role, **(details or {})},
        )
