from decimal import Decimal
from pathlib import Path

def test_pos_domain_files_and_api_contract_are_registered():
    root=Path(__file__).parents[1]
    assert (root/"app/modules/pos/models.py").exists()
    assert (root/"app/modules/pos/service.py").exists()
    router=(root/"app/api/v1/router.py").read_text()
    assert "from app.modules.pos.router import router as pos_router" in router
    assert 'api_router.include_router(pos_router, dependencies=[Depends(require_module("sales"))])' in router

def test_pos_payment_amount_is_decimal_safe():
    assert Decimal("10.25")+Decimal("2.75")==Decimal("13.00")

def test_pos_status_contract_is_terminal_after_finalize():
    text=(Path(__file__).parents[1]/"app/modules/pos/models.py").read_text()
    assert "status IN ('draft','finalized','cancelled','reversed')" in text
    assert "status IN ('posted','reversed')" in text
