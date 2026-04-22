from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.domain.schemas.job_schema import (
    JobExtract,
    JobSchema,
    JobUpdate,
    JobIdentifier,
)
from app.domain.schemas.handler_reply import HandlerReply
from app.domain.models.job import Job
from app.domain.models.client import Client
from app.domain.models.job_item import JobItem
from app.domain.enums.job_status import JobStatus
import uuid
from app.infrastructure.database.repositories.client_repository import ClientRepository
from app.infrastructure.database.repositories.job_repository import JobRepository
from app.infrastructure.database.repositories.business_repository import (
    BusinessRepository,
)
from app.services.document_service import DocumentService


class JobService:
    def __init__(
        self,
        session_maker: AsyncSession,
        client_repository: ClientRepository,
        job_repository: JobRepository,
        business_repository: BusinessRepository,
        document_service: DocumentService,
    ):
        self.session_maker = session_maker
        self.client_repo = client_repository
        self.job_repo = job_repository
        self.business_repo = business_repository
        self.document_service = document_service

    async def draft_quote(
        self, business_id: uuid.UUID, user_id: uuid.UUID, job_data: JobExtract
    ) -> JobSchema:
        async with self.session_maker() as session:
            client = await self.client_repo.find_by_name(
                business_id, job_data.client_name, session
            )
            if not client:
                client = Client(
                    name=job_data.client_name,
                    phone=job_data.client_phone or "Unknown",
                    address=job_data.client_address or "Unknown",
                    business_id=business_id,
                )
                await self.client_repo.save(client, session)

            # Generate a sequential, per-tenant invoice number (e.g., QUOTE-0001)
            invoice_number = await self.job_repo.get_next_invoice_number(
                business_id, JobStatus.QUOTE, session
            )
            business_currency_code = await self.business_repo.get_currency_code(
                business_id, session
            )

            new_job = Job(
                title=job_data.title,
                description=job_data.description,
                location=job_data.location,
                job_type=job_data.job_type,
                status=JobStatus.QUOTE,
                raw_data="Transferred from Intent Handler",
                parsed_data=job_data.model_dump(mode="json"),
                business_id=business_id,
                client_id=client.id,
                created_by_id=user_id,
                invoice_number=invoice_number,
                currency_code=business_currency_code,
            )
            await self.job_repo.save(new_job, session)

            total_price = 0
            for item in job_data.items:
                new_item = JobItem(
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=int(round(item.quantity * item.unit_price)),
                    job_id=new_job.id,
                )
                session.add(new_item)
                total_price += new_item.total_price

            new_job.total_price = total_price

            await session.commit()
            await session.refresh(new_job)
            await session.refresh(new_job, attribute_names=["items"])
            return JobSchema.model_validate(new_job)

    async def convert_to_invoice(
        self, business_id: uuid.UUID, user_id: uuid.UUID, identifier: JobIdentifier
    ) -> HandlerReply | str:
        async with self.session_maker() as session:
            matching_jobs = await self.job_repo.find_quotes_for_client(
                business_id, identifier.client_name, session
            )

            if len(matching_jobs) > 1:
                lines = [f"{i+1}. {job.title}" for i, job in enumerate(matching_jobs)]
                return (
                    f"I found multiple open quotes for {identifier.client_name}. Which one?\n"
                    + "\n".join(lines)
                )

            if not matching_jobs:
                return f"I couldn't find any open quotes for {identifier.client_name}."

            target_job = matching_jobs[0]
            target_job.status = JobStatus.INVOICE
            target_job.is_finalized = True

            total = await self.job_repo.get_total_price(target_job.id, session)
            target_job.total_price = total

            # ── Trigger PDF Generation ────────────────────────────────────────
            # Inject the active session so DocumentService participates in the
            # same transaction. It will NOT commit — we commit once at the end.
            business = await self.business_repo.find_by_id(business_id, session)
            document_url: str | None = None

            if business and business.default_invoice_template_id:
                self.document_service.session = session
                document_url = await self.document_service.generate_document(
                    job_id=target_job.id,
                    template_id=business.default_invoice_template_id,
                    user_id=user_id,
                )

            # Single commit covers: job status change + document tracking
            await session.commit()

            # ── Build reply ───────────────────────────────────────────────────
            currency = target_job.currency_code
            if not currency and business:
                currency = business.currency_code
            currency = currency or "ILS"
            
            amount = f"{target_job.total_price:.2f} {currency}"
            text = f"✅ Invoice ready for {target_job.title}.\nTotal: {amount}."

            if document_url:
                text += "\nYour invoice PDF is attached."

            return HandlerReply(text=text, media_url=document_url)

    async def update_job(
        self, business_id: uuid.UUID, user_id: uuid.UUID, update_data: JobUpdate
    ) -> JobSchema | str:
        async with self.session_maker() as session:
            job = await self.job_repo.find_by_title(
                business_id, update_data.target_job.job_title, session
            )
            if not job:
                return f"Job '{update_data.target_job.job_title}' not found."
            if job.is_finalized:
                return f"Job '{job.title}' is finalized and cannot be updated. You must issue a credit note or revision."

            # Apply scalar field updates
            if update_data.title is not None:
                job.title = update_data.title
            if update_data.description is not None:
                job.description = update_data.description
            if update_data.location is not None:
                job.location = update_data.location
            if update_data.job_type is not None:
                job.job_type = update_data.job_type
            if update_data.status is not None:
                job.status = update_data.status

            # Replace line items if provided
            if update_data.items is not None:
                job.items.clear()
                for item in update_data.items:
                    job.items.append(
                        JobItem(
                            description=item.description,
                            quantity=item.quantity,
                            unit_price=item.unit_price,
                            total_price=int(round(item.quantity * item.unit_price)),
                        )
                    )

            # Update client details if provided (these live on the Client model, not Job)
            if any(
                [
                    update_data.client_name,
                    update_data.client_phone,
                    update_data.client_address,
                    update_data.client_email,
                ]
            ):
                client = await self.client_repo.find_by_name(
                    business_id,
                    update_data.target_job.client_name or update_data.client_name,
                    session,
                )
                if client:
                    if update_data.client_name is not None:
                        client.name = update_data.client_name
                    if update_data.client_phone is not None:
                        client.phone = update_data.client_phone
                    if update_data.client_address is not None:
                        client.address = update_data.client_address
                    if update_data.client_email is not None:
                        client.email = update_data.client_email

            await session.commit()
            await session.refresh(job)
            await session.refresh(job, attribute_names=["items"])
            return JobSchema.model_validate(job)

    async def delete_job(
        self, business_id: uuid.UUID, user_id: uuid.UUID, identifier: JobIdentifier
    ) -> str:
        async with self.session_maker() as session:
            job = await self.job_repo.find_by_title(
                business_id, identifier.job_title, session
            )
            if not job:
                return f"Job '{identifier.job_title}' not found."
            if job.is_finalized:
                return f"Job '{job.title}' is finalized and cannot be deleted. You must void the invoice properly."

            job.is_deleted = True
            await session.commit()
            return f"Job '{identifier.job_title}' deleted successfully."

    async def list_jobs(
        self, business_id: uuid.UUID, user_id: uuid.UUID, filter_data: None = None
    ) -> list[JobSchema] | str:
        async with self.session_maker() as session:
            jobs = await self.job_repo.find_by_business_id(business_id, session)
            if not jobs:
                return "No jobs found."
            return [JobSchema.model_validate(job) for job in jobs]
