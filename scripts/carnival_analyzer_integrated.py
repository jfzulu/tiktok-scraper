# =============================================================================
# CARNIVAL CRUISES - ANALIZADOR INTEGRADO COMPLETO
# Pipeline: API Info → Media Download → AI Analysis
# Version: 1.0 - Integración completa con Dify API
# =============================================================================

import os
import yaml
import json
import time
import requests
import traceback
import urllib3
import re
from datetime import datetime
from configparser import ConfigParser

# Importaciones para análisis multimedia
try:
    import cv2
    import easyocr
    import speech_recognition as sr
    from PIL import Image
    import numpy as np
    from moviepy.editor import VideoFileClip
    MULTIMEDIA_AVAILABLE = True
    print("[MOVIE] Módulos de análisis multimedia cargados exitosamente")
except ImportError as e:
    MULTIMEDIA_AVAILABLE = False
    print(f"[WARNING]  Módulos multimedia no disponibles: {e}")
    print("   [MEMO] Instala: pip install opencv-python easyocr SpeechRecognition moviepy pillow numpy")

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================================================
# 1. CONFIGURACIÓN Y CARGA DE API KEYS
# =============================================================================

def cargar_configuracion_dify():
    """Carga la configuración del API de Dify desde config_company.ini"""
    config = ConfigParser()
    config_path = 'config_company.ini'
    
    try:
        print(f"[PAGE] Cargando configuración de Dify desde: {config_path}")
        config.read(config_path)
        
        if 'company_api' not in config or 'api_key' not in config['company_api']:
            raise KeyError("Configuración de API de Dify no encontrada")
        
        api_key = config['company_api']['api_key']
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***masked***"
        print(f"   [OK] API Key de Dify cargada: {masked_key}")
        
        return {
            'api_key': api_key,
            'api_url': config['company_api'].get('api_url', 'https://dify-api.factory.tools/service/api/v1/chat-messages')
        }
        
    except Exception as e:
        print(f"[ERROR] Error cargando configuración de Dify: {e}")
        raise

# =============================================================================
# 2. DETECCIÓN Y CARGA DE DATOS GENERADOS
# =============================================================================

def detectar_datos_disponibles():
    """Detecta automáticamente archivos YAML generados por el pipeline"""
    
    rutas_datos = {
        'user_info': 'data/Output/user_info',
        'videos_info': 'data/Output/videos_info', 
        'video_details': 'data/Output/video_details',
        'media_results': 'data/Output/media'
    }
    
    usuarios_encontrados = {}
    
    print(f"[SEARCH] Detectando datos disponibles del pipeline...")
    
    # Buscar archivos de información de usuario
    if os.path.exists(rutas_datos['user_info']):
        for archivo in os.listdir(rutas_datos['user_info']):
            if archivo.endswith('_user_info.yml'):
                username = archivo.replace('_user_info.yml', '')
                usuarios_encontrados[username] = {
                    'user_info_file': os.path.join(rutas_datos['user_info'], archivo),
                    'videos_info_file': None,
                    'video_details_file': None,
                    'media_results_files': []
                }
                print(f"   [USER] Usuario encontrado: @{username}")
    
    # Buscar archivos de videos para cada usuario
    if os.path.exists(rutas_datos['videos_info']):
        for archivo in os.listdir(rutas_datos['videos_info']):
            if archivo.endswith('_videos.yml'):
                username = archivo.replace('_videos.yml', '')
                if username in usuarios_encontrados:
                    usuarios_encontrados[username]['videos_info_file'] = os.path.join(rutas_datos['videos_info'], archivo)
                    print(f"      [VIDEO] Videos info: [OK]")
    
    # Buscar archivos de detalles de videos
    if os.path.exists(rutas_datos['video_details']):
        for archivo in os.listdir(rutas_datos['video_details']):
            if archivo.endswith('.yml'):
                # Los detalles no están por usuario específico, los asignamos a todos
                for username in usuarios_encontrados:
                    usuarios_encontrados[username]['video_details_file'] = os.path.join(rutas_datos['video_details'], archivo)
                print(f"      [SEARCH] Video details: [OK]")
                break
    
    # Buscar resultados de media descargada
    if os.path.exists(rutas_datos['media_results']):
        for item in os.listdir(rutas_datos['media_results']):
            item_path = os.path.join(rutas_datos['media_results'], item)
            if os.path.isdir(item_path):
                # Buscar archivo de resultados en esta carpeta de usuario
                for archivo in os.listdir(item_path):
                    if archivo == 'media_download_results.yml':
                        if item in usuarios_encontrados:
                            usuarios_encontrados[item]['media_results_files'].append(os.path.join(item_path, archivo))
                            print(f"      [PHONE] Media results: [OK]")
    
    print(f"   [CHART] Total usuarios con datos: {len(usuarios_encontrados)}")
    return usuarios_encontrados

