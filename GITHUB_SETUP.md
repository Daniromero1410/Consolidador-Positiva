# Guía: Crear Repositorio en GitHub

Esta guía te ayudará a crear un repositorio en GitHub y subir el proyecto Consolidador T25.

## 📋 Requisitos Previos

- Cuenta de GitHub (crear en [github.com](https://github.com))
- Git instalado en tu computadora

### Verificar si Git está instalado:

```bash
git --version
```

Si no está instalado:
- **Windows:** Descarga desde [git-scm.com](https://git-scm.com/download/win)
- **Mac:** `brew install git` o descarga desde [git-scm.com](https://git-scm.com/download/mac)
- **Linux:** `sudo apt-get install git` (Ubuntu/Debian)

## 🚀 Paso 1: Crear Repositorio en GitHub

1. **Inicia sesión** en [github.com](https://github.com)

2. **Haz clic en el botón "+"** en la esquina superior derecha → **"New repository"**

3. **Completa el formulario:**
   - **Repository name:** `consolidador-t25-app`
   - **Description:** (Opcional) "Aplicación web para consolidación de tarifas T25 de contratos médicos"
   - **Visibility:**
     - ✅ **Private** (Recomendado para proyectos internos)
     - ⬜ **Public** (Si quieres que sea público)
   - ⬜ **NO marques** "Add a README file"
   - ⬜ **NO marques** "Add .gitignore"
   - ⬜ **NO marques** "Choose a license"

4. **Haz clic en "Create repository"**

GitHub te mostrará instrucciones. **NO las sigas aún**, usa las de abajo que están adaptadas a este proyecto.

## 💻 Paso 2: Configurar Git Local (Primera vez solamente)

Si es la primera vez que usas Git en esta computadora:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu.email@ejemplo.com"
```

**Usa el mismo email que tu cuenta de GitHub.**

## 📦 Paso 3: Preparar el Proyecto

Abre una terminal en la carpeta del proyecto:

```bash
cd "c:\Users\daniel.romero\OneDrive - GESTAR INNOVACION S.A.S\Documentos\CONSOLIDADOR POSITIVA\consolidador-t25-app"
```

**IMPORTANTE:** Antes de continuar, asegúrate de:

1. **Eliminar archivos temporales sensibles:**

```bash
# En Windows (PowerShell)
Remove-Item -Recurse -Force backend\outputs\* -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backend\uploads\* -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backend\temp\* -ErrorAction SilentlyContinue

# En Mac/Linux
rm -rf backend/outputs/*
rm -rf backend/uploads/*
rm -rf backend/temp/*
```

2. **Verificar que `.gitignore` existe:**

```bash
# Debería mostrar el contenido del archivo
cat .gitignore
```

Si no existe, ya fue creado en el paso anterior.

## 🔗 Paso 4: Conectar con GitHub

1. **Inicializa el repositorio Git:**

```bash
git init
```

2. **Agrega todos los archivos:**

```bash
git add .
```

3. **Crea el primer commit:**

```bash
git commit -m "Initial commit: Consolidador T25 v1.0"
```

4. **Conecta con GitHub:**

Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub:

```bash
git remote add origin https://github.com/TU_USUARIO/consolidador-t25-app.git
```

Ejemplo:
```bash
git remote add origin https://github.com/daniel-romero/consolidador-t25-app.git
```

5. **Crea la rama principal:**

```bash
git branch -M main
```

6. **Sube el código a GitHub:**

```bash
git push -u origin main
```

**Se te pedirá autenticación:**
- **Usuario:** Tu nombre de usuario de GitHub
- **Contraseña:** **NO uses tu contraseña de GitHub**, usa un **Personal Access Token**

### Crear un Personal Access Token:

1. Ve a GitHub → **Settings** (tu perfil) → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Clic en **"Generate new token"** → **"Generate new token (classic)"**
3. **Note:** "Token para Consolidador T25"
4. **Expiration:** 90 days (o el tiempo que prefieras)
5. **Selecciona scopes:**
   - ✅ **repo** (todos los sub-checkboxes)
6. Clic en **"Generate token"**
7. **COPIA EL TOKEN INMEDIATAMENTE** (no podrás verlo después)
8. Usa este token como contraseña cuando Git lo pida

## ✅ Paso 5: Verificar

1. **Ve a tu repositorio en GitHub:** `https://github.com/TU_USUARIO/consolidador-t25-app`

2. **Deberías ver todos los archivos del proyecto**

## 🔄 Comandos Git Útiles

### Cada vez que hagas cambios:

```bash
# Ver qué archivos cambiaron
git status

# Ver los cambios específicos
git diff

# Agregar cambios
git add .

# Crear commit
git commit -m "Descripción de los cambios"

# Subir a GitHub
git push
```

### Descargar cambios del repositorio:

```bash
git pull
```

### Ver historial de commits:

```bash
git log --oneline
```

### Crear una nueva rama:

```bash
git checkout -b nombre-rama
git push -u origin nombre-rama
```

## 🛡️ Seguridad: Archivos que NO deben subirse

El archivo `.gitignore` ya está configurado para ignorar:

- ❌ Archivos `.env` con credenciales
- ❌ Carpetas `venv/`, `node_modules/`
- ❌ Archivos de salida `.xlsx`, `.csv`
- ❌ Carpetas `outputs/`, `uploads/`, `temp/`

**NUNCA subas:**
- Contraseñas o tokens en el código
- Archivos de configuración con credenciales SFTP
- Bases de datos con información sensible
- Archivos Excel con datos reales de pacientes

## 📞 Solución de Problemas

### Error: "remote origin already exists"

```bash
git remote remove origin
git remote add origin https://github.com/TU_USUARIO/consolidador-t25-app.git
```

### Error: "rejected - non-fast-forward"

```bash
git pull --rebase origin main
git push
```

### Olvidé agregar un archivo al `.gitignore` y ya lo subí

```bash
# Eliminar del repositorio pero mantener local
git rm --cached archivo_sensible.env

# Agregar al .gitignore
echo "archivo_sensible.env" >> .gitignore

# Commit y push
git add .gitignore
git commit -m "Remove sensitive file"
git push
```

## 🎉 ¡Listo!

Tu proyecto ahora está en GitHub y puedes:
- ✅ Trabajar en equipo
- ✅ Tener respaldo en la nube
- ✅ Ver historial de cambios
- ✅ Desplegar en Railway y Vercel

**Siguiente paso:** Lee `RAILWAY_VERCEL_DEPLOY.md` para desplegar la aplicación.
