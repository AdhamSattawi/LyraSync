import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.domain.models.job import Job
from app.services.builders.document_context_builder import DocumentContextBuilder


class InvoiceContextBuilder(DocumentContextBuilder):
    async def build_context(self, job_id: uuid.UUID, session: AsyncSession) -> dict:
        """
        Builds the context dictionary for an Invoice document.
        Handles ADR 016 integer formatting and tax calculations.
        """
        # 1. Fetch Job with all related data
        query = (
            select(Job)
            .where(Job.id == job_id)
            .options(
                selectinload(Job.items),
                selectinload(Job.client),
                selectinload(Job.business),
            )
        )
        result = await session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found.")

        business = job.business
        client = job.client

        # 2. Calculate Totals (ADR 016)
        subtotal = sum(item.total_price for item in job.items)
        tax_rate = business.tax_rate_percent or 0.0
        tax_amount = int(subtotal * (tax_rate / 100))
        final_total = subtotal + tax_amount

        # 3. Formatter helper
        def format_money(amount_cents: int) -> str:
            return f"{amount_cents / 100:.2f} {job.currency_code}"

        # 4. Final Context
        return {
            "language_code": business.language_code,
            "date_format": business.date_format,
            "text_direction": business.text_direction,
            "business": {
                "name": business.name,
                "address": business.address,
                "phone": business.phone,
                "email": business.email,
            },
            "client": {
                "name": client.name,
                "address": client.address,
                "phone": client.phone,
            },
            "invoice": {
                "number": job.invoice_number
                or f"INV-{job.created_at.strftime('%Y%m%d')}-{str(job.id)[:4]}",
                "date": datetime.now().strftime(business.date_format),
                "due_date": (datetime.now() + timedelta(days=14)).strftime(
                    business.date_format
                ),
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