def cargar_datos_usuario(usuario_data):
    """Carga y consolida todos los datos disponibles de un usuario"""
    
    datos_consolidados = {
        'profile_basic_info': {},
        'videos_list': [],
        'video_details': [],
        'media_analysis': {},
        'data_completeness': {
            'has_user_info': False,
            'has_videos_info': False,
            'has_video_details': False,
            'has_media_results': False
        }
    }
    
    try:
        # 1. Cargar información básica del usuario
        if usuario_data['user_info_file'] and os.path.exists(usuario_data['user_info_file']):
            print(f"      [PAGE] Cargando user info...")
            with open(usuario_data['user_info_file'], 'r', encoding='utf-8') as f:
                user_data = yaml.safe_load(f)
                datos_consolidados['profile_basic_info'] = user_data.get('profile_basic_info', {})
                datos_consolidados['profile_stats'] = user_data.get('profile_stats', {})
                datos_consolidados['data_completeness']['has_user_info'] = True
        
        # 2. Cargar información de videos
        if usuario_data['videos_info_file'] and os.path.exists(usuario_data['videos_info_file']):
            print(f"      [VIDEO] Cargando videos info...")
            with open(usuario_data['videos_info_file'], 'r', encoding='utf-8') as f:
                videos_data = yaml.safe_load(f)
                datos_consolidados['videos_list'] = videos_data.get('videos_list', [])
                datos_consolidados['videos_summary'] = videos_data.get('videos_summary', {})
                datos_consolidados['data_completeness']['has_videos_info'] = True
        
        # 3. Cargar detalles de videos
        if usuario_data['video_details_file'] and os.path.exists(usuario_data['video_details_file']):
            print(f"      [SEARCH] Cargando video details...")
            with open(usuario_data['video_details_file'], 'r', encoding='utf-8') as f:
                details_data = yaml.safe_load(f)
                datos_consolidados['video_details'] = details_data.get('video_details', [])
                datos_consolidados['data_completeness']['has_video_details'] = True
        
        # 4. Cargar resultados de media
        if usuario_data['media_results_files']:
            print(f"      [PHONE] Cargando media results...")
            for media_file in usuario_data['media_results_files']:
                if os.path.exists(media_file):
                    with open(media_file, 'r', encoding='utf-8') as f:
                        media_data = yaml.safe_load(f)
                        datos_consolidados['media_analysis'] = media_data
                        datos_consolidados['data_completeness']['has_media_results'] = True
                    break
        
        return datos_consolidados
        
    except Exception as e:
        print(f"      [ERROR] Error cargando datos: {e}")
        return None

# =============================================================================
# 3. ANÁLISIS MULTIMEDIA COMPLETO
# =============================================================================

def extraer_screenshots_video(video_path, video_id, output_dir, num_frames=5):
    """Extrae screenshots en momentos clave del video"""
    if not MULTIMEDIA_AVAILABLE:
        return []
        
    screenshots = []
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return []
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Momentos clave: inicio, 25%, 50%, 75%, final
        frame_positions = [
            int(total_frames * 0.1),   # 10%
            int(total_frames * 0.25),  # 25%
            int(total_frames * 0.5),   # 50%
            int(total_frames * 0.75),  # 75%
            int(total_frames * 0.9)    # 90%
        ]
        
        for i, frame_pos in enumerate(frame_positions):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            
            if ret:
                timestamp = frame_pos / fps if fps > 0 else i
                screenshot_filename = f"{video_id}_frame_{i+1}_{timestamp:.1f}s.jpg"
                screenshot_path = os.path.join(output_dir, screenshot_filename)
                
                # Crear directorio si no existe
                os.makedirs(output_dir, exist_ok=True)
                cv2.imwrite(screenshot_path, frame)
                
                screenshots.append({
                    "frame_number": i+1,
                    "timestamp": timestamp,
                    "file_path": screenshot_path,
                    "position_percent": frame_pos / total_frames * 100
                })
        
        cap.release()
        print(f"        [CAMERA] {len(screenshots)} screenshots extraídos")
        
    except Exception as e:
        print(f"        [ERROR] Error extrayendo screenshots: {e}")
    
    return screenshots

