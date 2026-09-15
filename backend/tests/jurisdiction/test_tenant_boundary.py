from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_jurisdiction_router_validates_partner_inside_current_tenant() -> None:
    source = (ROOT / "app/modules/jurisdiction/router.py").read_text(encoding="utf-8")
    assert "def partner_for_user" in source
    assert "Company.tenant_id == user.tenant_id" in source
    assert "partner_for_user(db, payload.partner_id, current_user)" in source


def test_jurisdiction_resolve_checks_optional_partner_tenant_boundary() -> None:
    source = (ROOT / "app/modules/jurisdiction/router.py").read_text(encoding="utf-8")
    assert 'if payload.partner_id is not None:' in source
    assert 'partner_for_user(db, payload.partner_id, current_user)' in source


def test_global_jurisdiction_master_data_requires_platform_admin() -> None:
    source = (ROOT / "app/modules/jurisdiction/router.py").read_text(encoding="utf-8")
    assert 'Depends(require_platform_admin())' in source
    assert '@router.post("", status_code=201, dependencies=[Depends(require_permission("commerce.write")), Depends(require_platform_admin())])' in source
    assert '@router.post("/tax-rules", status_code=201, dependencies=[Depends(require_permission("commerce.write")), Depends(require_platform_admin())])' in source
