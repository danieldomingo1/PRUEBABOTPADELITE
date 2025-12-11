import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN ---
SPREADSHEET_ID = '13Sib273ZatH4fuSAUU6b8YrDdmYHhmS_ZkRnjYeE6RI' # <--- ¡PEGA TU ID AQUÍ!
PASSWORD_DEFAULT = "1234"
NIVEL_DEFAULT = "NIVEL_TEST"
FASE_ACTIVA = "PILOTO-01"

# --- DATOS REALES (Extraídos de tus capturas) ---
JUGADORES = [
    "Miguel Ángel Salas García",
    "César Rodríguez Tomillo",
    "Álvaro Montes Alonso",
    "Miguel Ángel Ausín Ortega",
    "Roberto Rica Cámara",
    "Sergio De La Cámara Gómez",
    "Álvaro Muñoz López",
    "Daniel Domingo Ruiz",
    "Mario García Martínez"
]

# Lista de partidos transcrita de las imágenes
# Formato: [Jornada, Jugador1, Jugador2, Jugador3, Jugador4]
PARTIDOS_A_CARGAR = [
    # Jornada 1
    ["J1", "Álvaro Muñoz López", "Miguel Ángel Ausín Ortega", "Miguel Ángel Salas García", "Sergio De La Cámara Gómez"],
    ["J1", "Daniel Domingo Ruiz", "Mario García Martínez", "Álvaro Muñoz López", "Sergio De La Cámara Gómez"], # Nota: Algunos jugadores repiten según imagen
    
    # Jornada 2
    ["J2", "Roberto Rica Cámara", "Daniel Domingo Ruiz", "César Rodríguez Tomillo", "Álvaro Montes Alonso"],
    
    # Jornada 3
    ["J3", "Mario García Martínez", "Roberto Rica Cámara", "Miguel Ángel Salas García", "Miguel Ángel Ausín Ortega"],
    ["J3", "César Rodríguez Tomillo", "Sergio De La Cámara Gómez", "Álvaro Muñoz López", "Álvaro Montes Alonso"],

    # Jornada 4
    ["J4", "Álvaro Muñoz López", "Miguel Ángel Salas García", "Álvaro Montes Alonso", "Mario García Martínez"],
    ["J4", "Sergio De La Cámara Gómez", "Daniel Domingo Ruiz", "Miguel Ángel Ausín Ortega", "Roberto Rica Cámara"],

    # Jornada 5
    ["J5", "Sergio De La Cámara Gómez", "Miguel Ángel Ausín Ortega", "Mario García Martínez", "César Rodríguez Tomillo"],
    ["J5", "Daniel Domingo Ruiz", "César Rodríguez Tomillo", "Mario García Martínez", "Miguel Ángel Salas García"],

    # Jornada 6
    ["J6", "César Rodríguez Tomillo", "Álvaro Muñoz López", "Miguel Ángel Ausín Ortega", "Daniel Domingo Ruiz"],
    ["J6", "Álvaro Montes Alonso", "Roberto Rica Cámara", "Sergio De La Cámara Gómez", "Mario García Martínez"],

    # Jornada 7
    ["J7", "Roberto Rica Cámara", "Miguel Ángel Salas García", "Daniel Domingo Ruiz", "Álvaro Muñoz López"],
    ["J7", "Miguel Ángel Ausín Ortega", "Álvaro Montes Alonso", "Roberto Rica Cámara", "Álvaro Muñoz López"],

    # Jornada 8
    ["J8", "Miguel Ángel Ausín Ortega", "Mario García Martínez", "Álvaro Montes Alonso", "Daniel Domingo Ruiz"],

    # Jornada 9
    ["J9", "Álvaro Montes Alonso", "Sergio De La Cámara Gómez", "Daniel Domingo Ruiz", "Miguel Ángel Salas García"],
    ["J9", "Mario García Martínez", "Álvaro Muñoz López", "Roberto Rica Cámara", "César Rodríguez Tomillo"]
]

def generar_id(nombre, contador):
    """Genera ID tipo MS01 (Iniciales + Numero)"""
    partes = nombre.split()
    # Tomar inicial nombre y primer apellido
    iniciales = (partes[0][0] + partes[-2][0]).upper() 
    return f"{iniciales}{str(contador).zfill(2)}"

def run():
    print("🚀 Iniciando carga de datos reales...")
    
    # Conexión
    scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID)

    # 1. LIMPIEZA
    print("🧹 Limpiando base de datos antigua...")
    sheet.worksheet("USUARIOS").clear()
    sheet.worksheet("USUARIOS").append_row(["ID_USUARIO", "NOMBRE_REAL", "ALIAS_TELEGRAM", "TELEGRAM_ID", "PASSWORD"])
    
    sheet.worksheet("ASIGNACIONES").clear()
    sheet.worksheet("ASIGNACIONES").append_row(["ID_ASIGNACION", "ID_FASE", "NIVEL", "ID_USUARIO"])
    
    sheet.worksheet("PARTIDOS").clear()
    sheet.worksheet("PARTIDOS").append_row(["ID_PARTIDO", "ID_FASE", "NIVEL", "JUGADORES_IDS", "ESTADO"])

    # 2. CREAR JUGADORES
    print("👤 Creando jugadores...")
    mapa_nombre_id = {}
    rows_usuarios = []
    rows_asignaciones = []
    
    for i, nombre in enumerate(JUGADORES):
        nuevo_id = generar_id(nombre, i+1)
        mapa_nombre_id[nombre] = nuevo_id # Guardamos para usarlo luego en los partidos
        
        # Fila Usuario: ID, Nombre, Alias(Vacio), TelegramID(Vacio), Password
        rows_usuarios.append([nuevo_id, nombre, "", "", PASSWORD_DEFAULT])
        
        # Fila Asignacion
        rows_asignaciones.append([f"ASIG-{nuevo_id}", FASE_ACTIVA, NIVEL_DEFAULT, nuevo_id])
        
        print(f"   -> Creado: {nombre} (ID: {nuevo_id} / Pass: {PASSWORD_DEFAULT})")

    sheet.worksheet("USUARIOS").append_rows(rows_usuarios)
    sheet.worksheet("ASIGNACIONES").append_rows(rows_asignaciones)

    # 3. CREAR PARTIDOS
    print("🎾 Creando partidos programados...")
    rows_partidos = []
    
    for i, p_data in enumerate(PARTIDOS_A_CARGAR):
        jornada = p_data[0]
        nombres_jugadores = p_data[1:]
        
        # Convertir Nombres Reales a IDs usando el mapa
        try:
            ids_jugadores = [mapa_nombre_id[n] for n in nombres_jugadores]
            ids_string = ",".join(ids_jugadores)
            
            id_partido = f"P-{str(i+1).zfill(2)}-{jornada}"
            
            # Fila Partido: ID, Fase, Nivel, IDs, Estado
            rows_partidos.append([id_partido, FASE_ACTIVA, NIVEL_DEFAULT, ids_string, "PENDIENTE"])
        except KeyError as e:
            print(f"⚠️ ERROR: No encuentro el ID para el jugador: {e}. Revisa que el nombre en la lista de partidos coincida EXACTAMENTE con la lista de jugadores.")

    sheet.worksheet("PARTIDOS").append_rows(rows_partidos)
    print(f"✅ ¡Carga completada! Se han creado {len(rows_usuarios)} jugadores y {len(rows_partidos)} partidos.")

if __name__ == "__main__":
    run()