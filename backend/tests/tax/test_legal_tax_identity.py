from datetime import datetime

from app.modules.companies.schemas import CompanyCreate, CompanyResponse, CompanyUpdate
from app.modules.commerce.schemas import PartnerCreate, PartnerResponse


def test_company_legal_tax_profile_round_trip():
    payload = CompanyCreate(
        name="Prime Test",
        legal_name="Prime Test LLC",
        tax_id="123456789",
        commercial_registration_number="987654",
        tax_authority="Cairo Tax Office",
    )
    assert payload.legal_name == "Prime Test LLC"
    assert payload.tax_id == "123456789"
    assert payload.commercial_registration_number == "987654"

    update = CompanyUpdate(commercial_registration_number="111222")
    assert update.commercial_registration_number == "111222"


def test_customer_tax_identity_fields_are_supported():
    payload = PartnerCreate(
        company_id=1,
        code="C001",
        name="Customer One",
        partner_type="customer",
        tax_number="555666777",
        commercial_registration_number="CR-100",
        tax_authority="Giza Tax Office",
        eta_registration_status="pending",
        eta_party_id="555666777",
        eta_last_verified_at=datetime.now(),
    )
    assert payload.tax_number == "555666777"
    assert payload.commercial_registration_number == "CR-100"
    assert payload.eta_party_id == "555666777"

    response = PartnerResponse(
        id=1,
        is_active=True,
        **payload.model_dump(),
    )
    assert response.eta_registration_status == "pending"
