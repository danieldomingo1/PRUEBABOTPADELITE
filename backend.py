import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st

class PadelDB:
    def __init__(self):
        scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
        
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
            except:
                st.error("❌ No se encuentra el archivo 'credentials.json' ni la configuración de Secrets.")
                st.stop()
            
        client = gspread.authorize(creds)
        self.spreadsheet_id = '13Sib273ZatH4fuSAUU6b8YrDdmYHhmS_ZkRnjYeE6RI'
        self.sheet = client.open_by_key(self.spreadsheet_id)

    def validar_login(self, usuario, password):
        try:
            ws = self.sheet.worksheet("USUARIOS")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            
            user_row = df[
                (df['ID_USUARIO'].astype(str) == str(usuario)) & 
                (df['PASSWORD'].astype(str) == str(password))
            ]
            
            if not user_row.empty:
                return self.get_info_usuario(usuario) # Reutilizamos la lógica
            return None, None
            
        except Exception as e:
            print(f"Error en login: {e}")
            return None, None

    # --- NUEVA FUNCIÓN PARA EL AUTO-LOGIN ---
    def get_info_usuario(self, usuario):
        try:
            ws = self.sheet.worksheet("USUARIOS")
            # Buscamos el nombre real
            cell = ws.find(str(usuario))
            nombre_real = ws.cell(cell.row, 2).value # Columna 2 es NOMBRE_REAL
            
            # Buscamos el nivel
            ws_asig = self.sheet.worksheet("ASIGNACIONES")
            try:
                cell_asig = ws_asig.find(str(usuario))
                nivel = ws_asig.cell(cell_asig.row, 2).value # Columna 2 es NIVEL
            except:
                nivel = "NIVEL_TEST"
                
            return nombre_real, nivel
        except:
            return None, None

    def get_mis_horas(self, id_usuario):
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        data = ws.get_all_records()
        mis_slots = []
        for row in data:
            if str(row['ID_USUARIO']) == str(id_usuario):
                mis_slots.append(f"{row['FECHA']} {row['HORA_INICIO']}")
        return mis_slots

    def guardar_disponibilidad(self, id_usuario, fechas_horas):
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        all_data = ws.get_all_records()
        
        new_data_rows = []
        for row in all_data:
            if str(row['ID_USUARIO']) != str(id_usuario):
                new_data_rows.append([row['ID_USUARIO'], row['FECHA'], row['HORA_INICIO'], row['HORA_FIN']])
        
        for fh in fechas_horas:
            parts = fh.split(" ")
            new_data_rows.append([id_usuario, parts[0], parts[1], ""])
            
        ws.clear()
        ws.append_row(["ID_USUARIO", "FECHA", "HORA_INICIO", "HORA_FIN"])
        if new_data_rows:
            ws.append_rows(new_data_rows)

    def get_matriz_disponibilidad(self, nivel):
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

    def get_partidos_posibles(self, nivel):
        ws_partidos = self.sheet.worksheet("PARTIDOS")
        partidos = [p for p in ws_partidos.get_all_records() if p['ESTADO'] == 'PENDIENTE' and p['NIVEL'] == nivel]
        matches = []
        ws_disp = self.sheet.worksheet("DISPONIBILIDAD")
        all_disp = ws_disp.get_all_records()
        disp_set = set([(str(d['ID_USUARIO']), f"{d['FECHA']} {d['HORA_INICIO']}") for d in all_disp])
        all_slots = sorted(list(set([f"{d['FECHA']} {d['HORA_INICIO']}" for d in all_disp])))
        for p in partidos:
            jugadores_raw = str(p['JUGADORES_IDS']).split(",")
            jugadores = [j.strip() for j in jugadores_raw]
            if len(jugadores) < 4: continue
            coincidencias = []
            for slot in all_slots:
                if all( (j, slot) in disp_set for j in jugadores ):
                    coincidencias.append(slot)
            if coincidencias:
                matches.append({
                    "id_partido": p['ID_PARTIDO'],
                    "jugadores": ", ".join(jugadores),
                    "slots": coincidencias
                })
        return matches

    def cerrar_partido(self, id_partido):
        ws = self.sheet.worksheet("PARTIDOS")
        cell = ws.find(id_partido)
        ws.update_cell(cell.row, 5, "CERRADO")