def extraer_texto_ocr(screenshots):
    """Extrae texto de screenshots usando OCR"""
    if not MULTIMEDIA_AVAILABLE:
        return []
        
    textos_extraidos = []
    
    try:
        # Inicializar EasyOCR
        reader = easyocr.Reader(['en', 'es'], gpu=False)
        
        for screenshot in screenshots:
            try:
                results = reader.readtext(screenshot["file_path"])
                
                texto_frame = {
                    "frame_number": screenshot["frame_number"],
                    "timestamp": screenshot["timestamp"],
                    "text_detected": [],
                    "full_text": ""
                }
                
                texto_completo = []
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:  # Solo texto con confianza > 50%
                        texto_frame["text_detected"].append({
                            "text": text,
                            "confidence": confidence
                        })
                        texto_completo.append(text)
                
                texto_frame["full_text"] = " ".join(texto_completo)
                textos_extraidos.append(texto_frame)
                
                if texto_completo:
                    print(f"        [MEMO] OCR frame {screenshot['frame_number']}: {' '.join(texto_completo)[:50]}...")
                
            except Exception as e:
                print(f"        [WARNING]  Error OCR frame {screenshot.get('frame_number', '?')}: {e}")
    
    except Exception as e:
        print(f"        [ERROR] Error inicializando OCR: {e}")
    
    return textos_extraidos

def extraer_transcripcion_audio(video_path, video_id, temp_dir):
    """Extrae y transcribe el audio del video"""
    if not MULTIMEDIA_AVAILABLE:
        return ""
        
    transcripcion = ""
    
    try:
        # Crear directorio temporal
        os.makedirs(temp_dir, exist_ok=True)
        audio_path = os.path.join(temp_dir, f"{video_id}_temp_audio.wav")
        
        with VideoFileClip(video_path) as video:
            if video.audio is not None:
                # Extraer solo primeros 30 segundos
                audio_duration = min(video.duration, 30)
                audio_clip = video.audio.subclip(0, audio_duration)
                audio_clip.write_audiofile(audio_path, verbose=False, logger=None)
                audio_clip.close()
                
                # Transcribir usando speech_recognition
                r = sr.Recognizer()
                
                with sr.AudioFile(audio_path) as source:
                    audio_data = r.record(source)
                    
                    try:
                        # Intentar transcripción en español primero
                        transcripcion = r.recognize_google(audio_data, language='es-ES')
                        print(f"        [EMOJI] Transcripción (ES): {transcripcion[:50]}...")
                    except:
                        try:
                            # Si falla, intentar en inglés
                            transcripcion = r.recognize_google(audio_data, language='en-US')
                            print(f"        [EMOJI] Transcripción (EN): {transcripcion[:50]}...")
                        except:
                            transcripcion = "No se pudo transcribir el audio"
                            print(f"        [WARNING]  No se pudo transcribir audio")
                
                # Limpiar archivo temporal
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            else:
                transcripcion = "El video no contiene audio"
                print(f"        ℹ[EMOJI]  Video sin audio")
    
    except Exception as e:
        transcripcion = f"Error en transcripción: {str(e)}"
        print(f"        [ERROR] Error transcripción: {e}")
    
    return transcripcion

def analizar_elementos_visuales(video_path):
    """Analiza elementos visuales del video"""
    if not MULTIMEDIA_AVAILABLE:
        return {}
        
    elementos = {
        "duration_seconds": 0,
        "resolution": "unknown",
        "brightness_analysis": "unknown",
        "color_analysis": "unknown"
    }
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        if cap.isOpened():
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            elementos["duration_seconds"] = total_frames / fps if fps > 0 else 0
            elementos["resolution"] = f"{width}x{height}"
            
            # Analizar frame del medio
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            ret, frame = cap.read()
            
            if ret:
                # Análisis de brillo
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = np.mean(gray)
                
                if brightness < 50:
                    elementos["brightness_analysis"] = "dark"
                elif brightness > 200:
                    elementos["brightness_analysis"] = "bright"
                else:
                    elementos["brightness_analysis"] = "normal"
                
                # Análisis de color dominante
                b, g, r = cv2.split(frame)
                avg_colors = [np.mean(b), np.mean(g), np.mean(r)]
                dominant_channel = ["blue", "green", "red"][np.argmax(avg_colors)]
                elementos["color_analysis"] = f"dominant_{dominant_channel}"
        
        cap.release()
        
    except Exception as e:
        print(f"        [ERROR] Error análisis visual: {e}")
    
    return elementos

