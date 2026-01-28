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

# --- POPUP DE CONFIRMAR PARTIDO ---
@st.dialog("Confirmar partido", width="small")
def popup_confirmar_partido(partido):
    """
    Popup para seleccionar día y hora del partido.
    partido: dict con 'id_partido', 'titulo', 'nombres_str', 'coincidencias'
    """
    coincidencias = partido.get('coincidencias', [])
    
    if not coincidencias:
        st.error("No hay fechas disponibles")
        return
    
    # Separar jugadores en 4 líneas (igual que las tarjetas)
    nombres_str = partido.get('nombres_str', '')
    try:
        eq1, eq2 = nombres_str.split(" vs ")
        j1, j2 = eq1.split("/")
        j3, j4 = eq2.split("/")
    except:
        j1, j2, j3, j4 = nombres_str, "", "", ""
    
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem;'>
            <h3 style='margin: 0 0 0.75rem; color: var(--primary);'>{partido['titulo']}</h3>
            <p style='margin: 0; font-size: 0.9rem;'>{j1}</p>
            <p style='margin: 0; font-size: 0.9rem;'>{j2}</p>
            <p style='margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-muted); font-weight: 600;'>vs</p>
            <p style='margin: 0; font-size: 0.9rem;'>{j3}</p>
            <p style='margin: 0; font-size: 0.9rem;'>{j4}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Diccionario para mapear fecha a opciones de hora
    dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
    
    # Formatear fechas para mostrar
    opciones_fecha = []
    for c in coincidencias:
        from datetime import datetime
        fecha_dt = datetime.strptime(c['fecha'], '%Y-%m-%d')
        dia_semana = dias_es[fecha_dt.weekday()]
        fecha_fmt = f"{dia_semana} {fecha_dt.day}/{fecha_dt.month}"
        opciones_fecha.append({
            'fecha': c['fecha'],
            'fecha_fmt': fecha_fmt,
            'hora_inicio': c['hora_inicio'],
            'hora_fin': c['hora_fin']
        })
    
    # Selección de día
    if len(opciones_fecha) == 1:
        # Solo un día - mostrarlo directamente
        fecha_seleccionada = opciones_fecha[0]
        st.markdown(f"""
            <div style='background: #e3f2fd; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;'>
                <p style='margin: 0; font-weight: 600;'>📅 {fecha_seleccionada['fecha_fmt']}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Múltiples días - radio buttons
        st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>📅 Selecciona el día:</p>", unsafe_allow_html=True)
        labels = [o['fecha_fmt'] for o in opciones_fecha]
        idx = st.radio("Día", labels, label_visibility="collapsed", horizontal=True)
        fecha_seleccionada = opciones_fecha[labels.index(idx)]
    
    # Generar opciones de hora (cada 30 min dentro del rango)
    def generar_horas(inicio, fin):
        horas = []
        h_ini, m_ini = map(int, inicio.split(':'))
        h_fin, m_fin = map(int, fin.split(':'))
        min_ini = h_ini * 60 + m_ini
        min_fin = h_fin * 60 + m_fin
        
        # Cada 30 minutos
        current = min_ini
        while current <= min_fin - 90:  # Dejar al menos 90 min para el partido
            h = current // 60
            m = current % 60
            horas.append(f"{h:02d}:{m:02d}")
            current += 30
        
        if not horas:
            horas = [inicio]
        return horas
    
    horas_disponibles = generar_horas(fecha_seleccionada['hora_inicio'], fecha_seleccionada['hora_fin'])
    
    # Selección de hora
    st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>⏰ Hora de inicio:</p>", unsafe_allow_html=True)
    
    if len(horas_disponibles) == 1:
        hora_seleccionada = horas_disponibles[0]
        st.markdown(f"""
            <div style='background: #e3f2fd; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;'>
                <p style='margin: 0; font-weight: 600;'>⏰ {hora_seleccionada}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        hora_seleccionada = st.select_slider(
            "Hora",
            options=horas_disponibles,
            value=horas_disponibles[0],
            label_visibility="collapsed"
        )
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Resumen
    st.markdown(f"""
        <div style='background: #f0fdf4; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; border-left: 3px solid #10b981;'>
            <p style='margin: 0; font-size: 0.85rem;'>
                <strong>Resumen:</strong> {fecha_seleccionada['fecha_fmt']} a las {hora_seleccionada}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # CSS para botón azul
    st.markdown("""
        <style>
        [data-testid="stDialog"] button[kind="primary"] {
            background-color: #1E88E5 !important;
            background: #1E88E5 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.partido_confirmar = None
            st.rerun()
    with col2:
        if st.button("✓ Confirmar", type="primary", use_container_width=True):
            # Guardar en BD
            st.session_state.db.confirmar_partido(
                partido['id_partido'],
                fecha_seleccionada['fecha'],
                hora_seleccionada
            )
            st.session_state.partido_confirmar = None
            st.session_state.needs_match_refresh = True
            st.success("¡Partido programado!")
            time.sleep(1)
            st.rerun()

# --- POPUP DE EDITAR PARTIDO PROGRAMADO ---
@st.dialog("Editar partido", width="small")
def popup_editar_partido(partido):
    """Popup para editar horario o cancelar un partido programado."""
    
    # Separar jugadores para mostrar en 4 líneas
    nombres_str = partido.get('nombres_str', '')
    try:
        eq1, eq2 = nombres_str.split(" vs ")
        j1, j2 = eq1.split("/")
        j3, j4 = eq2.split("/")
    except:
        j1, j2, j3, j4 = nombres_str, "", "", ""
    
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem;'>
            <h3 style='margin: 0 0 0.75rem; color: var(--primary);'>{partido.get('titulo', '')}</h3>
            <p style='margin: 0; font-size: 0.85rem;'>{j1}</p>
            <p style='margin: 0; font-size: 0.85rem;'>{j2}</p>
            <p style='margin: 0.25rem 0; font-size: 0.7rem; color: var(--text-muted); font-weight: 600;'>vs</p>
            <p style='margin: 0; font-size: 0.85rem;'>{j3}</p>
            <p style='margin: 0; font-size: 0.85rem;'>{j4}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='background: #f1f5f9; padding: 0.5rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;'>
            <p style='margin: 0; font-size: 0.8rem; color: #64748b;'>Programado: {partido.get('fecha', '')} a las {partido.get('hora', '')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Estado del popup
    if 'modo_edicion' not in st.session_state:
        st.session_state.modo_edicion = None
    
    # Vista inicial: 2 botones
    if st.session_state.modo_edicion is None:
        # CSS para botones amarillo y rojo
        st.markdown("""
            <style>
            [data-testid="stDialog"] [data-testid="column"]:first-child button {
                background-color: #D4D700 !important;
                color: #1a1a1a !important;
                border: none !important;
            }
            [data-testid="stDialog"] [data-testid="column"]:last-child button {
                background-color: #dc2626 !important;
                color: white !important;
                border: none !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Editar horario", use_container_width=True):
                st.session_state.modo_edicion = 'horario'
                st.rerun()
        with col2:
            if st.button("Cancelar partido", use_container_width=True):
                st.session_state.modo_edicion = 'cancelar'
                st.rerun()
        
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Cerrar", use_container_width=True):
            st.session_state.partido_editar = None
            st.session_state.modo_edicion = None
            st.rerun()
    
    # Vista de editar horario
    elif st.session_state.modo_edicion == 'horario':
        st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>Selecciona nueva fecha:</p>", unsafe_allow_html=True)
        
        # Generar próximas 2 semanas divididas por semana
        from datetime import datetime, timedelta
        hoy = datetime.now()
        dias_es = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
        
        # Separar días por semana
        semana1 = []
        semana2 = []
        
        for i in range(14):
            d = hoy + timedelta(days=i+1)
            dia_info = {
                'fecha': d.strftime('%Y-%m-%d'),
                'label': f"{dias_es[d.weekday()]} {d.day}/{d.month}"
            }
            if i < 7:
                semana1.append(dia_info)
            else:
                semana2.append(dia_info)
        
        # Mostrar en 2 columnas
        col1, col2 = st.columns(2)
        
        # Inicializar fecha seleccionada
        if 'fecha_edit_seleccionada' not in st.session_state:
            st.session_state.fecha_edit_seleccionada = semana1[0]['fecha']
        
        with col1:
            st.markdown("<p style='font-size: 0.75rem; color: #64748b; margin-bottom: 0.25rem;'>Esta semana</p>", unsafe_allow_html=True)
            for dia in semana1:
                if st.button(dia['label'], key=f"sem1_{dia['fecha']}", use_container_width=True):
                    st.session_state.fecha_edit_seleccionada = dia['fecha']
                    st.rerun()
        
        with col2:
            st.markdown("<p style='font-size: 0.75rem; color: #64748b; margin-bottom: 0.25rem;'>Próxima semana</p>", unsafe_allow_html=True)
            for dia in semana2:
                if st.button(dia['label'], key=f"sem2_{dia['fecha']}", use_container_width=True):
                    st.session_state.fecha_edit_seleccionada = dia['fecha']
                    st.rerun()
        
        fecha_nueva = st.session_state.fecha_edit_seleccionada
        # Obtener label de la fecha seleccionada
        todas_fechas = semana1 + semana2
        fecha_label = next((f['label'] for f in todas_fechas if f['fecha'] == fecha_nueva), "")
        
        st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>Hora de inicio:</p>", unsafe_allow_html=True)
        horas = ["16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00"]
        hora_nueva = st.select_slider("Hora", options=horas, value="20:00", label_visibility="collapsed")
        
        st.markdown(f"""
            <div style='background: #f0fdf4; padding: 0.75rem; border-radius: 8px; margin: 1rem 0; border-left: 3px solid #10b981;'>
                <p style='margin: 0; font-size: 0.85rem;'>
                    <strong>Nuevo horario:</strong> {fecha_label} a las {hora_nueva}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Volver", use_container_width=True):
                st.session_state.modo_edicion = None
                st.rerun()
        with col2:
            if st.button("✓ Guardar", type="primary", use_container_width=True):
                st.session_state.db.editar_partido(partido['id_partido'], fecha_nueva, hora_nueva)
                st.session_state.partido_editar = None
                st.session_state.modo_edicion = None
                st.session_state.needs_match_refresh = True
                st.success("¡Horario actualizado!")
                time.sleep(1)
                st.rerun()
    
    # Vista de cancelar
    elif st.session_state.modo_edicion == 'cancelar':
        st.markdown("""
            <div style='background: #fef2f2; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center; border-left: 3px solid #dc2626;'>
                <p style='margin: 0; font-weight: 600; color: #dc2626;'>¿Seguro que quieres cancelar este partido?</p>
                <p style='margin: 0.5rem 0 0; font-size: 0.8rem; color: #64748b;'>El partido volverá a estado PENDIENTE</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Volver", use_container_width=True):
                st.session_state.modo_edicion = None
                st.rerun()
        with col2:
            if st.button("Sí, cancelar", type="primary", use_container_width=True):
                st.session_state.db.cancelar_partido(partido['id_partido'])
                st.session_state.partido_editar = None
                st.session_state.modo_edicion = None
                st.session_state.needs_match_refresh = True
                st.success("Partido cancelado")
                time.sleep(1)
                st.rerun()

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
            # Separar jugadores en 4 líneas
            nombres_str = m.get('nombres_str', '')
            try:
                eq1, eq2 = nombres_str.split(" vs ")
                j1, j2 = eq1.split("/")
                j3, j4 = eq2.split("/")
            except:
                j1, j2, j3, j4 = nombres_str, "", "", ""
            
            # Obtener resumen de coincidencias
            coincidencias = m.get('coincidencias', [])
            primera = coincidencias[0] if coincidencias else {}
            num_dias = len(coincidencias)
            
            # Formatear primera fecha
            fecha_display = primera.get('fecha', '')
            if num_dias > 1:
                fecha_display = f"{num_dias} días disponibles"
            else:
                fecha_display = f"{fecha_display} · {primera.get('hora_inicio', '')} - {primera.get('hora_fin', '')}"
            
            # Card con info del partido - jugadores en 4 líneas
            card_html = f"""
                <div style='background: linear-gradient(135deg, #e3f2fd 0%, #fff 100%); padding: 0.75rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 3px solid #1E88E5;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-weight: 600; font-size: 0.85rem;'>{m['titulo']}</span>
                        <span style='background: #1E88E5; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700;'>DISPONIBLE</span>
                    </div>
                    <p style='font-size: 0.75rem; color: #64748b; margin: 0 0 0.5rem;'>{fecha_display}</p>
                    <div style='font-size: 0.85rem; margin-bottom: 0.75rem; text-align: center;'>
                        <p style='margin: 0;'>{j1}</p>
                        <p style='margin: 0;'>{j2}</p>
                        <p style='margin: 0.25rem 0; font-size: 0.7rem; color: #64748b; font-weight: 600;'>vs</p>
                        <p style='margin: 0;'>{j3}</p>
                        <p style='margin: 0;'>{j4}</p>
                    </div>
                </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Botón que abre el popup - con CSS para forzar azul
            st.markdown("""
                <style>
                div[data-testid="stButton"] > button[kind="primary"] {
                    background-color: #1E88E5 !important;
                    color: white !important;
                    border: none !important;
                }
                div[data-testid="stButton"] > button[kind="primary"]:hover {
                    background-color: #1565C0 !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("Confirmar partido", key=f"btn_confirmar_{m['id_partido']}", type="primary", use_container_width=True):
                st.session_state.partido_confirmar = m
                st.rerun()
    
    # Mostrar popup si hay partido a confirmar
    if st.session_state.get('partido_confirmar'):
        popup_confirmar_partido(st.session_state.partido_confirmar)
    
    # Próximos Partidos - Estilo con degradado amarillo
    if programados:
        st.markdown("<h3 style='margin-top: 1.5rem;'>Próximos partidos</h3>", unsafe_allow_html=True)
        
        for p in programados:
            titulo = p.get('titulo', p.get('id_partido', ''))
            nombres_str = p.get('nombres_str', "")
            
            # Separar jugadores en 4 líneas
            try:
                eq1, eq2 = nombres_str.split(" vs ")
                j1, j2 = eq1.split("/")
                j3, j4 = eq2.split("/")
            except:
                j1, j2, j3, j4 = nombres_str, "", "", ""
            
            card_html = f"""
                <div style='background: linear-gradient(135deg, #f7f8cc 0%, #fff 100%); padding: 0.75rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 3px solid #D4D700;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-weight: 600; font-size: 0.85rem;'>{titulo}</span>
                        <span style='background: #D4D700; color: #1a1a1a; padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700;'>PROGRAMADO</span>
                    </div>
                    <p style='font-size: 0.75rem; color: #64748b; margin: 0 0 0.5rem;'>{p.get('fecha', '')} · {p.get('hora', '')}</p>
                    <div style='font-size: 0.85rem; text-align: center;'>
                        <p style='margin: 0;'>{j1}</p>
                        <p style='margin: 0;'>{j2}</p>
                        <p style='margin: 0.25rem 0; font-size: 0.7rem; color: #64748b; font-weight: 600;'>vs</p>
                        <p style='margin: 0;'>{j3}</p>
                        <p style='margin: 0;'>{j4}</p>
                    </div>
                </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Botón Editar AZUL (igual que Confirmar partido)
            st.markdown("""
                <style>
                div[data-testid="stButton"] > button[kind="primary"] {
                    background-color: #1E88E5 !important;
                    color: white !important;
                    border: none !important;
                }
                div[data-testid="stButton"] > button[kind="primary"]:hover {
                    background-color: #1565C0 !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("Editar", key=f"btn_editar_{p['id_partido']}", type="primary", use_container_width=True):
                st.session_state.partido_editar = p
                st.session_state.modo_edicion = None
                st.rerun()
    
    # Mostrar popup de editar si hay partido a editar
    if st.session_state.get('partido_editar'):
        popup_editar_partido(st.session_state.partido_editar)
    
    # Historial de Partidos Jugados - Con botón para expandir
    st.markdown("<h3 style='margin-top: 1.5rem;'>Historial de partidos</h3>", unsafe_allow_html=True)
    
    if 'mostrar_historial' not in st.session_state:
        st.session_state.mostrar_historial = False
    
    btn_text = "▼ Ver historial de partidos" if not st.session_state.mostrar_historial else "▲ Ocultar historial"
    
    # Usar contenedor con clase única para el botón gris
    st.markdown("""
        <style>
        .historial-btn-container + div button {
            background-color: #e2e8f0 !important;
            background: #e2e8f0 !important;
            color: #64748b !important;
            border: 1px solid #cbd5e1 !important;
        }
        .historial-btn-container + div button:hover {
            background-color: #cbd5e1 !important;
        }
        </style>
        <div class="historial-btn-container"></div>
    """, unsafe_allow_html=True)
    
    if st.button(btn_text, key="toggle_historial", use_container_width=True):
        st.session_state.mostrar_historial = not st.session_state.mostrar_historial
        st.rerun()
    
    if st.session_state.mostrar_historial:
        if jugados:
            for p in jugados:
                titulo = p.get('titulo', p.get('id_partido', ''))
                nombres_str = p.get('nombres_str', "")
                
                # Separar jugadores en 4 líneas
                try:
                    eq1, eq2 = nombres_str.split(" vs ")
                    j1, j2 = eq1.split("/")
                    j3, j4 = eq2.split("/")
                except:
                    j1, j2, j3, j4 = nombres_str, "", "", ""
                
                card_html = f"""
                    <div style='background: linear-gradient(135deg, #e2e8ed 0%, #fff 100%); padding: 0.75rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 3px solid #94a3b8;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                            <span style='font-weight: 600; font-size: 0.85rem;'>{titulo}</span>
                            <span style='background: #94a3b8; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700;'>JUGADO</span>
                        </div>
                        <p style='font-size: 0.7rem; color: #64748b; margin: 0 0 0.5rem;'>{p.get('fecha', '')}</p>
                        <div style='font-size: 0.8rem; text-align: center;'>
                            <p style='margin: 0;'>{j1}</p>
                            <p style='margin: 0;'>{j2}</p>
                            <p style='margin: 0.1rem 0; font-size: 0.65rem; color: #94a3b8; font-weight: 600;'>vs</p>
                            <p style='margin: 0;'>{j3}</p>
                            <p style='margin: 0;'>{j4}</p>
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