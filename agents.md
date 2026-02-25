# Python Flask Application Coding Standards (AI-Enforced)

## Purpose

This document defines **mandatory coding standards** for a Python Flask application.

An AI agent generating or modifying code **MUST** follow these standards strictly.

---

# 1. Core Principles

* MUST follow **PEP 8**
* MUST use type hints
* MUST prefer explicit code over implicit behavior
* MUST write deterministic, testable logic
* MUST NOT introduce unnecessary abstractions
* MUST NOT duplicate business logic

---

# 2. Required Project Structure

```
project_root/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   ├── errors/
│   └── utils/
│
├── migrations/
├── tests/
├── wsgi.py
└── requirements.txt
```

## Structural Rules

* MUST use Blueprints
* MUST use Application Factory pattern
* MUST separate:

  * Routes (HTTP layer)
  * Services (business logic)
  * Repositories (data access)
* MUST NOT place business logic in routes
* MUST NOT access database directly from routes

---

# 3. Application Factory Pattern (Mandatory)

```python
def create_app(config_object: str = "app.config.Config") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)

    return app
```

Rules:

* MUST NOT create global app instance
* MUST initialize extensions inside `extensions.py`
* MUST register blueprints in a dedicated function

---

# 4. Naming Conventions

## Files

* snake_case
* Example: `user_service.py`

## Classes

* PascalCase
* Example: `UserService`

## Functions and Variables

* snake_case

## Constants

* UPPER_SNAKE_CASE

---

# 5. Routes Layer Rules

Routes MUST:

* Validate request input
* Call service layer
* Return serialized response

Routes MUST NOT:

* Contain business rules
* Perform database queries
* Contain complex logic
* Catch broad exceptions

Example:

```python
@user_bp.get("/users/<int:user_id>")
def get_user(user_id: int):
    user = user_service.get_user(user_id)
    return jsonify(UserSchema().dump(user)), 200
```

---

# 6. Service Layer Rules

Services MUST:

* Contain all business logic
* Be framework-agnostic
* Be independently unit testable
* Raise domain-specific exceptions

Example:

```python
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return user
```

---

# 7. Repository Layer Rules

Repositories MUST:

* Be the only layer accessing the database
* Encapsulate ORM logic
* Return domain models
* Not contain business logic

Repositories MUST NOT:

* Access request context
* Perform validation
* Call external services

---

# 8. Database Standards

* MUST use SQLAlchemy ORM
* MUST use migrations
* MUST define explicit column types
* MUST define `__tablename__`
* MUST use transactions for multi-step writes
* MUST NOT auto-create tables in production

---

# 9. Validation & Serialization

* MUST validate all external input
* MUST use Marshmallow or Pydantic
* MUST NOT trust request.json directly
* MUST validate both:

  * Schema constraints
  * Business constraints (in services)

---

# 10. Error Handling

* MUST define custom exception classes
* MUST register centralized error handlers
* MUST NOT expose stack traces in production
* MUST return consistent error format

Standard error response:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found"
  }
}
```

---

# 11. Logging Standards

* MUST use `logging` module
* MUST NOT use print statements
* MUST use structured logs in production
* MUST NOT log sensitive data

---

# 12. Security Requirements

* MUST hash passwords with bcrypt
* MUST enforce HTTPS in production
* MUST use secure cookies
* MUST configure CORS explicitly
* MUST NOT hardcode secrets
* MUST read secrets from environment variables

---

# 13. Testing Standards

* MUST use pytest
* MUST achieve minimum 80% coverage
* MUST unit test services
* MUST integration test routes
* MUST use separate test database
* MUST NOT depend on production services

Test structure:

```
tests/
├── unit/
├── integration/
└── conftest.py
```

---

# 14. API Design Standards

* MUST follow REST conventions
* MUST use plural resource names
* MUST use correct HTTP methods
* MUST paginate list endpoints
* MUST version API if public (`/api/v1/`)

Standard success response:

```json
{
  "data": {},
  "message": "",
  "error": null
}
```

---

# 15. Code Quality Tooling (Required)

The project MUST use:

* black
* isort
* ruff or flake8
* mypy
* pre-commit hooks

Import order:

1. Standard library
2. Third-party packages
3. Local modules

---

# 16. Performance Requirements

* MUST avoid N+1 queries
* MUST use eager loading when appropriate
* MUST paginate large queries
* MUST NOT perform blocking I/O in request lifecycle
* SHOULD use caching for high-read endpoints

---

# 17. Git & PR Standards

* MUST use feature branches
* MUST NOT commit directly to main
* MUST pass:

  * Lint
  * Type checking
  * Tests
  * CI
* MUST use conventional commits:

```
feat: add user registration
fix: correct token validation
refactor: extract auth service
```

---

# 18. Prohibited Patterns

The AI agent MUST NOT generate:

* Business logic inside routes
* Direct DB queries inside routes
* Hardcoded credentials
* Global mutable state
* Circular imports
* Catch-all `except Exception`
* Fat models
* Side effects inside model constructors

---

# 19. AI Agent Enforcement Rules

When generating code, the AI MUST:

* Respect layer boundaries
* Generate complete imports
* Add type hints
* Add docstrings for public methods
* Follow consistent response format
* Avoid speculative features
* Avoid unnecessary comments
* Avoid TODO placeholders unless explicitly requested

---

# 20. Deterministic Output Requirements

Generated code MUST:

* Be production-ready
* Not contain unused imports
* Not contain commented-out code
* Not contain debugging prints
* Not depend on implicit Flask globals

---


