# =============================================================================
# CARNIVAL CRUISES - PIPELINE PRINCIPAL
# Ejecuta los 3 scripts del pipeline en orden secuencial
# =============================================================================

import os
import sys
import subprocess
import time
import traceback
from datetime import datetime

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Rutas de los scripts
SCRIPTS_DIR = "scripts"
SCRIPTS_ORDER = [
    "tiktok_api_analyzer.py",
    "tiktok_media_downloader.py", 
    "profile_categorizer.py"
]

# Configuración de logging
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"pipeline_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def crear_directorio_logs():
    """Crea el directorio de logs si no existe"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"[FOLDER] Directorio de logs creado: {LOG_DIR}")

def log_mensaje(mensaje, tipo="INFO"):
    """Registra un mensaje en el log y lo muestra en consola"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{tipo}] {mensaje}"
    
    # Mostrar en consola
    print(log_entry)
    
    # Guardar en archivo
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"[ERROR] Error escribiendo en log: {e}")

def verificar_script(script_path):
    """Verifica que un script existe y es ejecutable"""
    if not os.path.exists(script_path):
        log_mensaje(f"[ERROR] Script no encontrado: {script_path}", "ERROR")
        return False
    
    log_mensaje(f"[OK] Script encontrado: {script_path}")
    return True

def ejecutar_script(script_name, script_path):
    """Ejecuta un script de Python y maneja errores"""
    log_mensaje(f"[ROCKET] Ejecutando: {script_name}")
    log_mensaje(f"   [EMOJI] Ruta: {script_path}")
    
    start_time = time.time()
    
    try:
        # Ejecutar script con subprocess con manejo robusto de encoding
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Reemplaza caracteres problemáticos
            cwd=os.getcwd()  # Ejecutar desde el directorio actual
        )
        
        execution_time = time.time() - start_time
        
        # Verificar resultado
        if result.returncode == 0:
            log_mensaje(f"[OK] {script_name} completado exitosamente en {execution_time:.2f}s")
            
            # Mostrar salida estándar si hay contenido (manejo seguro de None)
            if result.stdout and result.stdout.strip():
                log_mensaje(f"   [EMOJI] Salida: {result.stdout.strip()[:200]}...")
            
            return True
        else:
            log_mensaje(f"[ERROR] {script_name} falló con código {result.returncode}", "ERROR")
            
            # Mostrar errores (manejo seguro de None)
            if result.stderr and result.stderr.strip():
                log_mensaje(f"   [EMOJI] Error: {result.stderr.strip()}", "ERROR")
            
            if result.stdout and result.stdout.strip():
                log_mensaje(f"   [EMOJI] Salida: {result.stdout.strip()}", "ERROR")
            
            return False
            
    except Exception as e:
        execution_time = time.time() - start_time
        log_mensaje(f"[ERROR] Error ejecutando {script_name}: {e}", "ERROR")
        log_mensaje(f"   ⏱[EMOJI]  Tiempo transcurrido: {execution_time:.2f}s", "ERROR")
        traceback.print_exc()
        return False

