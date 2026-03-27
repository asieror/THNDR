import streamlit as st
import subprocess
import os
import shlex
import yaml
import zipfile
import shutil
from pathlib import Path

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="THNDR Agency OS v3.0", page_icon="⚡", layout="wide")

# Estilo de Terminal
st.markdown("""
    <style>
    .stCodeBlock { background-color: #0e1117 !important; }
    .stTextArea textarea { font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---
def preparar_workspace_desde_zip(archivo_zip):
    """Limpia el workspace actual y extrae el contenido del ZIP"""
    workspace_path = "workspace"
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    os.makedirs(workspace_path)
    
    with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
        zip_ref.extractall(workspace_path)
    return True

# --- INTERFAZ - BARRA LATERAL ---
st.title("⚡ THNDR: Centro de Mando e Iteración")

with st.sidebar:
    st.header("⚙️ Configuración")
    modelo = st.selectbox("Cerebro Activo:", [
        "llama-3.3-70b-versatile", 
        "claude-3-5-sonnet-20240620"
    ])
    
    st.divider()
    
    st.subheader("📂 Memoria de Proyecto")
    st.info("Sube un .zip de un proyecto anterior para iterar sobre él.")
    archivo_subido = st.file_uploader("Cargar proyecto (.zip)", type=["zip"])
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🧹 Limpiar Todo"):
            if os.path.exists("workspace"):
                shutil.rmtree("workspace")
            st.rerun()

# --- INTERFAZ - CUERPO PRINCIPAL ---
col_input, col_status = st.columns([1, 1])

with col_input:
    st.subheader("💡 Orden de Producción")
    idea = st.text_area(
        "¿Qué vamos a fabricar o mejorar hoy?", 
        height=250, 
        placeholder="Ej: 'Añade un sistema de logros al código de RunRank que ya está en el workspace...'"
    )
    
    # Interruptor clave para la iteración
    modo_incremental = st.toggle("🔄 Modo Incremental (No borrar, mejorar existente)", value=True)
    
    btn_lanzar = st.button("🚀 EJECUTAR ACCIÓN", use_container_width=True)

with col_status:
    st.subheader("🕵️ Seguimiento de los Agentes")
    status_placeholder = st.empty()
    log_placeholder = st.empty()

# --- LÓGICA DE EJECUCIÓN ---
if btn_lanzar:
    if not idea:
        st.warning("El CEO debe dar una orden antes de empezar.")
    else:
        with st.status("🏗️ Preparando oficina...", expanded=True) as status:
            
            # 1. Gestionar el ZIP si existe
            if archivo_subido:
                st.write("📦 Extrayendo proyecto base en el workspace...")
                preparar_workspace_desde_zip(archivo_subido)

            # 2. Inyectar Configuración de Groq (Ruta Sagrada)
            home = Path.home()
            config_dir = home / ".metagpt"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "config2.yaml"
            
            llm_config = {
                "llm": {
                    "api_type": "openai",
                    "api_key": st.secrets["GROQ_API_KEY"],
                    "base_url": "https://api.groq.com/openai/v1",
                    "model": modelo
                }
            }
            
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(llm_config, f)
            
            st.write(f"✅ Configuración inyectada.")

            # 3. Construir comando (con o sin --inc)
            idea_segura = shlex.quote(idea)
            comando = f"metagpt {idea_segura}"
            if modo_incremental:
                comando += " --inc"
                st.write("🔄 Trabajando en modo incremental sobre archivos existentes.")

            # 4. Lanzar Proceso
            process = subprocess.Popen(
                comando, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1
            )

            full_log = ""
            for line in iter(process.stdout.readline, ""):
                full_log += line
                log_placeholder.code(line, language="bash")
                
                # Actualización de mensajes según el log
                if "PrepareDocuments" in line: status.update(label="📄 Alice analizando contexto/mejoras...", state="running")
                if "WriteDesign" in line: status.update(label="📐 Bob rediseñando arquitectura...", state="running")
                if "WriteCode" in line: status.update(label="💻 Eve editando el código...", state="running")

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                status.update(label="✅ TAREA COMPLETADA", state="complete", expanded=False)
                st.balloons()
            else:
                status.update(label="❌ ERROR EN LA PRODUCCIÓN", state="error")
                st.error("Revisa el log para más detalles.")

# --- EXPLORADOR DE ARCHIVOS ---
st.markdown("---")
if os.path.exists("workspace"):
    with st.expander("📂 Explorador de Archivos (Workspace Actual)"):
        # Listar carpetas de proyectos
        proyectos = [d for d in os.listdir("workspace") if os.path.isdir(os.path.join("workspace", d))]
        if proyectos:
            for proj in proyectos:
                st.write(f"📁 **Proyecto: {proj}**")
                archivos = os.listdir(os.path.join("workspace", proj))
                for f in archivos:
                    st.text(f"   └── {f}")
        else:
            st.write("Workspace vacío. Listo para una nueva idea.")
