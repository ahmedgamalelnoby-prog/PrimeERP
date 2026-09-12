ETA_DOCUMENT_SUBMISSION_PATH = "/api/v1.0/documentsubmissions/"
ETA_DOCUMENT_PATH_TEMPLATE = "/api/v1.0/documents/{uuid}/raw"
ETA_SUBMISSION_PATH_TEMPLATE = "/api/v1.0/submissions/{uuid}"
SUPPORTED_STATUSES = {
    "draft",
    "queued",
    "submitted",
    "valid",
    "rejected",
    "cancelled",
    "error",
}
