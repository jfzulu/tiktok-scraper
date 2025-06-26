# =============================================================================
# TIKTOK API ANALYZER - VERSION 2.0
# Carnival Cruises Audience Analysis Tool
# =============================================================================
# Nuevo enfoque usando APIs en lugar de scraping para evitar captchas
# Primer paso: Extracción de información básica de usuarios

import os
import json
import yaml
import time
import requests
import pandas as pd
from datetime import datetime
from configparser import ConfigParser
import traceback

# =============================================================================
# 1. CONFIGURACIÓN Y CARGA DE API KEYS
# =============================================================================

def cargar_configuracion():
    """Carga la configuración desde el archivo config_api.ini"""
    config = ConfigParser()
    config_path = 'config/config_api.ini'
    
    try:
        config.read(config_path)
        print(f"[OK] Configuracion cargada desde: {config_path}")
        
        # Validar que existan las secciones necesarias
        required_sections = ['tiktok_api', 'tiktok_scraper_api', 'video_detail_api', 'general_config', 'testing']
        for section in required_sections:
            if section not in config:
                raise KeyError(f"Seccion '{section}' no encontrada en configuracion")
        
        # Crear objeto de configuración
        app_config = {
            # API principal (info de usuarios)
            'rapidapi_key': config['tiktok_api']['rapidapi_key'],
            'rapidapi_host': config['tiktok_api']['rapidapi_host'],
            # API alternativa (videos)
            'scraper_rapidapi_key': config['tiktok_scraper_api']['rapidapi_key'],
            'scraper_rapidapi_host': config['tiktok_scraper_api']['rapidapi_host'],
            # API de detalles de video
            'video_detail_rapidapi_key': config['video_detail_api']['rapidapi_key'],
            'video_detail_rapidapi_host': config['video_detail_api']['rapidapi_host'],
            'video_detail_endpoint': config['video_detail_api']['endpoint'],
            # Configuración general
            'output_base_dir': config['general_config']['output_base_dir'],
            'max_retries': int(config['general_config']['max_retries']),
            'request_timeout': int(config['general_config']['request_timeout']),
            'test_username': config['testing']['test_username']
        }
        
        # Mostrar API keys enmascaradas para verificación
        masked_key = f"{app_config['rapidapi_key'][:4]}...{app_config['rapidapi_key'][-4:]}"
        masked_scraper_key = f"{app_config['scraper_rapidapi_key'][:4]}...{app_config['scraper_rapidapi_key'][-4:]}"
        masked_detail_key = f"{app_config['video_detail_rapidapi_key'][:4]}...{app_config['video_detail_rapidapi_key'][-4:]}"
        print(f"   [KEY] API Key (Principal): {masked_key}")
        print(f"   [HOST] Host (Principal): {app_config['rapidapi_host']}")
        print(f"   [KEY] API Key (Videos): {masked_scraper_key}")
        print(f"   [HOST] Host (Videos): {app_config['scraper_rapidapi_host']}")
        print(f"   [KEY] API Key (Detalles): {masked_detail_key}")
        print(f"   [HOST] Host (Detalles): {app_config['video_detail_rapidapi_host']}")
        print(f"   [USER] Usuario de prueba: {app_config['test_username']}")
        
        return app_config
        
    except Exception as e:
        print(f"[ERROR] Error cargando configuracion: {e}")
        raise

# =============================================================================
# 2. CONFIGURACIÓN DE DIRECTORIOS
# =============================================================================

def configurar_directorios(username, config):
    """Configura los directorios de salida organizados (directamente en Output)"""
    
    # Estructura de directorios simplificada - directamente en base_dir
    base_dir = config['output_base_dir']
    
    # Subdirectorios directamente en Output (sin subcarpetas de sesión/usuario)
    subdirs = {
        'user_info': os.path.join(base_dir, 'user_info'),
        'videos_info': os.path.join(base_dir, 'videos_info')
    }
    
    # Crear directorios (se sobreescriben si ya existen)
    for dir_name, dir_path in subdirs.items():
        os.makedirs(dir_path, exist_ok=True)
        print(f"   [FOLDER] Configurado: {dir_name}")
    
    # Para mantener compatibilidad, retornamos base_dir como user_dir y session_dir
    return base_dir, subdirs, base_dir

# =============================================================================
# 3. FUNCIÓN PRINCIPAL DE EXTRACCIÓN DE INFORMACIÓN DE USUARIO
# =============================================================================

def obtener_info_usuario_tiktok(username, config):
    """
    Obtiene información detallada de un usuario de TikTok usando la API
    
    Args:
        username (str): Nombre de usuario de TikTok (sin @)
        config (dict): Configuración con API keys y parámetros
        
    Returns:
        dict: Información completa del usuario o None si falla
    """
    print(f"\n[TARGET] Obteniendo información de usuario: @{username}")
    
    # URL y parámetros de la API
    url = "https://tiktok-api23.p.rapidapi.com/api/user/info-with-region"
    querystring = {"uniqueId": username}
    
    headers = {
        "x-rapidapi-key": config['rapidapi_key'],
        "x-rapidapi-host": config['rapidapi_host']
    }
    
    # Realizar solicitud con reintentos
    for intento in range(1, config['max_retries'] + 1):
        try:
            print(f"   [SATELLITE] Intento {intento}/{config['max_retries']} - Llamando a API...")
            
            response = requests.get(
                url, 
                headers=headers, 
                params=querystring,
                timeout=config['request_timeout']
            )
            
            # Verificar código de estado
            if response.status_code == 200:
                print(f"   [OK] Respuesta exitosa - Status: {response.status_code}")
                
                # Parsear respuesta JSON
                data = response.json()
                
                # Validar que la respuesta tenga la estructura esperada
                if 'userInfo' in data and 'statusCode' in data:
                    if data['statusCode'] == 0:
                        print(f"   [PARTY] Información obtenida exitosamente")
                        return data
                    else:
                        print(f"   [WARNING]  API devolvió error: {data.get('statusMsg', 'Error desconocido')}")
                        return None
                else:
                    print(f"   [WARNING]  Estructura de respuesta inesperada")
                    return None
                    
            elif response.status_code == 429:
                print(f"   [WAIT] Rate limit alcanzado - Esperando antes del siguiente intento...")
                time.sleep(5)
                continue
                
            else:
                print(f"   [ERROR] Error HTTP {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   [WAIT] Timeout en intento {intento}")
            time.sleep(2)
            
        except requests.exceptions.RequestException as e:
            print(f"   [ERROR] Error de conexión en intento {intento}: {e}")
            time.sleep(2)
            
        except json.JSONDecodeError as e:
            print(f"   [ERROR] Error parseando JSON en intento {intento}: {e}")
            time.sleep(2)
            
        except Exception as e:
            print(f"   [ERROR] Error inesperado en intento {intento}: {e}")
            time.sleep(2)
    
    print(f"   [BOOM] Falló después de {config['max_retries']} intentos")
    return None

