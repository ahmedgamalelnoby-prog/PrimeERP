# PrimeERP automatic integration sync worker

The `integration-worker` Compose service polls active Salla connections and
uses each connection's company policy `integrations.auto_sync_enabled` before
running a full sync. The default is disabled, so existing companies do not
start syncing automatically unless an authorized company administrator enables
the policy.

## Runtime controls

- `PRIMEERP_INTEGRATION_WORKER_POLL_SECONDS`: polling delay, default 60 seconds
  (minimum 5 seconds).
- `PRIMEERP_INTEGRATION_SYNC_INTERVAL_MINUTES`: minimum interval between
  automatic sync claims, default 15 minutes (minimum 1 minute).
- `PRIMEERP_INTEGRATION_WORKER_ID`: optional worker identifier for logs.

The worker claims a due connection using a database row lock and updates
`last_sync_at` before making external requests. This reduces duplicate claims
between worker replicas during the configured interval. It is not a durable
lease, and manual sync requests remain independently callable. A failed
automatic sync is logged and becomes eligible again after the interval; it
does not disable the integration or change the company's policy.

Only active Salla connections are currently supported by this worker. Other
providers require an explicit provider-specific sync implementation before
they can be scheduled.

## Deployment notes

The worker is declared in the root `docker-compose.yml` and waits for the
existing `migrate` service to complete. Do not run migrations as part of a
settings edit. In local environments, use the project's established Compose
and environment configuration; never paste credentials into this document or
commit them to source control.
