from datetime import datetime, timezone 

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..dependencies import get_db, get_current_user
from ...database.models import Invoice
from ...utils.logger import get_logger

logger = get_logger()
router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.get("/")
async def get_user_invoices(
    user = Depends(get_current_user()),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get invoices for current user."""
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    query = (
        select(Invoice)
        .where(Invoice.user_id == user.id)
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return [
        {
            "id": str(inv.id),
            "vendor_name": inv.vendor_name,
            "invoice_number": inv.invoice_number,
            "total_amount": inv.total_amount,
            "currency": inv.currency,
            "invoice_date": inv.invoice_date.isoformat(),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "status": "paid" if inv.due_date and inv.due_date < datetime.now(timezone.utc) else "unpaid"
        }
        for inv in invoices
    ]