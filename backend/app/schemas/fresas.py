"""
Fresas Standalone - Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class FresaCreate(BaseModel):
    """Request to create a new fresa in the catalog."""
    barcode: str
    referencia: Optional[str] = None
    marca: Optional[str] = None
    tipo: Optional[str] = None
    precio: Optional[float] = None


class FresaOut(BaseModel):
    """Fresa catalog entry for API response."""
    barcode: str
    referencia: Optional[str] = None
    marca: Optional[str] = None
    tipo: Optional[str] = None
    precio: Optional[float] = None


class ConsumoRequest(BaseModel):
    """Request to register a consumo."""
    barcode: str
    cantidad: int = 1
    operario: str
    proyecto: Optional[str] = None  # Número de proyecto/ficha
    # Para fresas nuevas (no catalogadas)
    marca: Optional[str] = None
    tipo: Optional[str] = None


class ConsumoOut(BaseModel):
    """Consumo for API response."""
    fecha: str
    barcode: str
    cantidad: int
    operario: str
    proyecto: Optional[str] = None
    referencia: Optional[str] = None
    marca: Optional[str] = None
    tipo: Optional[str] = None
    precio: Optional[float] = None


class ConsumoResponse(BaseModel):
    """Response after registering consumo."""
    success: bool
    pending: bool = False
    message: str
    data: Optional[ConsumoOut] = None


class LookupResponse(BaseModel):
    """Response for barcode lookup."""
    found: bool
    fresa: Optional[FresaOut] = None


class CatalogoResponse(BaseModel):
    """Response for catalog listing."""
    total: int
    fresas: List[FresaOut]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    excel_ok: bool
    pending_count: int
    fresa_count: int
    last_modified: Optional[str] = None


class SyncResponse(BaseModel):
    """Response from sync operation."""
    synced: int
    failed: int
    message: Optional[str] = None


class ExportRequest(BaseModel):
    """Request for CSV export."""
    desde: Optional[str] = None
    hasta: Optional[str] = None