# =============================================================================
# 4. PROCESAMIENTO Y ESTRUCTURACIÓN DE DATOS
# =============================================================================

def procesar_datos_usuario(raw_data, username):
    """
    Procesa y estructura los datos crudos de la API en un formato organizado
    
    Args:
        raw_data (dict): Datos crudos de la API
        username (str): Nombre de usuario
        
    Returns:
        dict: Datos procesados y estructurados
    """
    print(f"   [SHARE] Procesando datos para @{username}...")
    
    try:
        user_info = raw_data.get('userInfo', {})
        user = user_info.get('user', {})
        stats = user_info.get('stats', {})
        stats_v2 = user_info.get('statsV2', {})
        share_meta = raw_data.get('shareMeta', {})
        
        # Datos estructurados
        datos_procesados = {
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "extraction_method": "TikTok API (RapidAPI)",
                "username_requested": username,
                "api_version": "tiktok-api23",
                "status_code": raw_data.get('statusCode', -1),
                "status_message": raw_data.get('statusMsg', '')
            },
            
            "profile_basic_info": {
                "id": user.get('id'),
                "unique_id": user.get('uniqueId'),
                "nickname": user.get('nickname'),
                "signature": user.get('signature', ''),
                "verified": user.get('verified', False),
                "private_account": user.get('privateAccount', False),
                "region": user.get('region', ''),
                "language": user.get('language', ''),
                "create_time": user.get('createTime'),
                "is_organization": user.get('isOrganization', 0)
            },
            
            "profile_media": {
                "avatar_large": user.get('avatarLarger', ''),
                "avatar_medium": user.get('avatarMedium', ''),
                "avatar_thumb": user.get('avatarThumb', '')
            },
            
            "profile_stats": {
                "follower_count": stats.get('followerCount', 0),
                "following_count": stats.get('followingCount', 0),
                "heart_count": stats.get('heartCount', 0),
                "video_count": stats.get('videoCount', 0),
                "digg_count": stats.get('diggCount', 0),
                "friend_count": stats.get('friendCount', 0)
            },
            
            "profile_stats_v2": {
                "follower_count": stats_v2.get('followerCount', '0'),
                "following_count": stats_v2.get('followingCount', '0'),
                "heart_count": stats_v2.get('heartCount', '0'),
                "video_count": stats_v2.get('videoCount', '0'),
                "digg_count": stats_v2.get('diggCount', '0'),
                "friend_count": stats_v2.get('friendCount', '0')
            },
            
            "commerce_info": {
                "commerce_user": user.get('commerceUserInfo', {}).get('commerceUser', False),
                "category": user.get('commerceUserInfo', {}).get('category', ''),
                "tt_seller": user.get('ttSeller', False)
            },
            
            "profile_settings": {
                "comment_setting": user.get('commentSetting', 0),
                "duet_setting": user.get('duetSetting', 0),
                "stitch_setting": user.get('stitchSetting', 0),
                "download_setting": user.get('downloadSetting', 0),
                "following_visibility": user.get('followingVisibility', 1)
            },
            
            "bio_link": user.get('bioLink', {}),
            
            "share_metadata": {
                "title": share_meta.get('title', ''),
                "description": share_meta.get('desc', '')
            },
            
            "raw_api_response": raw_data
        }
        
        print(f"   [OK] Datos procesados exitosamente")
        print(f"      [USER] Usuario: {datos_procesados['profile_basic_info']['nickname']}")
        print(f"      [USERS] Seguidores: {datos_procesados['profile_stats']['follower_count']:,}")
        print(f"      [MOVIE] Videos: {datos_procesados['profile_stats']['video_count']:,}")
        print(f"      [HEART]  Likes: {datos_procesados['profile_stats']['heart_count']:,}")
        
        return datos_procesados
        
    except Exception as e:
        print(f"   [ERROR] Error procesando datos: {e}")
        traceback.print_exc()
        return None

# =============================================================================
# 5. GUARDADO DE RESULTADOS
# =============================================================================

def guardar_resultados_usuario(datos_procesados, username, subdirs):
    """
    Guarda los resultados de información de usuario en archivo YAML (nombre fijo, se sobreescribe)
    
    Args:
        datos_procesados (dict): Datos estructurados del usuario
        username (str): Nombre de usuario
        subdirs (dict): Diccionario con rutas de subdirectorios
        
    Returns:
        str: Ruta del archivo guardado
    """
    print(f"   [SAVE] Guardando información de usuario para @{username}...")
    
    try:
        # Guardar información completa del usuario (nombre fijo, formato YAML)
        user_info_file = os.path.join(
            subdirs['user_info'], 
            f"{username}_user_info.yml"
        )
        
        with open(user_info_file, 'w', encoding='utf-8') as f:
            yaml.dump(datos_procesados, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"      [PAGE] Info guardada: {os.path.basename(user_info_file)}")
        print(f"   [OK] Archivo YAML guardado exitosamente (sobreescrito)")
        return user_info_file
        
    except Exception as e:
        print(f"   [ERROR] Error guardando archivo: {e}")
        return None

# =============================================================================
# 6. FUNCIONES PARA OBTENER VIDEOS
# =============================================================================

def obtener_videos_usuario_tiktok(sec_uid, username, config, count=20):
    """
    Obtiene los últimos videos de un usuario de TikTok usando la API
    
    Args:
        sec_uid (str): SecUid del usuario obtenido de la info básica
        username (str): Nombre de usuario de TikTok (para logging)
        config (dict): Configuración con API keys y parámetros
        count (int): Número de videos a obtener (máximo 35, default 20)
        
    Returns:
        dict: Información de videos o None si falla
    """
    print(f"\n[MOVIE] Obteniendo últimos {count} videos de @{username}...")
    
    # URL y parámetros de la API de videos
    url = "https://tiktok-api23.p.rapidapi.com/api/user/posts"
    querystring = {
        "secUid": sec_uid,
        "count": str(min(count, 35)),  # Máximo 35 según la API
        "cursor": "0"
    }
    
    headers = {
        "x-rapidapi-key": config['rapidapi_key'],
        "x-rapidapi-host": config['rapidapi_host']
    }
    
    # Realizar solicitud con reintentos
    for intento in range(1, config['max_retries'] + 1):
        try:
            print(f"   [SATELLITE] Intento {intento}/{config['max_retries']} - Llamando a API de videos...")
            
            response = requests.get(
                url, 
                headers=headers, 
                params=querystring,
                timeout=config['request_timeout']
            )
            
            # Verificar código de estado
            if response.status_code == 200:
                print(f"   [OK] Respuesta exitosa - Status: {response.status_code}")
                
                # Parsear respuesta JSON
                data = response.json()
                
                # Validar que la respuesta tenga la estructura esperada
                if 'data' in data and 'statusCode' in data:
                    if data['statusCode'] == 0:
                        videos_count = len(data.get('data', []))
                        print(f"   [PARTY] {videos_count} videos obtenidos exitosamente")
                        return data
                    else:
                        print(f"   [WARNING]  API devolvió error: {data.get('statusMsg', 'Error desconocido')}")
                        return None
                else:
                    print(f"   [WARNING]  Estructura de respuesta inesperada")
                    return None
                    
            elif response.status_code == 429:
                print(f"   [WAIT] Rate limit alcanzado - Esperando antes del siguiente intento...")
                time.sleep(5)
                continue
                
            else:
                print(f"   [ERROR] Error HTTP {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   [WAIT] Timeout en intento {intento}")
            time.sleep(2)
            
        except requests.exceptions.RequestException as e:
            print(f"   [ERROR] Error de conexión en intento {intento}: {e}")
            time.sleep(2)
            
        except json.JSONDecodeError as e:
            print(f"   [ERROR] Error parseando JSON en intento {intento}: {e}")
            time.sleep(2)
            
        except Exception as e:
            print(f"   [ERROR] Error inesperado en intento {intento}: {e}")
            time.sleep(2)
    
    print(f"   [BOOM] Falló después de {config['max_retries']} intentos")
    return None