def procesar_medios_descargados(username, media_results):
    """Procesa todos los medios descargados para extraer información multimedia"""
    
    if not MULTIMEDIA_AVAILABLE:
        print(f"      [WARNING]  Análisis multimedia no disponible - falta instalar dependencias")
        return {
            'transcripciones': [],
            'textos_ocr': [],
            'analisis_visual': {},
            'total_procesados': 0
        }
    
    print(f"      [MOVIE] Iniciando análisis multimedia completo...")
    
    resultados_multimedia = {
        'transcripciones': [],
        'textos_ocr': [],
        'analisis_visual': {},
        'total_procesados': 0
    }
    
    # Directorio base de medios del usuario
    media_base_dir = f"data/Output/media/{username}"
    videos_dir = os.path.join(media_base_dir, "videos")
    temp_dir = os.path.join(media_base_dir, "temp_analysis")
    screenshots_dir = os.path.join(media_base_dir, "screenshots")
    
    if not os.path.exists(videos_dir):
        print(f"      [WARNING]  No se encontró directorio de videos: {videos_dir}")
        return resultados_multimedia
    
    # Procesar cada video descargado
    resultados_videos = media_results.get('resultados', [])
    videos_exitosos = [r for r in resultados_videos if r.get('video_download', {}).get('status') == 'success']
    
    print(f"      [CHART] Videos a procesar: {len(videos_exitosos)}")
    
    for i, video_result in enumerate(videos_exitosos[:5]):  # Máximo 5 videos para no sobrecargar
        video_id = video_result.get('video_id', f'video_{i+1}')
        video_path = video_result.get('video_download', {}).get('path', '')
        
        if not os.path.exists(video_path):
            print(f"        [WARNING]  Video no encontrado: {video_path}")
            continue
        
        print(f"        [MOVIE] Procesando video {i+1}: {video_id}")
        
        try:
            # 1. Extraer screenshots
            screenshots = extraer_screenshots_video(video_path, video_id, screenshots_dir)
            
            # 2. OCR en screenshots
            if screenshots:
                textos_ocr = extraer_texto_ocr(screenshots)
                resultados_multimedia['textos_ocr'].extend(textos_ocr)
            
            # 3. Transcripción de audio
            transcripcion = extraer_transcripcion_audio(video_path, video_id, temp_dir)
            if transcripcion and transcripcion != "El video no contiene audio":
                resultados_multimedia['transcripciones'].append({
                    'video_id': video_id,
                    'transcripcion': transcripcion
                })
            
            # 4. Análisis visual
            elementos_visuales = analizar_elementos_visuales(video_path)
            resultados_multimedia['analisis_visual'][video_id] = elementos_visuales
            
            resultados_multimedia['total_procesados'] += 1
            
        except Exception as e:
            print(f"        [ERROR] Error procesando video {video_id}: {e}")
            continue
    
    # Limpiar directorio temporal
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print(f"      [OK] Análisis multimedia completado: {resultados_multimedia['total_procesados']} videos procesados")
    return resultados_multimedia

# =============================================================================
# 4. PREPARACIÓN DEL PROMPT PARA DIFY
# =============================================================================

def cargar_prompt_template():
    """Carga el template del prompt desde analysis_prompt.txt"""
    
    prompt_file = 'data/Input/analysis_prompt.txt'
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        print(f"   [MEMO] Prompt template cargado desde: {prompt_file}")
        return prompt_template
        
    except Exception as e:
        print(f"   [ERROR] Error cargando prompt: {e}")
        # Prompt de respaldo simplificado
        return """
        Analiza este perfil de TikTok para Carnival Cruises y responde en formato JSON:
        
        **DATOS DEL PERFIL:**
        {datos_completos}
        
        Responde SOLO con JSON válido siguiendo la estructura especificada en el prompt original.
        """

