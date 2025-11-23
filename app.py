import streamlit as st
import time

# ==========================================
# DEFINICIÓN DE LA MÁQUINA DE TURING
# L = { 0^n 1^m 0^n | n >= 0, m >= 0 }
# ==========================================

class TuringMachine:
    """
    Simula una Máquina de Turing para el lenguaje L = { 0^n 1^m 0^n }.
    
    Regla: Empareja cada '0' inicial con un '0' final, dejando los '1's del centro
    sin modificar (si existen).
    """
    def __init__(self, tape, blank="_"):
        # Inicializa la cinta con la entrada del usuario y el símbolo de espacio en blanco
        self.tape = list(tape) + [blank] * 10
        self.blank = blank
        self.head = 0
        self.state = "q0"
        self.final_states = {"q_accept"}
        self.history = [] # Almacena el historial de transiciones
        
        # TRANSICIONES PARA L = { 0^n 1^m 0^n }
        # Alfabeto de la cinta: {0, 1, X, _}
        self.transitions = {
            # q0: Buscar el primer '0' no marcado (o ir a q_check_ones si se encuentra un '1')
            ("q0", "0"): ("q1", "X", "R"),      # Encontró '0', lo marca con 'X', va a buscar '0' final (q1)
            ("q0", "X"): ("q0", "X", "R"),      # Pasa sobre 'X's ya marcados
            ("q0", "1"): ("q_check_ones", "1", "R"), # Encontró '1', verifica el centro y la cola (q_check_ones)
            ("q0", "_"): ("q_accept", "_", "R"), # Cadena vacía o todos los '0's emparejados (n=0)

            # q1: Recorrer a la derecha, pasando '0', '1', 'X', hasta encontrar el blanco
            ("q1", "0"): ("q1", "0", "R"),      # Pasa por '0's
            ("q1", "1"): ("q1", "1", "R"),      # Pasa por '1's (el centro 1^m)
            ("q1", "X"): ("q1", "X", "R"),      # Pasa por 'X's (si n > 1 y ya marcó algunos)
            ("q1", "_"): ("q2", "_", "L"),      # Encontró el blanco, regresa a marcar el último '0' (q2)

            # q2: Marcar el '0' final correspondiente. DEBE saltar las 'X' que ya marcó en pasadas anteriores.
            ("q2", "0"): ("q_return", "X", "L"),# Encontró '0' final, lo marca con 'X', regresa (q_return)
            ("q2", "1"): ("q_reject", "1", "L"),# Error: No hay '0' final.
            ("q2", "X"): ("q2", "X", "L"),      # FIX 1: Continúa moviéndose a la izquierda sobre 'X's marcadas.
            ("q2", "_"): ("q_reject", "_", "R"), # Error: La cinta ya está vacía

            # q_return: Volver al inicio (al primer '_' o 'X')
            ("q_return", "0"): ("q_return", "0", "L"),
            ("q_return", "1"): ("q_return", "1", "L"),
            ("q_return", "X"): ("q_return", "X", "L"),
            ("q_return", "_"): ("q0", "_", "R"), # Volvió al inicio, empezar de nuevo con q0

            # q_check_ones: Verificar el centro (solo 1’s) y pasar a verificar la cola de 'X's.
            ("q_check_ones", "1"): ("q_check_ones", "1", "R"), # Pasa sobre los '1's centrales
            ("q_check_ones", "0"): ("q_reject", "0", "R"),     # Error: Quedó un '0' suelto
            ("q_check_ones", "X"): ("q_final_scan", "X", "R"), # FIX 2: Found the end of 1^m. Start scanning X^n.
            ("q_check_ones", "_"): ("q_accept", "_", "R"),     # Aceptación: Si n=0, acepta 1^m (m>0).

            # q_final_scan: (Nuevo estado) Verifica que solo queden 'X's hasta el blank.
            ("q_final_scan", "X"): ("q_final_scan", "X", "R"), # Pass over final X^n block
            ("q_final_scan", "_"): ("q_accept", "_", "R"),     # Aceptación final: $X^n 1^m X^n\_$
            ("q_final_scan", "0"): ("q_reject", "0", "R"),     # Error: Unmarked 0 found
            ("q_final_scan", "1"): ("q_reject", "1", "R"),     # Error: Unmarked 1 found
        }

    def step(self):
        """Ejecuta una única transición de la MT."""
        symbol = self.tape[self.head]
        # Asegurarse de que la cinta tenga un símbolo en la posición del cabezal
        while self.head >= len(self.tape):
            self.tape.append(self.blank)
            
        symbol = self.tape[self.head]
        key = (self.state, symbol)

        if self.state in self.final_states or self.state == "q_reject":
            return # Detiene la ejecución si ya está en un estado final

        if key not in self.transitions:
            # Transición no definida -> Rechazo
            new_state, new_symbol, move = "q_reject", symbol, "R"
            self.state = new_state
            
            # Formato de la transición para el historial
            transition_str = f"({key[0]}, {key[1]}) → ({new_state}, {new_symbol}, {move}) [NO DEFINIDA]"
            self.history.append(transition_str)
            return

        # Aplicar la transición
        new_state, new_symbol, move = self.transitions[key]
        
        # Registrar en el historial
        transition_str = f"({self.state}, {symbol}) → ({new_state}, {new_symbol}, {move})"
        self.history.append(transition_str)
        
        # Actualizar cinta y estado
        self.tape[self.head] = new_symbol
        self.state = new_state

        # Mover cabezal
        if move == "R":
            self.head += 1
            # Extender la cinta si el cabezal se mueve al último elemento
            if self.head == len(self.tape):
                 self.tape.append(self.blank)
        elif move == "L":
            self.head -= 1
        
        # Extender la cinta a la izquierda si el cabezal se sale del límite
        if self.head < 0:
            self.tape.insert(0, self.blank)
            self.head = 0
            