def obtener_videos_usuario_scraper_api(user_id, username, config, count=15):
    """
    Obtiene los últimos videos de un usuario usando la API alternativa (tiktok-scraper7)
    Implementa paginación para obtener más videos usando cursor
    
    Args:
        user_id (str): ID del usuario obtenido de la info básica
        username (str): Nombre de usuario de TikTok (para logging)
        config (dict): Configuración con API keys y parámetros
        count (int): Número total de videos a obtener (default 15)
        
    Returns:
        dict: Información de videos o None si falla
    """
    print(f"\n[MOVIE] [API SCRAPER7] Obteniendo últimos {count} videos de @{username}...")
    print(f"   [KEY] User ID: {user_id}")
    
    # URL y headers
    url = "https://tiktok-scraper7.p.rapidapi.com/user/posts"
    headers = {
        "x-rapidapi-key": config['scraper_rapidapi_key'],
        "x-rapidapi-host": "tiktok-scraper7.p.rapidapi.com"
    }
    
    # Variables para paginación
    all_videos = []
    cursor = "0"
    page = 1
    videos_per_request = min(count, 15)  # Máximo por petición
    
    print(f"   [SATELLITE] Llamando a API con paginación: {url}")
    
    try:
        while len(all_videos) < count:
            # Calcular cuántos videos necesitamos en esta petición
            remaining_videos = count - len(all_videos)
            current_count = min(remaining_videos, videos_per_request)
            
            querystring = {
                "user_id": str(user_id),
                "count": str(current_count),
                "cursor": cursor
            }
            
            print(f"   [CLIPBOARD] Página {page}: cursor={cursor}, count={current_count}")
            
            # Realizar la petición
            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            
            if response.status_code != 200:
                print(f"   [ERROR] Error HTTP {response.status_code}")
                print(f"   [PAGE] Respuesta: {response.text[:200]}...")
                break
            
            # Obtener la respuesta en formato JSON
            data = response.json()
            
            # Extraer videos de esta página
            current_videos = []
            has_more = False
            new_cursor = None
            
            if 'data' in data:
                if 'videos' in data['data']:
                    current_videos = data['data']['videos']
                    has_more = data['data'].get('hasMore', False)
                    new_cursor = data['data'].get('cursor', None)
                elif isinstance(data['data'], list):
                    current_videos = data['data']
                    # Para estructuras de lista simple, asumimos que no hay más si obtenemos menos del solicitado
                    has_more = len(current_videos) >= current_count
            
            # Validar que current_videos es una lista de diccionarios
            if not isinstance(current_videos, list):
                print(f"      [WARNING]  current_videos no es una lista: {type(current_videos)}")
                current_videos = []
            
            # Filtrar solo videos válidos (diccionarios)
            valid_videos = []
            for i, video in enumerate(current_videos):
                if isinstance(video, dict):
                    valid_videos.append(video)
                else:
                    print(f"      [WARNING]  Video {i+1} en página {page} no es diccionario: {type(video)}")
            
            current_videos = valid_videos
            
            videos_found = len(current_videos)
            print(f"      [OK] {videos_found} videos obtenidos en página {page}")
            
            if videos_found == 0:
                print(f"      [WARNING]  No se encontraron más videos")
                break
            
            # Agregar videos a la lista total
            all_videos.extend(current_videos)
            
            # Verificar si hay más páginas
            if not has_more or not new_cursor or new_cursor == cursor:
                print(f"      [EMOJI] No hay más videos disponibles")
                break
            
            # Preparar para la siguiente página
            cursor = new_cursor
            page += 1
            
            # Pausa entre páginas para evitar rate limiting
            time.sleep(1)
        
        # Truncar a la cantidad solicitada
        all_videos = all_videos[:count]
        
        print(f"   [PARTY] Total de {len(all_videos)} videos obtenidos en {page} páginas")
        
        # Construir respuesta unificada
        unified_response = {
            "code": 0,
            "msg": "success",
            "processed_time": 0,
            "data": {
                "videos": all_videos,
                "cursor": cursor,
                "hasMore": len(all_videos) == count and has_more
            }
        }
        
        return unified_response
        
    except requests.exceptions.RequestException as e:
        print(f"   [ERROR] Error en la petición: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"   [ERROR] Error al decodificar JSON: {e}")
        return None
    except Exception as e:
        print(f"   [ERROR] Error inesperado: {e}")
        return None

def procesar_datos_videos_scraper_api(raw_video_data, username):
    """
    Procesa datos de videos de la API scraper (tiktok-scraper7) con estructura mejorada
    Basado en el enfoque del pytest_video.py funcional
    
    Args:
        raw_video_data (dict): Datos crudos de la API scraper
        username (str): Nombre de usuario
        
    Returns:
        dict: Datos de videos procesados y estructurados
    """
    print(f"   [SHARE] Procesando datos de videos (API Scraper7) para @{username}...")
    
    try:
        # Detectar estructura de datos dinámicamente
        videos_raw = []
        estructura_detectada = "desconocida"
        
        if 'data' in raw_video_data:
            data_section = raw_video_data['data']
            
            if isinstance(data_section, list):
                videos_raw = data_section
                estructura_detectada = "data[]"
            elif 'posts' in data_section:
                videos_raw = data_section['posts']
                estructura_detectada = "data.posts[]"
            elif 'videos' in data_section:
                videos_raw = data_section['videos']
                estructura_detectada = "data.videos[]"
            elif isinstance(data_section, dict):
                # Buscar la primera clave que contenga una lista
                for key, value in data_section.items():
                    if isinstance(value, list) and len(value) > 0:
                        videos_raw = value
                        estructura_detectada = f"data.{key}[]"
                        break
        
        # Validar que tenemos videos válidos
        if not videos_raw:
            print(f"   [WARNING]  No se encontraron videos en la respuesta")
            return None
        
        print(f"   [CHART] Estructura detectada: {estructura_detectada}")
        print(f"   [VIDEO] Videos encontrados: {len(videos_raw)}")
        
        # Datos estructurados
        datos_videos_procesados = {
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "extraction_method": "TikTok Scraper7 API (RapidAPI - pytest_video approach)",
                "username": username,
                "api_version": "tiktok-scraper7",
                "structure_detected": estructura_detectada,
                "status_code": raw_video_data.get('code', raw_video_data.get('statusCode', 200)),
                "status_message": raw_video_data.get('msg', raw_video_data.get('message', 'OK')),
                "total_videos_extracted": len(videos_raw)
            },
            
            "videos_summary": {
                "total_videos": len(videos_raw),
                "has_more": raw_video_data.get('hasMore', False),
                "api_response_code": raw_video_data.get('code', raw_video_data.get('statusCode', 200))
            },
            
            "videos_list": [],
            
            "raw_api_response": raw_video_data
        }
        
        # Procesar cada video con detección flexible de campos
        for i, video in enumerate(videos_raw):
            try:
                # DEBUG: Mostrar tipo y contenido del video
                print(f"      [SEARCH] DEBUG Video {i+1}: tipo={type(video)}")
                if not isinstance(video, dict):
                    print(f"         Contenido: {str(video)[:100]}...")
                
                # Verificar que el video sea un diccionario válido
                if not isinstance(video, dict):
                    print(f"      [WARNING]  Video {i+1} no es un diccionario válido")
                    continue
                
                # DEBUG: Verificar campos específicos
                print(f"         author tipo: {type(video.get('author', 'N/A'))}")
                print(f"         music_info tipo: {type(video.get('music_info', 'N/A'))}")
                
                # Campos básicos con múltiples posibilidades (safe access)
                video_id = (video.get('video_id') or 
                           video.get('id') or 
                           video.get('aweme_id') or 
                           video.get('videoId', ''))
                
                title = (video.get('title') or 
                        video.get('desc') or 
                        video.get('description', ''))
                
                # Proceso individual paso a paso con debug
                try:
                    author_safe = video.get('author', {})
                    if not isinstance(author_safe, dict):
                        author_safe = {}
                    
                    music_info_safe = video.get('music_info', {})
                    if not isinstance(music_info_safe, dict):
                        music_info_safe = {}
                    
                    music_safe = video.get('music', {})
                    if not isinstance(music_safe, dict):
                        music_safe = {}
                    
                    video_processed = {
                        "video_index": i + 1,
                        "video_id": str(video_id),
                        "aweme_id": video.get('aweme_id', video_id),
                        "title": title,
                        "region": video.get('region', ''),
                        "create_time": video.get('create_time', video.get('createTime', 0)),
                        "duration": video.get('duration', 0),
                        "author_info": {
                            "id": author_safe.get('id', ''),
                            "unique_id": author_safe.get('unique_id', author_safe.get('uniqueId', '')),
                            "nickname": author_safe.get('nickname', ''),
                            "avatar": author_safe.get('avatar', '')
                        },
                        "video_stats": {
                            "play_count": video.get('play_count', video.get('playCount', 0)),
                            "digg_count": video.get('digg_count', video.get('diggCount', 0)),
                            "comment_count": video.get('comment_count', video.get('commentCount', 0)),
                            "share_count": video.get('share_count', video.get('shareCount', 0)),
                            "download_count": video.get('download_count', 0),
                            "collect_count": video.get('collect_count', video.get('collectCount', 0))
                        },
                        "video_info": {
                            "duration": video.get('duration', 0),
                            "size": video.get('size', 0),
                            "cover": video.get('cover', ''),
                            "ai_dynamic_cover": video.get('ai_dynamic_cover', ''),
                            "origin_cover": video.get('origin_cover', ''),
                            "play_url": video.get('play', video.get('playAddr', '')),
                            "wmplay_url": video.get('wmplay', '')
                        },
                        "music_info": {
                            "id": music_info_safe.get('id', music_safe.get('id', '')),
                            "title": music_info_safe.get('title', music_safe.get('title', '')),
                            "author": music_info_safe.get('author', music_safe.get('authorName', '')),
                            "duration": music_info_safe.get('duration', music_safe.get('duration', 0)),
                            "original": music_info_safe.get('original', music_safe.get('original', False)),
                            "play_url": music_info_safe.get('play', music_safe.get('playUrl', '')),
                            "cover": music_info_safe.get('cover', '')
                        },
                        "hashtags": [],
                        "mentions": [],
                        "mentioned_users": video.get('mentioned_users', ''),
                        "is_ad": video.get('is_ad', False),
                        "item_comment_settings": video.get('item_comment_settings', 0),
                        "images": video.get('images', [])  # Para posts de imagen
                    }
                except Exception as e:
                    print(f"         [ERROR] Error específico creando video_processed: {e}")
                    continue
                
                # Extraer hashtags y menciones del título
                if title:
                    import re
                    hashtags = re.findall(r'#[a-zA-Z0-9_]+', title)
                    video_processed["hashtags"] = hashtags
                    
                    mentions = re.findall(r'@[a-zA-Z0-9_.]+', title)
                    video_processed["mentions"] = mentions
                
                datos_videos_procesados["videos_list"].append(video_processed)
                print(f"      [OK] Video {i+1}: {video_id} - {title[:30]}...")
                
            except Exception as e:
                print(f"      [WARNING]  Error procesando video {i+1}: {e}")
                continue
        
        videos_procesados = len(datos_videos_procesados['videos_list'])
        print(f"   [OK] {videos_procesados} videos procesados exitosamente de {len(videos_raw)} encontrados")
        
        # Estadísticas rápidas
        if datos_videos_procesados["videos_list"]:
            total_plays = sum(v['video_stats']['play_count'] for v in datos_videos_procesados['videos_list'])
            total_likes = sum(v['video_stats']['digg_count'] for v in datos_videos_procesados['videos_list'])
            total_comments = sum(v['video_stats']['comment_count'] for v in datos_videos_procesados['videos_list'])
            total_shares = sum(v['video_stats']['share_count'] for v in datos_videos_procesados['videos_list'])
            
            print(f"      [PHONE] Total reproducciones: {total_plays:,}")
            print(f"      [EMOJI] Total likes: {total_likes:,}")
            print(f"      [CHAT] Total comentarios: {total_comments:,}")
            print(f"      [SHARE] Total shares: {total_shares:,}")
        
        return datos_videos_procesados
        
    except Exception as e:
        print(f"   [ERROR] Error procesando datos de videos: {e}")
        traceback.print_exc()
        return None