def preparar_datos_para_prompt(datos_consolidados, username):
    """Prepara y estructura los datos para el prompt de análisis"""
    
    # Extraer información clave para el prompt
    profile_info = datos_consolidados.get('profile_basic_info', {})
    profile_stats = datos_consolidados.get('profile_stats', {})
    videos_list = datos_consolidados.get('videos_list', [])
    
    # Construir estructura de datos para el prompt
    datos_prompt = {
        'url': f"https://www.tiktok.com/@{username}",
        'username': profile_info.get('unique_id', username),
        'display_name': profile_info.get('nickname', 'N/A'),
        'bio': profile_info.get('signature', 'N/A'),
        'follower_count': profile_stats.get('follower_count', 'N/A'),
        'following_count': profile_stats.get('following_count', 'N/A'),
        'likes_count': profile_stats.get('heart_count', 'N/A'),
        'is_verified': profile_info.get('verified', False),
        'is_private': profile_info.get('private_account', False),
        'video_descriptions': [],
        'common_hashtags': [],
        'video_transcriptions': [],
        'video_ocr_texts': [],
        'enhanced_video_analysis': {}
    }
    
    # Procesar videos para extraer descripciones y hashtags
    for video in videos_list[:10]:  # Máximo 10 videos
        if video.get('title'):
            datos_prompt['video_descriptions'].append(video['title'])
        
        # Extraer hashtags de los títulos
        if video.get('hashtags'):
            datos_prompt['common_hashtags'].extend(video['hashtags'])
    
    # Procesar resultados de media con análisis multimedia completo
    media_analysis = datos_consolidados.get('media_analysis', {})
    if media_analysis:
        print(f"   [MOVIE] Procesando análisis multimedia...")
        
        # Realizar análisis multimedia completo de videos descargados
        multimedia_results = procesar_medios_descargados(username, media_analysis)
        
        # Integrar transcripciones de audio
        transcripciones_texto = []
        for transcripcion in multimedia_results.get('transcripciones', []):
            if transcripcion.get('transcripcion'):
                transcripciones_texto.append(f"Video {transcripcion['video_id']}: {transcripcion['transcripcion']}")
        datos_prompt['video_transcriptions'] = transcripciones_texto
        
        # Integrar textos OCR extraídos
        ocr_textos = []
        for ocr_frame in multimedia_results.get('textos_ocr', []):
            if ocr_frame.get('full_text'):
                ocr_textos.append(f"Frame {ocr_frame['frame_number']} ({ocr_frame['timestamp']:.1f}s): {ocr_frame['full_text']}")
        datos_prompt['video_ocr_texts'] = ocr_textos
        
        # Análisis visual mejorado
        datos_prompt['enhanced_video_analysis'] = {
            'total_downloaded': media_analysis.get('total_videos', 0),
            'successful_downloads': len([r for r in media_analysis.get('resultados', []) 
                                       if r.get('video_download', {}).get('status') == 'success']),
            'audio_extractions': len([r for r in media_analysis.get('resultados', []) 
                                    if r.get('audio_extraction', {}).get('status') == 'success']),
            'multimedia_processed': multimedia_results.get('total_procesados', 0),
            'transcriptions_obtained': len(multimedia_results.get('transcripciones', [])),
            'ocr_texts_extracted': len(multimedia_results.get('textos_ocr', [])),
            'visual_analysis': multimedia_results.get('analisis_visual', {})
        }
        
        print(f"      [EMOJI] Transcripciones obtenidas: {len(transcripciones_texto)}")
        print(f"      [MEMO] Textos OCR extraídos: {len(ocr_textos)}")
        print(f"      [ART] Videos con análisis visual: {len(multimedia_results.get('analisis_visual', {}))}")
    else:
        # Si no hay medios, inicializar campos vacíos
        datos_prompt['video_transcriptions'] = []
        datos_prompt['video_ocr_texts'] = []
        datos_prompt['enhanced_video_analysis'] = {}
    
    # Eliminar hashtags duplicados
    datos_prompt['common_hashtags'] = list(set(datos_prompt['common_hashtags']))
    
    return datos_prompt

def crear_prompt_final(prompt_template, datos_prompt):
    """Crea el prompt final reemplazando los placeholders"""
    
    try:
        # Reemplazar placeholders en el template
        prompt_final = prompt_template.format(**datos_prompt)
        return prompt_final
        
    except KeyError as e:
        print(f"   [WARNING]  Placeholder faltante en template: {e}")
        # Crear prompt simplificado como fallback
        return f"""
        Analiza este perfil de TikTok para Carnival Cruises:
        
        **URL:** {datos_prompt.get('url', 'N/A')}
        **Usuario:** {datos_prompt.get('username', 'N/A')}
        **Datos completos:** {datos_prompt}
        
        Responde SOLO con JSON válido siguiendo la estructura del prompt original.
        """

# =============================================================================
# 4. ANÁLISIS CON API DE DIFY
# =============================================================================

