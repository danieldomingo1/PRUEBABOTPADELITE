import streamlit as st
import pandas as pd
from backend import PadelDB
from datetime import datetime, timedelta
import pytz

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Liga Padel", layout="wide")

# --- CSS DE DISEÑO FINAL ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
        
        .block-container {
            padding-top: 3.5rem !important; 
            padding-bottom: 3rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            max-width: 1600px;
        }
        
        h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            font-family: 'Bebas Neue', sans-serif !important;
            letter-spacing: 1px;
            padding-top: 0rem !important;
            margin-bottom: 0rem !important;
        }
        h3 { font-size: 2rem !important; }

        div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
        
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 8px 12px !important;
            border-radius: 10px !important;
            border: 1px solid #e0e0e0;
        }
        
        .week-header {
            font-family: 'Bebas Neue', sans-serif !important;
            font-size: 1.2rem;
            color: #888;
            margin-top: 10px;
            margin-bottom: 10px !important;
            letter-spacing: 1px;
            border-bottom: 2px solid #1aa1b0;
            display: inline-block;
        }

        p { margin-bottom: 0px !important; }
        div[data-testid="column"] button { margin-top: 0px; padding-top: 0px; }
        .stToggle { margin-top: 4px !important; }
        
        div[data-testid="stMarkdownContainer"] p {
            line-height: 1.2;
        }
    </style>
