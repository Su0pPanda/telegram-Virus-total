from enum import StrEnum


class InputType(StrEnum):
    FILE = "file"
    URL = "url"
    IP = "ip"


class RequestStatus(StrEnum):
    RECEIVED = "received"
    REJECTED = "rejected"
    CACHED = "cached"
    QUEUED = "queued"
    PROVIDER_LOOKUP = "provider_lookup"
    PROVIDER_UPLOAD = "provider_upload"
    WAITING_ANALYSIS = "waiting_analysis"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultSource(StrEnum):
    CACHE = "cache"
    PROVIDER_EXISTING = "provider_existing"
    PROVIDER_NEW = "provider_new"


class CleanupStatus(StrEnum):
    PENDING = "pending"
    DELETED = "deleted"
    FAILED = "failed"