def analizar_con_dify(api_config, prompt_final, username):
    """Envía el prompt al API de Dify y obtiene el análisis"""
    
    print(f"   🧠 Enviando análisis a Dify API para @{username}...")
    print(f"      [EMOJI] Tamaño del prompt: {len(prompt_final)} caracteres")
    
    headers = {
        'Authorization': f'Bearer {api_config["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "model": "gpt-4",
        "query": prompt_final,
        "inputs": {},
        "response_mode": "streaming",
        "user": "carnival-cruise-analyzer-integrated",
        "temperature": 0.1,
        "frequency_penalty": 1
    }
    
    retry_count = 3
    
    while retry_count > 0:
        try:
            with requests.post(api_config['api_url'], json=payload, headers=headers, 
                             verify=False, stream=True, timeout=180) as response:  # Más tiempo
                
                if response.status_code == 200:
                    full_response = ""
                    chunk_count = 0
                    print(f"      [SATELLITE] Recibiendo respuesta", end="", flush=True)
                    
                    try:
                        for line in response.iter_lines():
                            if not line:
                                continue
                            
                            chunk_count += 1
                            if chunk_count % 10 == 0:  # Punto cada 10 chunks
                                print(".", end="", flush=True)
                            
                            decoded_line = line.decode('utf-8')
                            
                            if decoded_line.startswith('data: '):
                                data_str = decoded_line[6:]
                                
                                if data_str == "[DONE]":
                                    print(" [DONE]")
                                    break
                                
                                try:
                                    data = json.loads(data_str)
                                    
                                    if "event" in data:
                                        event_type = data.get("event")
                                        
                                        if event_type in ["message", "agent_message"]:
                                            content = data.get("answer", "")
                                            if content:
                                                full_response += content
                                        elif event_type == "message_end":
                                            print(" [END]")
                                            break
                                        elif event_type == "error":
                                            error_msg = data.get("message", "Error desconocido")
                                            print(f" [ERROR: {error_msg}]")
                                            return None
                                
                                except json.JSONDecodeError as e:
                                    # Mostrar más info del error para debug
                                    print(f"\n      [WARNING]  JSON decode error en chunk: {str(e)[:50]}")
                                    print(f"      [PAGE] Chunk problemático: {data_str[:100]}...")
                                    continue
                        
                        print(f"\n      [CHART] Respuesta recibida: {len(full_response)} caracteres, {chunk_count} chunks")
                        
                        if not full_response.strip():
                            print(f"      [WARNING]  Respuesta vacía recibida")
                            retry_count -= 1
                            continue
                        
                        # Procesar la respuesta completa
                        return procesar_respuesta_dify(full_response)
                    
                    except Exception as stream_error:
                        print(f"\n      [ERROR] Error procesando stream: {stream_error}")
                        retry_count -= 1
                        continue
                
                elif response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", 15))
                    print(f"      [WAIT] Rate limit - esperando {wait_time}s...")
                    time.sleep(wait_time)
                    retry_count -= 1
                
                elif response.status_code == 401:
                    print(f"      [ERROR] Error de autorización - verifica API key")
                    return None
                
                elif response.status_code == 400:
                    print(f"      [ERROR] Error 400 - Request inválido")
                    print(f"      [PAGE] Response: {response.text[:200]}")
                    return None
                
                else:
                    print(f"      [ERROR] Error HTTP {response.status_code}")
                    print(f"      [PAGE] Response: {response.text[:200]}")
                    retry_count -= 1
        
        except requests.exceptions.Timeout:
            print(f"      ⏰ Timeout - reintentando...")
            retry_count -= 1
            time.sleep(5)
        
        except Exception as e:
            print(f"      [ERROR] Error en petición: {e}")
            retry_count -= 1
            time.sleep(5)
    
    print(f"      [BOOM] Falló después de todos los intentos")
    return None

