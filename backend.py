"""
PadelLite Backend - Conexión con Google Sheets
==============================================
Última actualización: 2026-01-28
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st
import time
import os
import re
from functools import wraps


# =============================================================================
# UTILIDADES
# =============================================================================

def retry_on_error(max_retries=3, delay=1):
    """Decorador para reintentar operaciones que fallen."""
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


def clean_private_key(pk):
    """Limpia y corrige formato de clave privada para Streamlit Cloud."""
    if not pk:
        return ""
    pk = pk.strip().strip('"').strip("'")
    
    # Intentar decodificar Base64 si no tiene headers PEM
    import base64
    try:
        if "-----BEGIN PRIVATE KEY-----" not in pk:
            missing_padding = len(pk) % 4
            if missing_padding:
                pk += '=' * (4 - missing_padding)
            decoded = base64.b64decode(pk).decode('utf-8')
            if "-----BEGIN PRIVATE KEY-----" in decoded:
                return decoded
    except Exception:
        pass
    
    # Limpiar escapes de newline
    return pk.replace('\\n', '\n').replace('\\\\n', '\n')


def time_to_minutes(time_str):
    """Convierte HH:MM a minutos desde medianoche."""
    try:
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    except:
        return 0


def calculate_overlap(slots):
    """
    Calcula el solapamiento en minutos entre múltiples slots.
    slots: lista de dicts con 'hora_inicio' y 'hora_fin'
    Retorna: minutos de solapamiento (0 si no hay)
    """
    if not slots:
        return 0
    
    # Encontrar el inicio más tardío y el fin más temprano
    inicio_max = max(time_to_minutes(s['hora_inicio']) for s in slots)
    fin_min = min(time_to_minutes(s['hora_fin']) for s in slots)
    
    overlap = fin_min - inicio_max
    return max(0, overlap)


# =============================================================================
# CLASE PRINCIPAL
# =============================================================================

class PadelDB:
    """Gestiona la conexión y operaciones con la base de datos (Google Sheets)."""
    
    def __init__(self):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = None
        errors = []
        
        # Opción 1: Archivo local (desarrollo)
        if os.path.exists('credentials.json'):
            try:
                creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
            except Exception as e:
                errors.append(f"Local: {e}")
        
        # Opción 2: Streamlit Secrets (producción)
        if creds is None:
            try:
                if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    if "private_key" in creds_dict:
                        creds_dict["private_key"] = clean_private_key(creds_dict["private_key"])
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            except Exception as e:
                errors.append(f"Secrets: {e}")

        # Opción 3: Variables de entorno
        if creds is None:
            try:
                pk = os.environ.get('GCP_PRIVATE_KEY', '')
                if pk:
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
            st.error(f"❌ No se encuentran credenciales. Errores: {'; '.join(errors)}")
            st.stop()
        
        try:
            client = gspread.authorize(creds)
            self.spreadsheet_id = '15MAbaPH1gqrCIcUtj6JgdSJXiYMdOBNIxaOqtAHsOB0'
            self.sheet = client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            st.error(f"❌ Error conectando con Google Sheets: {e}")
            st.stop()
        
        # Sistema de caché simple
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 300  # 5 minutos

    # -------------------------------------------------------------------------
    # CACHÉ
    # -------------------------------------------------------------------------
    
    def _get_cached(self, key, fetch_func, force_refresh=False):
        """Obtiene datos del caché o los recupera si han expirado."""
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

    # -------------------------------------------------------------------------
    # USUARIOS
    # -------------------------------------------------------------------------
    
    def _get_users_map(self):
        """Devuelve diccionario {ID_USUARIO: NOMBRE}."""
        def fetch():
            try:
                ws = self.sheet.worksheet("USUARIOS")
                data = ws.get_all_records()
                return {str(r.get('ID_USUARIO', '')): r.get('NOMBRE', '') for r in data if r.get('ID_USUARIO')}
            except:
                return {}
        return self._get_cached("users_map", fetch)

    @retry_on_error()
    def get_info_usuario(self, user_id):
        """Obtiene nombre y nivel de un usuario."""
        try:
            ws = self.sheet.worksheet("USUARIOS")
            data = ws.get_all_records()
            for row in data:
                if str(row.get('ID_USUARIO', '')) == str(user_id):
                    return row.get('NOMBRE'), row.get('NIVEL')
            return None, None
        except:
            return None, None

    @retry_on_error()
    def validar_login(self, usuario, password):
        """Valida credenciales de login."""
        try:
            def fetch():
                ws = self.sheet.worksheet("USUARIOS")
                return ws.get_all_records()
            
            data = self._get_cached("usuarios_data", fetch)
            
            for row in data:
                if (str(row.get('ID_USUARIO', '')) == str(usuario) and 
                    str(row.get('PASSWORD', '')) == str(password)):
                    return row.get('NOMBRE'), row.get('NIVEL')
            return None, None
        except:
            return None, None

    # -------------------------------------------------------------------------
    # DISPONIBILIDAD
    # -------------------------------------------------------------------------
    
    @retry_on_error()
    def get_mis_horas(self, user_id):
        """Obtiene la disponibilidad guardada del usuario."""
        try:
            def fetch():
                ws = self.sheet.worksheet("DISPONIBILIDAD")
                return ws.get_all_records()
            
            data = self._get_cached("disponibilidad", fetch)
            
            return [
                {
                    'fecha': d.get('FECHA', ''),
                    'hora_inicio': d.get('HORA_INICIO', ''),
                    'hora_fin': d.get('HORA_FIN', '')
                }
                for d in data if str(d.get('ID_USUARIO', '')) == str(user_id)
            ]
        except:
            return []

    @retry_on_error()
    def guardar_disponibilidad(self, user_id, nivel, nuevos_slots):
        """Guarda la disponibilidad del usuario (reemplaza la anterior)."""
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        data = ws.get_all_records()
        
        # Mantener registros de otros usuarios
        otros = [d for d in data if str(d.get('ID_USUARIO', '')) != str(user_id)]
        
        # Crear nuevos registros
        nuevos = [
            {
                'ID_USUARIO': user_id,
                'FECHA': slot['fecha'],
                'HORA_INICIO': slot['hora_inicio'],
                'HORA_FIN': slot['hora_fin'],
                'NIVEL': nivel
            }
            for slot in nuevos_slots
        ]
        
        # Combinar y ordenar
        todos = sorted(otros + nuevos, key=lambda x: x.get('FECHA', ''))
        
        # Reescribir hoja
        ws.clear()
        headers = ['ID_USUARIO', 'FECHA', 'HORA_INICIO', 'HORA_FIN', 'NIVEL']
        ws.append_row(headers)
        if todos:
            rows = [[d.get(h, '') for h in headers] for d in todos]
            ws.append_rows(rows)
        
        self._invalidate_cache("disponibilidad")
        return True

    def _get_disponibilidad_por_fecha(self):
        """Obtiene disponibilidad agrupada por usuario y fecha."""
        def fetch():
            ws = self.sheet.worksheet("DISPONIBILIDAD")
            data = ws.get_all_records()
            
            # Estructura: {user_id: {fecha: {'hora_inicio': X, 'hora_fin': Y}}}
            result = {}
            for d in data:
                uid = str(d.get('ID_USUARIO', ''))
                fecha = d.get('FECHA', '')
                if uid and fecha:
                    if uid not in result:
                        result[uid] = {}
                    result[uid][fecha] = {
                        'hora_inicio': d.get('HORA_INICIO', ''),
                        'hora_fin': d.get('HORA_FIN', '')
                    }
            return result
        return self._get_cached("disponibilidad_mapa", fetch)

    # -------------------------------------------------------------------------
    # PARTIDOS
    # -------------------------------------------------------------------------
    
    @retry_on_error()
    def get_partidos_usuario(self, user_id):
        """
        Obtiene todos los partidos donde el usuario es jugador.
        Retorna dict con keys: 'pendientes', 'programados', 'jugados'
        """
        try:
            ws = self.sheet.worksheet("PARTIDOS")
            data = ws.get_all_records()
            users_map = self._get_users_map()
            
            pendientes = []
            programados = []
            jugados = []
            
            for p in data:
                # Verificar si el usuario es uno de los 4 jugadores
                jugadores = [
                    str(p.get('JUGADOR_1', '') or ''),
                    str(p.get('JUGADOR_2', '') or ''),
                    str(p.get('JUGADOR_3', '') or ''),
                    str(p.get('JUGADOR_4', '') or '')
                ]
                
                if str(user_id) not in jugadores:
                    continue  # El usuario no está en este partido
                
                # Formatear título (P-M2-J4-01 -> Jornada 4)
                pid = str(p.get('ID_PARTIDO', ''))
                match = re.search(r'J(\d+)', pid)
                titulo = f"Jornada {match.group(1)}" if match else pid
                
                # Formatear nombres
                nombres = [users_map.get(uid, uid) if uid else "..." for uid in jugadores]
                nombres_str = f"{nombres[0]}/{nombres[1]} vs {nombres[2]}/{nombres[3]}"
                
                partido_fmt = {
                    'id_partido': pid,
                    'titulo': titulo,
                    'jugadores': jugadores,
                    'nombres_str': nombres_str,
                    'fecha': p.get('FECHA', ''),
                    'hora': p.get('HORA', ''),
                    'estado': p.get('ESTADO', ''),
                    'resultado': p.get('RESULTADO', '')
                }
                
                estado = p.get('ESTADO', '')
                if estado == 'PENDIENTE':
                    pendientes.append(partido_fmt)
                elif estado == 'PROGRAMADO':
                    programados.append(partido_fmt)
                elif estado == 'JUGADO':
                    jugados.append(partido_fmt)
            
            return {
                'pendientes': pendientes,
                'programados': programados,
                'jugados': jugados
            }
        except Exception as e:
            print(f"Error en get_partidos_usuario: {e}")
            return {'pendientes': [], 'programados': [], 'jugados': []}

    @retry_on_error()
    def get_partidos_disponibles(self, user_id):
        """
        Obtiene partidos PENDIENTES donde los 4 jugadores coinciden en disponibilidad.
        Mínimo 60 minutos de solapamiento.
        Devuelve TODAS las fechas donde coinciden (no solo la primera).
        """
        try:
            # Obtener partidos pendientes del usuario
            partidos = self.get_partidos_usuario(user_id)
            pendientes = partidos['pendientes']
            
            if not pendientes:
                return []
            
            # Obtener disponibilidad de todos
            disponibilidad = self._get_disponibilidad_por_fecha()
            hoy = datetime.now().strftime("%Y-%m-%d")
            
            disponibles = []
            
            for partido in pendientes:
                jugadores = partido['jugadores']
                
                # Buscar fechas donde TODOS los jugadores tienen disponibilidad
                fechas_candidatas = set()
                for uid in jugadores:
                    if uid in disponibilidad:
                        for fecha in disponibilidad[uid].keys():
                            if fecha >= hoy:
                                fechas_candidatas.add(fecha)
                
                # Lista de todas las coincidencias para este partido
                coincidencias = []
                
                # Para cada fecha, verificar si los 4 coinciden con >= 60 min
                for fecha in sorted(fechas_candidatas):
                    slots = []
                    todos_tienen = True
                    
                    for uid in jugadores:
                        if uid in disponibilidad and fecha in disponibilidad[uid]:
                            slots.append(disponibilidad[uid][fecha])
                        else:
                            todos_tienen = False
                            break
                    
                    if todos_tienen and len(slots) == 4:
                        overlap = calculate_overlap(slots)
                        if overlap >= 60:  # Mínimo 1 hora
                            # Calcular hora común
                            inicio_comun = max(time_to_minutes(s['hora_inicio']) for s in slots)
                            fin_comun = min(time_to_minutes(s['hora_fin']) for s in slots)
                            
                            hora_inicio = f"{inicio_comun // 60:02d}:{inicio_comun % 60:02d}"
                            hora_fin = f"{fin_comun // 60:02d}:{fin_comun % 60:02d}"
                            
                            coincidencias.append({
                                'fecha': fecha,
                                'hora_inicio': hora_inicio,
                                'hora_fin': hora_fin,
                                'solapamiento_min': overlap
                            })
                
                # Si hay alguna coincidencia, añadir el partido con todas sus opciones
                if coincidencias:
                    disponibles.append({
                        'id_partido': partido['id_partido'],
                        'titulo': partido['titulo'],
                        'nombres_str': partido['nombres_str'],
                        'coincidencias': coincidencias  # Lista de todas las opciones
                    })
            
            return disponibles
        except Exception as e:
            print(f"Error en get_partidos_disponibles: {e}")
            return []

    @retry_on_error()
    def confirmar_partido(self, id_partido, fecha, hora):
        """Cambia un partido de PENDIENTE a PROGRAMADO."""
        try:
            ws = self.sheet.worksheet("PARTIDOS")
            data = ws.get_all_records()
            
            # Encontrar el partido y actualizar
            for i, p in enumerate(data):
                if str(p.get('ID_PARTIDO', '')) == str(id_partido):
                    # Actualizar celdas (fila i+2 porque row 1 son headers)
                    row = i + 2
                    # Columnas: FECHA=8, HORA=9, ESTADO=11 (según estructura)
                    ws.update_cell(row, 8, fecha)
                    ws.update_cell(row, 9, hora)
                    ws.update_cell(row, 11, 'PROGRAMADO')
                    return True
            return False
        except Exception as e:
            print(f"Error en confirmar_partido: {e}")
            return False