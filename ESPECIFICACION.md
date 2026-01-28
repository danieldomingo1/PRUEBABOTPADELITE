# PadelLite - Especificación Técnica

## 📋 Resumen del Proyecto

**Propósito**: Webapp para facilitar la coordinación de disponibilidad entre jugadores de padel y programar partidos de liga.

**Alcance actual**: 1 grupo de 9 personas (M2)
**Escalabilidad futura**: 14 grupos masculinos (M1-M14) + 12 femeninos (F1-F12) = 26 grupos

---

## 🎯 Funcionalidad Principal

### Flujo de Usuario
1. **Login** → Usuario introduce ID y contraseña
2. **Disponibilidad** → Marca días/horas disponibles (próximas 4 semanas)
3. **Partidos Disponibles** → Ve jornadas donde los 4 jugadores coinciden
4. **Confirmar** → Cuadran por WhatsApp y confirman en la app
5. **Historial** → Ve partidos jugados

---

## 🏗️ Estructura de Base de Datos (Google Sheets)

### Hoja: USUARIOS
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| ID_USUARIO | Iniciales + 01/02 | DDR01 |
| NOMBRE | Nombre completo | Daniel Domingo Ruiz |
| EMAIL | Email | ejemplo@mail.com |
| TELEFONO | Teléfono | 600123456 |
| PASSWORD | Contraseña | 1234 |
| GENERO | M/F | M |
| NIVEL | Grupo/Liga | M2 |
| ACTIVO | TRUE/FALSE | TRUE |

### Hoja: DISPONIBILIDAD
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| ID_USUARIO | FK a USUARIOS | DDR01 |
| FECHA | Fecha YYYY-MM-DD | 2026-01-29 |
| HORA_INICIO | Hora inicio HH:MM | 19:00 |
| HORA_FIN | Hora fin HH:MM | 22:00 |
| NIVEL | Grupo del usuario | M2 |

### Hoja: PARTIDOS
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| ID_PARTIDO | Identificador único | P-M2-J4-01 |
| ID_GRUPO | Grupo/Liga | M2 |
| FASE | Fase de liga | 25/26-F1 |
| JUGADOR_1 | FK a USUARIOS | DDR01 |
| JUGADOR_2 | FK a USUARIOS | SDG01 |
| JUGADOR_3 | FK a USUARIOS | MAO01 |
| JUGADOR_4 | FK a USUARIOS | RRC01 |
| FECHA | Fecha programada | 2026-01-30 |
| HORA | Hora programada | 20:30 |
| RESULTADO | Resultado (ej: 2-0) | 2-0 |
| ESTADO | PENDIENTE/PROGRAMADO/JUGADO | PENDIENTE |

---

## 🔄 Lógica de Negocio

### Estados de Partido (solo 3)
- PENDIENTE → Jornada creada pero no programada
- PROGRAMADO → Fecha/hora confirmada, pendiente de jugar
- JUGADO → Partido ya disputado

### Partidos Disponibles
Un partido aparece en esta sección si:
1. El usuario logueado es JUGADOR_1, _2, _3 o _4
2. El estado es PENDIENTE
3. Los 4 jugadores tienen disponibilidad que se solapa:
   - Misma fecha
   - Horarios con >=60 min de solapamiento

### Próximos Partidos
Un partido aparece aquí si:
1. El usuario logueado es uno de los 4 jugadores
2. El estado es PROGRAMADO

### Historial
Un partido aparece aquí si:
1. El usuario logueado es uno de los 4 jugadores
2. El estado es JUGADO

---

## 🔢 Algoritmo de Solapamiento

Para detectar si 4 jugadores coinciden:

```
Para cada partido PENDIENTE donde usuario es jugador:
  jugadores = [JUGADOR_1, JUGADOR_2, JUGADOR_3, JUGADOR_4]
  
  Para cada fecha futura:
    solapamiento = calcular_solapamiento(
      disponibilidad[jugador1],
      disponibilidad[jugador2],
      disponibilidad[jugador3],
      disponibilidad[jugador4]
    )
    
    Si solapamiento >= 60 minutos:
      → Partido disponible para esa fecha/hora
```

### Función Solapamiento
```
inicio_comun = MAX(inicio_1, inicio_2, inicio_3, inicio_4)
fin_comun = MIN(fin_1, fin_2, fin_3, fin_4)
duracion = fin_comun - inicio_comun

Si duracion >= 60 min → HAY COINCIDENCIA
```

---

## 📱 Interfaz de Usuario

### Pantalla Login
- Campo usuario (ID)
- Campo contraseña
- Botón entrar

### Pantalla Principal
1. Header: Saludo con nombre
2. Disponibilidad: Calendario 4 semanas con toggles/sliders
3. Botón Guardar
4. Partidos Disponibles: Cards azules con botón confirmar
5. Próximos Partidos: Cards amarillas
6. Historial: Desplegable con cards grises

---

## 🚀 Roadmap Futuro (no implementar ahora)
- [ ] Cancelar partido programado (vuelve a PENDIENTE)
- [ ] Selección de fecha/hora al confirmar partido
- [ ] Transición automática PROGRAMADO → JUGADO por fecha
- [ ] Integración WhatsApp (compartir)
- [ ] Notificaciones push
- [ ] Panel admin multi-grupo

---

## 📁 Estructura de Archivos

```
BOT PADELITE/
├── .streamlit/config.toml  # Config Streamlit
├── .gitignore              # Exclusiones git
├── README.md               # Documentación
├── app.py                  # Frontend Streamlit
├── backend.py              # Lógica + conexión BD
├── credentials.json        # Credenciales (solo local)
└── requirements.txt        # Dependencias Python
```

---

*Documento creado: 2026-01-28*
