# PrimeERP Coding Standards

## Python Version

Python 3.10+

---

## Formatting

- Black
- Line Length = 88

---

## Imports

Always ordered as:

1. Standard Library
2. Third Party
3. Local Imports

Example:

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import BaseRepository

---

## Type Hints

Required for every function.

Correct:

def create_company(
    company: CompanyCreate,
) -> Company:
    ...

Wrong:

def create_company(company):
    ...

---

## Naming

Classes:
PascalCase

Functions:
snake_case

Variables:
snake_case

Constants:
UPPER_CASE

---

## Repository

Repository contains only database logic.

No business rules.

---

## Services

Services contain business rules.

No SQL.

---

## API

Routers contain:

- Request validation
- Calling services
- Returning responses

Nothing else.

---

## Exceptions

Never use:

except:

Always use:

except ValueError:

or

except SQLAlchemyError:

---

## Documentation

Every public class must contain a Docstring.

Every public service method should contain a Docstring.

---

## Testing

Every new Service

↓

Unit Test

Every API

↓

Integration Test