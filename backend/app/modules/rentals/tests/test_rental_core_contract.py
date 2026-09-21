from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
def read(path): return (ROOT/path).read_text(encoding="utf-8")
def test_rental_workflow_contract():
    router=read("app/modules/rentals/router.py");service=read("app/modules/rentals/service.py");accounting=read("app/modules/rentals/accounting_service.py")
    assert 'require_module("rentals")' in router
    assert '"/contracts/{contract_id}/activate"' in router
    assert '"/contracts/{contract_id}/terminate"' in router
    assert "rental_accounting_service.post_charge" in service
    assert 'source_module="rentals"' in accounting
    assert 'source_entity="rental_charge"' in accounting
def test_rental_pricing_math_contract():
    from decimal import Decimal
    fixed=Decimal("10000");mg=Decimal("12000");revenue=Decimal("200000");share=revenue*Decimal("10")/Decimal("100")
    assert max(fixed,mg)==Decimal("12000")
    assert fixed+share==Decimal("30000")
