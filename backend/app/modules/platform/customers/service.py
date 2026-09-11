from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.platform.customers.models import Customer


class CustomerService:
    def list(self, db: Session, company_id: int):
        return list(db.scalars(select(Customer).where(Customer.company_id == company_id).order_by(Customer.name)).all())

    def get(self, db: Session, company_id: int, customer_id: int):
        return db.scalar(select(Customer).where(Customer.company_id == company_id, Customer.id == customer_id))

    def create(self, db: Session, payload):
        duplicate = db.scalar(select(Customer).where(Customer.company_id == payload.company_id, Customer.code == payload.code))
        if duplicate:
            raise ValueError("Customer code already exists for this company")
        customer = Customer(**payload.model_dump())
        db.add(customer)
        db.flush()
        return customer

    def update(self, db: Session, company_id: int, customer_id: int, payload):
        customer = db.scalar(select(Customer).where(Customer.company_id == company_id, Customer.id == customer_id).with_for_update())
        if customer is None:
            raise ValueError("Customer not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(customer, key, value)
        db.flush()
        return customer


customer_service = CustomerService()
