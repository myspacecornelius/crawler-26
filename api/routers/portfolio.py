"""
Portfolio intelligence endpoints — query portfolio companies by fund.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import PortfolioCompany
from ..schemas import PortfolioCompanyResponse, PortfolioCompanyList

router = APIRouter(prefix="/funds", tags=["portfolio"])


@router.get("/{fund}/portfolio", response_model=PortfolioCompanyList)
async def get_fund_portfolio(
    fund: str,
    sector: Optional[str] = None,
    stage: Optional[str] = None,
    year: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get portfolio companies for a fund. Fund name is matched case-insensitively."""
    query = select(PortfolioCompany).where(
        PortfolioCompany.fund_name.ilike(f"%{fund}%")
    )

    if sector:
        query = query.where(PortfolioCompany.sector.ilike(f"%{sector}%"))
    if stage:
        query = query.where(PortfolioCompany.stage.ilike(f"%{stage}%"))
    if year:
        query = query.where(PortfolioCompany.year == year)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.order_by(PortfolioCompany.company_name.asc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    companies = result.scalars().all()

    return PortfolioCompanyList(
        companies=[PortfolioCompanyResponse.model_validate(c) for c in companies],
        total=total,
        fund_name=fund,
    )