def procesar_datos_videos(raw_video_data, username):
    """
    Procesa y estructura los datos crudos de videos de la API
    
    Args:
        raw_video_data (dict): Datos crudos de la API de videos
        username (str): Nombre de usuario
        
    Returns:
        dict: Datos de videos procesados y estructurados
    """
    print(f"   [SHARE] Procesando datos de videos para @{username}...")
    
    try:
        videos_raw = raw_video_data.get('data', [])
        
        # Datos estructurados
        datos_videos_procesados = {
            "extraction_metadata": {
                "extraction_date": datetime.now().isoformat(),
                "extraction_method": "TikTok Videos API (RapidAPI)",
                "username": username,
                "api_version": "tiktok-api23",
                "status_code": raw_video_data.get('statusCode', -1),
                "total_videos_extracted": len(videos_raw)
            },
            
            "videos_summary": {
                "total_videos": len(videos_raw),
                "has_more": raw_video_data.get('hasMore', False),
                "cursor": raw_video_data.get('cursor', '0')
            },
            
            "videos_list": [],
            
            "raw_api_response": raw_video_data
        }
        
        # Procesar cada video
        for i, video in enumerate(videos_raw):
            try:
                video_processed = {
                    "video_index": i + 1,
                    "video_id": video.get('id', ''),
                    "description": video.get('desc', ''),
                    "create_time": video.get('createTime', 0),
                    "author_info": {
                        "id": video.get('author', {}).get('id', ''),
                        "unique_id": video.get('author', {}).get('uniqueId', ''),
                        "nickname": video.get('author', {}).get('nickname', '')
                    },
                    "video_stats": {
                        "digg_count": video.get('stats', {}).get('diggCount', 0),
                        "share_count": video.get('stats', {}).get('shareCount', 0),
                        "comment_count": video.get('stats', {}).get('commentCount', 0),
                        "play_count": video.get('stats', {}).get('playCount', 0),
                        "collect_count": video.get('stats', {}).get('collectCount', 0)
                    },
                    "video_info": {
                        "duration": video.get('video', {}).get('duration', 0),
                        "ratio": video.get('video', {}).get('ratio', ''),
                        "cover": video.get('video', {}).get('cover', ''),
                        "download_addr": video.get('video', {}).get('downloadAddr', '')
                    },
                    "music_info": {
                        "id": video.get('music', {}).get('id', ''),
                        "title": video.get('music', {}).get('title', ''),
                        "author_name": video.get('music', {}).get('authorName', ''),
                        "duration": video.get('music', {}).get('duration', 0)
                    },
                    "hashtags": [],
                    "mentions": []
                }
                
                # Extraer hashtags de la descripción
                description = video.get('desc', '')
                if description:
                    import re
                    hashtags = re.findall(r'#[a-zA-Z0-9_]+', description)
                    video_processed["hashtags"] = hashtags
                    
                    mentions = re.findall(r'@[a-zA-Z0-9_.]+', description)
                    video_processed["mentions"] = mentions
                
                datos_videos_procesados["videos_list"].append(video_processed)
                
            except Exception as e:
                print(f"      [WARNING]  Error procesando video {i+1}: {e}")
                continue
        
        print(f"   [OK] {len(datos_videos_procesados['videos_list'])} videos procesados exitosamente")
        
        # Estadísticas rápidas
        total_likes = sum(v['video_stats']['digg_count'] for v in datos_videos_procesados['videos_list'])
        total_comments = sum(v['video_stats']['comment_count'] for v in datos_videos_procesados['videos_list'])
        total_shares = sum(v['video_stats']['share_count'] for v in datos_videos_procesados['videos_list'])
        
        print(f"      [EMOJI] Total likes: {total_likes:,}")
        print(f"      [CHAT] Total comentarios: {total_comments:,}")
        print(f"      [SHARE] Total shares: {total_shares:,}")
        
        return datos_videos_procesados
        
    except Exception as e:
        print(f"   [ERROR] Error procesando datos de videos: {e}")
        traceback.print_exc()
        return None

