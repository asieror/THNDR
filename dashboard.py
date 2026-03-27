import streamlit as st
import subprocess
import sys
import os
import shlex
import yaml

st.set_page_config(page_title="THNDR Agency OS", page_icon="⚡", layout="wide")

# Estilo para que los logs parezcan una terminal real
st.markdown("""
    <style>
    .terminal-style {
        background-color: #0e1117;
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #444;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ THNDR: Centro de Mando de IA")

with st.sidebar:
    st.header("⚙️ Configuración")
    modelo = st.selectbox("Cerebro Activo:", ["llama-3.3-70b-versatile", "claude-3-5-sonnet-20240620"])
    st.divider()
    if st.button("🧹 Limpiar Pantalla"):
        st.rerun()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💡 Orden de Producción")
    idea = st.text_area("¿Qué vamos a fabricar hoy?", height=200, placeholder="Ej: RunRank - El LoL de los corredores...")
    
    btn_lanzar = st.button("🚀 INICIAR PROCESO", use_container_width=True)

with col2:
    st.subheader("🕵️ Seguimiento de los Agentes")
    # Este espacio se actualizará en tiempo real
    status_placeholder = st.empty()
    log_placeholder = st.empty()

if btn_lanzar:
    if not idea:
        st.warning("El CEO debe dar una orden antes de empezar.")
    else:
        # 1. Crear un contenedor de estado profesional
        with st.status("🏗️ Preparando oficina y configurando agentes...", expanded=True) as status:
            
            # --- NUEVO: Crear archivo de configuración para la nube ---
            config_path = "config2.yaml"
            llm_config = {
                "llm": {
                    "api_type": "openai",
                    "api_key": st.secrets["GROQ_API_KEY"], # Usa el secreto de la nube
                    "base_url": "https://api.groq.com/openai/v1",
                    "model": modelo # El modelo que elegiste en el selectbox
                }
            }
            
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(llm_config, f)
            
            st.write("✅ Configuración de Groq inyectada correctamente.")
            # ---------------------------------------------------------
            st.write("Conectando con los servidores de Groq...")
            
            # 2. Ejecutar el comando y leer la salida línea a 
            # shlex.quote limpia los paréntesis y comillas automáticamente para Linux
            idea_segura = shlex.quote(idea)
            comando = f"metagpt {idea_segura}"
            #comando = f'metagpt "{idea}"'
            process = subprocess.Popen(
                comando, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1
            )

            full_log = ""
            # Bucle para leer la terminal en vivo
            for line in iter(process.stdout.readline, ""):
                full_log += line
                # Mostramos los últimos 15 líneas de logs para no saturar
                log_placeholder.code(line, language="bash")
                
                # Cambiar mensajes del estado según lo que detectemos en el log
                if "PrepareDocuments" in line: status.update(label="📄 Alice está redactando el PRD...", state="running")
                if "WriteDesign" in line: status.update(label="📐 Bob está diseñando la arquitectura...", state="running")
                if "WriteCode" in line: status.update(label="💻 Eve está programando el sistema...", state="running")

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                status.update(label="✅ ¡PROYECTO FINALIZADO CON ÉXITO!", state="complete", expanded=False)
                st.balloons()
                st.success("Revisa la carpeta 'workspace' para ver el código y los documentos.")
            else:
                status.update(label="❌ ERROR EN LA PRODUCCIÓN", state="error")
                st.error(f"La agencia se ha detenido. Código de salida: {return_code}")
                with st.expander("Ver Log de Error Completo"):
                    st.text(full_log)

st.markdown("---")
if os.path.exists("workspace"):
    with st.expander("📂 Explorador de Proyectos"):
        for p in os.listdir("workspace"):
            st.write(f"📁 {p}")
