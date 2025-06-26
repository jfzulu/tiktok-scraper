# =============================================================================
# TIKTOK MEDIA DOWNLOADER - DESCARGA DE VIDEOS, IMÁGENES Y AUDIO
# Basado en la información extraída por tiktok_api_analyzer.py
# =============================================================================

import os
import json
import yaml
import requests
import subprocess
import time
import pandas as pd
from datetime import datetime
import urllib.parse
from tqdm import tqdm
from PIL import Image
import traceback

# =============================================================================
# 1. CONFIGURACIÓN Y RUTAS
# =============================================================================

# Rutas de entrada y salida
FFMPEG_PATH = r"C:\Users\dany2\Downloads\pathmatics_media_extractor\ffmpeg\bin\ffmpeg.exe"
OUTPUT_BASE_DIR = "data/Output"
VIDEOS_INFO_DIR = "data/Output/videos_info"

def detectar_archivos_videos_disponibles():
    """Detecta automáticamente archivos de videos YAML disponibles"""
    
    if not os.path.exists(VIDEOS_INFO_DIR):
        print(f"[ERROR] Directorio no encontrado: {VIDEOS_INFO_DIR}")
        return []
    
    archivos_videos = []
    for archivo in os.listdir(VIDEOS_INFO_DIR):
        if archivo.endswith('_videos.yml'):  # Cambiado a YAML
            # Extraer username del nombre del archivo
            username = archivo.replace('_videos.yml', '')
            archivo_path = os.path.join(VIDEOS_INFO_DIR, archivo)
            archivos_videos.append({
                'username': username,
                'archivo': archivo,
                'path': archivo_path
            })
    
    return archivos_videos

def configurar_directorios_media(username):
    """Configura los directorios para descargar medios organizados por usuario"""
    
    # Crear carpeta media con subcarpeta por usuario
    media_folder = os.path.join(OUTPUT_BASE_DIR, "media")
    user_media_folder = os.path.join(media_folder, username)
    
    # Subcarpetas organizadas por usuario
    subdirs = {
        'videos': os.path.join(user_media_folder, 'videos'),
        'images': os.path.join(user_media_folder, 'images'), 
        'audio': os.path.join(user_media_folder, 'audio')
    }
    
    # Crear directorios
    os.makedirs(user_media_folder, exist_ok=True)
    for dir_name, dir_path in subdirs.items():
        os.makedirs(dir_path, exist_ok=True)
        print(f"   [FOLDER] Configurado: {username}/{dir_name}")
    
    return user_media_folder, subdirs

# =============================================================================
# 2. FUNCIONES DE DESCARGA
# =============================================================================

