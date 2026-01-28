import streamlit as st
print("🚀 INICIANDO APP DE STREAMLIT...") # Debug log
import pandas as pd
from backend import PadelDB
from datetime import datetime, timedelta
import pytz
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="PadelLite", 
    layout="centered",  # Centrado para móvil
    initial_sidebar_state="collapsed"
)

# --- CSS PREMIUM MINIMAL ---
st.markdown("""
<style>
    /* === FONTS === */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons+Round');
    
    /* Material Icons Class */
    .material-icons-round {
        font-family: 'Material Icons Round';
        font-weight: normal;
        font-style: normal;
        font-size: 20px;
        display: inline-block;
        line-height: 1;
        text-transform: none;
        letter-spacing: normal;
        word-wrap: normal;
        white-space: nowrap;
        direction: ltr;
        vertical-align: middle;
        -webkit-font-smoothing: antialiased;
        text-rendering: optimizeLegibility;
        -moz-osx-font-smoothing: grayscale;
        font-feature-settings: 'liga';
    }

    /* === VARIABLES === */
    :root {
        --primary: #1E88E5;       /* Padel Blue - Court color */
        --primary-light: #e3f2fd;
        --primary-dark: #1565C0;
        --accent: #D4D700;        /* Padel Yellow - Ball color (softened) */
        --accent-light: #f7f8cc;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg: #f8fafc;
        --bg-card: #ffffff;
        --text: #0f172a;
        --text-muted: #64748b;
        --border: #e2e8f0;
        --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        --radius: 10px;
        --radius-lg: 14px;
    }

    /* === BASE === */
    .stApp {
        background-color: var(--bg) !important;
    }
    
    /* Hide Streamlit Chrome */
    header[data-testid="stHeader"] { display: none !important; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    #MainMenu { visibility: hidden; }
    
    .block-container {
        padding: 1rem 1rem 6rem 1rem !important;
        max-width: 480px !important;
        margin: 0 auto !important;
    }

    /* === TYPOGRAPHY === */
    * {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    h1, h2, h3 {
        font-weight: 700 !important;
        color: var(--text) !important;
        letter-spacing: -0.025em !important;
    }
    
    h1 { font-size: 1.875rem !important; }
    h2 { font-size: 1.5rem !important; }
    h3 { font-size: 1.125rem !important; }
    
    p, span, div, label {
        color: var(--text);
        line-height: 1.5;
    }
    
    .text-muted {
        color: var(--text-muted) !important;
    }

    /* === CARDS === */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow) !important;
        padding: 0.65rem 0.75rem !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
        box-shadow: var(--shadow-md) !important;
        border-color: var(--primary-light) !important;
    }

    /* === BUTTONS === */
    .stButton > button {
        width: 100% !important;
        background: var(--accent) !important;
        color: #1a1a1a !important;
        border: none !important;
        border-radius: var(--radius) !important;
        padding: 0.875rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.9375rem !important;
        letter-spacing: -0.01em !important;
        box-shadow: var(--shadow) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stButton > button:hover {
        background: #c4c900 !important;
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Yellow Spinner - comprehensive selectors */
    .stSpinner > div,
    .stSpinner > div > div,
    .stSpinner svg circle,
    [data-testid="stSpinner"] > div,
    [data-testid="stSpinner"] svg,
    div[data-testid="stMarkdownContainer"] + div svg circle {
        stroke: #D4D700 !important;
        border-color: #D4D700 !important;
        border-top-color: #D4D700 !important;
    }
    /* Dialog/Modal spinner */
    [data-testid="stModal"] .stSpinner > div,
    [role="dialog"] .stSpinner svg circle {
        stroke: #D4D700 !important;
    }
    
    /* Secondary Button (default) */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        color: var(--text-muted) !important;
        box-shadow: none !important;
        border: 1px solid var(--border) !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: var(--bg) !important;
        color: var(--text) !important;
    }

    /* === TOGGLE === */
    .stToggle > label {
        font-weight: 600 !important;
        font-size: 0.9375rem !important;
    }
    
    .stToggle div[role="switch"] {
        background-color: #cbd5e1 !important;
    }
    
    .stToggle div[role="switch"][aria-checked="true"] {
        background-color: var(--accent) !important;
    }

    /* === SLIDER === */
    .stSlider {
        padding: 0 !important;
    }
    .stSlider > div > div > div[data-baseweb="slider"] {
        padding: 0.5rem 0 !important;
    }
    .stSlider [data-testid="stTickBarMin"], 
    .stSlider [data-testid="stTickBarMax"] {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: var(--primary) !important;
    }
    /* Slider Track - Blue */
    .stSlider div[data-baseweb="slider"] div[role="slider"] {
        background: var(--accent) !important;
        border: 2px solid white !important;
        box-shadow: var(--shadow-md) !important;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.2rem !important;
        background: transparent !important;
        padding: 0 !important;
        border-radius: var(--radius) !important;
        display: inline-flex !important;
        width: auto !important;
    }
    
    /* Hide the tab line/border */
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 0.35rem 0.5rem !important;
        font-weight: 600 !important;
        font-size: 0.65rem !important;
        color: #64748b !important;
        background: #e2e8f0 !important;
        white-space: nowrap !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent) !important;
        color: #1a1a1a !important;
        box-shadow: var(--shadow) !important;
    }

    /* === EXPANDER === */
    div[data-testid="stExpander"] {
        background: transparent !important;
        border: none !important;
    }
    
    div[data-testid="stExpander"] details > summary {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        color: var(--text) !important;
    }
    
    /* Fix expander icon */
    div[data-testid="stExpander"] details > summary svg {
        display: inline-block !important;
    }
    /* CRITICAL FIX: Force expander text to not use Material Icons font */
    div[data-testid="stExpander"] details > summary {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    div[data-testid="stExpander"] details > summary span {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    div[data-testid="stExpander"] details > summary p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* === INPUTS === */
    .stTextInput > div > div > input {
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-light) !important;
    }
    
    /* Hide form submit helper text - AGGRESSIVE */
    .stForm small {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    /* Hide the "Press Enter to submit" caption specifically */
    .stForm [class*="InputInstructions"],
    .stForm [class*="instructions"],
    div[data-testid="InputInstructions"],
    .stForm p:has(+ button),
    .stForm div[data-baseweb="form-control-container"] > div:last-child:not(:first-child) {
        display: none !important;
        visibility: hidden !important;
    }
    /* Hide any text with "Enter" */
    .stForm *[class*="Caption"] {
        display: none !important;
    }

    /* === SUCCESS/ERROR STATES === */
    .stSuccess {
        background: #ecfdf5 !important;
        border: 1px solid #a7f3d0 !important;
        border-radius: var(--radius) !important;
        color: #065f46 !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border: 1px solid #fecaca !important;
        border-radius: var(--radius) !important;
        color: #991b1b !important;
    }

    /* === ANIMATIONS === */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .element-container {
        animation: fadeIn 0.3s ease-out backwards;
    }
    
    /* Stagger animation */
    .element-container:nth-child(1) { animation-delay: 0.05s; }
    .element-container:nth-child(2) { animation-delay: 0.1s; }
    .element-container:nth-child(3) { animation-delay: 0.15s; }
    .element-container:nth-child(4) { animation-delay: 0.2s; }
    .element-container:nth-child(5) { animation-delay: 0.25s; }

    /* === CUSTOM CLASSES === */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-primary {
        background: var(--primary-light);
        color: var(--primary-dark);
    }
    
    .badge-success {
        background: #dcfce7;
        color: #166534;
    }
    
    .badge-muted {
        background: var(--bg);
        color: var(--text-muted);
    }
    
    .divider {
        height: 1px;
        background: var(--border);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- LISTA DE HORAS ---
OPCIONES_HORAS = [
    "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", 
    "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", 
    "21:00", "21:30", "22:00", "22:30", "23:00"
]

# --- POPUP DE GUARDADO ---
@st.dialog("Guardando", width="small")
def popup_guardando(db, user_id, user_nombre, id_grupo, slots):
    placeholder = st.empty()
    
    if st.session_state.get('guardado_exito', False):
        with placeholder.container():
            st.markdown("""
                <div style='text-align: center; padding: 2rem;'>
                    <h3 style='margin: 0 0 0.75rem; color: var(--primary);'>¡Disponibilidad guardada!</h3>
                    <p style='color: var(--text-muted); margin: 0 0 1rem; font-size: 0.9rem;'>Si compartes disponibilidad con tus compañeros, te saldrán los partidos en la sección "Partidos disponibles".</p>
                    <p style='color: var(--text); margin: 0 0 1rem; font-size: 0.85rem; background: #fffbeb; padding: 0.75rem; border-radius: 8px; border-left: 3px solid #D4D700;'>📱 <strong>Avisa a tus compañeros por WhatsApp</strong> de que ya has puesto tu disponibilidad para que ellos pongan la suya.</p>
                    <p style='color: var(--text-muted); margin: 0; font-size: 0.8rem;'>Puedes modificar tu disponibilidad en cualquier momento.</p>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("Continuar", type="primary", use_container_width=True):
            st.session_state.mostrar_popup_guardado = False
            st.session_state.guardado_exito = False
            st.rerun()
        return

    with placeholder.container():
        st.markdown("""
            <div style='text-align: center; padding: 2rem;'>
                <div style='width: 48px; height: 48px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem;'></div>
                <p style='color: var(--text-muted); margin: 0;'>Guardando disponibilidad...</p>
            </div>
            <style>@keyframes spin { to { transform: rotate(360deg); } }</style>
        """, unsafe_allow_html=True)
    
    try:
        db.guardar_disponibilidad(user_id, id_grupo, slots)
        st.session_state.mis_slots_cache = slots
        st.session_state.needs_match_refresh = True
        st.session_state.guardado_exito = True
        time.sleep(0.5)
        st.rerun()
            
    except Exception as e:
        placeholder.empty()
        with placeholder.container():
            st.markdown("""
                <div style='text-align: center; padding: 2rem;'>
                    <div style='width: 64px; height: 64px; background: #fef2f2; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem;'>
                        <span class="material-icons-round" style="font-size: 32px; color: #dc2626;">close</span>
                    </div>
                    <h3 style='margin: 0 0 0.5rem; color: #dc2626;'>Error</h3>
                    <p style='color: var(--text-muted); margin: 0;'>No se pudo guardar. Inténtalo de nuevo.</p>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("Cerrar", type="primary", use_container_width=True):
            st.session_state.mostrar_popup_guardado = False
            st.rerun()

def crear_registro_disponibilidad(fecha_str, hora_inicio_str, hora_fin_str):
    return {
        'fecha': fecha_str,
        'hora_inicio': hora_inicio_str,
        'hora_fin': hora_fin_str
    }

# --- INICIALIZACIÓN ---
if 'db' not in st.session_state:
    try: 
        st.session_state.db = PadelDB()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.stop()

if 'user' not in st.session_state: 
    st.session_state.user = None

# Auto-login desde URL
if st.session_state.user is None:
    params = st.query_params
    if "u" in params:
        user_id_url = params["u"]
        n, l = st.session_state.db.get_info_usuario(user_id_url)
        if n:
            st.session_state.user = {'id': user_id_url, 'nombre': n, 'nivel': l}

# --- VISTA: LOGIN ---
def login():
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    # Logo / Título - Amarillo igual que botón y sliders
    st.markdown("""
        <div style='text-align: center; margin-bottom: 3rem;'>
            <h1 style='font-size: 1.8rem !important; font-weight: 800 !important; background: linear-gradient(135deg, #D4D700 0%, #E6E82D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;'>
                DISPONIBILIDAD BULIP PRUEBA
            </h1>
            <p style='color: var(--text-muted); font-size: 0.8rem; margin-top: 0.5rem;'>Hecho por: daniel domingo</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        with st.form("login"):
            st.markdown("<p style='text-align: center; color: var(--text-muted); font-size: 0.875rem; margin-bottom: 1.5rem;'>Introduce tus credenciales</p>", unsafe_allow_html=True)
            
            u = st.text_input("Usuario", placeholder="Tu ID de usuario", label_visibility="collapsed")
            p = st.text_input("Contraseña", type="password", placeholder="Contraseña", label_visibility="collapsed")
            
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            
            if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                with st.spinner("Verificando..."):
                    n, l = st.session_state.db.validar_login(u, p)
                if n:
                    st.session_state.user = {'id': u, 'nombre': n, 'nivel': l}
                    st.query_params["u"] = u 
                    st.rerun()
                else: 
                    st.error("Credenciales incorrectas")

# --- VISTA: MAIN APP ---
def main_app():
    # Cache de disponibilidad
    if 'mis_slots_cache' not in st.session_state:
        try:
            st.session_state.mis_slots_cache = st.session_state.db.get_mis_horas(st.session_state.user['id'])
        except:
            st.error("Error de conexión")
            return

    mis_slots_guardados = st.session_state.mis_slots_cache
    nuevos_registros = []
    
    # === HEADER (sin botón de salir) ===
    nombre_completo = st.session_state.user['nombre']
    st.markdown(f"""
        <div style='margin-bottom: 0.75rem;'>
            <span style='color: var(--text-muted); font-size: 0.75rem;'>Hola, </span>
            <span style='font-size: 1.2rem; font-weight: 700;'>{nombre_completo}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # === CALENDARIO ===
    zona_madrid = pytz.timezone('Europe/Madrid')
    hoy = datetime.now(zona_madrid)
    lunes_esta_semana = hoy - timedelta(days=hoy.weekday())
    
    # Selector de semanas
    st.markdown("<h3 style='margin-bottom: 0.5rem;'>Tu disponibilidad</h3>", unsafe_allow_html=True)
    st.markdown("""
        <p style='color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem; line-height: 1.5;'>
            Indica tu hora de inicio y fin de disponibilidad. 
            <span style='color: var(--text); font-weight: 500;'>La hora final es cuando termina el partido</span>
            (Ej: Si pones 22:00, el partido empieza a las 20:30).
        </p>
    """, unsafe_allow_html=True)
    
    semanas = []
    for i in range(4):
        inicio = lunes_esta_semana + timedelta(days=7*i)
        fin = inicio + timedelta(days=6)
        semanas.append((inicio, fin, i*7))
    
    # Tabs para semanas - usar fechas como etiquetas
    meses_cortos = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 
                    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
    tab_labels = []
    for inicio, fin, _ in semanas:
        if inicio.month == fin.month:
            tab_labels.append(f"{inicio.day}-{fin.day} {meses_cortos[inicio.month]}")
        else:
            tab_labels.append(f"{inicio.day}{meses_cortos[inicio.month]}-{fin.day}{meses_cortos[fin.month]}")
    tabs = st.tabs(tab_labels)
    
    dias_es = {"Mon": "Lunes", "Tue": "Martes", "Wed": "Miércoles", "Thu": "Jueves", "Fri": "Viernes", "Sat": "Sábado", "Sun": "Domingo"}
    meses_completos = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 
                    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    
    for tab_idx, tab in enumerate(tabs):
        with tab:
            inicio_sem, fin_sem, offset = semanas[tab_idx]
            
            # No need for header inside tab since tab label already shows dates
            
            
            # Días de la semana
            for dia_idx in range(7):
                i = offset + dia_idx
                fecha = lunes_esta_semana + timedelta(days=i)
                fecha_str = fecha.strftime('%Y-%m-%d')
                es_pasado = fecha.date() < hoy.date()
                
                dia_nombre = dias_es[fecha.strftime('%a')]
                dia_num = fecha.day
                
                registro_hoy = next((r for r in mis_slots_guardados if r['fecha'] == fecha_str), None)
                activo_por_defecto = registro_hoy is not None
                
                with st.container(border=True):
                    if es_pasado:
                        st.markdown(f"<span style='color: var(--text-muted);'>{dia_nombre} {dia_num}</span>", unsafe_allow_html=True)
                    else:
                        col1, col2 = st.columns([1.2, 2])
                        with col1:
                            activo = st.toggle(f"{dia_nombre} {dia_num}", value=activo_por_defecto, key=f"t_{i}")
                        
                        if activo:
                            with col2:
                                val = (registro_hoy['hora_inicio'], registro_hoy['hora_fin']) if registro_hoy else ("17:00", "21:00")
                                rango = st.select_slider("Horario", options=OPCIONES_HORAS, value=val, key=f"s_{i}", label_visibility="collapsed")
                                nuevos_registros.append(crear_registro_disponibilidad(fecha_str, rango[0], rango[1]))
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # === BOTÓN GUARDAR ===
    if st.button("Guardar disponibilidad", type="primary", use_container_width=True):
        st.session_state.mostrar_popup_guardado = True

    if st.session_state.get('mostrar_popup_guardado', False):
        popup_guardando(
            st.session_state.db, 
            st.session_state.user['id'], 
            st.session_state.user['nombre'], 
            st.session_state.user.get('nivel', ''),
            nuevos_registros
        )
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # === PARTIDOS ===
    if 'partidos_cache' not in st.session_state or st.session_state.get('needs_match_refresh', False):
        with st.spinner("Cargando partidos..."):
            try:
                user_id = st.session_state.user['id']
                st.session_state.disponibles_cache = st.session_state.db.get_partidos_disponibles(user_id)
                partidos_data = st.session_state.db.get_partidos_usuario(user_id)
                st.session_state.programados_cache = partidos_data.get('programados', [])
                st.session_state.jugados_cache = partidos_data.get('jugados', [])
                st.session_state.partidos_cache = True
                st.session_state.needs_match_refresh = False
            except: 
                pass
        
    matches = st.session_state.get('disponibles_cache', [])
    programados = st.session_state.get('programados_cache', [])
    jugados = st.session_state.get('jugados_cache', [])
    
    # Partidos Disponibles - Cards con degradado azul
    if matches:
        st.markdown("<h3>Partidos disponibles</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748b; font-size: 0.8rem; margin-bottom: 1rem;'>Partidos donde coincides en disponibilidad con tus compañeros</p>", unsafe_allow_html=True)
        
        for m in matches:
            # Separar parejas
            try:
                eq1, eq2 = m['nombres_str'].split(" vs ")
            except:
                eq1, eq2 = m['nombres_str'], ""
            
            # Card con botón azul integrado
            card_html = f"""
                <div style='background: linear-gradient(135deg, #e3f2fd 0%, #fff 100%); padding: 0.75rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 3px solid #1E88E5;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-weight: 600; font-size: 0.85rem;'>{m['titulo']}</span>
                        <span style='background: #1E88E5; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700;'>DISPONIBLE</span>
                    </div>
                    <p style='font-size: 0.75rem; color: #64748b; margin: 0 0 0.5rem;'>{m['fecha']} · {m['hora_inicio']} - {m['hora_fin']}</p>
                    <div style='font-size: 0.85rem; margin-bottom: 0.75rem;'>
                        <p style='margin: 0; font-weight: 500;'>{eq1}</p>
                        <p style='margin: 0.15rem 0; font-size: 0.7rem; color: #64748b; font-weight: 600;'>vs</p>
                        <p style='margin: 0; font-weight: 500;'>{eq2}</p>
                    </div>
                </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Usar st.form para aislar el botón y poder aplicar CSS específico
            partido_id = m['id_partido']
            with st.form(key=f"form_{partido_id}", border=False):
                # CSS ultra-específico para botón azul
                st.markdown("""
                    <style>
                    /* Botón azul FORZADO */
                    form[data-testid="stForm"] button,
                    form button[kind="primary"],
                    [data-testid="stFormSubmitButton"] button,
                    [data-testid="stFormSubmitButton"] > button[kind="primary"],
                    div[data-testid="stForm"] button[type="submit"],
                    .stForm button {
                        background-color: #1E88E5 !important;
                        background: #1E88E5 !important;
                        color: white !important;
                        border: none !important;
                    }
                    form[data-testid="stForm"] button:hover,
                    [data-testid="stFormSubmitButton"] button:hover {
                        background-color: #1565C0 !important;
                        background: #1565C0 !important;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                submitted = st.form_submit_button("Confirmar partido", type="primary", use_container_width=True)
                if submitted:
                    st.session_state.db.confirmar_partido(m['id_partido'], m['fecha'], f"{m['hora_inicio']}")
                    st.session_state.needs_match_refresh = True
                    st.success("¡Partido confirmado!")
                    time.sleep(1)
                    st.rerun()
    
    # Próximos Partidos - Estilo con degradado amarillo
    if programados:
        st.markdown("<h3 style='margin-top: 1.5rem;'>Próximos partidos</h3>", unsafe_allow_html=True)
        
        for p in programados:
            titulo = p.get('titulo', p.get('id_partido', ''))
            nombres = p.get('nombres_str', "")
            
            # Separar parejas para mostrar en 3 líneas
            try:
                eq1, eq2 = nombres.split(" vs ")
            except:
                eq1, eq2 = nombres, ""
            
            card_html = f"""
                <div style='background: linear-gradient(135deg, #f7f8cc 0%, #fff 100%); padding: 0.75rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 3px solid #D4D700;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-weight: 600; font-size: 0.85rem;'>{titulo}</span>
                        <span style='background: #D4D700; color: #1a1a1a; padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700;'>PROGRAMADO</span>
                    </div>
                    <p style='font-size: 0.75rem; color: #64748b; margin: 0 0 0.5rem;'>{p.get('fecha', '')} · {p.get('hora', '')}</p>
                    <div style='font-size: 0.85rem;'>
                        <p style='margin: 0; font-weight: 500;'>{eq1}</p>
                        <p style='margin: 0.15rem 0; font-size: 0.7rem; color: #64748b; font-weight: 600;'>vs</p>
                        <p style='margin: 0; font-weight: 500;'>{eq2}</p>
                    </div>
                </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
    
    # Historial de Partidos Jugados - Con botón para expandir
    st.markdown("<h3 style='margin-top: 1.5rem;'>Historial de partidos</h3>", unsafe_allow_html=True)
    
    if 'mostrar_historial' not in st.session_state:
        st.session_state.mostrar_historial = False
    
    btn_text = "▼ Ver historial de partidos" if not st.session_state.mostrar_historial else "▲ Ocultar historial"
    st.markdown(f"""
        <style>
        div[data-testid="stButton"][key="toggle_historial"] button {{
            background: linear-gradient(135deg, #f1f5f9 0%, #fff 100%) !important;
            border: 1px solid #e2e8f0 !important;
            color: #64748b !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    if st.button(btn_text, key="toggle_historial", use_container_width=True):
        st.session_state.mostrar_historial = not st.session_state.mostrar_historial
        st.rerun()
    
    if st.session_state.mostrar_historial:
        if jugados:
            for p in jugados:
                titulo = p.get('titulo', p.get('id_partido', ''))
                nombres = p.get('nombres_str', "")
                
                # Separar parejas
                try:
                    eq1, eq2 = nombres.split(" vs ")
                except:
                    eq1, eq2 = nombres, ""
                
                card_html = f"""
                    <div style='background: linear-gradient(135deg, #e2e8ed 0%, #fff 100%); padding: 0.75rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 3px solid #94a3b8;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                            <span style='font-weight: 600; font-size: 0.85rem;'>{titulo}</span>
                            <span style='background: #94a3b8; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700;'>JUGADO</span>
                        </div>
                        <p style='font-size: 0.7rem; color: #64748b; margin: 0 0 0.5rem;'>{p.get('fecha', '')}</p>
                        <div style='font-size: 0.8rem;'>
                            <p style='margin: 0;'>{eq1}</p>
                            <p style='margin: 0.1rem 0; font-size: 0.65rem; color: #94a3b8; font-weight: 600;'>vs</p>
                            <p style='margin: 0;'>{eq2}</p>
                        </div>
                    </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #64748b; font-size: 0.85rem; text-align: center;'>No hay partidos jugados aún</p>", unsafe_allow_html=True)

# === ROUTER ===
if st.session_state.user is None:
    login()
else:
    main_app()