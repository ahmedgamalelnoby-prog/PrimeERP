from app.core.context import get_request_context


class ContextTestService:
    def get_current_context(self) -> dict:
        ctx = get_request_context()

        return {
            "request_id": ctx.request_id,
            "ip_address": ctx.ip_address,
            "user_agent": ctx.user_agent,
            "language": ctx.language,
            "timezone": ctx.timezone,
            "user_id": ctx.user_id,
            "tenant_id": ctx.tenant_id,
            "company_id": ctx.company_id,
            "branch_id": ctx.branch_id,
        }


context_test_service = ContextTestService()