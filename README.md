# Fresas Standalone

Control de fresas con escaneo de código de barras.  
Módulo independiente listo para desplegar en el servidor de la empresa.

---

## 📋 Requisitos

- Docker y Docker Compose
- El archivo Excel `Control FRESAS.xls` del taller

---

## 🚀 Despliegue Rápido

### 1. Copiar archivos

Copiar la carpeta `fresas-standalone/` al servidor.

### 2. Colocar Excel en /data

```bash
cp "/ruta/al/Control FRESAS.xls" fresas-standalone/data/
```

### 3. Configurar (opcional)

Copiar y editar `.env.example` → `.env`:

```bash
cp .env.example .env
nano .env
```

### 4. Levantar

```bash
cd fresas-standalone
docker compose up -d --build
```

### 5. Acceder

- **Web:** http://[IP-SERVIDOR]:3000
- **API Docs:** http://[IP-SERVIDOR]:8000/docs
- **Health:** http://[IP-SERVIDOR]:8000/api/health

---

## 📱 Uso en el Taller

### Flujo normal:

1. Abrir la web en tablet/PC del taller
2. Escanear código de barras (o escribirlo)
3. **Se autocompleta todo** (referencia, marca, tipo, precio)
4. Escribir nombre del operario
5. Click **Registrar Consumo**
6. ✅ Guardado

### Si Excel está bloqueado:

- El consumo se guarda en **cola pendiente**
- Aparece indicador "X pendientes"
- Click en el botón para **sincronizar** cuando Excel esté disponible

---

## 📁 Estructura de Datos

```
fresas-standalone/
├── data/
│   ├── Control FRESAS.xls      ← Excel del taller (fuente de verdad)
│   └── pending_consumos.csv    ← Cola de pendientes (fallback)
├── backend/                     ← API FastAPI
├── frontend/                    ← Web Next.js
└── docker-compose.yml
```

---

## 🔧 Endpoints API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/health` | Estado del sistema |
| GET | `/api/lookup?barcode=XXX` | Buscar fresa por código |
| POST | `/api/consumo` | Registrar consumo |
| GET | `/api/catalogo` | Listar fresas |
| POST | `/api/sync` | Sincronizar pendientes |
| GET | `/api/export/consumos` | Exportar CSV |

---

## ✅ Checklist de Verificación

- [ ] Excel accesible en `./data/`
- [ ] `docker compose up` sin errores
- [ ] Web carga en puerto 3000
- [ ] `/api/health` muestra `excel_ok: true`
- [ ] Scan de código conocido → datos se muestran
- [ ] Click Registrar → guardado confirmado
- [ ] Si Excel bloqueado → mensaje de pendiente

---

## 🔄 Compatibilidad con ERP

Los consumos se guardan con la misma estructura que el ERP:

```
fecha, barcode, referencia, marca, tipo, precio, cantidad, operario
```

Para importar al ERP después:

1. Ir a `/api/export/consumos`
2. Descargar CSV
3. Importar en el ERP principal

---

## 📞 Soporte

Si algo falla:

1. Ver logs: `docker compose logs -f`
2. Reiniciar: `docker compose restart`
3. Health check: `curl http://localhost:8000/api/health`
