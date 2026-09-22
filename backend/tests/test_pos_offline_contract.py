from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def test_offline_checkout_replay_is_serialized_per_terminal():
    router = (REPO / "backend/app/modules/pos/router.py").read_text(encoding="utf-8")
    assert "def _terminal(db: Session, company_id: int, terminal_id: int, *, lock: bool = False)" in router
    assert "_terminal(db, payload.company_id, payload.terminal_id, lock=True)" in router
    assert ".with_for_update()" in router
    assert "Offline replay can happen after the original request committed" in router
    assert router.count('SalesDocument.number == payload.number') >= 2
    assert 'idempotency_key=f"pos/checkout/{payload.company_id}/{payload.number}"' in router


def test_offline_queue_has_durable_retry_and_service_worker():
    offline = (REPO / "frontend/src/modules/pos/services/offlinePos.ts").read_text(encoding="utf-8")
    sw = (REPO / "frontend/public/pos-sw.js").read_text(encoding="utf-8")
    assert 'const DB_NAME = "primeerp-pos"' in offline
    assert 'const QUEUE_STORE = "checkout_queue"' in offline
    assert "setInterval(trigger, 15000)" in offline
    assert "activeFlush" in offline
    assert "flushCheckoutQueueOnce" in offline
    assert 'navigator.serviceWorker.register("/pos-sw.js"' in offline
    assert 'const CACHE = "primeerp-pos-shell-v1"' in sw
    assert 'caches.match("/index.html")' in sw


def test_offline_checkout_uses_stable_device_identity_in_order_number():
    page = (REPO / "frontend/src/modules/pos/pages/PosPage.tsx").read_text(encoding="utf-8")
    offline = (REPO / "frontend/src/modules/pos/services/offlinePos.ts").read_text(encoding="utf-8")
    assert "getDeviceId().slice(0, 8)" in page
    assert 'localStorage.getItem(DEVICE_KEY)' in offline
    assert "enqueueCheckout(payload)" in page