def verificar_dependencias():
    """Verifica que las dependencias necesarias estén disponibles"""
    log_mensaje("[SEARCH] Verificando dependencias...")
    
    # Verificar archivos de configuración (en directorio config/)
    config_files = [
        "config/config_api.ini",
        "config/config_company.ini", 
        "config/config_multimedia.ini"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            log_mensaje(f"   [OK] Configuración: {config_file}")
        else:
            log_mensaje(f"   [WARNING]  Configuración faltante: {config_file}", "WARNING")
    
    # Verificar directorio de datos
    if os.path.exists("data"):
        log_mensaje(f"   [OK] Directorio de datos: data/")
    else:
        log_mensaje(f"   [WARNING]  Directorio de datos faltante: data/", "WARNING")
    
    # Verificar prompt de análisis (ruta correcta)
    prompt_file = "data/Input/prompts/analysis_prompt.txt"
    if os.path.exists(prompt_file):
        log_mensaje(f"   [OK] Prompt de análisis: {prompt_file}")
    else:
        log_mensaje(f"   [WARNING]  Prompt de análisis faltante: {prompt_file}", "WARNING")

def mostrar_resumen_final(resultados):
    """Muestra un resumen final del pipeline"""
    log_mensaje("=" * 80)
    log_mensaje("[CHART] RESUMEN FINAL DEL PIPELINE")
    log_mensaje("=" * 80)
    
    total_scripts = len(SCRIPTS_ORDER)
    exitosos = sum(1 for resultado in resultados if resultado['exitoso'])
    fallidos = total_scripts - exitosos
    
    log_mensaje(f"[TREND_UP] Scripts ejecutados: {total_scripts}")
    log_mensaje(f"[OK] Exitosos: {exitosos}")
    log_mensaje(f"[ERROR] Fallidos: {fallidos}")
    
    if exitosos == total_scripts:
        log_mensaje("[PARTY] ¡PIPELINE COMPLETADO EXITOSAMENTE!", "SUCCESS")
        log_mensaje("[IDEA] Todos los scripts se ejecutaron sin errores")
    else:
        log_mensaje("[WARNING]  PIPELINE COMPLETADO CON ERRORES", "WARNING")
        log_mensaje("[SEARCH] Revisa los logs para más detalles")
    
    # Mostrar detalles de cada script
    log_mensaje("\n[CLIPBOARD] DETALLES POR SCRIPT:")
    for i, resultado in enumerate(resultados):
        status = "[OK]" if resultado['exitoso'] else "[ERROR]"
        tiempo = f"{resultado['tiempo']:.2f}s"
        log_mensaje(f"   {i+1}. {status} {resultado['script']} ({tiempo})")
    
    log_mensaje(f"\n[FOLDER] Log completo guardado en: {LOG_FILE}")
    log_mensaje("=" * 80)

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal que ejecuta el pipeline completo"""
    
    # Crear directorio de logs
    crear_directorio_logs()
    
    # Inicio del pipeline
    log_mensaje("[SHIP] CARNIVAL CRUISES - PIPELINE PRINCIPAL")
    log_mensaje("=" * 80)
    log_mensaje("[SHARE] Pipeline: API Info → Media Download → Profile Categorization")
    log_mensaje("[CHART] Procesamiento masivo desde Excel con categorización AI")
    log_mensaje(f"[EMOJI] Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_mensaje(f"[FOLDER] Directorio de trabajo: {os.getcwd()}")
    log_mensaje("=" * 80)
    
    # Verificar dependencias
    verificar_dependencias()
    
    # Verificar que todos los scripts existan
    log_mensaje("\n[SEARCH] Verificando scripts...")
    scripts_faltantes = []
    
    for script_name in SCRIPTS_ORDER:
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        if not verificar_script(script_path):
            scripts_faltantes.append(script_name)
    
    if scripts_faltantes:
        log_mensaje(f"[ERROR] Scripts faltantes: {', '.join(scripts_faltantes)}", "ERROR")
        log_mensaje("[BOOM] Pipeline no puede continuar", "ERROR")
        return False
    
    # Ejecutar pipeline
    log_mensaje("\n[ROCKET] INICIANDO PIPELINE...")
    log_mensaje("=" * 80)
    
    resultados = []
    pipeline_exitoso = True
    
    for i, script_name in enumerate(SCRIPTS_ORDER, 1):
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        
        log_mensaje(f"\n[CLIPBOARD] PASO {i}/{len(SCRIPTS_ORDER)}: {script_name}")
        log_mensaje("-" * 60)
        
        start_time = time.time()
        exitoso = ejecutar_script(script_name, script_path)
        execution_time = time.time() - start_time
        
        resultados.append({
            'script': script_name,
            'exitoso': exitoso,
            'tiempo': execution_time
        })
        
        if not exitoso:
            pipeline_exitoso = False
            log_mensaje(f"[WARNING]  Pipeline continuará con el siguiente script", "WARNING")
        
        # Pausa entre scripts
        if i < len(SCRIPTS_ORDER):
            log_mensaje(f"[WAIT] Pausa de 3 segundos antes del siguiente script...")
            time.sleep(3)
    
    # Mostrar resumen final
    mostrar_resumen_final(resultados)
    
    return pipeline_exitoso

# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    try:
        # Ejecutar pipeline
        exito = main()
        
        # Código de salida
        if exito:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n[WARNING]  Pipeline interrumpido por el usuario")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n[BOOM] ERROR CRÍTICO: {e}")
        traceback.print_exc()
        sys.exit(1) 