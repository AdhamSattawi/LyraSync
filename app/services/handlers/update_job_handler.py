from app.core.intent_handler import IntentHandler
from app.domain.schemas.intent_schema import IntentType
from app.domain.schemas.job_schema import JobUpdate
from app.services.job_service import JobService
import uuid


class UpdateJobHandler(IntentHandler):
    def __init__(self, job_service: JobService):
        self.job_service = job_service

    @property
    def intent_type(self) -> IntentType:
        return IntentType.UPDATE_JOB

    @property
    def extraction_schema(self):
        return JobUpdate

    def get_system_prompt(self, profession: str) -> str:
        return (
            f"You are an AI assistant for a {profession} business. "
            "Extract the job fields that need to be updated from the user's message. "
            "Return the data in the JobUpdate schema."
        )

    async def execute(
        self, business_id: uuid.UUID, user_id: uuid.UUID, extracted_data: JobUpdate
    ) -> str:
        res = await self.job_service.update_job(business_id, user_id, extracted_data)
        if isinstance(res, str):
            return res
        return f"Updated job '{res.title}' successfully."
