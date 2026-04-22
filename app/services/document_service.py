import uuid
from jinja2 import Template
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.document_template import DocumentTemplate
from app.infrastructure.pdf.pdf_generator import WeasyPrintGenerator
from app.infrastructure.database.repositories.job_document_repository import (
    JobDocumentRepository,
)
from app.infrastructure.storage.storage_service import StorageService
from app.services.builders.invoice_context_builder import InvoiceContextBuilder
from app.services.builders.quote_context_builder import QuoteContextBuilder


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        job_doc_repo: JobDocumentRepository,
        storage_service: StorageService,
    ):
        self.session = session
        self.job_doc_repo = job_doc_repo
        self.storage_service = storage_service
        self.pdf_generator = WeasyPrintGenerator()

        # ── Builder Registry ────────────────────────────────────────────────
        # To add a new document type: create a ContextBuilder and register it here.
        self._builders = {
            "INVOICE": InvoiceContextBuilder(),
            "QUOTE": QuoteContextBuilder(),
        }

    async def generate_document(
        self,
        job_id: uuid.UUID,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        """
        Orchestrates the generation of any document type.

        Returns:
            A publicly accessible URL (SAS URL for Azure, file path for local dev)
            pointing to the generated PDF. The caller is responsible for committing
            the session — this method does not commit.
        """
        # 1. Fetch Template
        template = await self.session.get(DocumentTemplate, template_id)
        if not template:
            raise ValueError(f"DocumentTemplate {template_id} not found.")

        # 2. Get Builder
        builder = self._builders.get(template.type.upper())
        if not builder:
            raise ValueError(
                f"No ContextBuilder registered for template type: '{template.type}'"
            )

        # 3. Build Context
        context = await builder.build_context(job_id, self.session)

        # 4. Render HTML
        html_content = Template(template.html).render(**context)

        # 5. Generate PDF bytes
        pdf_bytes = await self.pdf_generator.generate(html_content)

        # 6. Upload via StorageService (returns SAS URL or local path)
        # Path convention: documents/{business_id}/{type}_{job_id}_{uid}.pdf
        destination = (
            f"documents/{template.business_id}/"
            f"{template.type.lower()}_{job_id}_{uuid.uuid4().hex[:6]}.pdf"
        )
        document_url = await self.storage_service.upload(
            file_bytes=pdf_bytes,
            destination_path=destination,
            content_type="application/pdf",
        )

        # 7. Record document tracking in DB (caller commits)
        await self.job_doc_repo.track_job_document(
            job_id=job_id,
            document_template_id=template.id,
            document_url=document_url,
            created_by_id=user_id,
            session=self.session,
        )

        return document_url
