# 🧹 HERRAMIENTAS DE LIMPIEZA - TikTok Profile Analyzer

Esta carpeta contiene herramientas para limpiar y mantener el espacio de trabajo del analizador de perfiles de TikTok.

## 📁 Archivos incluidos

### `clean_output_folder.py`
Script principal de limpieza en Python que elimina todo el contenido de la carpeta `data/Output`.

**Características:**
- 📊 Muestra estadísticas detalladas antes de la limpieza
- ⚠️ Requiere confirmación del usuario antes de proceder
- 🗂️ Elimina todas las sesiones de análisis anteriores
- 📋 Crea logs de las operaciones de limpieza
- 🛡️ Manejo seguro de errores
- 📏 Calcula y muestra el espacio liberado

### `clean_output.bat`
Script batch para Windows que ejecuta la herramienta de limpieza de forma fácil.

**Características:**
- ✅ Verifica que Python esté instalado
- 🔍 Valida que todos los archivos necesarios existan
- 🖥️ Interfaz de usuario amigable
- ⏸️ Pausa al final para revisar resultados

## 🚀 Cómo usar

### Opción 1: Usando el script batch (Windows - Recomendado)
1. Hacer doble clic en `clean_output.bat`
2. Seguir las instrucciones en pantalla
3. Confirmar la operación cuando se solicite

### Opción 2: Usando Python directamente
```bash
# Desde el directorio raíz del proyecto
python clean_tools/clean_output_folder.py
```

### Opción 3: Desde la carpeta clean_tools
```bash
# Navegar a la carpeta clean_tools
cd clean_tools

# Ejecutar el script
python clean_output_folder.py
```

## ⚠️ Precauciones importantes

1. **Eliminación permanente**: Los archivos eliminados NO van a la papelera de reciclaje
2. **Sin recuperación**: Una vez eliminados, los archivos NO se pueden recuperar
3. **Confirmación requerida**: El script siempre pide confirmación antes de proceder
4. **Respaldo recomendado**: Si tienes análisis importantes, haz una copia de seguridad primero

## 📊 Qué se elimina

La herramienta elimina completamente:
- 📁 Todas las carpetas de sesiones (`session_YYYYMMDD_HHMMSS`)
- 📄 Todos los archivos de análisis JSON
- 🎬 Todos los videos descargados
- 📸 Todas las capturas de pantalla
- 📝 Todas las transcripciones
- 🔍 Todos los textos extraídos por OCR
- 📋 Todos los datos extraídos

## 📋 Logs de limpieza

Los logs de las operaciones de limpieza se guardan en:
```
clean_tools/logs/cleanup_log_YYYYMMDD_HHMMSS.txt
```

Cada log contiene:
- 📅 Fecha y hora de la operación
- 📊 Cantidad de espacio liberado
- 📄 Número de archivos eliminados
- 📂 Número de carpetas eliminadas
- ✅ Estado de la operación

## 🔧 Requisitos

- **Python 3.6+** instalado y en el PATH del sistema
- **Permisos de escritura** en la carpeta del proyecto
- **Windows** (para el script batch)

## 🆘 Solución de problemas

### Error: "Python no está instalado"
- Instalar Python desde https://python.org
- Asegurarse de marcar "Add Python to PATH" durante la instalación

### Error: "No se encontró clean_output_folder.py"
- Verificar que ambos archivos estén en la misma carpeta `clean_tools/`
- No mover los archivos de su ubicación original

### Error: "Acceso denegado"
- Ejecutar como administrador
- Cerrar cualquier aplicación que pueda estar usando los archivos
- Verificar permisos de la carpeta

## 🎯 Cuándo usar esta herramienta

**Se recomienda limpiar cuando:**
- 💾 El disco duro esté quedando sin espacio
- 📊 Hayas completado un lote de análisis y ya no necesites los datos
- 🔄 Quieras empezar con un espacio de trabajo limpio
- 🧪 Estés haciendo pruebas y necesites resetear frecuentemente

**NO limpiar si:**
- 📋 Todavía necesitas los datos de análisis previos
- 📊 Estás en medio de un proyecto importante
- 🔍 No has hecho respaldo de datos importantes

## 🎉 Beneficios

✅ **Libera espacio en disco** - Los análisis pueden ocupar mucho espacio  
✅ **Mejora el rendimiento** - Menos archivos = navegación más rápida  
✅ **Organización** - Mantiene el proyecto limpio y ordenado  
✅ **Privacidad** - Elimina datos sensibles de análisis anteriores  
✅ **Automatización** - Proceso rápido y seguro  

---

**💡 Tip:** Ejecuta esta herramienta regularmente para mantener tu espacio de trabajo optimizado y organizado. 