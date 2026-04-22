import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.domain.models.job import Job
from app.services.builders.document_context_builder import DocumentContextBuilder


class QuoteContextBuilder(DocumentContextBuilder):
    async def build_context(self, job_id: uuid.UUID, session: AsyncSession) -> dict:
        """
        Builds the context dictionary for a Quote document.
        Focuses on "Proposed" values and "Estimated" terminology.
        """
        # 1. Fetch Job
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

        # 2. Formatter helper
        def format_money(amount_cents: int) -> str:
            return f"{amount_cents / 100:.2f} {job.currency_code}"

        # 3. Final Context
        # Note: Quotes often don't include taxes until converted to invoices,
        # but this depends on business settings. We'll mirror invoice for now.
        subtotal = sum(item.total_price for item in job.items)

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
            "invoice": {  # The template uses the 'invoice' key for compatibility
                "number": job.invoice_number,
                "date": datetime.now().strftime(business.date_format),
                "due_date": (datetime.now() + timedelta(days=30)).strftime(
                    business.date_format
                ),  # Quotes valid for 30 days
                "subtotal_formatted": format_money(subtotal),
                "final_amount_formatted": format_money(subtotal),  # No tax on quote for now
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
