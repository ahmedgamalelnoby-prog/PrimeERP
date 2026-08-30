from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.context import (
    RequestContext,
    reset_request_context,
    set_request_context,
)


RequestHandler = Callable[[Request], Awaitable[Response]]


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Create and manage RequestContext for every HTTP request.
    """

    REQUEST_ID_HEADER = "X-Request-ID"
    LANGUAGE_HEADER = "Accept-Language"
    TIMEZONE_HEADER = "X-Timezone"

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestHandler,
    ) -> Response:
        request_id = self._resolve_request_id(request)

        context = RequestContext(
            request_id=request_id,
            ip_address=self._resolve_ip_address(request),
            user_agent=request.headers.get("user-agent"),
            language=self._resolve_language(request),
            timezone=request.headers.get(self.TIMEZONE_HEADER),
        )

        token = set_request_context(context)

        request.state.request_context = context
        request.state.request_id = request_id

        try:
            response = await call_next(request)

        finally:
            reset_request_context(token)

        response.headers[self.REQUEST_ID_HEADER] = request_id

        return response

    def _resolve_request_id(
        self,
        request: Request,
    ) -> str:
        incoming_request_id = request.headers.get(
            self.REQUEST_ID_HEADER
        )

        if incoming_request_id:
            cleaned_request_id = incoming_request_id.strip()

            if cleaned_request_id:
                return cleaned_request_id[:128]

        return str(uuid4())

    def _resolve_ip_address(
        self,
        request: Request,
    ) -> str | None:
        forwarded_for = request.headers.get("x-forwarded-for")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")

        if real_ip:
            return real_ip.strip()

        if request.client:
            return request.client.host

        return None

    def _resolve_language(
        self,
        request: Request,
    ) -> str | None:
        accept_language = request.headers.get(
            self.LANGUAGE_HEADER
        )

        if not accept_language:
            return None

        primary_language = accept_language.split(",")[0].strip()

        return primary_language or None