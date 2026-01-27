import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st
import time
import os
from functools import wraps

# --- DECORADOR DE REINTENTOS ---
def retry_on_error(max_retries=3, delay=1):
    """Reintenta una función si falla, con backoff exponencial."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Backoff exponencial
            # Si llegamos aquí, todos los intentos fallaron
            raise last_error
        return wrapper
    return decorator

# --- HELPER: LIMPIEZA DE CLAVE PRIVADA ---
def clean_private_key(pk):
    """Limpia y corrige formato de clave privada (nativa, env var o base64)."""
    if not pk: return ""
    
    # 1. Limpieza inicial
    pk = pk.strip().strip('"').strip("'")
    
    # 2. Intento Base64
    import base64
    try:
        # Si NO tiene los headers estándar, sospechamos de Base64 o formato RAW sucio
        if "-----BEGIN PRIVATE KEY-----" not in pk:
            # Intentamos decodificar como si fuera Base64 puro
            missing_padding = len(pk) % 4
            if missing_padding:
                pk += '=' * (4 - missing_padding)
            decoded_bytes = base64.b64decode(pk)
            decoded_str = decoded_bytes.decode('utf-8')
            if "-----BEGIN PRIVATE KEY-----" in decoded_str:
                return decoded_str
    except Exception:
        pass

    # 3. Limpieza de saltos de línea (si no era base64 o si era texto plano con escapes)
    # Reemplazamos \n literal por salto de línea real
    return pk.replace('\\n', '\n').replace('\\\\n', '\n')

class PadelDB:
    def __init__(self):
        # Scopes modernos para google-auth
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = None
        creds_dict = None
        
        # ----------------------------------------------------
        # ESTRATEGIA DE CARGA DE CREDENCIALES
        # ----------------------------------------------------
        
        # 1. Archivo local (Desarrollo)
        if os.path.exists('credentials.json'):
            try:
                creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
            except Exception:
                pass
        
        # 2. Streamlit Cloud Secrets (Producción 1)
        if creds is None:
            try:
                if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
                    # Copiamos para no modificar el objeto original de secrets
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    
                    if "private_key" in creds_dict:
                        creds_dict["private_key"] = clean_private_key(creds_dict["private_key"])
                    
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            except Exception as e:
                print(f"⚠️ Error secrets: {e}")

        # 3. Variables de Entorno (Render/Railway - Producción 2)
        if creds is None:
            try:
                if os.environ.get('GCP_PRIVATE_KEY'):
                    pk = os.environ.get('GCP_PRIVATE_KEY', '')
                    cleaned_key = clean_private_key(pk)
                    
                    creds_dict = {
                        "type": os.environ.get('GCP_TYPE', 'service_account'),
                        "project_id": os.environ.get('GCP_PROJECT_ID', ''),
                        "private_key_id": os.environ.get('GCP_PRIVATE_KEY_ID', ''),
                        "private_key": cleaned_key,
                        "client_email": os.environ.get('GCP_CLIENT_EMAIL', ''),
                        "client_id": os.environ.get('GCP_CLIENT_ID', ''),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            except Exception as e:
                print(f"⚠️ Error env vars: {e}")

        # ----------------------------------------------------
        # VALIDACIÓN Y CONEXIÓN
        # ----------------------------------------------------
        
        if creds is None:
            st.error("❌ No se encuentran credenciales (credentials.json, Secrets o Env Vars).")
            st.stop()
            
        try:
            # gspread moderno acepta el objeto Credentials de google-auth directamente
            client = gspread.authorize(creds)
            self.spreadsheet_id = '15MAbaPH1gqrCIcUtj6JgdSJXiYMdOBNIxaOqtAHsOB0'
            self.sheet = client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            # DEBUGGING VISUAL PARA EL USUARIO
            import traceback
            st.error(f"❌ Error conectando con Google Sheets: {e}")
            
            with st.expander("🕵️ Ver detalles técnicos (Debug)", expanded=True):
                st.code(traceback.format_exc())
                st.write("--- INFO DE DEBUG ---")
                
                # Intentar mostrar info de la clave usada
                pk_used = "Desconocida"
                if creds_dict and "private_key" in creds_dict:
                    pk_used = creds_dict["private_key"]
                
                if isinstance(pk_used, str) and len(pk_used) > 20:
                    st.write(f"Longitud clave: {len(pk_used)}")
                    st.write(f"Inicio: '{pk_used[:15]}'")
                    st.write(f"Fin: '{pk_used[-15:]}'")
                    st.write(f"¿Contiene \\n real?: {'\n' in pk_used}")
                    st.write(f"¿Header correcto?: {'-----BEGIN PRIVATE KEY-----' in pk_used}")
                else:
                    st.write("No se pudo inspeccionar la clave privada.")
            
            st.stop()
        
        # Cache interno para reducir llamadas
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 300  # 5 minutos

    def _get_cached(self, key, fetch_func, force_refresh=False):
        """Sistema de caché interno con TTL."""
        now = time.time()
        if not force_refresh and key in self._cache:
            if now - self._cache_time.get(key, 0) < self._cache_ttl:
                return self._cache[key]
        
        # Fetch fresh data
        data = fetch_func()
        self._cache[key] = data
        self._cache_time[key] = now
        return data

    @retry_on_error()
    def obtener_disponibilidad(self, force=False):
        """Obtiene datos de la hoja 'Disponibilidad'."""
        try:
            def fetch():
                try:
                    worksheet = self.sheet.worksheet('Disponibilidad')
                    data = worksheet.get_all_records()
                    if not data:
                        # Si está vacía o solo headers, retornamos DF vacío con columnas esperadas
                        return pd.DataFrame(columns=['Pista', 'Hora', 'Estado', 'Fecha'])
                    return pd.DataFrame(data)
                except gspread.WorksheetNotFound:
                    # Crear hoja si no existe (fallback)
                    self.sheet.add_worksheet(title="Disponibilidad", rows="100", cols="20")
                    return pd.DataFrame(columns=['Pista', 'Hora', 'Estado', 'Fecha'])
            
            df = self._get_cached('disponibilidad', fetch, force_refresh=force)
            return df
        except Exception as e:
            st.error(f"Error leyendo Disponibilidad: {e}")
            return pd.DataFrame()

    @retry_on_error()
    def guardar_reserva(self, reserva_data):
        """Guarda nueva reserva en la hoja 'Reservas'."""
        try:
            try:
                worksheet = self.sheet.worksheet('Reservas')
            except gspread.WorksheetNotFound:
                worksheet = self.sheet.add_worksheet(title="Reservas", rows="100", cols="20")
                # Añadir headers si es nueva
                worksheet.append_row(['Fecha_Reserva', 'Usuario', 'Pista', 'Hora', 'Estado'])
            
            # Añadir timestamp
            reserva_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Orden de columnas esperado
            row = [
                reserva_data.get('Timestamp', ''),
                reserva_data.get('Usuario', ''),
                reserva_data.get('Pista', ''),
                reserva_data.get('Hora', ''),
                reserva_data.get('Estado', 'Pendiente')
            ]
            worksheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"Error guardando reserva: {e}")
            return False

    @retry_on_error()
    def obtener_reservas_usuario(self, usuario):
        """Obtiene reservas filtradas por usuario."""
        try:
            def fetch():
                try:
                    worksheet = self.sheet.worksheet('Reservas')
                    data = worksheet.get_all_records()
                    return pd.DataFrame(data)
                except gspread.WorksheetNotFound:
                    return pd.DataFrame()

            df = self._get_cached('reservas', fetch, force_refresh=True)
            if df.empty:
                return df
                
            # Filtrar por usuario (case insensitive simple)
            mask = df['Usuario'].astype(str).str.lower() == str(usuario).lower()
            return df[mask]
        except Exception as e:
            st.error(f"Error obteniendo reservas: {e}")
            return pd.DataFrame()

    @retry_on_error()
    def actualizar_disponibilidad(self, pista, hora, fecha, nuevo_estado):
        """Actualiza el estado de una pista en una hora concreta."""
        try:
            worksheet = self.sheet.worksheet('Disponibilidad')
            
            # Buscar la celda exacta (esto es ineficiente pero seguro para empezar)
            # En producción idealmente usaríamos identificadores únicos o batch update
            cell = worksheet.find(pista) # Busca la pista primero
            # Esta lógica es compleja porque depende de cómo esté estructurada la hoja "Disponibilidad"
            # Asumiendo estructura tabular plana
            
            records = worksheet.get_all_records()
            df = pd.DataFrame(records)
            
            # Encontrar índice de fila (localmente)
            mask = (df['Pista'] == pista) & (df['Hora'] == hora) & (df['Fecha'] == fecha)
            if not mask.any():
                # Si no existe, se crea nueva fila
                worksheet.append_row([pista, hora, nuevo_estado, fecha])
            else:
                # Si existe, actualizamos. Gspread usa 1-based index y tiene headers (+2)
                row_idx = df.index[mask][0] + 2 
                col_idx = df.columns.get_loc('Estado') + 1
                worksheet.update_cell(row_idx, col_idx, nuevo_estado)
                
            # Invalidar caché
            if 'disponibilidad' in self._cache:
                del self._cache['disponibilidad']
            return True
        except Exception as e:
            st.error(f"Error actualizando disponibilidad: {e}")
            return False