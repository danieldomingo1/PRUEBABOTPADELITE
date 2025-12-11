import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class PadelDB:
    def __init__(self):
        scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        # --- TU ID REAL ---
        self.spreadsheet_id = '13Sib273ZatH4fuSAUU6b8YrDdmYHhmS_ZkRnjYeE6RI'
        self.sheet = client.open_by_key(self.spreadsheet_id)

    def validar_login(self, usuario, password):
        try:
            ws = self.sheet.worksheet("USUARIOS")
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            user_row = df[(df['ID_USUARIO'].astype(str) == str(usuario)) & (df['PASSWORD'].astype(str) == str(password))]
            if not user_row.empty:
                ws_asig = self.sheet.worksheet("ASIGNACIONES")
                df_asig = pd.DataFrame(ws_asig.get_all_records())
                nivel_row = df_asig[df_asig['ID_USUARIO'].astype(str) == str(usuario)]
                nivel = "NIVEL_TEST" 
                if not nivel_row.empty: nivel = nivel_row.iloc[0]['NIVEL']
                return user_row.iloc[0]['NOMBRE_REAL'], nivel
            return None, None
        except: return None, None

    def get_mis_horas(self, id_usuario):
        """Devuelve slots guardados"""
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        data = ws.get_all_records()
        mis_slots = []
        for row in data:
            if str(row['ID_USUARIO']) == str(id_usuario):
                mis_slots.append(f"{row['FECHA']} {row['HORA_INICIO']}")
        return mis_slots

    def guardar_disponibilidad(self, id_usuario, fechas_horas):
        """Sobrescribe disponibilidad"""
        ws = self.sheet.worksheet("DISPONIBILIDAD")
        all_data = ws.get_all_records()
        # Filtramos para quitar lo viejo de este usuario
        new_data_rows = [ [row['ID_USUARIO'], row['FECHA'], row['HORA_INICIO'], row['HORA_FIN']] 
                          for row in all_data if str(row['ID_USUARIO']) != str(id_usuario) ]
        
        for fh in fechas_horas:
            parts = fh.split(" ")
            new_data_rows.append([id_usuario, parts[0], parts[1], ""])
            
        ws.clear()
        ws.append_row(["ID_USUARIO", "FECHA", "HORA_INICIO", "HORA_FIN"])
        if new_data_rows: ws.append_rows(new_data_rows)

    def get_matriz_disponibilidad(self, nivel):
        ws_asig = self.sheet.worksheet("ASIGNACIONES")
        users_nivel = [str(row['ID_USUARIO']) for row in ws_asig.get_all_records() if row['NIVEL'] == nivel]
        ws_disp = self.sheet.worksheet("DISPONIBILIDAD")
        data_disp = ws_disp.get_all_records()
        
        # Ordenar columnas cronológicamente
        horarios_unicos = sorted(list(set([f"{d['FECHA']} {d['HORA_INICIO']}" for d in data_disp])))
        
        matriz = pd.DataFrame(index=users_nivel, columns=horarios_unicos).fillna("")
        for row in data_disp:
            uid, time_slot = str(row['ID_USUARIO']), f"{row['FECHA']} {row['HORA_INICIO']}"
            if uid in users_nivel and time_slot in horarios_unicos:
                matriz.at[uid, time_slot] = "✅"
        return matriz

    def get_partidos_posibles(self, nivel):
        ws_partidos = self.sheet.worksheet("PARTIDOS")
        partidos = [p for p in ws_partidos.get_all_records() if p['ESTADO'] == 'PENDIENTE' and p['NIVEL'] == nivel]
        
        matches = []
        ws_disp = self.sheet.worksheet("DISPONIBILIDAD")
        all_disp = ws_disp.get_all_records()
        
        # Set de búsqueda optimizado
        disp_set = set([(str(d['ID_USUARIO']), f"{d['FECHA']} {d['HORA_INICIO']}") for d in all_disp])
        all_slots = sorted(list(set([f"{d['FECHA']} {d['HORA_INICIO']}" for d in all_disp])))

        for p in partidos:
            jugadores = [j.strip() for j in str(p['JUGADORES_IDS']).split(",") if j.strip()]
            if len(jugadores) < 4: continue
            
            coincidencias = []
            for slot in all_slots:
                if all( (j, slot) in disp_set for j in jugadores ):
                    # Formatear fecha para que se vea bonito en la tarjeta
                    try:
                        dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
                        slot_bonito = dt.strftime("%a %d %H:%M").replace("Mon","Lun").replace("Tue","Mar").replace("Wed","Mié").replace("Thu","Jue").replace("Fri","Vie")
                        coincidencias.append(slot_bonito)
                    except:
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