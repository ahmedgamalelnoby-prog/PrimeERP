from types import SimpleNamespace


def test_catalog_router_helpers_delegate_to_company_membership(monkeypatch):
    from app.modules.catalog import router, bundle_router, pricing_engine_router, variant_router

    calls = []
    def require(_db, user, company_id):
        calls.append((user.id, company_id))
        return SimpleNamespace(id=company_id, is_active=True)

    for module in (router, bundle_router, pricing_engine_router, variant_router):
        monkeypatch.setattr(module, "require_company_access", require)

    user = SimpleNamespace(id=17)
    class DB:
        def scalar(self, _query):
            return SimpleNamespace(is_active=True)

    db = DB()
    router._company_for_user(db, 101, user)
    bundle_router.guard_company(db, 102, user)
    pricing_engine_router._company_for_user(db, 103, user)
    variant_router._company_for_user(db, 104, user)

    assert calls == [(17, 101), (17, 102), (17, 103), (17, 104)]


def test_mobile_company_guard_delegates_to_company_membership(monkeypatch):
    from app.modules.mobile import router

    calls = []
    monkeypatch.setattr(
        router,
        "require_company_access",
        lambda _db, user, company_id: calls.append((user.id, company_id)),
    )
    monkeypatch.setattr(router, "get_effective_tenant_id", lambda _user: 42)

    tenant_id = router.company_ok(
        object(),
        205,
        SimpleNamespace(id=23),
    )

    assert tenant_id == 42
    assert calls == [(23, 205)]


def test_commerce_and_approval_guards_delegate_to_company_membership(monkeypatch):
    from app.modules.commerce import router as commerce_router
    from app.modules.operations.approvals import router as approvals_router

    calls = []
    def require(_db, user, company_id):
        calls.append((user.id, company_id))
        return SimpleNamespace(id=company_id, is_active=True)

    monkeypatch.setattr(commerce_router, "require_company_access", require)
    monkeypatch.setattr(approvals_router, "require_company_access", require)

    user = SimpleNamespace(id=31)
    commerce_router._company_for_user(object(), 301, user)
    approvals_router._company(object(), 302, user)

    assert calls == [(31, 301), (31, 302)]
