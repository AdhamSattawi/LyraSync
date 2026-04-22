from app.core.intent_handler import IntentHandler
from app.domain.schemas.intent_schema import IntentType
from app.services.job_service import JobService
import uuid


class ListJobsHandler(IntentHandler):
    def __init__(self, job_service: JobService):
        self.job_service = job_service

    @property
    def intent_type(self) -> IntentType:
        return IntentType.LIST_JOBS

    @property
    def extraction_schema(self):
        return None  # No schema required to simply list jobs

    def get_system_prompt(self, profession: str) -> str:
        return ""  # Not needed

    async def execute(
        self, business_id: uuid.UUID, user_id: uuid.UUID, extracted_data: None = None
    ) -> str:
        res = await self.job_service.list_jobs(business_id, user_id)
        if isinstance(res, str):
            return res
        lines = [f"- {j.title} ({j.status.value})" for j in res]
        return "Here are your jobs:\n" + "\n".join(lines)
