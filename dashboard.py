import streamlit as st
import subprocess
import os

# Sistema de Login Simple
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("Introduce la clave de acceso de THNDR:", type="password")
        if password == "TU_CONTRASEÑA_SECRETA": # <--- Pon aquí lo que quieras
            st.session_state.authenticated = True
            st.rerun()
        return False
    return True

if not check_password():
    st.stop() # Detiene la app si no hay contraseña

# Configuración de la página
st.set_page_config(page_title="THNDR AI Agency", page_icon="⚡", layout="wide")

st.title("⚡ THNDR: AI Software Factory")
st.markdown("---")

# Barra lateral para configuración
with st.sidebar:
    st.header("Configuración de la Agencia")
    modelo = st.selectbox(
        "Seleccionar Cerebro (LLM):",
        ["llama-3.3-70b-versatile", "llama3.1-70b-versatile", "claude-3-5-sonnet-20240620"]
    )
    st.info("Nota: Asegúrate de que el modelo coincida con tu config2.yaml")

# Cuerpo principal
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💡 Nueva Idea de Negocio")
    idea = st.text_area(
        "Describe lo que quieres que tu empresa desarrolle hoy:",
        placeholder="Ej: Una aplicación SaaS que analice el sentimiento de los comentarios en YouTube para creadores..."
    )
    
    if st.button("🚀 Lanzar Producción"):
        if idea:
            with st.spinner("La agencia está trabajando... Revisa la terminal para ver los logs en vivo."):
                # Comando para ejecutar MetaGPT
                # Usamos sys.executable para usar el python del venv
                try:
                    comando = f'metagpt "{idea}"'
                    # Ejecutamos el comando
                    process = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    
                    st.success("✅ ¡Agentes desplegados! Revisa la carpeta 'workspace' para ver los resultados.")
                except Exception as e:
                    st.error(f"Error al lanzar la agencia: {e}")
        else:
            st.warning("Por favor, introduce una idea primero.")

with col2:
    st.subheader("📁 Proyectos Recientes")
    if os.path.exists("workspace"):
        proyectos = os.listdir("workspace")
        for p in proyectos:
            st.write(f"📁 {p}")
    else:
        st.write("Aún no hay proyectos en el workspace.")

st.markdown("---")
st.caption("THNDR Agency OS v1.0 - Potenciado por MetaGPT y Groq")