def leer_user_id_desde_archivo(username, subdirs):
    """
    Lee el user_id desde el archivo YAML de información del usuario
    
    Args:
        username (str): Nombre de usuario
        subdirs (dict): Diccionario con rutas de subdirectorios
        
    Returns:
        str: User ID encontrado o None si no se encuentra
    """
    try:
        user_info_dir = subdirs['user_info']
        
        # Archivo YAML con nombre fijo
        user_file = f"{username}_user_info.yml"
        user_file_path = os.path.join(user_info_dir, user_file)
        
        if not os.path.exists(user_file_path):
            print(f"   [WARNING]  No se encontró archivo de usuario: {user_file}")
            return None
        
        print(f"   [EMOJI] Leyendo user_id desde: {user_file}")
        
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = yaml.safe_load(f)
        
        user_id = user_data.get('profile_basic_info', {}).get('id', '')
        
        if user_id:
            print(f"   [KEY] User ID encontrado: {user_id}")
            return user_id
        else:
            print(f"   [ERROR] No se encontró user_id en el archivo")
            return None
            
    except Exception as e:
        print(f"   [ERROR] Error leyendo user_id desde archivo: {e}")
        return None

def guardar_resultados_videos(datos_videos_procesados, username, subdirs):
    """
    Guarda los resultados de videos en archivo YAML (nombre fijo, se sobreescribe)
    
    Args:
        datos_videos_procesados (dict): Datos estructurados de videos
        username (str): Nombre de usuario
        subdirs (dict): Diccionario con rutas de subdirectorios
        
    Returns:
        str: Ruta del archivo guardado
    """
    print(f"   [SAVE] Guardando información de videos para @{username}...")
    
    try:
        # Guardar información completa de videos (nombre fijo, formato YAML)
        videos_info_file = os.path.join(
            subdirs['videos_info'], 
            f"{username}_videos.yml"
        )
        
        with open(videos_info_file, 'w', encoding='utf-8') as f:
            yaml.dump(datos_videos_procesados, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"      [PAGE] Videos guardados: {os.path.basename(videos_info_file)}")
        print(f"   [OK] Archivo YAML de videos guardado exitosamente (sobreescrito)")
        return videos_info_file
        
    except Exception as e:
        print(f"   [ERROR] Error guardando archivo de videos: {e}")
        return None

# =============================================================================
# 6B. FUNCIONES PARA DETALLES DE VIDEOS
# =============================================================================

