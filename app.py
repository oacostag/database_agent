import streamlit as st
import asyncio
import os

# 1. Configuración de la página (DEBE ser el primer comando de Streamlit)
st.set_page_config(
    page_title="Asistente de Datos Corporativo",
    page_icon="🤖",
    layout="centered"
)

# 2. Carga Segura de Credenciales 
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

if "GOOGLE_API_KEY" not in os.environ or not os.environ["GOOGLE_API_KEY"]:
    st.error("🚨 Error crítico: No se encontró GOOGLE_API_KEY.")
    st.stop()

# 3. Importaciones de ADK
# Importamos tu agente y el Runner específico de ADK
from agent import root_agent
from google.adk.runners import InMemoryRunner

# --- 4. MOTOR DE EJECUCIÓN PUENTE PARA STREAMLIT ---
def ejecutar_agente_adk(prompt_usuario: str) -> str:
    """
    Envuelve la ejecución asíncrona de ADK (basada en eventos) 
    para poder usarla en el flujo síncrono de Streamlit.
    """
    async def _run():
        # Inicializamos el Runner inyectando tu agente raíz
        runner = InMemoryRunner(agent=root_agent)
        
        # run_debug() ejecuta toda la cadena (root -> sql_worker -> db -> root)
        # y devuelve una lista con la traza de todos los eventos del proceso
        eventos = await runner.run_debug(prompt_usuario)
        
        texto_final = ""
        
        # Recorremos los eventos para extraer la respuesta definitiva del modelo
        for evento in eventos:
            # Buscamos el evento final marcado por ADK
            if hasattr(evento, "is_final_response") and evento.is_final_response():
                if hasattr(evento, "text") and evento.text:
                    texto_final = evento.text
                elif hasattr(evento, "content"):
                    texto_final = str(evento.content)
            
            # Fallback de seguridad en caso de que is_final_response no esté presente
            # Sobrescribe iterativamente para quedarse con el último bloque de texto generado
            elif hasattr(evento, "text") and evento.text:
                texto_final = evento.text
                
        return texto_final if texto_final else "El agente se ejecutó pero no generó una respuesta textual."

    # Ejecutamos el loop asíncrono desde el hilo principal de Streamlit
    return asyncio.run(_run())
# ---------------------------------------------------

# 5. Interfaz de Usuario
st.title("🤖 Asistente de Datos Corporativo")
st.markdown("Consulta información de la base de datos Sakila mediante lenguaje natural. El agente SQL traducirá tu petición, consultará la base de datos y te dará la respuesta.")

# Inicializar la memoria de la conversación
if "messages" not in st.session_state:
    st.session_state.messages = []

# Renderizar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capturar nuevo prompt del usuario
if prompt := st.chat_input("Ej: ¿Cuáles son las 5 películas más rentables?"):
    
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        # Feedback visual mientras el multi-agente trabaja
        with st.spinner("Orquestando agentes y consultando base de datos..."):
            try:
                # AQUÍ ESTÁ LA MAGIA: Llamamos a nuestra función puente en lugar de hacer un .run() directo
                respuesta_texto = ejecutar_agente_adk(prompt)
                
                st.markdown(respuesta_texto)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
                
            except Exception as e:
                mensaje_error = f"**Ocurrió un error en el sistema multiagente:**\n`{str(e)}`"
                st.error(mensaje_error)
                st.session_state.messages.append({"role": "assistant", "content": mensaje_error})