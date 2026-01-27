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
                        time.sleep(delay * (2 ** attempt))
            raise last_error
        return wrapper
    return decorator

# --- HELPER: LIMPIEZA DE CLAVE PRIVADA ---
def clean_private_key(pk):
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

    def _get_users_map(self):
        """Devuelve un diccionario {ID_USUARIO: NOMBRE}."""
        def fetch():
            try:
                ws = self.sheet.worksheet("USUARIOS")
                data = ws.get_all_records()
                return {str(r['ID_USUARIO']): r['NOMBRE'] for r in data}
            except:
                return {}
        return self._get_cached("users_map", fetch)

    @retry_on_error()
    def get_info_usuario(self, usuario):
        try:
            ws = self.sheet.worksheet("USUARIOS")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            # Asegurar tipos string para comparación
            df['ID_USUARIO'] = df['ID_USUARIO'].astype(str)
            row = df[df['ID_USUARIO'] == str(usuario)]
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
            df['ID_USUARIO'] = df['ID_USUARIO'].astype(str)
            df['PASSWORD'] = df['PASSWORD'].astype(str)
            
            user_row = df[(df['ID_USUARIO'] == str(usuario)) & (df['PASSWORD'] == str(password))]
            
            if not user_row.empty:
                return user_row.iloc[0]['NOMBRE'], user_row.iloc[0]['NIVEL']
            return None, None
        except:
            return None, None

    @retry_on_error()
    def get_mis_horas(self, id_usuario):
        try:
            def fetch():
                ws = self.sheet.worksheet("DISPONIBILIDAD")
                return ws.get_all_records()
            
            data = self._get_cached("todas_horas", fetch) # Cacheamos todo para no leer mil veces
            
            user_slots = [d for d in data if str(d['ID_USUARIO']) == str(id_usuario)]
            
            clean_data = []
            for d in user_slots:
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
        # Leer todo, filtrar localmente y reescribir (Estrategia segura para formato)
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            df = df[df['ID_USUARIO'].astype(str) != str(id_usuario)]
        
        new_rows = []
        for slot in nuevos_slots:
            new_rows.append({
                'ID_USUARIO': id_usuario,
                'FECHA': slot['fecha'],
                'HORA_INICIO': slot['hora_inicio'],
                'HORA_FIN': slot['hora_fin'],
                'NIVEL': nivel
            })
        
        if new_rows:
            df_new = pd.DataFrame(new_rows)
            df_final = pd.concat([df, df_new], ignore_index=True)
        else:
            df_final = df
            
        if not df_final.empty:
             df_final = df_final.sort_values('FECHA')
             
        ws.clear()
        if not df_final.empty:
            ws.update([df_final.columns.values.tolist()] + df_final.values.tolist())
        else:
            # Restaurar headers si se vacía
            ws.append_row(['ID_USUARIO', 'FECHA', 'HORA_INICIO', 'HORA_FIN', 'NIVEL'])
        
        # Invalidar caché
        del self._cache["todas_horas"]
        return True

    @retry_on_error()
    def get_partidos_posibles(self, nivel):
        try:
            ws = self.sheet.worksheet("DISPONIBILIDAD")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            
            if df.empty: return []
            
            hoy = datetime.now().strftime("%Y-%m-%d")
            df = df[df['FECHA'] >= hoy]
            if 'NIVEL' in df.columns:
                df = df[df['NIVEL'].astype(str) == str(nivel)]
                
            matches = []
            grouped = df.groupby(['FECHA', 'HORA_INICIO', 'HORA_FIN'])
            
            users_map = self._get_users_map()
            
            count = 0
            for (fecha, ini, fin), group in grouped:
                uids = group['ID_USUARIO'].unique()
                if len(uids) >= 4:
                    jugadores = uids[:4]
                    nombres = [users_map.get(str(u), str(u)) for u in jugadores]
                    
                    titulo = f"Jornada (Sugerida)"
                    # Intentar dar formato A/B vs C/D
                    nombres_fmt = f"{nombres[0]}/{nombres[1]} vs {nombres[2]}/{nombres[3]}"
                    
                    matches.append({
                        'id_partido': f"MATCH_{fecha}_{ini}_{count}",
                        'fecha': fecha,
                        'fecha_fmt': fecha,
                        'hora_inicio': ini,
                        'hora_fin': fin,
                        'titulo': titulo,
                        'jugadores_names': nombres_fmt
                    })
                    count += 1
            return matches
        except Exception as e:
            print(f"Error matching: {e}")
            return []

    @retry_on_error()
    def get_mis_partidos(self, nivel):
        try:
            ws = self.sheet.worksheet("PARTIDOS")
            data = ws.get_all_records()
            
            users_map = self._get_users_map()
            
            processed = []
            for p in data:
                # Filtrar por nivel si existe columna, sino mostrar todo
                # if str(p.get('NIVEL')) != str(nivel): continue 
                
                # --- FORMATO TÍTULO ---
                pid = str(p.get('ID_PARTIDO', ''))
                titulo = pid
                # Detectar formato "J1-..." -> "Jornada 1"
                try:
                    if "J" in pid and "-" in pid:
                        # J1-P3 -> Jornada 1
                        j_num = pid.split('-')[0].replace('J', '')
                        titulo = f"Jornada {j_num}"
                    elif pid.startswith("M"):
                        titulo = f"Partido {pid}"
                except:
                    pass
                
                p['titulo_fmt'] = titulo
                
                # --- FORMATO JUGADORES ---
                # Asumiendo columnas JUGADOR1, JUGADOR2, etc que contienen IDs
                ids = [
                    str(p.get('JUGADOR1', '')),
                    str(p.get('JUGADOR2', '')),
                    str(p.get('JUGADOR3', '')),
                    str(p.get('JUGADOR4', ''))
                ]
                
                # Resolver nombres
                names = [users_map.get(uid, uid) if uid else "?" for uid in ids]
                
                # Formato: "Juan/Pepe vs Ana/Maria"
                if all(ids):
                    p['nombres_str'] = f"{names[0]}/{names[1]} vs {names[2]}/{names[3]}"
                else:
                    p['nombres_str'] = "Jugadores sin asignar"
                
                processed.append(p)
                
            return processed
        except Exception as e:
            print(f"Error getting matches: {e}")
            return []

    @retry_on_error()
    def programar_partido(self, id_partido, fecha, hora_range):
        # Dummy save
        pass