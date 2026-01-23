# Guía: Despliegue en Railway + Vercel

Esta guía te llevará paso a paso para desplegar el Consolidador T25 en la nube de forma **GRATUITA**.

- **Backend (API):** Railway (500 horas gratis al mes)
- **Frontend (Web):** Vercel (gratis ilimitado)

## 📋 Requisitos Previos

✅ Proyecto subido a GitHub (ver `GITHUB_SETUP.md`)
✅ Cuenta de GitHub
✅ Credenciales SFTP del servidor GoAnywhere

## 🚂 PARTE 1: Desplegar Backend en Railway

### Paso 1.1: Crear Cuenta en Railway

1. Ve a [railway.app](https://railway.app)
2. Haz clic en **"Login"** → **"Login with GitHub"**
3. Autoriza Railway para acceder a tu GitHub
4. Completa tu perfil si es necesario

### Paso 1.2: Crear Nuevo Proyecto

1. En el dashboard de Railway, haz clic en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. **Conecta tu repositorio:**
   - Si es tu primer proyecto, autoriza Railway a acceder a tus repositorios
   - Busca `consolidador-t25-app`
   - Haz clic en el repositorio

### Paso 1.3: Configurar el Servicio Backend

1. Railway detectará automáticamente que es un proyecto Python
2. Haz clic en el servicio creado (debería llamarse algo como `consolidador-t25-app`)
3. Ve a la pestaña **"Settings"**

**Configurar carpeta raíz:**
4. En **"Root Directory"**, escribe: `backend`
5. Haz clic en **"Deploy"** o espera a que se despliegue automáticamente

### Paso 1.4: Configurar Variables de Entorno

1. Ve a la pestaña **"Variables"**
2. Haz clic en **"+ New Variable"**
3. **Agrega las siguientes variables:**

```env
SFTP_HOST=tu-servidor-sftp.com
SFTP_PORT=22
SFTP_USERNAME=tu_usuario
SFTP_PASSWORD=tu_contraseña
SFTP_CARPETA_PRINCIPAL=/ruta/principal/en/sftp
CORS_ORIGINS=*
```

**IMPORTANTE:** Reemplaza los valores con tus credenciales reales.

**Opcional pero recomendado:**
```env
MAX_SEDES=50
TIMEOUT_EXTRACCION=60
```

4. Haz clic en **"Add"** para cada variable

### Paso 1.5: Obtener la URL del Backend

1. Ve a la pestaña **"Settings"**
2. En **"Domains"**, haz clic en **"Generate Domain"**
3. Railway generará una URL como: `https://tu-proyecto-production.up.railway.app`
4. **COPIA ESTA URL** - la necesitarás para el frontend

✅ **Tu backend ya está desplegado!**

Puedes probarlo visitando: `https://tu-proyecto-production.up.railway.app/docs`

---

## ▲ PARTE 2: Desplegar Frontend en Vercel

### Paso 2.1: Crear Cuenta en Vercel

1. Ve a [vercel.com](https://vercel.com)
2. Haz clic en **"Sign Up"** → **"Continue with GitHub"**
3. Autoriza Vercel para acceder a tu GitHub

### Paso 2.2: Importar Proyecto

1. En el dashboard de Vercel, haz clic en **"Add New..."** → **"Project"**
2. Busca tu repositorio `consolidador-t25-app`
3. Haz clic en **"Import"**

### Paso 2.3: Configurar el Proyecto

En la pantalla de configuración:

1. **Framework Preset:** Next.js (debería detectarlo automáticamente)

2. **Root Directory:**
   - Haz clic en **"Edit"**
   - Selecciona `frontend`
   - Haz clic en **"Continue"**

3. **Build Settings:**
   - **Build Command:** `npm run build` (ya viene por defecto)
   - **Output Directory:** `.next` (ya viene por defecto)
   - **Install Command:** `npm install` (ya viene por defecto)

4. **Environment Variables:**
   - Haz clic en **"Environment Variables"**
   - Agrega la siguiente variable:

```env
NEXT_PUBLIC_API_URL=https://tu-proyecto-production.up.railway.app/api
```

**IMPORTANTE:** Reemplaza con la URL que copiaste de Railway (paso 1.5), agregando `/api` al final.

5. Haz clic en **"Deploy"**

### Paso 2.4: Esperar el Despliegue

Vercel mostrará el progreso del despliegue en tiempo real:
- ⏳ Building...
- ⏳ Deploying...
- ✅ Ready!

Esto puede tomar 2-5 minutos.

### Paso 2.5: Obtener la URL del Frontend

Una vez completado:

1. Vercel mostrará un mensaje de éxito con confeti 🎉
2. Tu aplicación estará disponible en: `https://tu-proyecto.vercel.app`
3. Haz clic en **"Visit"** para abrir la aplicación

✅ **Tu aplicación completa ya está desplegada!**

---

## 🎨 PARTE 3: Configuración de Dominio Personalizado (Opcional)

### Opción A: Dominio en Vercel (Frontend)

1. Ve a tu proyecto en Vercel → **"Settings"** → **"Domains"**
2. Agrega tu dominio: `consolidador.tuempresa.com`
3. Sigue las instrucciones para configurar DNS

### Opción B: Dominio en Railway (Backend)

1. Ve a tu servicio en Railway → **"Settings"** → **"Domains"**
2. Haz clic en **"Custom Domain"**
3. Agrega: `api.consolidador.tuempresa.com`
4. Configura el DNS según las instrucciones

**Después de configurar dominio personalizado:**

Actualiza la variable de entorno en Vercel:
```env
NEXT_PUBLIC_API_URL=https://api.consolidador.tuempresa.com/api
```

---

## 🔄 PARTE 4: Actualizar la Aplicación

Cada vez que hagas cambios y los subas a GitHub, la aplicación se actualizará automáticamente:

```bash
# Hacer cambios en el código
git add .
git commit -m "Descripción de cambios"
git push
```

**Railway y Vercel detectarán los cambios y redesplegarán automáticamente.**

Puedes ver el progreso:
- **Railway:** Dashboard → tu proyecto → "Deployments"
- **Vercel:** Dashboard → tu proyecto → "Deployments"

---

## 📊 Monitoreo y Logs

### Ver Logs del Backend (Railway)

1. Ve a tu proyecto en Railway
2. Haz clic en tu servicio
3. Pestaña **"Deployments"** → selecciona el deployment actual
4. Pestaña **"Logs"** → verás los logs en tiempo real

### Ver Logs del Frontend (Vercel)

1. Ve a tu proyecto en Vercel
2. Pestaña **"Deployments"** → selecciona el deployment
3. Haz clic en **"View Function Logs"**

---

## 💾 PARTE 5: Configurar Almacenamiento Persistente (Railway)

**IMPORTANTE:** Por defecto, Railway no guarda archivos entre despliegues.

Para guardar archivos de salida:

### Opción 1: Usar Railway Volumes (Recomendado)

1. En Railway, ve a tu servicio → **"Settings"**
2. En **"Volumes"**, haz clic en **"+ New Volume"**
3. **Mount Path:** `/app/outputs`
4. **Size:** 1 GB (o lo que necesites)
5. Haz clic en **"Add"**

### Opción 2: Usar S3 o Google Cloud Storage

Modifica el código para subir archivos a un bucket de almacenamiento en la nube.

---

## 💰 Costos y Límites

### Railway (Plan Gratuito)
- ✅ **500 horas/mes** de ejecución GRATIS
- ✅ **1 GB RAM** por servicio
- ✅ **100 GB transferencia** de datos
- ⚠️ **$5/mes** después de exceder límites (opcional)

**Cómo ahorrar horas:**
- El servicio se duerme después de inactividad
- Solo se cuenta cuando está activo procesando

### Vercel (Plan Gratuito)
- ✅ **Ancho de banda ilimitado**
- ✅ **Despliegues ilimitados**
- ✅ **100 GB de transferencia/mes**
- ✅ **Gratis para siempre**

---

## 🛠️ Solución de Problemas

### Error: "Build failed" en Railway

**Causa común:** Falta `requirements.txt` o error en dependencias

**Solución:**
1. Verifica que `backend/requirements.txt` existe
2. Verifica que todas las librerías sean compatibles
3. Revisa los logs de error en Railway

### Error: "Build failed" en Vercel

**Causa común:** Variable de entorno faltante

**Solución:**
1. Ve a Vercel → Settings → Environment Variables
2. Verifica que `NEXT_PUBLIC_API_URL` esté configurada
3. Haz clic en **"Redeploy"**

### Error: "Cannot connect to API" en el frontend

**Solución:**
1. Verifica que la URL en `NEXT_PUBLIC_API_URL` sea correcta
2. Debe incluir `/api` al final
3. Debe ser HTTPS (no HTTP)
4. Prueba abrir la URL directamente: `https://tu-backend.railway.app/docs`

### Error: "CORS" o "Access-Control-Allow-Origin"

**Solución:**
1. Agrega variable de entorno en Railway:
```env
CORS_ORIGINS=https://tu-proyecto.vercel.app
```
2. O usa `*` para permitir todos los orígenes (solo en desarrollo):
```env
CORS_ORIGINS=*
```

### La aplicación se "duerme" (Railway)

**Esto es normal en el plan gratuito.**

**Solución temporal:**
- El primer request puede tardar 30-60 segundos
- Después funciona normalmente

**Solución permanente:**
- Upgrade al plan de pago ($5/mes) para "keep alive"

---

## 📞 Soporte

- **Railway:** [docs.railway.app](https://docs.railway.app)
- **Vercel:** [vercel.com/docs](https://vercel.com/docs)
- **GitHub Issues:** Crea un issue en tu repositorio

---

## ✅ Checklist Final

Antes de dar por terminado el despliegue:

- [ ] Backend desplegado en Railway y funcionando
- [ ] URL del backend obtenida
- [ ] Frontend desplegado en Vercel
- [ ] Variable `NEXT_PUBLIC_API_URL` configurada
- [ ] Aplicación accesible desde el navegador
- [ ] Puedes subir maestra
- [ ] Puedes conectar al SFTP
- [ ] Puedes procesar contratos
- [ ] Puedes descargar archivos generados

## 🎉 ¡Felicitaciones!

Tu aplicación Consolidador T25 ahora está:
- ✅ Desplegada en la nube
- ✅ Accesible desde cualquier dispositivo
- ✅ Con despliegue automático
- ✅ Completamente operativa

**URL de tu aplicación:** `https://tu-proyecto.vercel.app`

¡Comparte esta URL con tu equipo!