def obtener_detalle_video(video_id, config):
    """
    Obtiene información detallada de un video específico usando la API de TikTok Detail
    """
    try:
        print(f"[SEARCH] Obteniendo detalles del video: {video_id}")
        
        # Obtener configuración de la API de detalles de video
        api_key = config['video_detail_rapidapi_key']
        host = config['video_detail_rapidapi_host']
        endpoint = config['video_detail_endpoint']
        
        url = f"https://{host}{endpoint}"
        
        querystring = {"videoId": video_id}
        
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": host
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] Detalles obtenidos exitosamente para video {video_id}")
            return data
        else:
            print(f"  [ERROR] Error HTTP {response.status_code} para video {video_id}")
            print(f"  [PAGE] Respuesta: {response.text[:200]}...")
            return None
            
    except requests.exceptions.Timeout:
        print(f"  ⏰ Timeout al obtener detalles del video {video_id}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Error de conexión para video {video_id}: {e}")
        return None
    except Exception as e:
        print(f"  [ERROR] Error inesperado para video {video_id}: {e}")
        return None

def obtener_detalles_videos_batch(video_ids, config, directorio_sesion):
    """
    Obtiene detalles de múltiples videos y guarda los resultados
    """
    try:
        print(f"\n[MOVIE] === OBTENIENDO DETALLES DE {len(video_ids)} VIDEOS ===")
        
        detalles_videos = []
        
        for idx, video_id in enumerate(video_ids, 1):
            print(f"\n[VIDEO] Procesando video {idx}/{len(video_ids)}: {video_id}")
            
            detalle = obtener_detalle_video(video_id, config)
            
            if detalle:
                video_detail_info = {
                    'video_index': idx,
                    'video_id': video_id,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'api_response': detalle,
                    'status': 'success'
                }
            else:
                video_detail_info = {
                    'video_index': idx,
                    'video_id': video_id,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'api_response': None,
                    'status': 'failed'
                }
            
            detalles_videos.append(video_detail_info)
            
            # Pausa entre requests para evitar rate limiting
            time.sleep(1)
        
        # Crear directorio para detalles de videos (directamente en Output)
        directorio_detalles = os.path.join(directorio_sesion, "video_details")
        os.makedirs(directorio_detalles, exist_ok=True)
        
        # Guardar resultados (nombre fijo, formato YAML)
        archivo_detalles = os.path.join(
            directorio_detalles, 
            f"video_details_batch.yml"
        )
        
        resultado_final = {
            'extraction_metadata': {
                'extraction_date': datetime.now().isoformat(),
                'extraction_method': 'TikTok Detail API (RapidAPI)',
                'total_videos_requested': len(video_ids),
                'successful_extractions': len([v for v in detalles_videos if v['status'] == 'success']),
                'failed_extractions': len([v for v in detalles_videos if v['status'] == 'failed']),
                'api_version': 'tiktok-api23'
            },
            'video_details': detalles_videos
        }
        
        with open(archivo_detalles, 'w', encoding='utf-8') as f:
            yaml.dump(resultado_final, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        exitosos = len([v for v in detalles_videos if v['status'] == 'success'])
        fallidos = len([v for v in detalles_videos if v['status'] == 'failed'])
        
        print(f"\n[OK] === PROCESO DE DETALLES COMPLETADO ===")
        print(f"[CHART] Videos exitosos: {exitosos}")
        print(f"[ERROR] Videos fallidos: {fallidos}")
        print(f"[SAVE] Archivo guardado: {archivo_detalles}")
        
        return resultado_final
        
    except Exception as e:
        print(f"\n[ERROR] Error en obtener_detalles_videos_batch: {e}")
        return None

# =============================================================================
# 6C. FUNCIÓN PARA PROCESAR VIDEOS EXISTENTES
# =============================================================================

def procesar_videos_existentes_con_detalle(username=None, limite_videos=3):
    """
    Función para cargar videos existentes y obtener sus detalles usando la nueva API
    
    Args:
        username (str): Usuario a procesar (usa el de prueba si no se especifica)
        limite_videos (int): Número de videos a procesar (default 3)
    """
    print(f"\n[MOVIE] === PROCESANDO VIDEOS EXISTENTES CON API DE DETALLES ===")
    
    try:
        # 1. Cargar configuración
        config = cargar_configuracion()
        
        # 2. Determinar usuario
        if username is None:
            username = config['test_username']
            print(f"   [TEST] Usando usuario de prueba: @{username}")
        else:
            print(f"   [TARGET] Analizando usuario: @{username}")
        
        # 3. Buscar archivo de videos existente
        # Buscar en el directorio de salida (estructura directa)
        base_dir = config['output_base_dir']
        
        # Directorios directamente en Output
        user_info_dir = os.path.join(base_dir, "user_info")
        videos_info_dir = os.path.join(base_dir, "videos_info")
        
        if not os.path.exists(user_info_dir) or not os.path.exists(videos_info_dir):
            print(f"   [ERROR] No se encontraron datos previos para @{username}")
            return None
        
        # Buscar archivo de detalles de videos (estructura directa)
        video_details_dir = os.path.join(base_dir, "video_details")
        
        if os.path.exists(video_details_dir):
            print(f"   [SEARCH] Estructura optimizada detectada - usando detalles existentes")
            detail_files = [f for f in os.listdir(video_details_dir) if f.endswith('.json')]
            if detail_files:
                detail_file = sorted(detail_files)[-1]
                detail_file_path = os.path.join(video_details_dir, detail_file)
                print(f"   [FOLDER] Archivo de detalles encontrado: {detail_file}")
                
                with open(detail_file_path, 'r', encoding='utf-8') as f:
                    existing_details = json.load(f)
                
                existing_video_ids = [detail['video_id'] for detail in existing_details.get('video_details', [])]
                if existing_video_ids:
                    print(f"   [OK] {len(existing_video_ids)} videos ya tienen detalles")
                    return existing_details
        
        # Si no hay detalles existentes, obtener nuevos IDs del usuario
        print(f"   [SHARE] Obteniendo nuevos IDs de videos para análisis...")
        
        # Obtener IDs directamente de la API (sin guardar archivo básico)
        # Necesitamos el user_id, no el username para esta API
        user_id = "7140234356736525355"  # User ID de shalom_mainnnnn 
        raw_video_data = obtener_videos_usuario_scraper_api(user_id, username, config, count=15)
        
        if not raw_video_data:
            print(f"   [ERROR] No se pudieron obtener videos del usuario")
            return None
        
        # Procesar solo para extraer IDs
        datos_videos_temp = procesar_datos_videos_scraper_api(raw_video_data, username)
        
        if not datos_videos_temp or 'videos_list' not in datos_videos_temp:
            print(f"   [ERROR] No se pudieron procesar los datos de videos")
            return None
        
        # Extraer IDs limitados
        videos_list = datos_videos_temp['videos_list']
        videos_a_procesar = videos_list[:limite_videos]
        video_ids = [video['video_id'] for video in videos_a_procesar]
        
        print(f"   [VIDEO] Videos encontrados: {len(videos_list)}")
        print(f"   [TARGET] Videos a procesar: {len(video_ids)}")
        
        for i, video_id in enumerate(video_ids, 1):
            video_info = videos_a_procesar[i-1]
            titulo = video_info.get('title', 'Sin título')
            print(f"      {i}. {video_id} - {titulo[:50]}...")
        
        # 6. Obtener detalles usando la nueva API
        resultado_detalles = obtener_detalles_videos_batch(video_ids, config, base_dir)
        
        if resultado_detalles:
            print(f"\n[PARTY] PROCESO COMPLETADO EXITOSAMENTE")
            return resultado_detalles
        else:
            print(f"\n[ERROR] Error en el proceso de detalles")
            return None
        
    except Exception as e:
        print(f"\n[ERROR] Error en procesar_videos_existentes_con_detalle: {e}")
        traceback.print_exc()
        return None

# =============================================================================
# 6.5. FUNCIÓN PARA LEER USUARIOS DESDE EXCEL
# =============================================================================

def cargar_usuarios_desde_csv(archivo_csv="data/generated_input/stats_progressive.csv", limite=10, solo_publicas=True):
    """
    Carga la lista de usuarios desde el archivo CSV generado por el scraper
    
    Args:
        archivo_csv (str): Ruta al archivo CSV
        limite (int): Número máximo de usuarios a procesar (None para todos)
        solo_publicas (bool): Si True, solo procesa cuentas públicas (is_private = False)
        
    Returns:
        list: Lista de diccionarios con username y URL
    """
    try:
        print(f"[CHART] Cargando usuarios desde: {archivo_csv}")
        
        # Leer archivo CSV
        df = pd.read_csv(archivo_csv)
        
        print(f"   [CLIPBOARD] Total usuarios en archivo: {len(df)}")
        
        # Filtrar solo cuentas públicas si se solicita
        if solo_publicas:
            # Filtrar donde is_private = False y username != 'error'
            df_filtrado = df[(df['is_private'] == False) & (df['username'] != 'error')]
            print(f"   [UNLOCK] Cuentas públicas encontradas: {len(df_filtrado)}")
            print(f"   [LOCK] Cuentas privadas filtradas: {len(df[df['is_private'] == True])}")
            print(f"   [ERROR] Cuentas con error filtradas: {len(df[df['username'] == 'error'])}")
        else:
            # Filtrar solo errores
            df_filtrado = df[df['username'] != 'error']
            print(f"   [USERS] Cuentas válidas (públicas + privadas): {len(df_filtrado)}")
            print(f"   [ERROR] Cuentas con error filtradas: {len(df[df['username'] == 'error'])}")
        
        # Aplicar límite si se especifica
        if limite is not None:
            df_limited = df_filtrado.head(limite)
            print(f"   [TARGET] Aplicando límite, usuarios a procesar: {len(df_limited)}")
        else:
            df_limited = df_filtrado
            print(f"   [TARGET] Procesando TODOS los usuarios válidos: {len(df_limited)}")
        
        # Convertir a lista de diccionarios
        usuarios = []
        for index, row in df_limited.iterrows():
            usuario = {
                'username': str(row['username']).replace('@', ''),
                'url': str(row['URL']),
                'followers_count': str(row['followers_count']),
                'following_count': str(row['following_count']),
                'likes_count': str(row['likes_count']),
                'bio': str(row['bio']),
                'is_verified': bool(row['is_verified']),
                'is_private': bool(row['is_private'])
            }
            usuarios.append(usuario)
            
            # Mostrar info de cuenta
            status_icon = "🔓" if not usuario['is_private'] else "🔒"
            verified_icon = "✅" if usuario['is_verified'] else ""
            print(f"      {len(usuarios)}. {status_icon}{verified_icon} @{usuario['username']} - {usuario['followers_count']} followers")
        
        return usuarios
        
    except Exception as e:
        print(f"[ERROR] Error cargando usuarios desde CSV: {e}")
        traceback.print_exc()
        return []

# =============================================================================
# 7. FUNCIÓN PRINCIPAL
# =============================================================================

def analizar_usuario_tiktok(username=None):
    """
    Función principal que orquesta todo el proceso de análisis
    
    Args:
        username (str, optional): Nombre de usuario a analizar. 
                                Si no se especifica, usa el de prueba.
    """
    print("TIKTOK API ANALYZER V2.3 - INTEGRACIÓN CON SCRAPER")
    print("=" * 65)
    print(" [INFO] Input: stats_progressive.csv (desde scraper)")
    print(" [INFO] Filtro: Solo cuentas públicas (is_private = False)")
    print(" [INFO] APIs: RapidAPI para análisis profundo")
    print(" [INFO] Output: user_info/ videos_info/ video_details/")
    print("=" * 65)
    
    try:
        # 1. Cargar configuración
        config = cargar_configuracion()
        
        # 2. Determinar usuario a analizar
        if username is None:
            username = config['test_username']
            print(f"\n[TEST] Usando usuario de prueba: @{username}")
        else:
            print(f"\n[TARGET] Analizando usuario: @{username}")
        
        # 3. Configurar directorios
        user_dir, subdirs, session_dir = configurar_directorios(username, config)
        print(f"   [FOLDER] Directorio base: {user_dir}")
        
        # 4. Obtener información del usuario
        raw_data = obtener_info_usuario_tiktok(username, config)
        
        if raw_data is None:
            print(f"\n[ERROR] No se pudo obtener información de @{username}")
            return None
        
        # 5. Procesar datos
        datos_procesados = procesar_datos_usuario(raw_data, username)
        
        if datos_procesados is None:
            print(f"\n[ERROR] No se pudieron procesar los datos de @{username}")
            return None
        
        # 6. Guardar información del usuario
        archivo_usuario = guardar_resultados_usuario(datos_procesados, username, subdirs)
        
        # 7. Obtener información de videos usando user_id del archivo JSON
        user_id = leer_user_id_desde_archivo(username, subdirs)
        
        archivo_videos = None
        archivo_videos_detalle = None
        video_ids = []
        
        if user_id:
            print(f"\n[MOVIE] Obteniendo información de videos usando user_id: {user_id}")
            
            # Usar API scraper7 para obtener lista de videos
            raw_video_data = obtener_videos_usuario_scraper_api(user_id, username, config, count=15)
            
            if raw_video_data:
                # Procesar datos de videos completamente
                datos_videos = procesar_datos_videos_scraper_api(raw_video_data, username)
                
                if datos_videos and 'videos_list' in datos_videos:
                    # Guardar información completa de videos
                    archivo_videos = guardar_resultados_videos(datos_videos, username, subdirs)
                    
                    # Extraer IDs de videos para análisis detallado (primeros 3)
                    video_ids = [video['video_id'] for video in datos_videos['videos_list'][:3] if video.get('video_id')]
                    
                    if video_ids:
                        print(f"\n[SEARCH] Obteniendo detalles específicos de {len(video_ids)} videos...")
                        resultado_detalles = obtener_detalles_videos_batch(video_ids, config, session_dir)
                        if resultado_detalles:
                            archivo_videos_detalle = "video_details_batch.json"
                            print(f"[OK] Detalles específicos guardados exitosamente")
                    else:
                        print("   [WARNING]  No se encontraron video IDs válidos para análisis detallado")
                else:
                    print("   [ERROR] No se pudieron procesar los datos de videos")
            else:
                print("   [ERROR] No se pudieron obtener videos del usuario con API scraper7")
                
                # Fallback: Intentar con API original si la alternativa falla
                sec_uid = datos_procesados.get('raw_api_response', {}).get('userInfo', {}).get('user', {}).get('secUid', '')
                if sec_uid:
                    print(f"   [SHARE] Intentando con API original (SecUid: {sec_uid[:20]}...)...")
                    raw_video_data = obtener_videos_usuario_tiktok(sec_uid, username, config, count=15)
                    
                    if raw_video_data:
                        datos_videos = procesar_datos_videos(raw_video_data, username)
                        if datos_videos:
                            archivo_videos = guardar_resultados_videos(datos_videos, username, subdirs)
                            if datos_videos.get('videos_list'):
                                video_ids = [video['video_id'] for video in datos_videos['videos_list'][:3] if video.get('video_id')]
                                if video_ids:
                                    resultado_detalles = obtener_detalles_videos_batch(video_ids, config, session_dir)
                                    if resultado_detalles:
                                        archivo_videos_detalle = "video_details_batch.json"
        else:
            print("   [WARNING]  No se pudo obtener user_id del archivo JSON, saltando videos")
        
        # 8. Resumen final
        archivos_creados = [f for f in [archivo_usuario, archivo_videos, archivo_videos_detalle] if f is not None]
        
        print(f"\n[PARTY] ANÁLISIS COMPLETADO PARA @{username}")
        print("=" * 65)
        print(f"[CHART] Usuario: {datos_procesados['profile_basic_info']['nickname']}")
        print(f"[OK] Verificado: {'Sí' if datos_procesados['profile_basic_info']['verified'] else 'No'}")
        print(f"[LOCK] Privado: {'Sí' if datos_procesados['profile_basic_info']['private_account'] else 'No'}")
        print(f"[USERS] Seguidores: {datos_procesados['profile_stats']['follower_count']:,}")
        print(f"[MOVIE] Videos en perfil: {datos_procesados['profile_stats']['video_count']:,}")
        print(f"[HEART]  Likes totales: {datos_procesados['profile_stats']['heart_count']:,}")
        
        # Información de archivos creados
        print(f"\n[FOLDER] ARCHIVOS GENERADOS:")
        if archivo_usuario:
            print(f"   [USER] Info de usuario: [OK] Guardado en user_info/")
        if archivo_videos:
            print(f"   [MOVIE] Info de videos: [OK] Guardado en videos_info/")
        if archivo_videos_detalle:
            print(f"   [SEARCH] Detalles de videos: [OK] Guardado en video_details/")
            print(f"   [VIDEO] Videos con análisis detallado: {len(video_ids)}")
        
        print(f"\n[SAVE] Total archivos creados: {len(archivos_creados)}")
        print("=" * 65)
        
        # Retornar datos completos
        resultado_completo = {
            "user_data": datos_procesados,
            "video_ids_analyzed": video_ids,
            "files_created": archivos_creados
        }
        
        return resultado_completo
        
    except Exception as e:
        print(f"\n[BOOM] ERROR CRÍTICO: {e}")
        traceback.print_exc()
        return None

def analizar_usuarios_desde_csv():
    """
    Función que procesa múltiples usuarios desde el archivo CSV (solo cuentas públicas)
    """
    print("[ROCKET] EJECUTANDO ANÁLISIS MASIVO DESDE CSV (SOLO CUENTAS PÚBLICAS)...")
    
    try:
        # 1. Cargar configuración
        config = cargar_configuracion()
        
        # 2. Cargar usuarios desde CSV (solo cuentas públicas)
        usuarios = cargar_usuarios_desde_csv(limite=None, solo_publicas=True)
        
        if not usuarios:
            print("[ERROR] No se pudieron cargar usuarios públicos desde CSV")
            return False
        
        # 3. Procesar cada usuario
        usuarios_exitosos = 0
        usuarios_fallidos = 0
        
        for i, usuario_info in enumerate(usuarios, 1):
            username = usuario_info['username']
            
            print(f"\n{'='*70}")
            print(f"PROCESANDO USUARIO {i}/{len(usuarios)}: @{username}")
            print(f"{'='*70}")
            
            try:
                resultado = analizar_usuario_tiktok(username)
                
                if resultado:
                    usuarios_exitosos += 1
                    print(f"[OK] Usuario @{username} procesado exitosamente")
                else:
                    usuarios_fallidos += 1
                    print(f"[ERROR] Error procesando usuario @{username}")
                
                # Pausa entre usuarios para evitar rate limiting
                if i < len(usuarios):
                    print(f"\n[WAIT] Pausa de 3 segundos antes del siguiente usuario...")
                    time.sleep(3)
                    
            except Exception as e:
                usuarios_fallidos += 1
                print(f"[BOOM] Error crítico procesando @{username}: {e}")
                continue
        
        # 4. Resumen final
        print(f"\n{'='*70}")
        print(f"[CHART] RESUMEN DEL ANÁLISIS MASIVO (CUENTAS PÚBLICAS)")
        print(f"{'='*70}")
        print(f"[USERS] Usuarios públicos procesados: {len(usuarios)}")
        print(f"[OK] Exitosos: {usuarios_exitosos}")
        print(f"[ERROR] Fallidos: {usuarios_fallidos}")
        print(f"[CHART] Tasa de éxito: {(usuarios_exitosos/len(usuarios)*100):.1f}%")
        
        return usuarios_exitosos > 0
        
    except Exception as e:
        print(f"[BOOM] ERROR CRÍTICO EN ANÁLISIS MASIVO: {e}")
        traceback.print_exc()
        return False

# =============================================================================
# 7. PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    # Ejecutar análisis masivo desde CSV (solo cuentas públicas)
    print("[ROCKET] EJECUTANDO ANÁLISIS MASIVO DESDE CSV (SOLO CUENTAS PÚBLICAS)...")
    resultado = analizar_usuarios_desde_csv()
    
    if resultado:
        print("\n[OK] Análisis masivo de cuentas públicas ejecutado exitosamente")
        print("[FOLDER] Estructura directa: user_info/ videos_info/ video_details/")
        print("\n[IDEA] SIGUIENTE PASO:")
        print("   [EMOJI] Para descargar medios ejecuta: python tiktok_media_downloader.py")
    else:
        print("\n[ERROR] Análisis masivo de cuentas públicas falló") 