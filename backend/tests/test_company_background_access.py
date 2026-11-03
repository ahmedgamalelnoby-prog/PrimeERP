import inspect


def test_approval_escalation_only_targets_active_company_members():
    from app.jobs.approval_escalation import process_due_approval_escalations

    source = inspect.getsource(process_due_approval_escalations)
    assert "UserCompanyAccess" in source
    assert "UserCompanyAccess.company_id == request.company_id" in source
    assert "User.tenant_id == request.tenant_id" in source
    assert "User.is_active.is_(True)" in source
    assert "User.is_deleted.is_(False)" in source
