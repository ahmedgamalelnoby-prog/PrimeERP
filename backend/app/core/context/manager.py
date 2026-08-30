from __future__ import annotations

from contextvars import ContextVar, Token

from app.core.context.request_context import RequestContext


_request_context: ContextVar[RequestContext | None] = ContextVar(
    "request_context",
    default=None,
)


def set_request_context(
    context: RequestContext,
) -> Token[RequestContext | None]:
    """
    Set the context for the current asynchronous execution flow.

    The returned token must be used to restore the previous value.
    """
    return _request_context.set(context)


def get_request_context() -> RequestContext:
    """
    Return the current request context.

    Raises RuntimeError when called outside an initialized request.
    """
    context = _request_context.get()

    if context is None:
        raise RuntimeError(
            "RequestContext has not been initialized."
        )

    return context


def get_optional_request_context() -> RequestContext | None:
    """
    Return the current context, or None when no request context exists.
    """
    return _request_context.get()


def reset_request_context(
    token: Token[RequestContext | None],
) -> None:
    """
    Restore the previous context value using its ContextVar token.
    """
    _request_context.reset(token)


def clear_request_context() -> None:
    """
    Explicitly clear the request context.

    Prefer reset_request_context() inside middleware.
    """
    _request_context.set(None)