# ==========================================
# VISUALIZACIÓN STREAMLIT CON ESTILOS
# ==========================================

def render_tape_html(tape, head_position):
    """Genera el código HTML/CSS para la visualización estilizada de la cinta (FIXED: CSS sin comentarios/multilínea)."""
    
    # CSS para los bloques de la cinta (Simplificado y sin comentarios)
    cell_style_base = "display:flex;justify-content:center;align-items:center;width:40px;height:50px;border-radius:8px;font-size:24px;font-weight:700;margin:2px;color:#E0E0E0;background-color:#262626;border:2px solid #555555;box-shadow:0 4px 6px rgba(0,0,0,0.3);transition:all 0.3s ease-in-out;"
    
    # CSS para el bloque bajo el cabezal (activo) (Simplificado y sin comentarios)
    cell_style_active = "border-color:#F63366;background-color:#4B1C2B;color:#FFFFFF;box-shadow:0 0 10px rgba(246,51,102,0.8);transform:scale(1.1);"
    
    tape_html = '<div style="display: flex; justify-content: center; padding: 20px 0;">'
    
    # Definir cuántas celdas mostrar
    window_size = 8
    start = max(0, head_position - window_size)
    end = min(len(tape), head_position + window_size + 1)

    for i in range(start, end):
        symbol = tape[i]
        
        # Usar colores para los símbolos marcados
        symbol_display = symbol
        color_style = ""
        if symbol == 'X':
            color_style = "color:#20C997;border-color:#20C997;" # Verde (marca de 0)
        elif symbol == 'Y':
            color_style = "color:#FFC107;border-color:#FFC107;" # Amarillo 
        elif symbol == '_':
            symbol_display = "B" # Mostrar Blanco como 'B'
            color_style = "color:#555555;"

        # Aplicar el estilo de cabezal si la posición coincide
        if i == head_position:
            style = cell_style_base + cell_style_active
        else:
            style = cell_style_base + color_style
        
        tape_html += f'<div style="{style}">{symbol_display}</div>'
    
    tape_html += '</div>'
    return tape_html

# --- UI Principal de Streamlit ---

st.set_page_config(layout="wide")
st.title("Simulador de Máquina de Turing Avanzado")
st.markdown("""
**Lenguaje de la Máquina de Turing:** $L = \{ 0^n 1^m 0^n \mid n \geq 0, m \geq 0 \}$
\n*Acepta cadenas con $n$ ceros iniciales, seguidos por $m$ unos, seguidos por $n$ ceros finales (e.g., `010`, `0011100`, `11`). Los símbolos 'X' se usan como marcas.*
""")

# Componentes de entrada
col1, col2 = st.columns([2, 1])

with col1:
    user_input = st.text_input("Ingresa la cadena (solo '0's y '1's):", "00100")

with col2:
    start = st.button("▶️ Ejecutar Simulación", type="primary")

# Contenedores para la actualización en vivo
st.markdown("---")
st.subheader("Estado Actual de la Máquina")
tape_placeholder = st.empty()
state_placeholder = st.empty()
result_placeholder = st.empty()

st.markdown("---")
st.subheader("Historial de Transiciones")
history_placeholder = st.empty()


if start:
    # Validación de entrada
    if not all(c in '01' for c in user_input):
        st.error("Error: La cadena solo debe contener los símbolos '0' y '1'.")
        start = False
    
    if start:
        mt = TuringMachine(user_input)
        
        # Inicializar el historial
        history_text = "-- Inicio de simulación --\n"
        history_placeholder.code(history_text)
        
        # Contar los pasos para mostrar en el historial
        step_count = 0
        max_steps = 500 # Límite de seguridad
        
        # FIX: Se cambia el bucle for por un bucle while para contar con precisión el número de transiciones.
        while mt.state not in mt.final_states and mt.state != "q_reject" and step_count < max_steps:
            
            # 1. Dibujar el estado ANTES de ejecutar el paso
            tape_html = render_tape_html(mt.tape, mt.head)
            tape_placeholder.markdown(tape_html, unsafe_allow_html=True)
            state_placeholder.markdown(f"**Estado:** `{mt.state}` | **Cabezal en:** `{mt.tape[mt.head]}`")
            
            # 2. Ejecutar el paso
            mt.step()
            step_count += 1 # Cuenta la transición ejecutada
            
            # 3. Actualizar el historial con el paso ejecutado
            if len(mt.history) > 0:
                last_transition = mt.history[-1]
                history_text += f"Paso {step_count}: {last_transition}\n"
                history_placeholder.code(history_text)

            # 4. Pausa para la animación
            time.sleep(0.4)
        
        # Actualizar la cinta y el estado UNA ÚLTIMA VEZ para mostrar el estado final.
        tape_html = render_tape_html(mt.tape, mt.head)
        tape_placeholder.markdown(tape_html, unsafe_allow_html=True)
        state_placeholder.markdown(f"**Estado:** `{mt.state}` | **Cabezal en:** `{mt.tape[mt.head]}`")

        # 5. Imprimir resultado final
        if mt.state in mt.final_states:
            result_placeholder.success(f"**>> CADENA ACEPTADA** (Llegó al estado {mt.state} en {step_count} pasos).")
        elif mt.state == "q_reject":
            result_placeholder.error(f"**>> CADENA RECHAZADA** (Llegó al estado {mt.state} en {step_count} pasos).")
        else:
            result_placeholder.warning(f"**AVISO:** La simulación se detuvo después de {max_steps} pasos para evitar un bucle infinito.")