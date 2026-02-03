/**
 * FRESAS STANDALONE - Main Scan Page
 * ===================================
 * Simplified clone of ERP scan page.
 * Flow: Scan barcode → autocomplete all → click Register → saved
 * NO projects, NO extra fields.
 */
'use client';

import { useState, useRef, useEffect } from 'react';
import { apiGet, apiPost } from '@/lib/api';
import {
    Scan, Check, AlertCircle, Package, DollarSign,
    RefreshCw, Loader2, CheckCircle2, XCircle, Clock
} from 'lucide-react';

interface FresaData {
    barcode: string;
    referencia: string | null;
    marca: string | null;
    tipo: string | null;
    precio: number | null;
}

interface ConsumoResult {
    success: boolean;
    pending: boolean;
    message: string;
    data?: any;
}

interface HealthStatus {
    status: string;
    excel_ok: boolean;
    pending_count: number;
    fresa_count: number;
}

export default function ScanPage() {
    // State
    const [barcode, setBarcode] = useState('');
    const [operario, setOperario] = useState('');
    const [proyecto, setProyecto] = useState('');
    const [cantidad, setCantidad] = useState(1);
    const [fresa, setFresa] = useState<FresaData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<ConsumoResult | null>(null);
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [currentDate, setCurrentDate] = useState('');

    // New fresa form state
    const [isNewFresaMode, setIsNewFresaMode] = useState(false);
    const [newFresaData, setNewFresaData] = useState<Partial<FresaData>>({});

    const barcodeRef = useRef<HTMLInputElement>(null);

    // Focus on barcode input on mount
    useEffect(() => {
        barcodeRef.current?.focus();
        checkHealth();
        // Update date
        const updateDate = () => {
            const now = new Date();
            setCurrentDate(now.toLocaleDateString('es-ES', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }));
        };
        updateDate();
        const interval = setInterval(updateDate, 60000); // Update every minute
        return () => clearInterval(interval);
    }, []);

    // Auto-hide success after 3 seconds
    useEffect(() => {
        if (success) {
            const timer = setTimeout(() => {
                setSuccess(null);
                resetForm();
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [success]);

    async function checkHealth() {
        try {
            const data = await apiGet('/health');
            setHealth(data);
        } catch (e) {
            console.error('Health check failed:', e);
        }
    }

    async function lookupBarcode(code: string) {
        if (!code.trim()) return;

        setLoading(true);
        setError(null);
        setFresa(null);
        setIsNewFresaMode(false);

        try {
            const result = await apiGet('/lookup', { barcode: code });

            if (result.found) {
                setFresa(result.fresa);
            } else {
                // Show form to add new fresa
                setIsNewFresaMode(true);
                setNewFresaData({ barcode: code.toUpperCase() });
                setError(null);
            }
        } catch (e: any) {
            setError(e.message || 'Error de conexión');
        } finally {
            setLoading(false);
        }
    }

    async function saveNewFresa() {
        if (!newFresaData.barcode || !newFresaData.marca) {
            setError('Código y marca son requeridos');
            return;
        }

        if (!operario.trim()) {
            setError('Ingresa tu nombre de operario');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Register consumo with new fresa data
            const result = await apiPost('/consumo', {
                barcode: newFresaData.barcode,
                cantidad,
                operario: operario.trim(),
                proyecto: proyecto.trim() || null,
                marca: newFresaData.marca,
                tipo: newFresaData.tipo || 'PENDIENTE'
            });

            setSuccess({
                success: true,
                pending: result.pending || false,
                message: 'Consumo registrado - FRESA NUEVA marcada en Excel'
            });
            checkHealth();
        } catch (e: any) {
            setError(e.message || 'Error al registrar consumo');
        } finally {
            setLoading(false);
        }
    }

    async function registerConsumo() {
        if (!fresa || !operario.trim()) {
            setError('Ingresa tu nombre de operario');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const result = await apiPost('/consumo', {
                barcode: fresa.barcode,
                cantidad,
                operario: operario.trim(),
                proyecto: proyecto.trim() || null
            });

            setSuccess(result as ConsumoResult);
            checkHealth(); // Refresh pending count
        } catch (e: any) {
            setError(e.message || 'Error al registrar');
        } finally {
            setLoading(false);
        }
    }

    function resetForm() {
        setBarcode('');
        setFresa(null);
        setCantidad(1);
        setProyecto('');
        setError(null);
        setIsNewFresaMode(false);
        setNewFresaData({});
        barcodeRef.current?.focus();
    }

    async function syncPending() {
        setLoading(true);
        try {
            await apiPost('/sync');
            checkHealth();
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }

    function formatCurrency(val: number | null) {
        if (val == null) return '—';
        return val.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });
    }

    // Handle barcode input - auto-lookup on Enter or after pause
    function handleBarcodeKeyDown(e: React.KeyboardEvent) {
        if (e.key === 'Enter' && barcode.trim()) {
            lookupBarcode(barcode.trim());
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
            {/* Header */}
            <div className="max-w-xl mx-auto mb-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                            <Scan className="h-8 w-8 text-emerald-400" />
                            Control de Fresas
                        </h1>
                        {currentDate && (
                            <p className="text-sm text-slate-400 mt-1 ml-11">{currentDate}</p>
                        )}
                    </div>

                    {/* Status indicator */}
                    <div className="flex items-center gap-2">
                        {health?.pending_count ? (
                            <button
                                onClick={syncPending}
                                className="flex items-center gap-2 px-3 py-1 bg-amber-500/20 text-amber-400 rounded-full text-sm"
                            >
                                <Clock className="h-4 w-4" />
                                {health.pending_count} pendientes
                            </button>
                        ) : null}
                        <div className={`flex items-center gap-1 text-sm ${health?.excel_ok ? 'text-emerald-400' : 'text-red-400'}`}>
                            {health?.excel_ok ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                            {health?.fresa_count || 0} fresas
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Card */}
            <div className="max-w-xl mx-auto">
                <div className="bg-slate-800 border border-slate-700 rounded-2xl shadow-xl overflow-hidden">

                    {/* Barcode Input */}
                    <div className="p-6 border-b border-slate-700 bg-slate-800/50">
                        <label className="block text-sm font-medium text-slate-400 mb-2">
                            Código de Barras
                        </label>
                        <input
                            ref={barcodeRef}
                            type="text"
                            value={barcode}
                            onChange={(e) => setBarcode(e.target.value.toUpperCase())}
                            onKeyDown={handleBarcodeKeyDown}
                            placeholder="Escanea o escribe el código..."
                            className="w-full px-4 py-4 rounded-xl border-2 border-slate-600 bg-slate-900 text-white text-xl font-mono placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none transition-colors"
                            autoComplete="off"
                        />
                        <button
                            onClick={() => lookupBarcode(barcode)}
                            disabled={!barcode.trim() || loading}
                            className="mt-3 w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 text-white rounded-xl font-medium flex items-center justify-center gap-2 transition-colors"
                        >
                            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Scan className="h-5 w-5" />}
                            Buscar
                        </button>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="p-4 bg-red-500/10 border-b border-red-500/20">
                            <div className="flex items-center gap-2 text-red-400">
                                <AlertCircle className="h-5 w-5" />
                                {error}
                            </div>
                        </div>
                    )}

                    {/* NEW FRESA FORM - when barcode not found */}
                    {isNewFresaMode && (
                        <div className="p-6 space-y-6">
                            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
                                <div className="flex items-center gap-2 text-amber-400 mb-2">
                                    <AlertCircle className="h-5 w-5" />
                                    <span className="font-medium">Código no encontrado</span>
                                </div>
                                <p className="text-slate-400 text-sm">
                                    Registra el consumo indicando la marca. Se marcará como NUEVA en el Excel.
                                </p>
                            </div>

                            {/* New Fresa Data Form */}
                            <div className="space-y-4">
                                <div className="bg-slate-900/50 p-4 rounded-xl">
                                    <div className="text-xs text-slate-500 uppercase mb-1">Código</div>
                                    <div className="text-lg font-mono text-emerald-400">{newFresaData.barcode}</div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">
                                        Marca <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={newFresaData.marca || ''}
                                        onChange={(e) => setNewFresaData(prev => ({ ...prev, marca: e.target.value }))}
                                        placeholder="Ej: MITSUBISHI, SUMITOMO..."
                                        className="w-full px-4 py-3 rounded-xl border border-slate-600 bg-slate-900 text-white focus:border-emerald-500 focus:outline-none"
                                        autoFocus
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">
                                        Tipo (opcional)
                                    </label>
                                    <input
                                        type="text"
                                        value={newFresaData.tipo || ''}
                                        onChange={(e) => setNewFresaData(prev => ({ ...prev, tipo: e.target.value }))}
                                        placeholder="Ej: PB0.5X4X4..."
                                        className="w-full px-4 py-3 rounded-xl border border-slate-600 bg-slate-900 text-white focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>
                            </div>

                            {/* Operario + Proyecto fields */}
                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">
                                        Operario
                                    </label>
                                    <input
                                        type="text"
                                        value={operario}
                                        onChange={(e) => setOperario(e.target.value)}
                                        placeholder="Tu nombre"
                                        className="w-full px-4 py-3 rounded-xl border border-slate-600 bg-slate-900 text-white focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">
                                        Nº Proyecto
                                    </label>
                                    <input
                                        type="text"
                                        value={proyecto}
                                        onChange={(e) => setProyecto(e.target.value)}
                                        placeholder="Ficha..."
                                        className="w-full px-4 py-3 rounded-xl border border-slate-600 bg-slate-900 text-white focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">
                                        Cantidad
                                    </label>
                                    <input
                                        type="number"
                                        min="1"
                                        value={cantidad}
                                        onChange={(e) => setCantidad(parseInt(e.target.value) || 1)}
                                        className="w-full px-4 py-3 rounded-xl border border-slate-600 bg-slate-900 text-white focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>
                            </div>

                            {/* Save Button */}
                            <button
                                onClick={saveNewFresa}
                                disabled={loading || !newFresaData.marca}
                                className="w-full py-4 bg-amber-600 hover:bg-amber-700 disabled:bg-slate-700 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-colors"
                            >
                                {loading ? (
                                    <Loader2 className="h-6 w-6 animate-spin" />
                                ) : (
                                    <>
                                        <Check className="h-6 w-6" />
                                        Registrar Consumo (NUEVA)
                                    </>
                                )}
                            </button>

                            {/* Cancel */}
                            <button
                                onClick={resetForm}
                                className="w-full py-2 text-slate-400 hover:text-white transition-colors flex items-center justify-center gap-2"
                            >
                                <RefreshCw className="h-4 w-4" />
                                Cancelar
                            </button>
                        </div>
                    )}

                    {/* Fresa Details (when found) */}
                    {fresa && (
                        <div className="p-6 space-y-6">
                            {/* Data Display */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-slate-900/50 p-4 rounded-xl">
                                    <div className="text-xs text-slate-500 uppercase">Código</div>
                                    <div className="text-lg font-mono text-emerald-400">{fresa.barcode}</div>
                                </div>
                                <div className="bg-slate-900/50 p-4 rounded-xl">
                                    <div className="text-xs text-slate-500 uppercase">Precio</div>
                                    <div className="text-lg font-semibold text-white flex items-center gap-1">
                                        <DollarSign className="h-4 w-4 text-emerald-400" />
                                        {formatCurrency(fresa.precio)}
                                    </div>
                                </div>
                                <div className="bg-slate-900/50 p-4 rounded-xl">
                                    <div className="text-xs text-slate-500 uppercase">Marca</div>
                                    <div className="text-lg text-white">{fresa.marca || '—'}</div>
                                </div>
                                <div className="bg-slate-900/50 p-4 rounded-xl">
                                    <div className="text-xs text-slate-500 uppercase">Tipo</div>
                                    <div className="text-lg text-white">{fresa.tipo || '—'}</div>
                                </div>
                                <div className="col-span-2 bg-slate-900/50 p-4 rounded-xl">
                                    <div className="text-xs text-slate-500 uppercase">Referencia</div>
                                    <div className="text-lg text-white">{fresa.referencia || '—'}</div>
                                </div>
                            </div>

                            {/* Operario, Proyecto & Cantidad */}
                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">
                                        Operario
                                    </label>
                                    <input
                                        type="text"
                                        value={operario}
                                        onChange={(e) => setOperario(e.target.value)}
                                        placeholder="Operario..."
                                        className="w-full px-4 py-3 rounded-xl border border-slate-600 bg-slate-900 text-white focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">
                                        Nº Proyecto
                                    </label>
                                    <input
                                        type="text"
                                        value={proyecto}
                                        onChange={(e) => setProyecto(e.target.value)}
                                        placeholder="Ficha..."
                                        className="w-full px-4 py-3 rounded-xl border border-slate-600 bg-slate-900 text-white focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-400 mb-2">
                                        Cantidad
                                    </label>
                                    <input
                                        type="number"
                                        value={cantidad}
                                        onChange={(e) => setCantidad(Math.max(1, parseInt(e.target.value) || 1))}
                                        min={1}
                                        className="w-full px-4 py-3 rounded-xl border border-slate-600 bg-slate-900 text-white text-center focus:border-emerald-500 focus:outline-none"
                                    />
                                </div>
                            </div>

                            {/* Register Button */}
                            <button
                                onClick={registerConsumo}
                                disabled={loading || !operario.trim()}
                                className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-colors"
                            >
                                {loading ? (
                                    <Loader2 className="h-6 w-6 animate-spin" />
                                ) : (
                                    <>
                                        <Package className="h-6 w-6" />
                                        Registrar Consumo
                                    </>
                                )}
                            </button>

                            {/* Reset */}
                            <button
                                onClick={resetForm}
                                className="w-full py-2 text-slate-400 hover:text-white transition-colors flex items-center justify-center gap-2"
                            >
                                <RefreshCw className="h-4 w-4" />
                                Nuevo escaneo
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Success Overlay */}
            {success && (
                <div className="fixed inset-0 bg-emerald-900/90 flex items-center justify-center z-50">
                    <div className="text-center">
                        <CheckCircle2 className="h-24 w-24 text-emerald-400 mx-auto mb-6" />
                        <h2 className="text-3xl font-bold text-white mb-2">
                            ¡Registrado!
                        </h2>
                        <p className="text-emerald-300 text-lg">
                            {success.pending ? 'Guardado en cola pendiente' : success.message}
                        </p>
                        {success.data && (
                            <p className="text-xl text-white mt-4">
                                {success.data.barcode} x{success.data.cantidad}
                            </p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
