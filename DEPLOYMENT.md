# Guía de Despliegue - Consolidador T25

Esta guía explica cómo configurar y desplegar la aplicación Consolidador T25 para que funcione desde cualquier dispositivo en la red local o en producción.

## 📋 Requisitos Previos

- Python 3.8 o superior
- Node.js 18 o superior
- Acceso a red local (para despliegue en LAN)

## 🚀 Configuración Rápida

### 1. Backend (API)

El backend usa FastAPI y se ejecuta en el puerto 8000 por defecto.

**Opción A: Desarrollo Local**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Opción B: Producción**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Frontend (Next.js)

**Configurar la URL de la API:**

1. Copia el archivo de ejemplo:
```bash
cd frontend
cp .env.example .env.local
```

2. Edita `.env.local` según tu entorno:

**Para desarrollo local:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

**Para red local (reemplaza con la IP del servidor backend):**
```env
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000/api
```

**Para producción:**
```env
NEXT_PUBLIC_API_URL=https://tu-dominio.com/api
```

3. Instala dependencias y ejecuta:
```bash
npm install
npm run dev  # Desarrollo
# O
npm run build && npm start  # Producción
```

## 🌐 Configuración para Red Local

### Paso 1: Obtener la IP del Servidor

**Windows:**
```cmd
ipconfig
```
Busca "Dirección IPv4" (ej: 192.168.1.100)

**Linux/Mac:**
```bash
ip addr show  # o ifconfig
```

### Paso 2: Configurar Backend

Ejecuta el backend con `--host 0.0.0.0` para aceptar conexiones externas:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Paso 3: Configurar Frontend

En `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000/api
```

### Paso 4: Acceder desde Otros Dispositivos

- **Frontend:** `http://192.168.1.100:3000`
- **Backend API:** `http://192.168.1.100:8000`

## 🔒 Firewall

Asegúrate de permitir conexiones en los puertos:
- **8000** (Backend API)
- **3000** (Frontend Next.js)

**Windows:**
```cmd
netsh advfirewall firewall add rule name="Consolidador Backend" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="Consolidador Frontend" dir=in action=allow protocol=TCP localport=3000
```

**Linux (UFW):**
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
```

## 📦 Estructura de Archivos Generados

La aplicación genera los siguientes archivos con nombres legibles:

- **Consolidado_Crudo_YYYY-MM-DD_HH-MM.xlsx** - Datos consolidados sin procesar
- **Consolidado_Limpio_YYYY-MM-DD_HH-MM.xlsx** - Datos procesados con ML
- **Alertas_YYYY-MM-DD_HH-MM.xlsx** - Alertas del procesamiento
- **Resumen_YYYY-MM-DD_HH-MM.xlsx** - Resumen de contratos
- **Archivos_No_Positiva_YYYY-MM-DD_HH-MM.xlsx** - Archivos sin formato POSITIVA

## ⚙️ Características Implementadas

✅ **Contador de servicios** - Muestra servicios reales extraídos del SFTP
✅ **Formato de fechas** - Fechas legibles (DD/MM/YYYY HH:MM)
✅ **Límite de 500,000 servicios por hoja** - División automática en múltiples hojas
✅ **Nombres legibles** - Archivos con nombres descriptivos
✅ **Configuración multiplataforma** - Funciona desde cualquier dispositivo

## 🛠️ Solución de Problemas

### Error de conexión CORS

Si ves errores de CORS, asegúrate de que el backend esté configurado correctamente en `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend no se conecta al backend

1. Verifica que `.env.local` tenga la URL correcta
2. Reinicia el servidor de desarrollo: `npm run dev`
3. Verifica que el backend esté escuchando en `0.0.0.0`

### No se pueden descargar archivos

Asegúrate de que la carpeta `backend/outputs` exista y tenga permisos de escritura.

## 📞 Soporte

Para más información o problemas, contacta al equipo de desarrollo.