""", unsafe_allow_html=True)

# --- LISTA DE HORAS ---
OPCIONES_HORAS = [
    "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", 
    "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", 
    "21:00", "21:30", "22:00", "22:30", "23:00"
]

# --- POPUP MEJORADO (CON ESPACIO) ---
@st.dialog("✅ ¡Confirmado!")
def popup_guardado(nombre):
    st.write(f"Perfecto, muchas gracias por marcar tu disponibilidad, **{nombre}**.")
    # AÑADIMOS DOBLE SALTO DE LÍNEA PARA QUE EL BOTÓN NO PISE EL TEXTO
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Cerrar", type="primary"):
        st.rerun()

def generar_slots_desde_seleccion(fecha_str, hora_inicio_str, hora_fin_str):
    slots = []
    try:
        idx_inicio = OPCIONES_HORAS.index(hora_inicio_str)
        idx_fin = OPCIONES_HORAS.index(hora_fin_str)
        idx_ultimo_inicio = idx_fin - 3 
        current_idx = idx_inicio
        while current_idx <= idx_ultimo_inicio:
            hora_str = OPCIONES_HORAS[current_idx]
            slots.append(f"{fecha_str} {hora_str}")
            current_idx += 1
    except ValueError: pass
    return slots

# --- INICIO ---
if 'db' not in st.session_state:
    try: st.session_state.db = PadelDB()
    except: st.stop()
if 'user' not in st.session_state: st.session_state.user = None

# --- LÓGICA DE AUTO-LOGIN (PERSISTENCIA) ---
# Si no hay usuario logueado, miramos la URL
if st.session_state.user is None:
    # Leemos el parámetro 'u' de la URL (ej: ?u=DD08)
    params = st.query_params
    if "u" in params:
        user_id_url = params["u"]
        # Intentamos recuperar datos de ese usuario
        n, l = st.session_state.db.get_info_usuario(user_id_url)
        if n:
            st.session_state.user = {'id': user_id_url, 'nombre': n, 'nivel': l}
            # No hacemos rerun aquí para evitar bucles, el flujo continuará a main_app

# --- VISTAS ---
def login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<h2 style='text-align: center; color: #1aa1b0; font-size: 3rem !important;'>ACCESO LIGA</h2>", unsafe_allow_html=True)
        st.write("") 
        with st.container(border=True):
            with st.form("login"):
                st.write("") 
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                st.write("") 
                if st.form_submit_button("ENTRAR", type="primary", use_container_width=True):
                    n, l = st.session_state.db.validar_login(u, p)
                    if n:
                        st.session_state.user = {'id': u, 'nombre': n, 'nivel': l}
                        # GUARDAMOS EL USUARIO EN LA URL PARA QUE NO SE BORRE AL REFRESCAR
                        st.query_params["u"] = u 
                        st.rerun()
                    else: st.error("Error credenciales")

def main_app():
    if 'mis_slots_cache' not in st.session_state:
        try:
            st.session_state.mis_slots_cache = st.session_state.db.get_mis_horas(st.session_state.user['id'])
        except Exception as e:
            st.error("Error de conexión. Espera un minuto y recarga.")
            return

    mis_slots_guardados = st.session_state.mis_slots_cache
    nuevos_slots_usuario = []
    
    c_titulo, c_vacio, c_boton = st.columns([3, 4, 1], vertical_alignment="center") 
    c_titulo.markdown(f"### HOLA, {st.session_state.user['nombre']}")
    
    if c_boton.button("SALIR", key="logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.clear()
        # BORRAMOS EL USUARIO DE LA URL AL SALIR
        st.query_params.clear()
        st.rerun()

    st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #eee;'/>", unsafe_allow_html=True)
    
    zona_madrid = pytz.timezone('Europe/Madrid')
    hoy = datetime.now(zona_madrid)
    lunes_esta_semana = hoy - timedelta(days=hoy.weekday())
    
    meses = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 
             7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    nombre_mes = meses[hoy.month]

    inicio_s1 = lunes_esta_semana
    fin_s1 = inicio_s1 + timedelta(days=6)
    inicio_s2 = inicio_s1 + timedelta(days=7)
    fin_s2 = inicio_s2 + timedelta(days=6)

    # === LAYOUT ===
    zona_agenda, zona_panel = st.columns([2.2, 1], gap="large") 

    # --- ZONA IZQUIERDA: AGENDA ---
    with zona_agenda:
        st.markdown(f"<h3 style='text-align: center; color: #1aa1b0; margin-bottom: 10px !important;'>📅 {nombre_mes}</h3>", unsafe_allow_html=True)
        st.markdown("**💡 Instrucciones:** Selecciona tus días.<br>**Nota:** La hora final es la de *finalización* (ej: hasta las 22:00 significa que el partido empieza a las 20:30).", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        col_sem1, col_sem2 = st.columns(2, gap="medium")
        
        for i in range(14):
            fecha = lunes_esta_semana + timedelta(days=i)
            fecha_str = fecha.strftime('%Y-%m-%d')
            es_pasado = fecha.date() < hoy.date()
            
            contenedor = col_sem1 if i < 7 else col_sem2
            
            with contenedor:
                if i == 0:
                    st.markdown(f"<div class='week-header'>SEMANA DEL {inicio_s1.day} AL {fin_s1.day}</div>", unsafe_allow_html=True)
                elif i == 7:
                    st.markdown(f"<div class='week-header'>SEMANA DEL {inicio_s2.day} AL {fin_s2.day}</div>", unsafe_allow_html=True)

                with st.container(border=True):
                    dias_es = {"Mon":"Lunes", "Tue":"Martes", "Wed":"Miércoles", "Thu":"Jueves", "Fri":"Viernes", "Sat":"Sábado", "Sun":"Domingo"}
                    dia_nombre = dias_es[fecha.strftime('%a')]
                    dia_num = fecha.day
                    
                    horas_guardadas_hoy = [h for h in mis_slots_guardados if h.startswith(fecha_str)]
                    activo_por_defecto = bool(horas_guardadas_hoy)

                    if es_pasado:
                        st.markdown(f"<span style='color: #bbb;'>**{dia_nombre} {dia_num}**</span>", unsafe_allow_html=True)
                        st.toggle("Disp", value=False, key=f"tog_{i}", label_visibility="collapsed", disabled=True)
                        st.caption("⛔ Día pasado")
                    else:
                        c_info, c_slider = st.columns([1.3, 3], vertical_alignment="center")
                        with c_info:
                            st.markdown(f"**{dia_nombre} {dia_num}**")
                            esta_activo = st.toggle("Disp", value=activo_por_defecto, key=f"tog_{i}", label_visibility="collapsed")
                        
                        with c_slider:
                            val_defecto = ("16:30", "22:00")
                            if horas_guardadas_hoy:
                                horas_solo = sorted([h.split(" ")[1] for h in horas_guardadas_hoy])
                                if horas_solo:
                                    try:
                                        idx_last = OPCIONES_HORAS.index(horas_solo[-1])
                                        idx_end = min(idx_last + 3, len(OPCIONES_HORAS)-1)
                                        val_defecto = (horas_solo[0], OPCIONES_HORAS[idx_end])
                                    except: pass
                            
                            rango = st.select_slider(
                                "R", options=OPCIONES_HORAS, value=val_defecto, 
                                key=f"sl_{i}", label_visibility="collapsed", 
                                disabled=not esta_activo
                            )
                        
                        if esta_activo:
                            nuevos_slots_usuario.extend(generar_slots_desde_seleccion(fecha_str, rango[0], rango[1]))

    # --- ZONA DERECHA: PANEL ---
    with zona_panel:
        st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
        
        if st.button("💾 GUARDAR DISPONIBILIDAD", type="primary", use_container_width=True):
            try:
                st.session_state.db.guardar_disponibilidad(st.session_state.user['id'], nuevos_slots_usuario)
                st.session_state.mis_slots_cache = nuevos_slots_usuario
                st.session_state.needs_match_refresh = True
                popup_guardado(st.session_state.user['nombre'])
            except Exception as e:
                st.error("Error guardando. Espera unos segundos.")

        st.markdown(f"""
            <div style="text-align: center; margin: 15px 0;">
                <a href="https://wa.me/?text=Disponibilidad actualizada." target="_blank" 
                   style="color: #25D366; text-decoration: none; font-size: 0.9rem; font-weight: bold;">
                   📢 Avisar por WhatsApp
                </a>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #eee;'/>", unsafe_allow_html=True)

        st.markdown("##### 🔥 Partidos Posibles")
        
        if 'matches_cache' not in st.session_state or st.session_state.get('needs_match_refresh', False):
            try:
                st.session_state.matches_cache = st.session_state.db.get_partidos_posibles(st.session_state.user['nivel'])
                st.session_state.needs_match_refresh = False
            except: pass 
            
        matches = st.session_state.get('matches_cache', [])
        
        if matches:
            for m in matches:
                with st.container(border=True):
                    st.markdown(f"**{m['id_partido']}**")
                    st.caption(f"👥 {m['jugadores']}")
                    st.markdown(f":green-background[⏰ {', '.join(m['slots'])}]")
                    
                    if st.button("✅ Cerrar", key=m['id_partido'], use_container_width=True):
                        st.session_state.db.cerrar_partido(m['id_partido'])
                        st.session_state.needs_match_refresh = True
                        st.balloons()
                        st.rerun()
        else:
            with st.container(border=True):
                st.info("Sin coincidencias (4/4) aún.")
                st.caption("Rellena tu horario.")

if st.session_state.user is None: login()
else: main_app()