def procesar_respuesta_dify(response_text):
    """Procesa la respuesta de Dify y extrae el JSON"""
    
    try:
        print(f"      [SEARCH] Procesando respuesta completa ({len(response_text)} chars)")
        response_clean = response_text.strip()
        
        # Múltiples estrategias para extraer JSON
        json_candidates = []
        
        # 1. JSON entre bloques de código (más común en respuestas de AI)
        json_blocks = re.findall(r'```(?:json)?\s*(.*?)\s*```', response_clean, re.DOTALL)
        if json_blocks:
            print(f"      [CLIPBOARD] Encontrados {len(json_blocks)} bloques de código JSON")
            json_candidates.extend(json_blocks)
        
        # 2. Buscar JSON completo más agresivamente
        # Buscar desde la primera { hasta la última } balanceada
        brace_count = 0
        start_idx = -1
        end_idx = -1
        
        for i, char in enumerate(response_clean):
            if char == '{':
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    end_idx = i + 1
                    break
        
        if start_idx != -1 and end_idx != -1:
            json_candidate = response_clean[start_idx:end_idx]
            json_candidates.append(json_candidate)
            print(f"      [TARGET] JSON extraído por balanceo de llaves: {len(json_candidate)} chars")
        
        # 3. JSON directo si empieza y termina correctamente
        if response_clean.startswith('{') and response_clean.endswith('}'):
            json_candidates.append(response_clean)
        
        # 4. Buscar patrones específicos del prompt
        # Buscar desde "profile_analysis" hasta el final del JSON
        profile_match = re.search(r'(\{[^}]*"profile_analysis".*\})', response_clean, re.DOTALL)
        if profile_match:
            json_candidates.append(profile_match.group(1))
            print(f"      [TARGET] JSON extraído por patrón profile_analysis")
        
        print(f"      [CHART] Total candidatos JSON: {len(json_candidates)}")
        
        # Intentar parsear cada candidato
        for i, candidate in enumerate(json_candidates):
            try:
                print(f"      [TEST] Probando candidato {i+1}: {len(candidate)} chars")
                
                # Limpiar el JSON más agresivamente
                cleaned = candidate.strip()
                
                # Corregir problemas comunes de formato
                cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)  # Comas extra antes de } o ]
                cleaned = re.sub(r'//.*?\n', '\n', cleaned)  # Comentarios de línea
                cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)  # Comentarios de bloque
                
                # Corregir caracteres de control problemáticos
                cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
                
                # Corregir comillas mixtas (problema común en respuestas AI)
                # Detectar patrones con comillas simples en lugar de dobles para claves JSON
                cleaned = re.sub(r"'([^']+)':", r'"\1":', cleaned)  # 'key': -> "key":
                cleaned = re.sub(r":\s*'([^']*)'", r': "\1"', cleaned)  # : 'value' -> : "value"
                
                # Corregir valores entre corchetes (otro problema común)
                cleaned = re.sub(r'"\[([^\]]+)\]"', r'"\1"', cleaned)
                
                # Corregir strings que pueden tener comillas mal escapadas
                if '\\"' in cleaned:
                    cleaned = cleaned.replace('\\"', '"')
                
                # Intentar parsear
                resultado = json.loads(cleaned)
                print(f"      [OK] JSON parseado exitosamente (candidato {i+1})")
                print(f"      [CLIPBOARD] Claves principales encontradas: {list(resultado.keys())}")
                
                # Validar que tenga la estructura esperada del prompt
                if 'profile_analysis' in resultado:
                    print(f"      [TARGET] Estructura válida detectada")
                    return resultado
                else:
                    print(f"      [WARNING]  JSON válido pero sin estructura esperada")
                    continue
                
            except json.JSONDecodeError as e:
                print(f"      [ERROR] Error parsing candidato {i+1}: {str(e)[:100]}")
                continue
            except Exception as e:
                print(f"      [ERROR] Error inesperado candidato {i+1}: {e}")
                continue
        
        # Si nada funciona, mostrar más debug info y crear respuesta básica
        print(f"      [WARNING]  No se pudo parsear ningún JSON válido")
        print(f"      [PAGE] Muestra de respuesta: {response_text[:200]}...")
        print(f"      [PAGE] Final de respuesta: ...{response_text[-200:]}")
        
        return {
            "profile_analysis": {
                "username": "parse_error",
                "account_type_primary": "unknown",
                "parsing_status": "failed"
            },
            "marketing_priority_assessment": {
                "overall_carnival_value": "unknown"
            },
                         "debug_info": {
                 "response_length": len(response_text),
                 "candidates_tried": len(json_candidates),
                 "full_response": response_text  # Respuesta completa
             }
        }
        
    except Exception as e:
        print(f"      [ERROR] Error crítico procesando respuesta: {e}")
        return None

# =============================================================================
# 5. GUARDADO DE RESULTADOS
# =============================================================================

