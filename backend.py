import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
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
            raise last_error
        return wrapper
    return decorator

# --- HELPER: LIMPIEZA DE CLAVE PRIVADA ---
def clean_private_key(pk):
    """Limpia y corrige formato de clave privada (nativa, env var o base64)."""
    if not pk: return ""
    pk = pk.strip().strip('"').strip("'")
    import base64
    try:
        if "-----BEGIN PRIVATE KEY-----" not in pk:
            missing_padding = len(pk) % 4
            if missing_padding:
                pk += '=' * (4 - missing_padding)
            decoded_bytes = base64.b64decode(pk)
            decoded_str = decoded_bytes.decode('utf-8')
            if "-----BEGIN PRIVATE KEY-----" in decoded_str:
                return decoded_str
    except Exception:
        pass
    return pk.replace('\\n', '\n').replace('\\\\n', '\n')

class PadelDB:
    def __init__(self):
        scopes = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
        creds = None
        creds_dict = None
        errors = []
        
        # 1. Archivo local
        if os.path.exists('credentials.json'):
            try:
                creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
            except Exception as e:
                errors.append(f"Local: {e}")
        
        # 2. Secrets
        if creds is None:
            try:
                if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    if "private_key" in creds_dict:
                        creds_dict["private_key"] = clean_private_key(creds_dict["private_key"])
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            except Exception as e:
                errors.append(f"Secrets: {e}")

        # 3. Env Vars
        if creds is None:
            try:
                if os.environ.get('GCP_PRIVATE_KEY'):
                    pk = os.environ.get('GCP_PRIVATE_KEY', '')
                    creds_dict = {
                        "type": os.environ.get('GCP_TYPE', 'service_account'),
                        "project_id": os.environ.get('GCP_PROJECT_ID', ''),
                        "private_key_id": os.environ.get('GCP_PRIVATE_KEY_ID', ''),
                        "private_key": clean_private_key(pk),
                        "client_email": os.environ.get('GCP_CLIENT_EMAIL', ''),
                        "client_id": os.environ.get('GCP_CLIENT_ID', ''),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            except Exception as e:
                errors.append(f"EnvVars: {e}")

        if creds is None:
            st.error(f"❌ No se encuentran credenciales. Detalle errores: {'; '.join(errors)}")
            st.stop()
            
        try:
            client = gspread.authorize(creds)
            self.spreadsheet_id = '15MAbaPH1gqrCIcUtj6JgdSJXiYMdOBNIxaOqtAHsOB0'
            self.sheet = client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            st.error(f"❌ Error conectando con Google Sheets: {e}")
            st.stop()
        
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 300 

    def _get_cached(self, key, fetch_func, force_refresh=False):
        now = time.time()
        if not force_refresh and key in self._cache:
            if now - self._cache_time.get(key, 0) < self._cache_ttl:
                return self._cache[key]
        data = fetch_func()
        self._cache[key] = data
        self._cache_time[key] = now
        return data

    @retry_on_error()
    def get_info_usuario(self, usuario):
        try:
            ws = self.sheet.worksheet("USUARIOS")
            cell = ws.find(str(usuario))
            # Column 2 assumed Name, using cell.row, col 4 for Level?
            # Improvised read:
            row_vals = ws.row_values(cell.row)
            # row_vals is 0-indexed list. Assuming order: ID, PASS, NAME, LEVEL
            # ID=0, PASS=1, NAME=2, LEVEL=3 (Adjust based on likely structure)
            # If finding by ID (col 1), row_vals[2] is Name.
            
            # Safer: Read as DF
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            row = df[df['ID_USUARIO'].astype(str) == str(usuario)]
            if not row.empty:
                return row.iloc[0]['NOMBRE'], row.iloc[0]['NIVEL']
            return None, None
        except:
            return None, None

    @retry_on_error()
    def validar_login(self, usuario, password):
        try:
            def fetch_users():
                ws = self.sheet.worksheet("USUARIOS")
                return pd.DataFrame(ws.get_all_records())
            
            df = self._get_cached("usuarios_df", fetch_users)
            # Clean types
            df['ID_USUARIO'] = df['ID_USUARIO'].astype(str)
            df['PASSWORD'] = df['PASSWORD'].astype(str)
            
            user_row = df[(df['ID_USUARIO'] == str(usuario)) & (df['PASSWORD'] == str(password))]
            
            if not user_row.empty:
                return user_row.iloc[0]['NOMBRE'], user_row.iloc[0]['NIVEL']
            return None, None
        except Exception as e:
            print(f"Login error: {e}")
            return None, None

    @retry_on_error()
    def get_mis_horas(self, id_usuario):
        try:
            def fetch():
                ws = self.sheet.worksheet("DISPONIBILIDAD")
                data = ws.get_all_records()
                # Filter locally
                return [d for d in data if str(d['ID_USUARIO']) == str(id_usuario)]
            
            data = self._get_cached(f"mis_horas_{id_usuario}", fetch, force_refresh=True)
            # Standardize keys
            clean_data = []
            for d in data:
                clean_data.append({
                    'fecha': d['FECHA'],
                    'hora_inicio': d['HORA_INICIO'],
                    'hora_fin': d['HORA_FIN']
                })
            return clean_data
        except:
            return []

    @retry_on_error()
    def guardar_disponibilidad(self, id_usuario, nivel, nuevos_slots):
        # 1. Borrar disponibilidad futura de este usuario
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        # Esto es ineficiente con delete_rows en bucle, pero seguro para MVP
        # Mejor: leer todo, filtrar en memoria lo que NO es de este user o es pasado, añadir lo nuevo, y reescribir hoja.
        # PERO reescribir hoja es peligroso si hay concurrencia.
        # Opción Append simple: Solo añadir. (Duplicados se gestionan en lectura tomando el último?) No.
        
        # Estrategia segura: Leer todo -> Filtrar -> Sobreescribir todo (Warning: Race conditions, but OK for low traffic)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        
        # Mantener otros usuarios
        if not df.empty:
            df = df[df['ID_USUARIO'].astype(str) != str(id_usuario)]
        
        # Crear DF de nuevos
        new_rows = []
        for slot in nuevos_slots:
            new_rows.append({
                'ID_USUARIO': id_usuario,
                'FECHA': slot['fecha'],
                'HORA_INICIO': slot['hora_inicio'],
                'HORA_FIN': slot['hora_fin'],
                'NIVEL': nivel
            })
        
        # Combinar
        if new_rows:
            df_new = pd.DataFrame(new_rows)
            df_final = pd.concat([df, df_new], ignore_index=True)
        else:
            df_final = df
            
        # Ordenar por fecha
        if not df_final.empty:
             df_final = df_final.sort_values('FECHA')
             
        # Update worksheet
        ws.clear()
        ws.update([df_final.columns.values.tolist()] + df_final.values.tolist())
        return True

    @retry_on_error()
    def get_partidos_posibles(self, nivel):
        # Lógica básica de coincidencia
        try:
            ws = self.sheet.worksheet("DISPONIBILIDAD")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            
            if df.empty: return []
            
            # Filtrar por nivel y fechas futuras
            hoy = datetime.now().strftime("%Y-%m-%d")
            df = df[df['FECHA'] >= hoy]
            if 'NIVEL' in df.columns:
                df = df[df['NIVEL'].astype(str) == str(nivel)]
                
            # Agrupar por FECHA, HORA_INICIO, HORA_FIN
            # Esto asume slots idénticos. Si los usuarios ponen horas dispares, no matcheará.
            # Para MVP asumimos slots estandarizados por la UI.
            matches = []
            grouped = df.groupby(['FECHA', 'HORA_INICIO', 'HORA_FIN'])
            
            count = 0
            for (fecha, ini, fin), group in grouped:
                users = group['ID_USUARIO'].unique()
                if len(users) >= 4:
                    # Crear partido posible
                    jugadores_names = " vs ".join([str(u) for u in users[:4]]) # Placeholder names
                    # Ideally join names from USERS logic, but ID is okay for now or fetch names
                    
                    matches.append({
                        'id_partido': f"MATCH_{fecha}_{ini}_{count}",
                        'fecha': fecha,
                        'fecha_fmt': fecha, # Format if needed
                        'hora_inicio': ini,
                        'hora_fin': fin,
                        'titulo': f"Partido {nivel}",
                        'jugadores_names': f"{len(users)} Jugadores Disponibles"
                    })
                    count += 1
            return matches
        except Exception as e:
            print(f"Error matching: {e}")
            return []

    @retry_on_error()
    def get_mis_partidos(self, nivel):
        # Retorna lista vacía o fake para que no pete la UI si faltan datos
        try:
            ws = self.sheet.worksheet("PARTIDOS") # Asumiendo hoja
            data = ws.get_all_records()
            return data # Asume estructura correcta
        except:
            return []

    @retry_on_error()
    def programar_partido(self, id_partido, fecha, hora_txt):
        # Lógica dummy de guardado
        pass