from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(slots=True)
class RequestContext:
    """
    Context associated with a single HTTP request.
    """

    request_id: str

    user_id: Optional[int] = None

    tenant_id: Optional[int] = None

    company_id: Optional[int] = None

    branch_id: Optional[int] = None

    username: Optional[str] = None

    ip_address: Optional[str] = None

    user_agent: Optional[str] = None

    language: Optional[str] = None

    timezone: Optional[str] = None