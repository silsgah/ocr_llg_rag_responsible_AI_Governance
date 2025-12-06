"""Production-grade invoice extraction service."""
import logging
from typing import Any
from pathlib import Path

from pydantic import BaseModel, Field, validator
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.llm import LLMClient
from ..config import Settings
from ..database.models import Invoice
from ..utils.logger import get_logger

logger = get_logger()

class InvoiceData(BaseModel):
    vendor_name: str = Field(description="Full name of the vendor/company")
    vendor_address: str | None = Field(default=None, description="Vendor address")
    invoice_number: str = Field(description="Unique invoice identifier")
    invoice_date: str = Field(description="Invoice date in YYYY-MM-DD format")
    due_date: str | None = Field(default=None, description="Due date in YYYY-MM-DD")
    total_amount: float = Field(description="Total amount including tax")
    tax_amount: float | None = Field(default=None, description="Tax amount")
    currency: str = Field(default="USD", description="Currency code (e.g., USD, EUR)")
    line_items: list[dict] = Field(default_factory=list, description="Line items")

    @validator('invoice_date', 'due_date', pre=True)
    def validate_date(cls, v):
        if v:
            if not (len(v) == 10 and v[4] == '-' and v[7] == '-'):
                raise ValueError("Date must be YYYY-MM-DD")
        return v

class InvoiceExtractor:
    def __init__(self, llm_client: LLMClient, settings: Settings):
        self.llm_client = llm_client
        self.settings = settings
        self.parser = PydanticOutputParser(pydantic_object=InvoiceData)
        self.prompt = PromptTemplate(
            template=(
                "You are an expert accounting assistant. Extract structured invoice data.\n"
                "{format_instructions}\n\n"
                "RULES:\n"
                "- Return ONLY valid JSON.\n"
                "- Omit missing fields or set to null.\n"
                "- Dates: YYYY-MM-DD.\n"
                "- total_amount includes tax.\n\n"
                "Text:\n{text}"
            ),
            input_variables=["text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )

    def extract(self, text: str) -> InvoiceData:
        logger.info("🧾 Extracting invoice data...")
        try:
            llm = self.llm_client.get_client()
            
            # Enable JSON mode for Ollama
            if hasattr(llm, '_client_kwargs'):
                llm._client_kwargs["format"] = "json"
            elif hasattr(llm, 'kwargs'):
                llm.kwargs["format"] = "json"
            else:
                # Fallback: hope model supports JSON
                pass

            chain = self.prompt | llm
            raw_output = chain.invoke({"text": text})
            content = raw_output.content if hasattr(raw_output, 'content') else str(raw_output)
            
            parsed = self.parser.parse(content)
            logger.success(f"✅ Extracted: {parsed.invoice_number} | {parsed.vendor_name}")
            return parsed
        except Exception as e:
            logger.error(f"❌ Extraction failed: {str(e)}")
            raise

    async def save_to_db(self, db: AsyncSession, invoice_data: InvoiceData, file_path: str) -> Invoice:
        """Save extracted invoice to database."""
        from datetime import datetime
        logger.info(f"💾 Saving invoice {invoice_data.vendor_name} to DB")
        logger.info(f"🔍 Preparing to save invoice: {invoice_data.invoice_number}")
        invoice = Invoice(
            vendor_name=invoice_data.vendor_name,
            vendor_address=invoice_data.vendor_address,
            invoice_number=invoice_data.invoice_number,
            invoice_date=datetime.strptime(invoice_data.invoice_date, "%Y-%m-%d"),
            due_date=datetime.strptime(invoice_data.due_date, "%Y-%m-%d") if invoice_data.due_date else None,
            total_amount=invoice_data.total_amount,
            tax_amount=invoice_data.tax_amount,
            currency=invoice_data.currency,
            line_items=invoice_data.line_items,
            file_path=file_path
        )
        db.add(invoice)
        logger.info("🔍 About to commit")
        await db.commit()  
        logger.info("✅ Invoice COMMITTED to DB!")
        await db.flush()
        logger.info(f"💾 Saved invoice {invoice.id} to DB")
        return invoice