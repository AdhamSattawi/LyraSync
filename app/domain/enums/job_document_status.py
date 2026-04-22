from enum import Enum


class JobDocumentStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    ERROR = "error"