def descargar_archivo(url, filepath, timeout=30):
    """Descarga un archivo desde una URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, stream=True, timeout=timeout, headers=headers)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # Verificar que el archivo se descargó correctamente
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
                return "success"
            else:
                return "failed"
        else:
            print(f"   [ERROR] Error HTTP {response.status_code} para: {url}")
            return "failed"
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout al descargar: {url}")
        return "failed"
    except requests.exceptions.RequestException as e:
        print(f"   [ERROR] Error de conexión: {e}")
        return "failed"
    except Exception as e:
        print(f"   [ERROR] Error inesperado: {e}")
        return "failed"

# =============================================================================
# 3. FUNCIONES DE CONVERSIÓN CON FFMPEG
# =============================================================================

def convertir_video_a_mp4(input_path):
    """Convierte un video a formato MP4 usando FFmpeg"""
    output_path = os.path.splitext(input_path)[0] + "_converted.mp4"
    
    try:
        # Verificar que FFmpeg existe
        if not os.path.exists(FFMPEG_PATH):
            print(f"   [ERROR] FFmpeg no encontrado en: {FFMPEG_PATH}")
            return "failed", ""
        
        # Comando FFmpeg para conversión
        comando = [
            FFMPEG_PATH, "-y", "-i", input_path,
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast", "-crf", "23",
            output_path
        ]
        
        result = subprocess.call(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        if result == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            return "success", output_path
        else:
            return "failed", ""
            
    except Exception as e:
        print(f"   [ERROR] Error en conversión de video: {e}")
        return "failed", ""

def convertir_imagen_a_jpg(input_path):
    """Convierte una imagen a formato JPG"""
    try:
        # Abrir imagen y convertir a RGB
        with Image.open(input_path) as img:
            img_rgb = img.convert("RGB")
            output_path = os.path.splitext(input_path)[0] + "_converted.jpg"
            img_rgb.save(output_path, "JPEG", quality=95)
            
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            return "success", output_path
        else:
            return "failed", ""
            
    except Exception as e:
        print(f"   [ERROR] Error en conversión de imagen: {e}")
        return "failed", ""

def extraer_audio_con_ffmpeg(video_path, audio_folder, base_name):
    """Extrae audio de un video usando FFmpeg"""
    audio_path = os.path.join(audio_folder, f"{base_name}_audio.mp3")
    
    try:
        # Verificar que FFmpeg existe
        if not os.path.exists(FFMPEG_PATH):
            print(f"   [ERROR] FFmpeg no encontrado en: {FFMPEG_PATH}")
            return "failed", ""
        
        # Comando FFmpeg para extracción de audio
        comando = [
            FFMPEG_PATH, "-y", "-i", video_path,
            "-vn", "-acodec", "mp3", "-ab", "192k",
            audio_path
        ]
        
        result = subprocess.call(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        if result == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1024:
            return "success", audio_path
        else:
            return "failed", ""
            
    except Exception as e:
        print(f"   [ERROR] Error en extracción de audio: {e}")
        return "failed", ""

# =============================================================================
# 4. FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# =============================================================================

def procesar_videos_tiktok(videos_yaml_path, subdirs):
    """Procesa y descarga todos los medios de TikTok"""
    
    print(f"\n[PHONE] LEYENDO DATOS DE VIDEOS DESDE: {videos_yaml_path}")
    
    try:
        # Cargar datos YAML
        with open(videos_yaml_path, 'r', encoding='utf-8') as f:
            videos_data = yaml.safe_load(f)
        
        # Extraer información de videos (nueva estructura YAML)
        videos_raw = videos_data.get('videos_list', [])
        
        if not videos_raw:
            print("   [ERROR] No se encontraron videos en el YAML")
            return None
        
        print(f"   [VIDEO] Videos encontrados: {len(videos_raw)}")
        
        # Resultados de descarga
        resultados_descarga = {
            "timestamp": datetime.now().isoformat(),
            "total_videos": len(videos_raw),
            "resultados": []
        }
        
        # Procesar cada video (nueva estructura YAML)
        for i, video in enumerate(tqdm(videos_raw, desc="Descargando medios TikTok")):
            video_id = video.get('video_id', f'video_{i+1}')
            titulo = video.get('title', 'Sin título')
            
            print(f"\n[MOVIE] Procesando video {i+1}/{len(videos_raw)}: {video_id}")
            print(f"   [MEMO] Título: {titulo[:50]}...")
            
            resultado_video = {
                "video_index": i + 1,
                "video_id": video_id,
                "title": titulo,
                "video_download": {"status": "skipped", "path": ""},
                "audio_extraction": {"status": "skipped", "path": ""},
                "images_download": {"status": "skipped", "paths": []}
            }
            
            # 1. DESCARGAR VIDEO (si existe) - Nueva estructura YAML
            video_info = video.get('video_info', {})
            video_url = video_info.get('play_url', '') or video_info.get('wmplay_url', '')
            if video_url:
                print(f"   [EMOJI] Descargando video...")
                
                # Nombre de archivo para video
                video_filename = f"{video_id}_video.mp4"
                video_path = os.path.join(subdirs['videos'], video_filename)
                
                # Descargar video
                download_status = descargar_archivo(video_url, video_path)
                
                if download_status == "success":
                    resultado_video["video_download"]["status"] = "success"
                    resultado_video["video_download"]["path"] = video_path
                    print(f"      [OK] Video descargado: {video_filename}")
                    
                    # Extraer audio del video
                    print(f"   [MUSIC] Extrayendo audio del video...")
                    audio_status, audio_path = extraer_audio_con_ffmpeg(
                        video_path, subdirs['audio'], video_id
                    )
                    
                    resultado_video["audio_extraction"]["status"] = audio_status
                    if audio_status == "success":
                        resultado_video["audio_extraction"]["path"] = audio_path
                        print(f"      [OK] Audio extraído: {os.path.basename(audio_path)}")
                    else:
                        print(f"      [ERROR] No se pudo extraer audio")
                
                else:
                    resultado_video["video_download"]["status"] = "failed"
                    print(f"      [ERROR] Error descargando video")
            
            # 2. DESCARGAR IMÁGENES (si es un post de imágenes)
            images = video.get('images', [])
            if images:
                print(f"   [IMAGE]  Descargando {len(images)} imágenes...")
                
                imagenes_descargadas = []
                for j, image_url in enumerate(images):
                    image_filename = f"{video_id}_image_{j+1}.jpg"
                    image_path = os.path.join(subdirs['images'], image_filename)
                    
                    download_status = descargar_archivo(image_url, image_path)
                    
                    if download_status == "success":
                        imagenes_descargadas.append(image_path)
                        print(f"      [OK] Imagen {j+1} descargada")
                    else:
                        print(f"      [ERROR] Error descargando imagen {j+1}")
                
                if imagenes_descargadas:
                    resultado_video["images_download"]["status"] = "success"
                    resultado_video["images_download"]["paths"] = imagenes_descargadas
                else:
                    resultado_video["images_download"]["status"] = "failed"
            
            resultados_descarga["resultados"].append(resultado_video)
            
            # Pausa entre descargas para evitar rate limiting
            time.sleep(1)
        
        return resultados_descarga
        
    except Exception as e:
        print(f"\n[ERROR] Error procesando videos: {e}")
        traceback.print_exc()
        return None

# =============================================================================
# 5. GUARDADO DE RESULTADOS
# =============================================================================

def guardar_resultados_descarga(resultados, output_dir):
    """Guarda los resultados de descarga en un archivo YAML"""
    
    if not resultados:
        print("   [WARNING]  No hay resultados para guardar")
        return None
    
    try:
        # Archivo de resultados (formato YAML)
        resultados_file = os.path.join(output_dir, "media_download_results.yml")
        
        with open(resultados_file, 'w', encoding='utf-8') as f:
            yaml.dump(resultados, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"\n[SAVE] RESULTADOS GUARDADOS EN: {resultados_file}")
        
        # Generar resumen
        total = resultados["total_videos"]
        videos_exitosos = len([r for r in resultados["resultados"] if r["video_download"]["status"] == "success"])
        audios_exitosos = len([r for r in resultados["resultados"] if r["audio_extraction"]["status"] == "success"])
        imagenes_exitosas = len([r for r in resultados["resultados"] if r["images_download"]["status"] == "success"])
        
        print(f"\n[CHART] RESUMEN DE DESCARGAS:")
        print(f"   [VIDEO] Videos descargados: {videos_exitosos}/{total}")
        print(f"   [MUSIC] Audios extraídos: {audios_exitosos}/{total}")
        print(f"   [IMAGE]  Posts con imágenes: {imagenes_exitosas}/{total}")
        
        return resultados_file
        
    except Exception as e:
        print(f"   [ERROR] Error guardando resultados: {e}")
        return None

# =============================================================================
# 6. FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal del descargador de medios de TikTok"""
    
    print("[MOVIE] TIKTOK MEDIA DOWNLOADER")
    print("=" * 50)
    print(" [PHONE] Descarga videos, imágenes y audio de TikTok")
    print(" [MUSIC] Extrae audio con FFmpeg") 
    print(" [IMAGE]  Soporte para posts de imágenes")
    print(" [USERS] Organización por usuario")
    print(" [CHART] Procesamiento masivo desde Excel")
    print("=" * 50)
    
    try:
        # 1. Detectar archivos de videos disponibles
        archivos_disponibles = detectar_archivos_videos_disponibles()
        
        if not archivos_disponibles:
            print(f"\n[ERROR] No se encontraron archivos de videos en: {VIDEOS_INFO_DIR}")
            print("   [MEMO] Primero ejecuta tiktok_api_analyzer.py para generar los datos")
            print("   [CHART] O verifica que los archivos YAML estén en formato correcto")
            return
        
        print(f"\n[CLIPBOARD] Archivos de videos detectados:")
        for i, archivo_info in enumerate(archivos_disponibles):
            print(f"   {i+1}. @{archivo_info['username']} - {archivo_info['archivo']}")
        
        # 2. Verificar FFmpeg
        if not os.path.exists(FFMPEG_PATH):
            print(f"\n[WARNING]  FFmpeg no encontrado en: {FFMPEG_PATH}")
            print("   [MEMO] La extracción de audio no funcionará")
        else:
            print(f"\n[OK] FFmpeg encontrado: {FFMPEG_PATH}")
        
        # 3. Procesar cada usuario
        total_usuarios_procesados = 0
        
        for archivo_info in archivos_disponibles:
            username = archivo_info['username']
            videos_json_path = archivo_info['path']
            
            print(f"\n[SHARE] PROCESANDO USUARIO: @{username}")
            print("=" * 50)
            
            # Configurar directorios para este usuario
            print(f"\n[FOLDER] Configurando directorios para @{username}...")
            user_media_folder, subdirs = configurar_directorios_media(username)
            
            # Procesar videos del usuario
            resultados = procesar_videos_tiktok(videos_json_path, subdirs)
            
            # Guardar resultados en la carpeta del usuario
            if resultados:
                user_output_dir = os.path.join(OUTPUT_BASE_DIR, "media", username)
                guardar_resultados_descarga(resultados, user_output_dir)
                print(f"\n[PARTY] DESCARGA COMPLETADA PARA @{username}")
                print(f"[FOLDER] Medios guardados en: {user_media_folder}")
                total_usuarios_procesados += 1
            else:
                print(f"\n[ERROR] No se pudieron procesar los videos de @{username}")
        
        print(f"\n[FLAG] PROCESO COMPLETO")
        print(f"[USERS] Usuarios procesados: {total_usuarios_procesados}/{len(archivos_disponibles)}")
        print(f"[FOLDER] Estructura final: data/Output/media/[username]/")
        
    except Exception as e:
        print(f"\n[BOOM] ERROR CRÍTICO: {e}")
        traceback.print_exc()

# =============================================================================
# 7. PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    main() 