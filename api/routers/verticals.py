"""
Vertical discovery and info endpoints.
"""

import csv
from pathlib import Path

from fastapi import APIRouter
from ..schemas import VerticalInfo
from verticals import load_vertical, list_verticals

router = APIRouter(prefix="/verticals", tags=["verticals"])


def _count_seed_rows(csv_path: str) -> int:
    """Count rows in a seed CSV file."""
    p = Path(csv_path)
    if not p.exists():
        return 0
    with open(p) as f:
        return sum(1 for _ in csv.reader(f)) - 1  # minus header


@router.get("", response_model=list[VerticalInfo])
async def get_verticals():
    """List all available verticals with metadata."""
    results = []
    for slug in list_verticals():
        vc = load_vertical(slug)
        seed_count = 0
        for src in vc.seed_sources:
            if src.type == "csv" and src.path:
                seed_count += _count_seed_rows(src.path)
        results.append(VerticalInfo(
            slug=vc.slug,
            name=vc.name,
            description=vc.description,
            seed_count=seed_count,
            search_queries=vc.search_queries[:3],
        ))
    return results


@router.get("/{slug}", response_model=VerticalInfo)
async def get_vertical(slug: str):
    """Get details for a specific vertical."""
    try:
        vc = load_vertical(slug)
    except FileNotFoundError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Vertical '{slug}' not found")

    seed_count = 0
    for src in vc.seed_sources:
        if src.type == "csv" and src.path:
            seed_count += _count_seed_rows(src.path)

    return VerticalInfo(
        slug=vc.slug,
        name=vc.name,
        description=vc.description,
        seed_count=seed_count,
        search_queries=vc.search_queries,
    )
