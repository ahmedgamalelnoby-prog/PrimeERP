from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.modules.audit.service import record_audit_event
from app.modules.core_integration.models import IntegrationTransaction


ACTIVE_STATUSES = {"processing", "completed", "failed", "reversed"}


class CoreIntegrationService:
    def begin(self, db, *, user, company_id, source_module, source_entity, source_id, operation, idempotency_key):
        if not getattr(user, "tenant_id", None):
            raise HTTPException(403, "Tenant context is required")
        if not idempotency_key or not str(idempotency_key).strip():
            raise HTTPException(422, "Idempotency key is required")
        existing = db.scalar(
            select(IntegrationTransaction).where(
                IntegrationTransaction.company_id == company_id,
                IntegrationTransaction.idempotency_key == str(idempotency_key).strip(),
            ).with_for_update()
        )
        if existing is not None:
            if existing.tenant_id != user.tenant_id:
                raise HTTPException(403, "Idempotency key belongs to another tenant")
            if existing.source_module != source_module or existing.source_entity != source_entity or str(existing.source_id) != str(source_id):
                raise HTTPException(409, "Idempotency key is already bound to another transaction")
            return existing, False
        tx = IntegrationTransaction(
            tenant_id=user.tenant_id,
            company_id=company_id,
            source_module=source_module,
            source_entity=source_entity,
            source_id=str(source_id),
            operation=operation,
            idempotency_key=str(idempotency_key).strip(),
            actor_id=user.id,
            status="processing",
        )
        db.add(tx)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(select(IntegrationTransaction).where(
                IntegrationTransaction.company_id == company_id,
                IntegrationTransaction.idempotency_key == str(idempotency_key).strip(),
            ))
            if existing is None:
                raise
            return existing, False
        record_audit_event(db, action="core.transaction.begin", entity_type="integration_transaction",
                            entity_id=tx.id, user_id=user.id, tenant_id=user.tenant_id,
                            company_id=company_id, metadata={"operation": operation, "source": f"{source_module}:{source_entity}:{source_id}"})
        return tx, True

    def complete(self, db, tx, status="completed", *, user_id=None, reason=None):
        if tx.status == "reversed":
            raise HTTPException(409, "Transaction is already reversed")
        if status not in {"completed", "failed"}:
            raise HTTPException(422, "Invalid transaction completion status")
        tx.status = status
        if reason:
            tx.reason = reason
        db.flush()
        record_audit_event(db, action=f"core.transaction.{status}", entity_type="integration_transaction",
                            entity_id=tx.id, user_id=user_id, tenant_id=tx.tenant_id,
                            company_id=tx.company_id, metadata={"operation": tx.operation, "reason": reason})
        return tx

    def reverse(self, db, tx, user, reason):
        if tx.reversed or tx.status == "reversed":
            raise HTTPException(409, "Transaction is already reversed")
        if tx.status != "completed":
            raise HTTPException(409, "Only completed transactions can be reversed")
        reversal = IntegrationTransaction(
            tenant_id=tx.tenant_id,
            company_id=tx.company_id,
            source_module=tx.source_module,
            source_entity=tx.source_entity,
            source_id=tx.source_id,
            operation="reverse:" + tx.operation,
            idempotency_key=f"reverse:{tx.id}",
            reversal_of_id=tx.id,
            reason=reason,
            actor_id=user.id,
            status="completed",
        )
        db.add(reversal)
        tx.reversed = True
        tx.status = "reversed"
        db.flush()
        record_audit_event(db, action="core.transaction.reverse", entity_type="integration_transaction",
                            entity_id=reversal.id, user_id=user.id, tenant_id=tx.tenant_id,
                            company_id=tx.company_id, metadata={"original_id": tx.id, "reason": reason})
        return reversal


core_integration_service = CoreIntegrationService()
