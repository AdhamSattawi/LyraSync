from enum import Enum


class JobStatus(str, Enum):
    QUOTE = "quote"
    INVOICE = "invoice"
    PAID = "paid"
    CANCELLED = "cancelled"
    DRAFT = "draft"
    VOIDED = "voided"
