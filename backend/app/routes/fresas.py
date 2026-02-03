"""
Fresas Standalone - API Routes
==============================
Endpoints for barcode scanning and consumo registration.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import csv
import io

from app.data_provider import get_data_provider, FresaData
from app.schemas.fresas import (
    FresaOut,
    FresaCreate,
    ConsumoRequest,
    ConsumoResponse,
    LookupResponse,
    CatalogoResponse,
    HealthResponse,
    SyncResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check system health: Excel accessibility, pending consumos.
    """
    provider = get_data_provider()
    
    excel_ok = provider.is_excel_accessible()
    pending_count = provider.get_pending_count()
    fresa_count = provider.get_fresa_count() if excel_ok else 0
    
    return HealthResponse(
        status="ok" if excel_ok else "degraded",
        excel_ok=excel_ok,
        pending_count=pending_count,
        fresa_count=fresa_count
    )


# =============================================================================
# BARCODE LOOKUP
# =============================================================================

@router.get("/lookup", response_model=LookupResponse)
async def lookup_barcode(barcode: str = Query(..., description="Barcode to lookup")):
    """
    Lookup fresa by barcode. Returns all data (autocomplete).
    """
    provider = get_data_provider()
    fresa = provider.lookup_barcode(barcode)
    
    logger.info(f"SCAN: {barcode} -> {'FOUND' if fresa else 'NOT_FOUND'}")
    
    if not fresa:
        return LookupResponse(found=False, fresa=None)
    
    return LookupResponse(
        found=True,
        fresa=FresaOut(
            barcode=fresa.barcode,
            referencia=fresa.referencia,
            marca=fresa.marca,
            tipo=fresa.tipo,
            precio=fresa.precio
        )
    )


@router.get("/marcas")
async def get_marcas():
    """Get list of unique marcas/proveedores from catalog."""
    provider = get_data_provider()
    marcas = provider.get_marcas()
    return {"marcas": marcas}


# =============================================================================
# REGISTER CONSUMO
# =============================================================================

@router.post("/consumo", response_model=ConsumoResponse)
async def register_consumo(data: ConsumoRequest):
    """
    Register fresa consumption. 
    Writes to Excel if possible, falls back to pending log if locked.
    Supports new fresas with marca/tipo provided.
    """
    provider = get_data_provider()
    
    logger.info(f"CONSUMO: {data.barcode} x{data.cantidad} by {data.operario} proyecto={data.proyecto}")
    
    result = provider.register_consumo(
        barcode=data.barcode,
        cantidad=data.cantidad,
        operario=data.operario,
        proyecto=data.proyecto,
        marca=data.marca,
        tipo=data.tipo
    )
    
    if not result.get("success"):
        # If not found, return special error for frontend to handle
        if result.get("not_found"):
            raise HTTPException(status_code=404, detail=result.get("error", "Barcode not found"))
        raise HTTPException(status_code=400, detail=result.get("error", "Error"))
    
    return ConsumoResponse(
        success=True,
        pending=result.get("pending", False),
        message=result.get("message", "OK"),
        data=result.get("data")
    )


# =============================================================================
# ADD NEW FRESA
# =============================================================================

@router.post("/fresa", response_model=ConsumoResponse)
async def create_fresa(data: FresaCreate):
    """
    Add a new fresa to the Excel catalog.
    """
    provider = get_data_provider()
    
    logger.info(f"CREAR FRESA: {data.barcode}")
    
    result = provider.add_fresa(
        barcode=data.barcode,
        referencia=data.referencia,
        marca=data.marca,
        tipo=data.tipo,
        precio=data.precio
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error"))
    
    return ConsumoResponse(
        success=True,
        pending=False,
        message=result.get("message", "Fresa añadida"),
        data=result.get("data")
    )


# =============================================================================
# CATALOG
# =============================================================================

@router.get("/catalogo", response_model=CatalogoResponse)
async def get_catalogo(
    search: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(200, ge=1, le=500)
):
    """
    Get fresa catalog.
    """
    provider = get_data_provider()
    fresas = provider.get_all_fresas()
    
    # Filter if search provided
    if search:
        search_lower = search.lower()
        fresas = [f for f in fresas if (
            search_lower in f.barcode.lower() or
            (f.referencia and search_lower in f.referencia.lower()) or
            (f.marca and search_lower in f.marca.lower())
        )]
    
    # Limit
    fresas = fresas[:limit]
    
    return CatalogoResponse(
        total=len(fresas),
        fresas=[FresaOut(
            barcode=f.barcode,
            referencia=f.referencia,
            marca=f.marca,
            tipo=f.tipo,
            precio=f.precio
        ) for f in fresas]
    )


# =============================================================================
# SYNC PENDING
# =============================================================================

@router.post("/sync", response_model=SyncResponse)
async def sync_pending():
    """
    Attempt to sync pending consumos to Excel.
    """
    provider = get_data_provider()
    result = provider.sync_pending()
    
    logger.info(f"SYNC: {result}")
    
    return SyncResponse(
        synced=result.get("synced", 0),
        failed=result.get("failed", 0),
        message=result.get("message")
    )


# =============================================================================
# EXPORT CSV
# =============================================================================

@router.get("/export/consumos")
async def export_consumos_csv(
    desde: Optional[str] = Query(None, description="From date YYYY-MM-DD"),
    hasta: Optional[str] = Query(None, description="To date YYYY-MM-DD")
):
    """
    Export consumos to CSV for future ERP import.
    """
    # TODO: Implement reading from pending log + Excel consumos sheet
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header matching ERP schema
    writer.writerow([
        'fecha', 'barcode', 'referencia', 'marca', 'tipo', 
        'precio', 'cantidad', 'operario'
    ])
    
    # TODO: Add rows from data
    
    output.seek(0)
    
    filename = f"consumos_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
