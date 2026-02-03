"""
Excel Data Provider - Source of Truth for Fresas
================================================
Handles read/write operations to Excel with file locking.
Falls back to pending log if Excel is locked.
"""
import os
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import threading

try:
    import xlrd
    import xlwt
    from xlutils.copy import copy as xlcopy
except ImportError:
    xlrd = None
    xlwt = None

try:
    import portalocker  # Cross-platform file locking
except ImportError:
    portalocker = None

from app.config import settings, get_excel_path, get_pending_log_path

logger = logging.getLogger(__name__)

# Thread lock for local synchronization
_write_lock = threading.Lock()


@dataclass
class FresaData:
    """Fresa catalog entry."""
    barcode: str
    referencia: Optional[str] = None
    marca: Optional[str] = None
    tipo: Optional[str] = None
    precio: Optional[float] = None


@dataclass
class ConsumoData:
    """Consumo record."""
    fecha: datetime
    barcode: str
    cantidad: int
    operario: str
    proyecto: Optional[str] = None
    referencia: Optional[str] = None
    marca: Optional[str] = None
    tipo: Optional[str] = None
    precio: Optional[float] = None
    synced: bool = False


class ExcelDataProvider:
    """
    Provides read/write access to Excel file with file locking.
    """
    
    def __init__(self, excel_path: Optional[Path] = None):
        self.excel_path = excel_path or get_excel_path()
        self.pending_path = get_pending_log_path()
        self._catalog_cache: Dict[str, FresaData] = {}
        self._last_load: Optional[datetime] = None
    
    def _load_catalog(self, force: bool = False) -> Dict[str, FresaData]:
        """Load fresa catalog from Excel into cache."""
        # Use cache if loaded recently (within 60 seconds)
        if not force and self._catalog_cache and self._last_load:
            age = (datetime.now() - self._last_load).total_seconds()
            if age < 60:
                return self._catalog_cache
        
        if not self.excel_path.exists():
            logger.warning(f"Excel file not found: {self.excel_path}")
            return {}
        
        try:
            wb = xlrd.open_workbook(str(self.excel_path))
            catalog = {}
            
            for sheet_idx in range(wb.nsheets):
                sheet = wb.sheet_by_index(sheet_idx)
                if sheet.nrows < 2:
                    continue
                
                # Detect columns
                headers = [str(c.value).strip().upper() for c in sheet.row(0)]
                col_map = self._detect_columns(headers)
                
                if col_map.get('codigo') is None:
                    continue
                
                # Process rows
                for row_idx in range(1, sheet.nrows):
                    raw_barcode = self._clean_str(sheet.cell(row_idx, col_map['codigo']).value)
                    if not raw_barcode:
                        continue
                    # Normalize barcode to handle comma/dot decimals
                    barcode = self._normalize_barcode(raw_barcode)
                    
                    fresa = FresaData(
                        barcode=barcode,
                        referencia=self._get_cell(sheet, row_idx, col_map.get('ref')),
                        marca=self._get_cell(sheet, row_idx, col_map.get('marca')),
                        tipo=self._get_cell(sheet, row_idx, col_map.get('tipo')),
                        precio=self._parse_precio(self._get_cell(sheet, row_idx, col_map.get('precio')))
                    )
                    
                    # Update existing or add new (last occurrence wins)
                    if barcode in catalog:
                        self._merge_fresa(catalog[barcode], fresa)
                    else:
                        catalog[barcode] = fresa
            
            self._catalog_cache = catalog
            self._last_load = datetime.now()
            logger.info(f"Loaded {len(catalog)} fresas from Excel")
            return catalog
            
        except Exception as e:
            logger.error(f"Error loading Excel: {e}")
            return self._catalog_cache  # Return cached data on error
    
    def _detect_columns(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """Detect column indices from header row."""
        col_map = {'codigo': None, 'ref': None, 'marca': None, 'tipo': None, 'precio': None}
        
        for i, h in enumerate(headers):
            if 'CODIGO' in h or 'ESCANEADO' in h:
                col_map['codigo'] = i
            elif 'REFERENCIA' in h or 'REF' in h:
                col_map['ref'] = i
            elif 'MARCA' in h or 'PROVEEDOR' in h:
                col_map['marca'] = i
            elif 'TIPO' in h:
                col_map['tipo'] = i
            elif 'PRECIO' in h:
                col_map['precio'] = i
        
        return col_map
    
    def _get_cell(self, sheet, row: int, col: Optional[int]) -> Optional[str]:
        """Get cell value safely."""
        if col is None:
            return None
        return self._clean_str(sheet.cell(row, col).value)
    
    def _normalize_barcode(self, code: str) -> str:
        """Normalize barcode: handle comma/dot decimals, remove trailing ,00 or .0"""
        if not code:
            return code
        
        # Convert to string and clean
        code = str(code).strip().upper()
        
        # Remove trailing .0, .00, ,0, ,00 (common in numeric Excel cells)
        import re
        code = re.sub(r'[,\.][0]+$', '', code)
        
        # Also handle scientific notation that Excel sometimes uses
        if 'E+' in code or 'E-' in code:
            try:
                code = str(int(float(code)))
            except:
                pass
        
        return code
    
    def _clean_str(self, val) -> Optional[str]:
        """Clean string value."""
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None
    
    def _parse_precio(self, val: Optional[str]) -> Optional[float]:
        """Parse price from string."""
        if not val:
            return None
        try:
            import re
            match = re.search(r'(\d+[,.]?\d*)', val)
            if match:
                return float(match.group(1).replace(',', '.'))
        except:
            pass
        return None
    
    def _merge_fresa(self, existing: FresaData, new: FresaData):
        """Merge new fresa data into existing (non-null values win)."""
        if new.referencia:
            existing.referencia = new.referencia
        if new.marca:
            existing.marca = new.marca
        if new.tipo:
            existing.tipo = new.tipo
        if new.precio:
            existing.precio = new.precio
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def lookup_barcode(self, barcode: str) -> Optional[FresaData]:
        """Lookup fresa by barcode."""
        catalog = self._load_catalog()
        # Normalize the searched barcode to match catalog
        normalized = self._normalize_barcode(barcode)
        return catalog.get(normalized)
    
    def get_all_fresas(self) -> List[FresaData]:
        """Get all fresas from catalog."""
        catalog = self._load_catalog()
        return list(catalog.values())
    
    def get_fresa_count(self) -> int:
        """Get count of fresas in catalog."""
        catalog = self._load_catalog()
        return len(catalog)
    
    def add_fresa(
        self,
        barcode: str,
        referencia: Optional[str] = None,
        marca: Optional[str] = None,
        tipo: Optional[str] = None,
        precio: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Add a new fresa to the Excel catalog.
        Returns success status and the saved fresa data.
        """
        barcode = barcode.upper().strip()
        if not barcode:
            return {"success": False, "error": "Código de barras requerido"}
        
        # Check if already exists
        existing = self.lookup_barcode(barcode)
        if existing:
            return {"success": False, "error": "Esta fresa ya existe en el catálogo"}
        
        with _write_lock:
            try:
                if not self.excel_path.exists():
                    return {"success": False, "error": "Archivo Excel no encontrado"}
                
                # Open workbook
                rb = xlrd.open_workbook(str(self.excel_path), formatting_info=True)
                wb = xlcopy(rb)
                
                # Use first sheet
                ws = wb.get_sheet(0)
                sheet = rb.sheet_by_index(0)
                
                # Find the next empty row
                next_row = sheet.nrows
                
                # Detect columns from headers
                headers = [str(c.value).strip().upper() for c in sheet.row(0)]
                col_map = self._detect_columns(headers)
                
                if col_map.get('codigo') is None:
                    return {"success": False, "error": "No se encontró columna de código"}
                
                # Write data to cells
                ws.write(next_row, col_map['codigo'], barcode)
                if col_map.get('ref') is not None and referencia:
                    ws.write(next_row, col_map['ref'], referencia)
                if col_map.get('marca') is not None and marca:
                    ws.write(next_row, col_map['marca'], marca)
                if col_map.get('tipo') is not None and tipo:
                    ws.write(next_row, col_map['tipo'], tipo)
                if col_map.get('precio') is not None and precio:
                    ws.write(next_row, col_map['precio'], precio)
                
                # Save workbook
                wb.save(str(self.excel_path))
                
                # Invalidate cache to force reload
                self._last_load = None
                self._catalog_cache = {}
                
                fresa = FresaData(
                    barcode=barcode,
                    referencia=referencia,
                    marca=marca,
                    tipo=tipo,
                    precio=precio
                )
                
                logger.info(f"FRESA AÑADIDA: {barcode}")
                
                return {
                    "success": True,
                    "message": "Fresa añadida al catálogo",
                    "data": {
                        "barcode": fresa.barcode,
                        "referencia": fresa.referencia,
                        "marca": fresa.marca,
                        "tipo": fresa.tipo,
                        "precio": fresa.precio
                    }
                }
                
            except Exception as e:
                logger.error(f"Error adding fresa to Excel: {e}")
                return {"success": False, "error": f"Error al guardar: {str(e)}"}
    
    def is_excel_accessible(self) -> bool:
        """Check if Excel file is accessible."""
        return self.excel_path.exists()
    
    def register_consumo(
        self,
        barcode: str,
        cantidad: int,
        operario: str,
        proyecto: Optional[str] = None,
        marca: Optional[str] = None,
        tipo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a consumo. Tries to write to Excel first.
        Falls back to pending log if Excel is locked.
        If fresa not found but marca/tipo provided, registers as NEW.
        """
        fresa = self.lookup_barcode(barcode)
        
        # If not found in catalog
        if not fresa:
            # Check if marca/tipo provided for new fresa
            if not marca:
                return {"success": False, "error": "Barcode not found", "not_found": True}
            
            # Create consumo for NEW fresa
            consumo = ConsumoData(
                fecha=datetime.now(),
                barcode=self._normalize_barcode(barcode),
                cantidad=cantidad,
                operario=operario,
                proyecto=proyecto,
                referencia="NUEVA",  # Mark as new
                marca=marca,
                tipo=tipo or "PENDIENTE",
                precio=None
            )
        else:
            # Use catalog data
            consumo = ConsumoData(
                fecha=datetime.now(),
                barcode=barcode.upper(),
                cantidad=cantidad,
                operario=operario,
                proyecto=proyecto,
                referencia=fresa.referencia,
                marca=fresa.marca,
                tipo=fresa.tipo,
                precio=fresa.precio
            )
        
        # Try to write to Excel with lock
        with _write_lock:
            success = self._write_consumo_to_excel(consumo)
            
            if not success:
                # Fallback: write to pending log
                logger.warning("Excel locked, writing to pending log")
                self._write_to_pending_log(consumo)
                return {
                    "success": True,
                    "pending": True,
                    "message": "Guardado en cola pendiente (Excel bloqueado)",
                    "data": self._consumo_to_dict(consumo)
                }
        
        return {
            "success": True,
            "pending": False,
            "message": "Consumo registrado",
            "data": self._consumo_to_dict(consumo)
        }
    
    def _find_sheet_for_marca(self, marca: str, rb) -> Optional[int]:
        """Find the sheet index that matches the marca/proveedor."""
        if not marca:
            return 0  # Default to first sheet
        
        marca_upper = marca.upper().strip()
        
        # Mapping of keywords to sheet patterns
        mappings = {
            'MITSUBISHI': 'MITSUBIS',
            'MITSHUBITSHI': 'MITSUBIS',
            'MITSUBIS': 'MITSUBIS',
            'SUMITOMO': 'SUM-WID',
            'WIDIN': 'SUM-WID',
            'WIDEAL': 'SUM-WID',
            'HORN': 'HORN',
            'SUM': 'SUM-WID',
            'WID': 'SUM-WID',
            'AYMA': 'AYMA',
            'WNT': 'WNT',
            'TAEGU': 'TAEGU',
            'TUNGA': 'TUNGA',
            'TUNGALOY': 'TUNGA',
        }
        
        # Find matching sheet
        for keyword, sheet_pattern in mappings.items():
            if keyword in marca_upper:
                # Search for sheet with this pattern
                for i in range(rb.nsheets):
                    sheet_name = rb.sheet_by_index(i).name.upper()
                    if sheet_pattern in sheet_name:
                        return i
        
        # Default to first sheet if no match
        return 0
    
    def _write_consumo_to_excel(self, consumo: ConsumoData) -> bool:
        """Write consumo to the correct Excel sheet based on marca."""
        try:
            if not self.excel_path.exists():
                logger.error(f"Excel file not found: {self.excel_path}")
                return False
            
            # Open workbook for editing
            rb = xlrd.open_workbook(str(self.excel_path), formatting_info=True)
            wb = xlcopy(rb)
            
            # Find the correct sheet based on marca
            sheet_idx = self._find_sheet_for_marca(consumo.marca, rb)
            ws = wb.get_sheet(sheet_idx)
            sheet = rb.sheet_by_index(sheet_idx)
            sheet_name = sheet.name
            
            # Find the last row with data in CÓDIGO column (column 3)
            # This is more reliable than checking FECHA since catalog entries have codes
            last_data_row = 0
            for row_idx in range(1, sheet.nrows):
                cell_val = sheet.cell(row_idx, 3).value  # Check CÓDIGO column
                if cell_val is not None and str(cell_val).strip() != '':
                    last_data_row = row_idx
            
            # Write in the next row after the last data row
            next_row = last_data_row + 1
            
            # Write data to columns matching Excel structure:
            # 0: FECHA, 1: OP, 2: UDS, 3: CÓDIGO ESCANEADO, 4: REFERENCIA FRESA,
            # 5: PROVEEDOR MARCA, 6: TIPO DE FRESA, 7: PRECIO, 8: FICHA (proyecto)
            ws.write(next_row, 0, consumo.fecha.strftime('%Y-%m-%d %H:%M'))  # FECHA
            ws.write(next_row, 1, consumo.operario)  # OP (operario)
            ws.write(next_row, 2, consumo.cantidad)  # UDS (unidades)
            ws.write(next_row, 3, consumo.barcode)  # CÓDIGO ESCANEADO
            ws.write(next_row, 4, consumo.referencia or '')  # REFERENCIA FRESA
            ws.write(next_row, 5, consumo.marca or '')  # PROVEEDOR MARCA
            ws.write(next_row, 6, consumo.tipo or '')  # TIPO DE FRESA
            if consumo.precio:
                ws.write(next_row, 7, consumo.precio)  # PRECIO
            if consumo.proyecto:
                ws.write(next_row, 8, consumo.proyecto)  # FICHA (proyecto)
            
            # Save workbook
            wb.save(str(self.excel_path))
            
            logger.info(f"CONSUMO GUARDADO EN EXCEL [{sheet_name}]: {consumo.barcode} x{consumo.cantidad} by {consumo.operario}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write consumo to Excel: {e}")
            return False
    
    def _write_to_pending_log(self, consumo: ConsumoData):
        """Write consumo to pending CSV log."""
        file_exists = self.pending_path.exists()
        
        with open(self.pending_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['fecha', 'barcode', 'cantidad', 'operario', 'proyecto',
                               'referencia', 'marca', 'tipo', 'precio', 'synced'])
            writer.writerow([
                consumo.fecha.isoformat(),
                consumo.barcode,
                consumo.cantidad,
                consumo.operario,
                consumo.proyecto or '',
                consumo.referencia or '',
                consumo.marca or '',
                consumo.tipo or '',
                consumo.precio or '',
                'N'
            ])
        logger.info(f"Wrote pending consumo: {consumo.barcode}")
    
    def get_pending_count(self) -> int:
        """Get count of pending consumos."""
        if not self.pending_path.exists():
            return 0
        with open(self.pending_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            return sum(1 for row in reader if row and row[-1] == 'N')
    
    def sync_pending(self) -> Dict[str, Any]:
        """Try to sync pending consumos to Excel."""
        if not self.pending_path.exists():
            return {"synced": 0, "failed": 0}
        
        synced = 0
        failed = 0
        rows_to_keep = []
        
        try:
            # Read all pending rows
            with open(self.pending_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    rows_to_keep.append(header)
                
                for row in reader:
                    if not row:
                        continue
                    
                    # Check if already synced (last column is 'Y')
                    if row[-1] == 'Y':
                        rows_to_keep.append(row)
                        continue
                    
                    # Try to write to Excel
                    try:
                        # Parse the row: fecha, barcode, cantidad, operario, referencia, marca, tipo, precio, synced
                        consumo = ConsumoData(
                            fecha=datetime.fromisoformat(row[0]),
                            barcode=row[1],
                            cantidad=int(row[2]),
                            operario=row[3],
                            proyecto=row[4] if len(row) > 4 and row[4] else None,
                            referencia=row[5] if len(row) > 5 and row[5] else None,
                            marca=row[6] if len(row) > 6 and row[6] else None,
                            tipo=row[7] if len(row) > 7 and row[7] else None,
                            precio=float(row[8]) if len(row) > 8 and row[8] else None
                        )
                        
                        with _write_lock:
                            if self._write_consumo_to_excel(consumo):
                                row[-1] = 'Y'  # Mark as synced
                                synced += 1
                            else:
                                failed += 1
                    except Exception as e:
                        logger.error(f"Error syncing row: {e}")
                        failed += 1
                    
                    rows_to_keep.append(row)
            
            # Rewrite the pending file with updated sync status
            with open(self.pending_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows_to_keep)
            
            logger.info(f"Sync complete: {synced} synced, {failed} failed")
            return {"synced": synced, "failed": failed}
            
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return {"synced": synced, "failed": failed, "error": str(e)}
    
    def _consumo_to_dict(self, consumo: ConsumoData) -> Dict[str, Any]:
        """Convert consumo to dict for API response."""
        return {
            "fecha": consumo.fecha.isoformat(),
            "barcode": consumo.barcode,
            "cantidad": consumo.cantidad,
            "operario": consumo.operario,
            "proyecto": consumo.proyecto,
            "referencia": consumo.referencia,
            "marca": consumo.marca,
            "tipo": consumo.tipo,
            "precio": consumo.precio
        }


# Global instance
_provider: Optional[ExcelDataProvider] = None


def get_data_provider() -> ExcelDataProvider:
    """Get singleton data provider instance."""
    global _provider
    if _provider is None:
        _provider = ExcelDataProvider()
    return _provider
