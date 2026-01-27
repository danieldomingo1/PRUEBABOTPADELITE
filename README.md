# 🎾 Disponibilidad Bulip

Aplicación web para gestionar la disponibilidad de jugadores de pádel y organizar partidos.

## 🚀 Despliegue en Streamlit Cloud

### Paso 1: Subir a GitHub

```bash
git init
git add .
git commit -m "Initial commit - Disponibilidad Bulip"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/disponibilidad-bulip.git
git push -u origin main
```

### Paso 2: Configurar en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de GitHub
3. Haz clic en **"New app"**
4. Selecciona:
   - Repositorio: `TU_USUARIO/disponibilidad-bulip`
   - Rama: `main`
   - Archivo principal: `app.py`

### Paso 3: Configurar Secrets

1. En la página de tu app, haz clic en **"Advanced settings"**
2. Ve a la sección **"Secrets"**
3. Copia el contenido del archivo `secrets_template.toml` (sin subir a GitHub)
4. Pégalo en el cuadro de texto de Secrets
5. Haz clic en **"Save"**

### Paso 4: Desplegar

Haz clic en **"Deploy"** y espera a que la aplicación se construya.

## 📁 Archivos importantes

- `app.py` - Aplicación principal
- `backend.py` - Conexión con Google Sheets
- `requirements.txt` - Dependencias
- `.streamlit/config.toml` - Configuración visual

## 🔒 Seguridad

**NUNCA subas estos archivos a GitHub:**
- `credentials.json`
- `secrets_template.toml`
- `.streamlit/secrets.toml`

## Hecho por Daniel Domingo