def guardar_resultado_analisis(username, datos_consolidados, analisis_dify):
    """Guarda el resultado final del análisis en YAML"""
    
    # Crear directorio de resultados
    resultados_dir = "data/Output/carnival_analysis"
    os.makedirs(resultados_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_resultado = os.path.join(resultados_dir, f"{username}_carnival_analysis_{timestamp}.yml")
    
    # Construir resultado completo
    resultado_completo = {
        'analysis_metadata': {
            'profile_username': username,
            'analysis_date': datetime.now().isoformat(),
            'pipeline_version': '1.0',
            'analysis_method': 'Integrated Pipeline (API + Media + Dify)',
            'data_sources': ['tiktok_api', 'media_downloader', 'dify_gpt4']
        },
        'data_completeness': datos_consolidados.get('data_completeness', {}),
        'profile_data_summary': {
            'basic_info': datos_consolidados.get('profile_basic_info', {}),
            'stats': datos_consolidados.get('profile_stats', {}),
            'videos_count': len(datos_consolidados.get('videos_list', [])),
            'media_analysis_available': bool(datos_consolidados.get('media_analysis'))
        },
        'carnival_analysis': analisis_dify,
        'raw_data_files': {
            'note': 'Raw data available in respective Output subdirectories',
            'user_info_location': 'data/Output/user_info/',
            'videos_info_location': 'data/Output/videos_info/',
            'media_results_location': 'data/Output/media/'
        }
    }
    
    try:
        with open(archivo_resultado, 'w', encoding='utf-8') as f:
            yaml.dump(resultado_completo, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"   [SAVE] Resultado guardado: {archivo_resultado}")
        return archivo_resultado
        
    except Exception as e:
        print(f"   [ERROR] Error guardando resultado: {e}")
        return None

# =============================================================================
# 6. FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal del analizador integrado"""
    
    print("[SHIP] CARNIVAL CRUISES - ANALIZADOR INTEGRADO COMPLETO")
    print("=" * 65)
    print(" [SHARE] Pipeline: API Info → Media Download → AI Analysis")
    print(" [ROBOT] AI Analysis: GPT-4 via Dify API")
    print(" [FOLDER] Formato: YAML para todos los archivos")
    print(" [TARGET] Objetivo: Análisis completo de audiencia TikTok")
    print("=" * 65)
    
    try:
        # 1. Cargar configuración
        print(f"\n[CLIPBOARD] PASO 1: Configuración")
        api_config = cargar_configuracion_dify()
        
        # 2. Detectar datos disponibles
        print(f"\n[CLIPBOARD] PASO 2: Detección de datos")
        usuarios_datos = detectar_datos_disponibles()
        
        if not usuarios_datos:
            print(f"\n[ERROR] No se encontraron datos del pipeline")
            print(f"   [IDEA] Ejecuta primero:")
            print(f"      1. python tiktok_api_analyzer.py")
            print(f"      2. python tiktok_media_downloader.py")
            return
        
        # 3. Cargar template del prompt
        print(f"\n[CLIPBOARD] PASO 3: Preparación del prompt")
        prompt_template = cargar_prompt_template()
        
        # 4. Procesar cada usuario
        print(f"\n[CLIPBOARD] PASO 4: Análisis de usuarios")
        resultados_totales = []
        
        for username, usuario_data in usuarios_datos.items():
            print(f"\n[USER] PROCESANDO: @{username}")
            print("-" * 50)
            
            # Cargar datos consolidados
            datos_consolidados = cargar_datos_usuario(usuario_data)
            
            if not datos_consolidados:
                print(f"   [ERROR] No se pudieron cargar datos para @{username}")
                continue
            
            # Mostrar completitud de datos
            completitud = datos_consolidados['data_completeness']
            print(f"   [CHART] Completitud de datos:")
            print(f"      [USER] User info: {'[OK]' if completitud['has_user_info'] else '[ERROR]'}")
            print(f"      [VIDEO] Videos info: {'[OK]' if completitud['has_videos_info'] else '[ERROR]'}")
            print(f"      [SEARCH] Video details: {'[OK]' if completitud['has_video_details'] else '[ERROR]'}")
            print(f"      [PHONE] Media results: {'[OK]' if completitud['has_media_results'] else '[ERROR]'}")
            
            # Preparar datos para prompt
            datos_prompt = preparar_datos_para_prompt(datos_consolidados, username)
            prompt_final = crear_prompt_final(prompt_template, datos_prompt)
            
            # Analizar con Dify
            analisis_result = analizar_con_dify(api_config, prompt_final, username)
            
            if analisis_result:
                # Guardar resultado
                archivo_guardado = guardar_resultado_analisis(username, datos_consolidados, analisis_result)
                
                if archivo_guardado:
                    resultados_totales.append({
                        'username': username,
                        'archivo': archivo_guardado,
                        'analisis': analisis_result
                    })
                    
                    # Mostrar resumen del análisis
                    profile_analysis = analisis_result.get('profile_analysis', {})
                    account_type = profile_analysis.get('account_type_primary', 'Unknown')
                    cruise_potential = analisis_result.get('marketing_priority_assessment', {}).get('overall_carnival_value', 'Unknown')
                    
                    print(f"   [TAG]  Tipo de cuenta: {account_type}")
                    print(f"   [TARGET] Potencial Carnival: {cruise_potential}")
                    print(f"   [OK] Análisis completado exitosamente")
                else:
                    print(f"   [ERROR] Error guardando resultado")
            else:
                print(f"   [ERROR] Error en análisis con Dify")
        
        # 5. Resumen final
        print(f"\n{'='*65}")
        print(f"[CHART] RESUMEN FINAL")
        print(f"{'='*65}")
        print(f"[USERS] Usuarios detectados: {len(usuarios_datos)}")
        print(f"[OK] Análisis completados: {len(resultados_totales)}")
        
        if resultados_totales:
            print(f"\n[FOLDER] Resultados guardados en: data/Output/carnival_analysis/")
            for resultado in resultados_totales:
                print(f"   [PAGE] @{resultado['username']}: {os.path.basename(resultado['archivo'])}")
            
            print(f"\n[PARTY] PIPELINE COMPLETADO EXITOSAMENTE")
            print(f"[IDEA] Los archivos YAML contienen el análisis completo para Carnival Cruises")
        else:
            print(f"\n[ERROR] No se completó ningún análisis")
        
    except Exception as e:
        print(f"\n[BOOM] ERROR CRÍTICO: {e}")
        traceback.print_exc()

# =============================================================================
# 7. PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    main() 