from enum import Enum
from pydantic import BaseModel, ConfigDict


class IntentType(str, Enum):
    # Actions
    DRAFT_QUOTE = "draft_quote"
    CONVERT_TO_INVOICE = "convert_to_invoice"
    CREATE_CLIENT = "create_client"
    UPDATE_JOB = "update_job"
    UPDATE_CLIENT = "update_client"
    DELETE_JOB = "delete_job"
    DELETE_CLIENT = "delete_client"
    LIST_JOBS = "list_jobs"
    LIST_CLIENTS = "list_clients"
    # Business Terms
    ADD_BUSINESS_TERM = "add_business_term"
    UPDATE_BUSINESS_TERM = "update_business_term"
    DELETE_BUSINESS_TERM = "delete_business_term"
    LIST_BUSINESS_TERMS = "list_business_terms"
    # Business Profile
    UPDATE_BUSINESS_PROFILE = "update_business_profile"
    GET_BUSINESS_PROFILE = "get_business_profile"
    # Ledger
    LOG_INCOME = "log_income"
    LOG_EXPENSE = "log_expense"
    CHECK_BALANCE = "check_balance"
    # Queries
    QUERY_BUSINESS = "query_business"
    QUERY_CLIENTS = "query_clients"
    QUERY_JOBS = "query_jobs"
    QUERY_BUSINESS_TERMS = "query_business_terms"
    QUERY_INVOICES = "query_invoices"
    QUERY_QUOTES = "query_quotes"
    QUERY_PAYMENTS = "query_payments"
    GENERAL_QUERY = "general_query"
    # Other
    OTHER = "other"


class CommandIntent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    reasoning: str
    confidence: float
    intent: IntentType
