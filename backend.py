import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st
import time
import os
import re
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

# --- HELPER: NORMALIZAR NIVEL ---
def normalize_nivel(nivel):
    """Normaliza niveles para comparación (M02 -> M2, etc)."""
    if not nivel:
        return ""
    # Quitar ceros después de letras: M02 -> M2, F01 -> F1
    return re.sub(r'([A-Z])0+(\d)', r'\1\2', str(nivel).upper())

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

    def _invalidate_cache(self, key=None):
        """Invalida el caché (todo o una clave específica)."""
        if key:
            self._cache.pop(key, None)
            self._cache_time.pop(key, None)
        else:
            self._cache.clear()
            self._cache_time.clear()

    def _get_users_map(self):
        """Devuelve un diccionario {ID_USUARIO: NOMBRE}."""
        def fetch():
            try:
                ws = self.sheet.worksheet("USUARIOS")
                data = ws.get_all_records()
                result = {}
                for r in data:
                    uid = str(r.get('ID_USUARIO', ''))
                    nombre = r.get('NOMBRE', uid)  # Fallback al ID si no hay nombre
                    if uid:
                        result[uid] = nombre
                return result
            except Exception as e:
                print(f"Error en _get_users_map: {e}")
                return {}
        return self._get_cached("users_map", fetch)

    @retry_on_error()
    def get_info_usuario(self, usuario):
        try:
            ws = self.sheet.worksheet("USUARIOS")
            data = ws.get_all_records()
            for row in data:
                if str(row.get('ID_USUARIO', '')) == str(usuario):
                    return row.get('NOMBRE'), row.get('NIVEL')
            return None, None
        except Exception as e:
            print(f"Error en get_info_usuario: {e}")
            return None, None

    @retry_on_error()
    def validar_login(self, usuario, password):
        try:
            def fetch_users():
                ws = self.sheet.worksheet("USUARIOS")
                return ws.get_all_records()
            
            data = self._get_cached("usuarios_data", fetch_users)
            
            for row in data:
                uid = str(row.get('ID_USUARIO', ''))
                pwd = str(row.get('PASSWORD', ''))
                if uid == str(usuario) and pwd == str(password):
                    return row.get('NOMBRE'), row.get('NIVEL')
            return None, None
        except Exception as e:
            print(f"Error en validar_login: {e}")
            return None, None

    @retry_on_error()
    def get_mis_horas(self, id_usuario):
        try:
            def fetch():
                ws = self.sheet.worksheet("DISPONIBILIDAD")
                return ws.get_all_records()
            
            data = self._get_cached("todas_horas", fetch)
            
            user_slots = []
            for d in data:
                if str(d.get('ID_USUARIO', '')) == str(id_usuario):
                    user_slots.append({
                        'fecha': d.get('FECHA', ''),
                        'hora_inicio': d.get('HORA_INICIO', ''),
                        'hora_fin': d.get('HORA_FIN', '')
                    })
            return user_slots
        except Exception as e:
            print(f"Error en get_mis_horas: {e}")
            return []

    @retry_on_error()
    def guardar_disponibilidad(self, id_usuario, nivel, nuevos_slots):
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        data = ws.get_all_records()
        
        # Mantener registros de otros usuarios
        otros = [d for d in data if str(d.get('ID_USUARIO', '')) != str(id_usuario)]
        
        # Crear nuevos registros
        nuevos = []
        for slot in nuevos_slots:
            nuevos.append({
                'ID_USUARIO': id_usuario,
                'FECHA': slot['fecha'],
                'HORA_INICIO': slot['hora_inicio'],
                'HORA_FIN': slot['hora_fin'],
                'NIVEL': nivel
            })
        
        # Combinar y ordenar
        todos = otros + nuevos
        todos.sort(key=lambda x: x.get('FECHA', ''))
        
        # Reescribir hoja
        ws.clear()
        headers = ['ID_USUARIO', 'FECHA', 'HORA_INICIO', 'HORA_FIN', 'NIVEL']
        ws.append_row(headers)
        
        if todos:
            rows = [[d.get(h, '') for h in headers] for d in todos]
            ws.append_rows(rows)
        
        # Invalidar caché
        self._invalidate_cache("todas_horas")
        return True

    @retry_on_error()
    def get_partidos_posibles(self, nivel):
        """Encuentra partidos donde 4+ jugadores coinciden en disponibilidad."""
        try:
            ws = self.sheet.worksheet("DISPONIBILIDAD")
            data = ws.get_all_records()
            
            if not data:
                return []
            
            hoy = datetime.now().strftime("%Y-%m-%d")
            nivel_normalizado = normalize_nivel(nivel)
            
            # Filtrar por fecha futura y nivel
            filtrados = []
            for d in data:
                fecha = d.get('FECHA', '')
                if fecha >= hoy:
                    nivel_disp = normalize_nivel(d.get('NIVEL', ''))
                    if nivel_disp == nivel_normalizado:
                        filtrados.append(d)
            
            if not filtrados:
                return []
            
            # Agrupar por fecha/hora
            grupos = {}
            for d in filtrados:
                key = (d.get('FECHA', ''), d.get('HORA_INICIO', ''), d.get('HORA_FIN', ''))
                if key not in grupos:
                    grupos[key] = []
                grupos[key].append(str(d.get('ID_USUARIO', '')))
            
            # Buscar grupos con 4+ jugadores
            users_map = self._get_users_map()
            matches = []
            count = 0
            
            for (fecha, ini, fin), uids in grupos.items():
                if len(uids) >= 4:
                    jugadores = uids[:4]
                    nombres = [users_map.get(u, u) for u in jugadores]
                    
                    matches.append({
                        'id_partido': f"MATCH_{fecha}_{ini}_{count}",
                        'fecha': fecha,
                        'fecha_fmt': fecha,
                        'hora_inicio': ini,
                        'hora_fin': fin,
                        'titulo': "Partido Sugerido",
                        'jugadores_names': f"{nombres[0]}/{nombres[1]} vs {nombres[2]}/{nombres[3]}"
                    })
                    count += 1
            
            return matches
        except Exception as e:
            print(f"Error en get_partidos_posibles: {e}")
            return []

    @retry_on_error()
    def get_mis_partidos(self, nivel):
        """Obtiene partidos del historial."""
        try:
            ws = self.sheet.worksheet("PARTIDOS")
            data = ws.get_all_records()
            
            users_map = self._get_users_map()
            
            processed = []
            for p in data:
                # --- FORMATO TÍTULO ---
                pid = str(p.get('ID_PARTIDO', ''))
                titulo = pid
                
                # Buscar patrón J seguido de número en cualquier parte
                # Ejemplo: P-M2-J4-01 -> Jornada 4
                match = re.search(r'J(\d+)', pid)
                if match:
                    titulo = f"Jornada {match.group(1)}"
                
                p['titulo_fmt'] = titulo
                
                # --- FORMATO JUGADORES ---
                ids = [
                    str(p.get('JUGADOR_1', '') or ''),
                    str(p.get('JUGADOR_2', '') or ''),
                    str(p.get('JUGADOR_3', '') or ''),
                    str(p.get('JUGADOR_4', '') or '')
                ]
                
                # Resolver nombres con fallback al ID
                nombres = []
                for uid in ids:
                    if uid:
                        nombre = users_map.get(uid, uid)
                        nombres.append(nombre)
                    else:
                        nombres.append("...")
                
                # Formato final
                if any(uid for uid in ids):
                    p['nombres_str'] = f"{nombres[0]}/{nombres[1]} vs {nombres[2]}/{nombres[3]}"
                else:
                    p['nombres_str'] = "Jugadores por asignar"
                
                processed.append(p)
            
            return processed
        except Exception as e:
            print(f"Error en get_mis_partidos: {e}")
            return []

    @retry_on_error()
    def programar_partido(self, id_partido, fecha, hora_range):
        # TODO: Implementar guardado de partido confirmado
        pass