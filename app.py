import streamlit as st
import os

# 1. Configuración de la página (DEBE ser el primer comando de Streamlit)
st.set_page_config(
    page_title="Asistente de Datos Corporativo",
    page_icon="🤖",
    layout="centered"
)

# 2. Carga Segura de Credenciales (ANTES DE IMPORTAR ADK)
# Primero, intentamos cargar .env si estamos en local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass # En producción (Streamlit Cloud) ignoramos esto

# Segundo, si estamos en Streamlit Cloud, extraemos la key de los "Secrets"
# y la forzamos dentro de las variables de entorno para que ADK la detecte.
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

# Validamos que la llave exista antes de continuar
if "GOOGLE_API_KEY" not in os.environ or not os.environ["GOOGLE_API_KEY"]:
    st.error("🚨 Error crítico: No se encontró GOOGLE_API_KEY.")
    st.markdown("Por favor, dirígete a la configuración de la app en Streamlit Cloud -> **Settings** -> **Secrets** e ingresa tu API Key.")
    st.stop()

# 3. Importación segura del agente
# Como ya inyectamos la API key en os.environ, ADK no fallará al inicializar 'sql_worker' y 'root_agent'
from agent import root_agent

# 4. Interfaz de Usuario
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
        with st.spinner("Analizando esquema y consultando base de datos..."):
            try:
                # Ejecución del agente principal de ADK
                response = root_agent.run(prompt)
                
                # Extracción segura de la respuesta de ADK
                if hasattr(response, 'text'):
                    respuesta_texto = response.text
                else:
                    respuesta_texto = str(response)
                
                st.markdown(respuesta_texto)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
                
            except Exception as e:
                mensaje_error = f"**Ocurrió un error en el sistema multiagente:**\n`{str(e)}`"
                st.error(mensaje_error)
                st.session_state.messages.append({"role": "assistant", "content": mensaje_error})