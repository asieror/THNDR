import streamlit as st
import subprocess
import os
import shlex
import yaml
import zipfile
import shutil
import io
from pathlib import Path

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="THNDR Agency OS v3.5", page_icon="⚡", layout="wide")

# Estilo de Terminal
st.markdown("""
    <style>
    .stCodeBlock { background-color: #0e1117 !important; }
    .stTextArea textarea { font-family: 'Courier New', monospace; font-size: 14px; }
    .stStatus { border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO (EL MOTOR) ---

def preparar_workspace_desde_zip(archivo_zip):
    """Limpia el workspace actual y extrae el contenido del ZIP"""
    workspace_path = "workspace"
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    os.makedirs(workspace_path)
    
    with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
        zip_ref.extractall(workspace_path)
    return True

def generar_zip_descarga():
    """Comprime el contenido del workspace en un buffer de memoria"""
    if os.path.exists("workspace") and os.listdir("workspace"):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk("workspace"):
                for file in files:
                    ruta_completa = os.path.join(root, file)
                    # Mantener estructura interna limpia
                    ruta_relativa = os.path.relpath(ruta_completa, "workspace")
                    zip_file.write(ruta_completa, ruta_relativa)
        return buffer.getvalue()
    return None

# --- INTERFAZ - BARRA LATERAL ---
st.title("⚡ THNDR: Agency OS")

with st.sidebar:
    st.header("⚙️ Configuración")
    modelo = st.selectbox("Cerebro Activo:", [
        "llama-3.3-70b-versatile", 
        "claude-3-5-sonnet-20240620"
    ])
    
    st.divider()
    
    st.subheader("📂 Memoria de Proyecto")
    st.info("Sube un proyecto anterior para iterar sobre él.")
    archivo_subido = st.file_uploader("Cargar proyecto (.zip)", type=["zip"])
    
    if st.button("🧹 Resetear Oficina", use_container_width=True):
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
        placeholder="Ej: 'Analiza el código de RunRank en el workspace y añade una función de medallas...'"
    )
    
    # Toggle para modo incremental
    modo_incremental = st.toggle("🔄 Modo Incremental (Editar código existente)", value=True)
    
    btn_lanzar = st.button("🚀 EJECUTAR ACCIÓN", use_container_width=True)

with col_status:
    st.subheader("🕵️ Seguimiento en Vivo")
    status_placeholder = st.empty()
    log_placeholder = st.empty()

# --- LÓGICA DE EJECUCIÓN ---
if btn_lanzar:
    if not idea:
        st.warning("El CEO debe dar una orden antes de empezar.")
    else:
        with st.status("🏗️ Preparando entorno de trabajo...", expanded=True) as status:
            
            # 1. Cargar contexto si hay ZIP
            if archivo_subido:
                st.write("📦 Descomprimiendo archivos base...")
                preparar_workspace_desde_zip(archivo_subido)

            # 2. Inyectar Configuración de Groq
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
            
            st.write(f"✅ Configuración inyectada correctamente.")

            # 3. Construir comando
            idea_segura = shlex.quote(idea)
            comando = f"metagpt {idea_segura}"
            if modo_incremental:
                comando += " --inc"
                st.write("🔄 Trabajando sobre archivos existentes.")

            # 4. Lanzar MetaGPT
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
                
                # Feedback visual dinámico
                if "PrepareDocuments" in line: status.update(label="📄 Alice redactando el PRD...", state="running")
                if "WriteDesign" in line: status.update(label="📐 Bob diseñando arquitectura...", state="running")
                if "WriteCode" in line: status.update(label="💻 Eve picando código...", state="running")

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                status.update(label="✅ TAREA COMPLETADA CON ÉXITO", state="complete", expanded=False)
                st.balloons()
                
                # --- BOTÓN DE DESCARGA POST-ÉXITO ---
                zip_data = generar_zip_descarga()
                if zip_data:
                    st.download_button(
                        label="🎁 DESCARGAR PROYECTO (.ZIP)",
                        data=zip_data,
                        file_name="thndr_output.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            else:
                status.update(label="❌ ERROR EN LA PRODUCCIÓN", state="error")
                st.error("La agencia se ha detenido. Revisa los logs arriba.")

# --- EXPLORADOR DE ARCHIVOS Y BACKUP ---
st.markdown("---")
if os.path.exists("workspace") and os.listdir("workspace"):
    col_exp, col_down = st.columns([3, 1])
    
    with col_exp:
        with st.expander("📂 Explorador del Workspace"):
            proyectos = [d for d in os.listdir("workspace") if os.path.isdir(os.path.join("workspace", d))]
            if proyectos:
                for proj in proyectos:
                    st.write(f"📁 **Proyecto: {proj}**")
                    for root, dirs, files in os.walk(os.path.join("workspace", proj)):
                        level = root.replace(os.path.join("workspace", proj), '').count(os.sep)
                        indent = ' ' * 4 * level
                        if os.path.basename(root) != proj:
                            st.text(f"{indent}📁 {os.path.basename(root)}/")
                        sub_indent = ' ' * 4 * (level + 1)
                        for f in files:
                            st.text(f"{sub_indent}└── {f}")
            else:
                st.write("No hay proyectos estructurados todavía.")
                
    with col_down:
        backup_data = generar_zip_descarga()
        if backup_data:
            st.download_button(
                label="📥 Bajar Todo",
                data=backup_data,
                file_name="thndr_workspace_full.zip",
                mime="application/zip",
                use_container_width=True
            )
