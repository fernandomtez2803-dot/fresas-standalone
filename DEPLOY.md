# 🍓 Control de Fresas - Guía de Despliegue

## Requisitos del Servidor

- **Docker** y **Docker Compose** instalados
- Acceso a la red donde está el archivo Excel compartido
- Puerto 3000 (frontend) y 8002 (backend) disponibles

---

## Opción 1: Despliegue con Docker (Recomendado)

### Paso 1: Copiar archivos al servidor

Copia toda la carpeta `fresas-standalone` al servidor:

```bash
# Desde tu portátil, usar SCP o copiar manualmente
scp -r fresas-standalone usuario@servidor:/ruta/destino/
```

### Paso 2: Configurar la ruta del Excel

Edita el archivo `docker-compose.yml` y cambia la ruta del volumen:

```yaml
volumes:
  # Cambia esta ruta a donde esté el Excel en el servidor
  - /ruta/al/excel/compartido:/data
```

### Paso 3: Copiar el Excel al servidor

Asegúrate de que `Control FRESAS.xls` esté en la carpeta de datos:

```bash
cp "Control FRESAS.xls" /ruta/al/excel/compartido/
```

### Paso 4: Construir e iniciar

```bash
cd fresas-standalone
docker-compose up -d --build
```

### Paso 5: Verificar que funciona

- Frontend: `http://IP-SERVIDOR:3000`
- Backend API: `http://IP-SERVIDOR:8002/api/health`

---

## Opción 2: Despliegue sin Docker (Windows Server)

### Paso 1: Instalar Python 3.11+

Descarga e instala Python desde https://python.org

### Paso 2: Instalar Node.js 18+

Descarga e instala Node.js desde https://nodejs.org

### Paso 3: Copiar archivos

Copia la carpeta `fresas-standalone` al servidor.

### Paso 4: Configurar el backend

```cmd
cd fresas-standalone\backend

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 5: Editar .env

Edita `backend\.env` con las rutas correctas:

```
EXCEL_PATH=C:\ruta\al\Control FRESAS.xls
PENDING_LOG_PATH=C:\ruta\al\pending_consumos.csv
```

### Paso 6: Configurar el frontend

```cmd
cd fresas-standalone\frontend
npm install
npm run build
```

### Paso 7: Iniciar servicios

Usa el script `start.bat` o crea un servicio de Windows.

---

## Acceso desde otros equipos

Una vez desplegado, los usuarios pueden acceder desde cualquier navegador:

```
http://IP-DEL-SERVIDOR:3000
```

Por ejemplo: `http://192.168.1.100:3000`

---

## Comandos útiles de Docker

```bash
# Ver estado de los contenedores
docker-compose ps

# Ver logs
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Parar servicios
docker-compose down

# Actualizar después de cambios
docker-compose up -d --build
```

---

## Solución de problemas

### El Excel no se puede escribir
- Asegúrate de que el archivo NO esté abierto en otro equipo
- Verifica los permisos de escritura en la carpeta

### No encuentra las fresas
- Verifica que la ruta del Excel en `.env` o `docker-compose.yml` sea correcta
- Reinicia el backend para recargar el catálogo

### Error de conexión
- Verifica que los puertos 3000 y 8002 estén abiertos en el firewall
- Comprueba que los contenedores estén corriendo: `docker-compose ps`
