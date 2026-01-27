import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
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

class PadelDB:
    def __init__(self):
        scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
        creds = None
        
        # OPCIÓN 1: Archivo local (desarrollo)
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        except FileNotFoundError:
            pass
        
        # OPCIÓN 2: Streamlit Cloud secrets
        if creds is None:
            try:
                if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            except Exception:
                pass
        
        # OPCIÓN 3: Variables de entorno (Railway, Render, etc.)
        if creds is None:
            try:
                if os.environ.get('GCP_PRIVATE_KEY'):
                    # Reconstruir el diccionario de credenciales desde variables de entorno
                    private_key = os.environ.get('GCP_PRIVATE_KEY', '').replace('\\n', '\n')
                    creds_dict = {
                        "type": os.environ.get('GCP_TYPE', 'service_account'),
                        "project_id": os.environ.get('GCP_PROJECT_ID', ''),
                        "private_key_id": os.environ.get('GCP_PRIVATE_KEY_ID', ''),
                        "private_key": private_key,
                        "client_email": os.environ.get('GCP_CLIENT_EMAIL', ''),
                        "client_id": os.environ.get('GCP_CLIENT_ID', ''),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            except Exception as e:
                st.error(f"Error con variables de entorno: {e}")
        
        if creds is None:
            st.error("❌ No se encuentra configuración de credenciales. Verifica credentials.json, Secrets, o variables de entorno.")
            st.stop()
            
        client = gspread.authorize(creds)
        self.spreadsheet_id = '15MAbaPH1gqrCIcUtj6JgdSJXiYMdOBNIxaOqtAHsOB0'  # PadelLite v2
        self.sheet = client.open_by_key(self.spreadsheet_id)
        
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

    def invalidate_cache(self, key=None):
        """Invalida el caché (todo o una clave específica)."""
        if key:
            self._cache.pop(key, None)
            self._cache_time.pop(key, None)
        else:
            self._cache.clear()
            self._cache_time.clear()

    @retry_on_error(max_retries=3, delay=0.5)
    def validar_login(self, usuario, password):
        """Valida credenciales de usuario."""
        try:
            ws = self.sheet.worksheet("USUARIOS")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            
            user_row = df[
                (df['ID_USUARIO'].astype(str) == str(usuario)) & 
                (df['PASSWORD'].astype(str) == str(password))
            ]
            
            if not user_row.empty:
                return self.get_info_usuario(usuario)
            return None, None
            
        except Exception as e:
            print(f"Error en login: {e}")
            return None, None

    @retry_on_error(max_retries=3, delay=0.5)
    def get_info_usuario(self, usuario):
        """Obtiene nombre y nivel de un usuario."""
        try:
            ws = self.sheet.worksheet("USUARIOS")
            cell = ws.find(str(usuario))
            nombre_real = ws.cell(cell.row, 2).value
            
            ws_asig = self.sheet.worksheet("ASIGNACIONES")
            try:
                cell_asig = ws_asig.find(str(usuario))
                nivel = ws_asig.cell(cell_asig.row, 2).value
            except:
                nivel = "NIVEL_TEST"
                
            return nombre_real, nivel
        except:
            return None, None

    @retry_on_error(max_retries=3, delay=0.5)
    def get_mis_horas(self, id_usuario):
        """Obtiene los registros de disponibilidad de un usuario."""
        def fetch():
            ws = self.sheet.worksheet("DISPONIBILIDAD")
            data = ws.get_all_records()
            return [
                {
                    'fecha': row['FECHA'],
                    'hora_inicio': row['HORA_INICIO'],
                    'hora_fin': row['HORA_FIN']
                }
                for row in data
                if str(row['ID_USUARIO']) == str(id_usuario)
            ]
        
        return self._get_cached(f"horas_{id_usuario}", fetch)

    @retry_on_error(max_retries=3, delay=0.5)
    def guardar_disponibilidad(self, id_usuario, id_grupo, registros):
        """Guarda disponibilidad con limpieza automática de fechas pasadas."""
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        all_data = ws.get_all_records()
        
        # Fecha de hoy para limpieza
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        
        # Filtrar datos:
        # 1. De otros usuarios (mantener)
        # 2. Eliminar fechas pasadas (limpieza automática)
        new_data_rows = []
        for row in all_data:
            fecha_row = row['FECHA']
            # Solo mantener si la fecha es hoy o futura
            if fecha_row >= hoy_str:
                if str(row['ID_USUARIO']) != str(id_usuario):
                    grupo = row.get('ID_GRUPO', '')
                    fin = row.get('HORA_FIN', '')
                    new_data_rows.append([row['ID_USUARIO'], fecha_row, row['HORA_INICIO'], fin, grupo])
        
        # Añadir nuevos registros del usuario
        for reg in registros:
            # Solo guardar si es fecha futura o hoy (aunque la UI ya lo filtra)
            if reg['fecha'] >= hoy_str:
                new_data_rows.append([
                    id_usuario, 
                    reg['fecha'], 
                    reg['hora_inicio'], 
                    reg['hora_fin'],
                    id_grupo
                ])
        
        # Operación batch: limpiar y reescribir todo
        ws.clear()
        ws.append_row(["ID_USUARIO", "FECHA", "HORA_INICIO", "HORA_FIN", "ID_GRUPO"])
        if new_data_rows:
            ws.append_rows(new_data_rows, value_input_option='RAW')
        
        # Invalidar caché
        self.invalidate_cache(f"horas_{id_usuario}")
        self.invalidate_cache("partidos")
        if new_data_rows:
            ws.append_rows(new_data_rows, value_input_option='RAW')
        
        # Invalidar caché del usuario
        self.invalidate_cache(f"horas_{id_usuario}")
        self.invalidate_cache("partidos")

    @retry_on_error(max_retries=3, delay=0.5)
    def get_matriz_disponibilidad(self, nivel):
        """Obtiene matriz de disponibilidad por nivel."""
        def fetch():
            ws_asig = self.sheet.worksheet("ASIGNACIONES")
            users_nivel = [str(row['ID_USUARIO']) for row in ws_asig.get_all_records() if row['NIVEL'] == nivel]
            
            ws_disp = self.sheet.worksheet("DISPONIBILIDAD")
            data_disp = ws_disp.get_all_records()
            
            horarios_unicos = sorted(list(set([f"{d['FECHA']} {d['HORA_INICIO']}" for d in data_disp])))
            matriz = pd.DataFrame(index=users_nivel, columns=horarios_unicos).fillna("")
            
            for row in data_disp:
                uid = str(row['ID_USUARIO'])
                time_slot = f"{row['FECHA']} {row['HORA_INICIO']}"
                if uid in users_nivel and time_slot in horarios_unicos:
                    matriz.at[uid, time_slot] = "✅"
            return matriz
        
        return self._get_cached(f"matriz_{nivel}", fetch)

    @retry_on_error(max_retries=3, delay=0.5)
    def get_partidos_posibles(self, nivel):
        """Encuentra partidos con 4 jugadores disponibles al mismo tiempo (Intersección de horarios)."""
        def fetch():
            # 1. Obtener partidos pendientes del grupo
            ws_partidos = self.sheet.worksheet("PARTIDOS")
            all_partidos = ws_partidos.get_all_records()
            partidos = [p for p in all_partidos if p['ESTADO'] == 'PENDIENTE' and str(p['ID_GRUPO']) == str(nivel)]
            
            # 2. Obtener toda la disponibilidad
            ws_disp = self.sheet.worksheet("DISPONIBILIDAD")
            all_disp = ws_disp.get_all_records()
            
            # Organizar disponibilidad por usuario: { 'USER_ID': { 'FECHA': ('INICIO', 'FIN') } }
            # Nota: Un usuario puede tener múltiples rangos por día, aunque ahora simplificamos a uno.
            # Usaremos una lista de rangos: { 'USER_ID': [ {'fecha': 'Y-m-d', 'inicio': 'HH:MM', 'fin': 'HH:MM'} ] }
            disp_map = {}
            hoy = datetime.now().strftime("%Y-%m-%d")
            
            for d in all_disp:
                uid = str(d['ID_USUARIO'])
                fecha = d['FECHA']
                if fecha < hoy: continue # Ignorar pasados
                
                if uid not in disp_map: disp_map[uid] = []
                disp_map[uid].append({
                    'fecha': fecha,
                    'inicio': d['HORA_INICIO'],
                    'fin': d.get('HORA_FIN', '23:00') # Default fin si falta
                })
            
            matches_encontrados = []
            
            def to_mins(h_str):
                try:
                    h, m = map(int, h_str.split(':'))
                    return h * 60 + m
                except: return 0
                
            def from_mins(mins):
                h = mins // 60
                m = mins % 60
                return f"{h:02d}:{m:02d}"

            # 2.5 Obtener mapa de nombres de usuarios
            ws_users = self.sheet.worksheet("USUARIOS")
            users_data = ws_users.get_all_records() # Lista de dicts
            id_to_name = {row['ID_USUARIO']: row['NOMBRE'] for row in users_data}
            
            def get_nombre_corto(uid):
                full_name = id_to_name.get(uid, uid)
                parts = full_name.split(" ")
                if len(parts) >= 2:
                    return f"{parts[0]} {parts[1]}"
                return full_name

            # 3. Analizar cada partido
            for p in partidos:
                # Obtener IDs de jugadores
                ids_jugadores = [
                    str(p['JUGADOR_1']), str(p['JUGADOR_2']), 
                    str(p['JUGADOR_3']), str(p['JUGADOR_4'])
                ]
                
                # Filtrar vacíos
                ids_jugadores = [uid for uid in ids_jugadores if uid and uid != '']
                
                if len(ids_jugadores) < 4: continue
                
                # Buscar fechas comunes
                fechas_por_jugador = []
                for uid in ids_jugadores:
                    fechas = set(r['fecha'] for r in disp_map.get(uid, []))
                    fechas_por_jugador.append(fechas)
                
                if not fechas_por_jugador: continue
                
                # Intersección de fechas
                fechas_comunes = set.intersection(*fechas_por_jugador)
                
                for fecha in fechas_comunes:
                    starts = []
                    ends = []
                    for uid in ids_jugadores:
                        rango = next((r for r in disp_map[uid] if r['fecha'] == fecha), None)
                        if rango:
                            starts.append(to_mins(rango['inicio']))
                            ends.append(to_mins(rango['fin']))
                    
                    max_start = max(starts)
                    min_end = min(ends)
                    
                    if min_end - max_start >= 90:
                        # Formatear datos para la UI
                        
                        # ID Partido -> Jornada
                        # Formato esperado: P-M2-J3-01 -> Jornada 3
                        # Si no sigue formato, mostrar ID
                        jornada_str = p['ID_PARTIDO']
                        try:
                            parts = p['ID_PARTIDO'].split('-')
                            # Buscar parte que empieza por J
                            for part in parts:
                                if part.startswith('J') and part[1:].isdigit():
                                    jornada_str = f"Jornada {part[1:]}"
                                    break
                        except: pass
                        
                        # Nombres cortos
                        nombres = [get_nombre_corto(uid) for uid in ids_jugadores]
                        
                        # Fecha amigable: 2026-01-27 -> 27 Ene
                        meses_cortos = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                                        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
                        dt = datetime.strptime(fecha, "%Y-%m-%d")
                        fecha_amigable = f"{dt.day} {meses_cortos[dt.month]}"

                        matches_encontrados.append({
                            "id_partido": p['ID_PARTIDO'],
                            "titulo": jornada_str, 
                            "jugadores_names": f"{nombres[0]} / {nombres[1]} vs {nombres[2]} / {nombres[3]}",
                            "fecha_fmt": fecha_amigable,
                            "fecha": fecha, # Raw date needed for scheduling
                            "hora_inicio": from_mins(max_start),
                            "hora_fin": from_mins(min_end),
                            "duracion": min_end - max_start
                        })
                        
            return matches_encontrados
                        
            return matches_encontrados
        
        return self._get_cached(f"partidos_{nivel}", fetch)

    @retry_on_error(max_retries=3, delay=0.5)
    def programar_partido(self, id_partido, fecha, hora):
        """
        Marca un partido como PROGRAMADO y guarda fecha/hora.
        Columns: 8=FECHA, 9=HORA, 11=ESTADO
        """
        ws = self.sheet.worksheet("PARTIDOS")
        cell = ws.find(id_partido)
        if cell:
            # Actualizar Fecha (8), Hora (9) y Estado (11)
            # gspread usa 1-based index
            ws.update_cell(cell.row, 8, fecha)
            ws.update_cell(cell.row, 9, hora)
            ws.update_cell(cell.row, 11, "PROGRAMADO")
            self.invalidate_cache("partidos")

    @retry_on_error(max_retries=3, delay=0.5)
    def get_mis_partidos(self, nivel):
        """Obtiene partidos PROGRAMADOS y JUGADOS del nivel."""
        def fetch():
            # Auto-actualizar estados antes de leer
            self.actualizar_estados_partidos(nivel)
            
            ws = self.sheet.worksheet("PARTIDOS")
            all_partidos = ws.get_all_records()
            
            # Filtramos por nivel y estados relevantes
            relevantes = [
                p for p in all_partidos 
                if str(p['ID_GRUPO']) == str(nivel) and p['ESTADO'] in ['PROGRAMADO', 'JUGADO', 'CERRADO']
            ]
            
            # Procesar datos p/ UI (Nombres, fechas, etc)
            ws_users = self.sheet.worksheet("USUARIOS")
            users_data = ws_users.get_all_records()
            id_to_name = {row['ID_USUARIO']: row['NOMBRE'] for row in users_data}
            
            def get_nombre_completo(uid):
                return id_to_name.get(uid, uid)

            for p in relevantes:
                # Inyectar nombres reales
                nombres = []
                for i in range(1, 5):
                    uid = str(p[f'JUGADOR_{i}'])
                    nombres.append(get_nombre_completo(uid))
                
                # Crear string legible
                p['nombres_str'] = f"{nombres[0]} / {nombres[1]} vs {nombres[2]} / {nombres[3]}"
                
                # Parsear Título Jornada si es posible
                titulo = p['ID_PARTIDO']
                if "J" in titulo:
                    try: titulo = f"Jornada {titulo.split('J')[1].split('-')[0]}"
                    except: pass
                p['titulo_fmt'] = titulo

            return relevantes
        
        return self._get_cached(f"historial_{nivel}", fetch)

    def actualizar_estados_partidos(self, nivel):
        """Revisa partidos PROGRAMADOS y si ya pasaron los marca como JUGADOS."""
        try:
            ws = self.sheet.worksheet("PARTIDOS")
            all_partidos = ws.get_all_records()
            hoy = datetime.now().strftime("%Y-%m-%d")
            
            updates = []
            
            for i, p in enumerate(all_partidos):
                # Row index en sheet = i + 2 (header es 1)
                row_idx = i + 2
                
                if str(p['ID_GRUPO']) == str(nivel) and p['ESTADO'] == 'PROGRAMADO':
                    fecha_partido = p['FECHA']
                    if fecha_partido and fecha_partido < hoy:
                        # Partido pasado -> JUGADO
                        # Estado es col 11
                        # Batch update cell object
                        updates.append({
                            'range': f"K{row_idx}", # Col K es la 11
                            'values': [['JUGADO']]
                        })
            
            # Ejecutar actualizaciones batch si hay (usando update_cells quizas es complejo aqui,
            # haremos loop simple por seguridad o batch_update de gspread si disponible facil)
            # Por simplicidad y robustez, usaremos update_cell en loop si son pocos
            # O mejor, batch_update generic
            if updates:
                ws.batch_update(updates)
                self.invalidate_cache("partidos")
        except Exception as e:
            print(f"Error actualizando estados: {e}")