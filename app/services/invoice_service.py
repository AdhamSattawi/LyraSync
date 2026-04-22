import os
import uuid
import aiofiles
from datetime import datetime, timedelta
from jinja2 import Template
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.domain.models.job import Job
from app.domain.models.business_profile import BusinessProfile
from app.domain.models.job_document import JobDocument
from app.domain.models.document_template import DocumentTemplate
from app.domain.enums.job_document_status import JobDocumentStatus
from app.infrastructure.pdf.pdf_generator import WeasyPrintGenerator
from app.infrastructure.database.repositories.job_document_repository import (
    JobDocumentRepository,
)


class InvoiceService:
    def __init__(self, session: AsyncSession, job_doc_repo: JobDocumentRepository):
        self.session = session
        self.job_doc_repo = job_doc_repo
        self.pdf_generator = WeasyPrintGenerator()

    async def generate_invoice_pdf(
        self, job_id: uuid.UUID, created_by_id: uuid.UUID
    ) -> str:
        """
        Generates a PDF invoice for a given job, saves it to storage,
        and records it in the database.
        """
        # 1. Fetch Job with all related data (Business, Client, Items)
        query = (
            select(Job)
            .where(Job.id == job_id)
            .options(
                selectinload(Job.items),
                selectinload(Job.client),
                selectinload(Job.business),
            )
        )
        result = await self.session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found.")

        business = job.business
        client = job.client

        # 2. Get the template
        if not business.default_invoice_template_id:
            # Fallback: find any invoice template for this business or a system one
            template_query = (
                select(DocumentTemplate)
                .where(
                    DocumentTemplate.business_id == business.id,
                    DocumentTemplate.type == "INVOICE",
                )
                .limit(1)
            )
            template_result = await self.session.execute(template_query)
            template = template_result.scalar_one_or_none()
        else:
            template = await self.session.get(
                DocumentTemplate, business.default_invoice_template_id
            )

        if not template:
            raise ValueError(
                "No invoice template found for this business. Please set one up."
            )

        # 3. Calculate Totals (ADR 016: Integers for money)
        subtotal = sum(item.total_price for item in job.items)
        tax_rate = business.tax_rate_percent or 0.0
        tax_amount = int(subtotal * (tax_rate / 100))
        final_total = subtotal + tax_amount

        # 4. Prepare data for Template (Formatting)
        def format_money(amount_cents: int) -> str:
            return f"{amount_cents / 100:.2f} {job.currency_code}"

        render_data = {
            "business": {
                "name": business.name,
                "address": business.address,
                "phone": business.phone,
                "email": business.email,
            },
            "client": {
                "name": client.first_name + " " + client.last_name,
                "address": client.address,
                "phone": client.phone,
            },
            "invoice": {
                "number": job.invoice_number
                or f"INV-{job.created_at.strftime('%Y%m%d')}-{str(job.id)[:4]}",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
                "subtotal_formatted": format_money(subtotal),
                "tax_rate": tax_rate,
                "tax_amount_formatted": format_money(tax_amount),
                "final_amount_formatted": format_money(final_total),
            },
            "items": [
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price_formatted": format_money(item.unit_price),
                    "total_formatted": format_money(item.total_price),
                }
                for item in job.items
            ],
        }

        # 5. Render HTML
        template_obj = Template(template.html)
        html_content = template_obj.render(**render_data)

        # 6. Generate PDF
        pdf_bytes = await self.pdf_generator.generate(html_content)

        # 7. Save to storage
        storage_dir = os.path.join("storage", "invoices", str(business.id))
        os.makedirs(storage_dir, exist_ok=True)

        file_name = f"invoice_{job.invoice_number or job.id}.pdf"
        file_path = os.path.join(storage_dir, file_name)

        async with aiofiles.open(file_path, mode="wb") as f:
            await f.write(pdf_bytes)

        # 8. Track in database
        await self.job_doc_repo.track_job_document(
            job_id=job.id,
            document_template_id=template.id,
            document_url=file_path,
            created_by_id=created_by_id,
        )

        await self.session.commit()

        return file_path
