#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMPLE TIKTOK PROFILE SCRAPER - VERSIÓN SIMPLE UNO POR UNO
Extrae información básica del perfil de forma secuencial y lenta pero segura
"""

import os
import json
import asyncio
import traceback
import pandas as pd
import csv
import random
from datetime import datetime
from playwright.async_api import async_playwright
from tqdm import tqdm
import time


class TikTokScraperSimple:
    """
    Scraper simple para TikTok que procesa un perfil por vez
    """
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None
        
    async def inicializar_navegador(self):
        """Inicializa el navegador invisible"""
        self.playwright = await async_playwright().start()
        
        # Navegador invisible y simple
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # INVISIBLE - No se abre pantalla
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Un solo contexto
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
            
    async def cerrar_navegador(self):
        """Cierra el navegador"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def extraer_perfil_simple(self, url: str) -> dict:
        """
        Extrae información del perfil de TikTok de forma simple
        
        Args:
            url (str): URL del perfil de TikTok
            
        Returns:
            dict: Información del perfil extraída
        """
        page = await self.context.new_page()
        
        try:
            # Timeouts optimizados
            page.set_default_timeout(15000)  # 15 segundos (reducido de 30)
            
            # Script anti-detección básico
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            print(f"[INFO] Navegando a: {url}")
            
            # Navegar con strategy optimizada
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            except:
                print(f"[FALLBACK] Timeout con domcontentloaded, intentando load...")
                try:
                    await page.goto(url, wait_until="load", timeout=15000)
                except:
                    print(f"[FALLBACK] Usando navegación básica...")
                    await page.goto(url, timeout=10000)
            
            # Espera optimizada para carga
            print(f"[INFO] Esperando carga completa...")
            await page.wait_for_timeout(4000)  # Reducido de 8s a 4s
            
            # Estructura de datos del perfil
            perfil_data = {
                "extraction_metadata": {
                    "url": url,
                    "extraction_date": datetime.now().isoformat(),
                    "extraction_method": "Playwright Simple Scraper",
                    "status": "success"
                },
                "profile_info": {
                    "username": "unknown",
                    "bio": "No bio yet.",
                    "follower_count": "No disponible",
                    "following_count": "No disponible",
                    "likes_count": "No disponible",
                    "is_verified": False,
                    "is_private": False
                }
            }
            
            # Verificar si la página cargó correctamente
            try:
                await page.wait_for_selector('body', timeout=10000)
                print(f"[SUCCESS] Página cargada correctamente")
            except:
                print(f"[ERROR] Página no cargó correctamente")
                raise Exception("Página no cargó")
            
            # Hacer scroll suave para activar contenido
            await page.evaluate("window.scrollTo(0, 200)")
            await page.wait_for_timeout(2000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)
            
            # 1. Extraer username
            print(f"[INFO] Extrayendo username...")
            try:
                # Probar selectores uno por uno
                username_selectors = [
                    'h1[data-e2e="user-title"]',
                    '[data-e2e="user-title"]',
                    'h1'
                ]
                
                username_encontrado = False
                for selector in username_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)  # Reducido de 8s a 5s
                        if element:
                            username_text = await element.inner_text()
                            if username_text and username_text.strip():
                                perfil_data["profile_info"]["username"] = username_text.strip()
                                username_encontrado = True
                                print(f"[SUCCESS] Username: {username_text}")
                                break
                    except:
                        continue
                
                # Si no encontró username, usar el de la URL
                if not username_encontrado:
                    username_from_url = url.split('@')[-1].split('?')[0].split('/')[0]
                    perfil_data["profile_info"]["username"] = username_from_url
                    print(f"[FALLBACK] Username desde URL: {username_from_url}")
                    
            except Exception as e:
                print(f"[ERROR] Error extrayendo username: {e}")
                username_from_url = url.split('@')[-1].split('?')[0].split('/')[0]
                perfil_data["profile_info"]["username"] = username_from_url
            
            # 2. Extraer biografía
            print(f"[INFO] Extrayendo biografía...")
            try:
                bio_element = await page.wait_for_selector('[data-e2e="user-bio"]', timeout=3000)  # Reducido de 8s a 3s
                if bio_element:
                    bio_text = await bio_element.inner_text()
                    if bio_text and bio_text.strip():
                        perfil_data["profile_info"]["bio"] = bio_text.strip()
                        print(f"[SUCCESS] Bio: {bio_text[:50]}...")
            except:
                print(f"[INFO] No se encontró biografía")
            
            # 3. Extraer métricas (followers, following, likes)
            print(f"[INFO] Extrayendo métricas...")
            
            # Followers
            try:
                followers_el = await page.wait_for_selector('[data-e2e="followers-count"]', timeout=3000)  # Reducido de 8s a 3s
                if followers_el:
                    followers_text = await followers_el.inner_text()
                    if followers_text:
                        perfil_data["profile_info"]["follower_count"] = followers_text.strip()
                        print(f"[SUCCESS] Followers: {followers_text}")
            except:
                print(f"[INFO] No se encontraron followers")
            
            # Following
            try:
                following_el = await page.wait_for_selector('[data-e2e="following-count"]', timeout=3000)  # Reducido de 8s a 3s
                if following_el:
                    following_text = await following_el.inner_text()
                    if following_text:
                        perfil_data["profile_info"]["following_count"] = following_text.strip()
                        print(f"[SUCCESS] Following: {following_text}")
            except:
                print(f"[INFO] No se encontró following")
            
            # Likes
            try:
                likes_el = await page.wait_for_selector('[data-e2e="likes-count"]', timeout=3000)  # Reducido de 8s a 3s
                if likes_el:
                    likes_text = await likes_el.inner_text()
                    if likes_text:
                        perfil_data["profile_info"]["likes_count"] = likes_text.strip()
                        print(f"[SUCCESS] Likes: {likes_text}")
            except:
                print(f"[INFO] No se encontraron likes")
            
            # 4. Verificar si es cuenta verificada o privada
            print(f"[INFO] Verificando estado de cuenta...")
            
            # === VERIFICAR SI ES CUENTA VERIFICADA ===
            try:
                # Múltiples selectores para cuenta verificada
                verified_selectors = [
                    '[data-e2e="user-verified"]',
                    '.tiktok-1b18hxz-DivVerifyIconContainer',
                    'svg[width="18"][height="18"]',  # Icono de verificado típico
                    '[aria-label*="verified"]',
                    '[aria-label*="Verified"]',
                    'span[data-e2e="user-verified"]',
                    '.verified-icon',
                    'svg[data-e2e="verified-icon"]'
                ]
                
                verified_found = False
                for selector in verified_selectors:
                    try:
                        verified_el = await page.wait_for_selector(selector, timeout=2000)
                        if verified_el:
                            # Verificar que el elemento sea visible
                            is_visible = await verified_el.is_visible()
                            if is_visible:
                                perfil_data["profile_info"]["is_verified"] = True
                                verified_found = True
                                print(f"[SUCCESS] ✅ Cuenta verificada detectada (selector: {selector})")
                                break
                    except:
                        continue
                
                # Verificación adicional por contenido HTML
                if not verified_found:
                    try:
                        page_content = await page.content()
                        verification_patterns = [
                            'verified',
                            'Verified',
                            'verificado',
                            'Verificado',
                            'checkmark',
                            'check-mark'
                        ]
                        
                        # Buscar patrones en el HTML
                        for pattern in verification_patterns:
                            if pattern in page_content and ('icon' in page_content.lower() or 'svg' in page_content.lower()):
                                # Verificación adicional: buscar cerca del nombre de usuario
                                if '@' in page_content:
                                    username_index = page_content.find('@')
                                    nearby_content = page_content[max(0, username_index-200):username_index+200]
                                    if pattern.lower() in nearby_content.lower():
                                        perfil_data["profile_info"]["is_verified"] = True
                                        verified_found = True
                                        print(f"[SUCCESS] ✅ Cuenta verificada detectada (contenido HTML)")
                                        break
                    except Exception as e:
                        print(f"[DEBUG] Error en verificación HTML: {e}")
                
                if not verified_found:
                    print(f"[INFO] Cuenta NO verificada")
                    
            except Exception as e:
                print(f"[DEBUG] Error verificando estado verificado: {e}")
            
            # === VERIFICAR SI ES CUENTA PRIVADA ===
            # REGLA PRINCIPAL: Si tenemos estadísticas visibles y bio, probablemente NO es privada
            has_visible_stats = (
                perfil_data["profile_info"]["follower_count"] not in ["No disponible", "Error", ""] and
                perfil_data["profile_info"]["following_count"] not in ["No disponible", "Error", ""] and
                perfil_data["profile_info"]["bio"] not in ["No bio yet.", "Error during extraction", ""]
            )
            
            try:
                if has_visible_stats:
                    print(f"[INFO] 🔓 Estadísticas y bio visibles → Cuenta PÚBLICA")
                    # No marcar como privada si tenemos datos visibles
                    perfil_data["profile_info"]["is_private"] = False
                else:
                    # Solo si NO tenemos estadísticas visibles, buscar indicadores de cuenta privada
                    print(f"[INFO] Sin estadísticas visibles, verificando indicadores de privacidad...")
                    
                    # Método 1: Buscar elementos específicos de cuenta privada
                    private_selectors = [
                        '[data-e2e="user-page-private-lock"]',
                        '.private-lock',
                        'svg[data-icon="lock"]',
                        'svg[class*="lock"]'
                    ]
                    
                    private_found = False
                    for selector in private_selectors:
                        try:
                            private_el = await page.wait_for_selector(selector, timeout=1000)
                            if private_el:
                                is_visible = await private_el.is_visible()
                                if is_visible:
                                    perfil_data["profile_info"]["is_private"] = True
                                    private_found = True
                                    print(f"[SUCCESS] 🔒 Cuenta privada detectada (selector: {selector})")
                                    break
                        except:
                            continue
                    
                    # Método 2: Buscar mensajes explícitos de cuenta privada
                    if not private_found:
                        try:
                            page_content = await page.content()
                            explicit_private_patterns = [
                                'This account is private',
                                'Esta cuenta es privada',
                                'Private account'
                            ]
                            
                            for pattern in explicit_private_patterns:
                                if pattern in page_content:
                                    perfil_data["profile_info"]["is_private"] = True
                                    private_found = True
                                    print(f"[SUCCESS] 🔒 Cuenta privada detectada (mensaje: {pattern})")
                                    break
                        except Exception as e:
                            print(f"[DEBUG] Error en detección privada HTML: {e}")
                    
                    if not private_found:
                        print(f"[INFO] 🔓 Sin indicadores claros de privacidad → Cuenta PÚBLICA")
                        perfil_data["profile_info"]["is_private"] = False
                    
            except Exception as e:
                print(f"[DEBUG] Error verificando estado privado: {e}")
                # En caso de error, asumir pública si tenemos datos
                if has_visible_stats:
                    perfil_data["profile_info"]["is_private"] = False
            
            # === VERIFICACIÓN CRUZADA ===
            # Log del estado final detectado
            verification_status = "✅ Verificada" if perfil_data["profile_info"]["is_verified"] else "⚪ No verificada"
            privacy_status = "🔒 Privada" if perfil_data["profile_info"]["is_private"] else "🔓 Pública"
            print(f"[ESTADO FINAL] {verification_status} | {privacy_status}")
            
            await page.close()
            print(f"[SUCCESS] ✅ Perfil extraído exitosamente")
            return perfil_data
            
        except Exception as e:
            print(f"[ERROR] ❌ Error extrayendo perfil {url}: {e}")
            await page.close()
            
            # Retornar estructura básica con error
            return {
                "extraction_metadata": {
                    "url": url,
                    "extraction_date": datetime.now().isoformat(),
                    "extraction_method": "Playwright Simple Scraper",
                    "status": "error",
                    "error": str(e)
                },
                "profile_info": {
                    "username": "error",
                    "bio": "Error during extraction",
                    "follower_count": "Error",
                    "following_count": "Error",
                    "likes_count": "Error",
                    "is_verified": False,
                    "is_private": False
                }
            }


def guardar_stats_csv(resultados_data, archivo_csv="data/generated_input/stats_final.csv"):
    """
    Guarda los resultados en un archivo CSV con las columnas solicitadas
    
    Args:
        resultados_data (list): Lista de datos de perfiles extraídos
        archivo_csv (str): Nombre del archivo CSV de salida
        
    Returns:
        str: Ruta del archivo guardado
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(archivo_csv), exist_ok=True)
        
        # Definir las columnas del CSV
        columnas = [
            'URL',
            'username',
            'followers_count',
            'following_count',
            'likes_count',
            'bio',
            'is_verified',
            'is_private'
        ]
        
        # Preparar datos para CSV
        filas_csv = []
        for resultado in resultados_data:
            if resultado.get("profile_data"):
                profile_info = resultado["profile_data"].get("profile_info", {})
                
                fila = {
                    'URL': resultado.get('url', 'N/A'),
                    'username': profile_info.get('username', 'N/A'),
                    'followers_count': profile_info.get('follower_count', 'N/A'),
                    'following_count': profile_info.get('following_count', 'N/A'),
                    'likes_count': profile_info.get('likes_count', 'N/A'),
                    'bio': profile_info.get('bio', 'N/A'),
                    'is_verified': profile_info.get('is_verified', False),
                    'is_private': profile_info.get('is_private', False)
                }
            else:
                # Datos de error
                fila = {
                    'URL': resultado.get('url', 'N/A'),
                    'username': resultado.get('username', 'error'),
                    'followers_count': 'Error',
                    'following_count': 'Error',
                    'likes_count': 'Error',
                    'bio': 'Error during extraction',
                    'is_verified': False,
                    'is_private': False
                }
            
            filas_csv.append(fila)
        
        # Guardar CSV
        with open(archivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columnas)
            writer.writeheader()
            writer.writerows(filas_csv)
        
        return archivo_csv
        
    except Exception as e:
        print(f"[ERROR] Error guardando CSV: {e}")
        return None


def guardar_perfil_incremental_csv(resultado, archivo_csv="data/generated_input/stats_progressive.csv"):
    """
    Guarda un resultado individual al CSV de forma incremental
    
    Args:
        resultado (dict): Datos de un perfil individual
        archivo_csv (str): Nombre del archivo CSV
        
    Returns:
        bool: True si se guardó exitosamente
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(archivo_csv), exist_ok=True)
        
        # Definir las columnas del CSV
        columnas = [
            'URL',
            'username',
            'followers_count',
            'following_count',
            'likes_count',
            'bio',
            'is_verified',
            'is_private'
        ]
        
        # Preparar fila de datos
        if resultado.get("profile_data"):
            profile_info = resultado["profile_data"].get("profile_info", {})
            
            fila = {
                'URL': resultado.get('url', 'N/A'),
                'username': profile_info.get('username', 'N/A'),
                'followers_count': profile_info.get('follower_count', 'N/A'),
                'following_count': profile_info.get('following_count', 'N/A'),
                'likes_count': profile_info.get('likes_count', 'N/A'),
                'bio': profile_info.get('bio', 'N/A'),
                'is_verified': profile_info.get('is_verified', False),
                'is_private': profile_info.get('is_private', False)
            }
        else:
            # Datos de error
            fila = {
                'URL': resultado.get('url', 'N/A'),
                'username': resultado.get('username', 'error'),
                'followers_count': 'Error',
                'following_count': 'Error',
                'likes_count': 'Error',
                'bio': 'Error during extraction',
                'is_verified': False,
                'is_private': False
            }
        
        # Verificar si el archivo ya existe
        archivo_existe = os.path.exists(archivo_csv)
        
        # Guardar la fila al CSV
        with open(archivo_csv, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columnas)
            
            # Escribir encabezado solo si es un archivo nuevo
            if not archivo_existe:
                writer.writeheader()
            
            writer.writerow(fila)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error guardando fila incremental: {e}")
        return False


def cargar_usuarios_desde_excel(archivo_excel="data/Input/usernames.xlsx", limite=None):
    """
    Carga la lista de usuarios desde el archivo Excel
    
    Args:
        archivo_excel (str): Ruta al archivo Excel
        limite (int or None): Número máximo de usuarios a procesar. Si es None, carga todos
        
    Returns:
        list: Lista de diccionarios con username y URL
    """
    try:
        print(f"[INFO] Cargando usuarios desde: {archivo_excel}")
        
        # Leer archivo Excel
        df = pd.read_excel(archivo_excel)
        
        # Verificar que existan las columnas necesarias
        if "username" not in df.columns:
            print("[ERROR] Columna username no encontrada en el archivo Excel")
            return []
        
        # Aplicar límite solo si se especifica
        if limite is not None:
            df = df.head(limite)
            print(f"[INFO] Aplicando límite de {limite} usuarios")
        else:
            print(f"[INFO] Cargando TODOS los usuarios ({len(df)} encontrados)")
        
        usuarios = []
        for _, row in df.iterrows():
            username = row["username"]
            url = row.get("URL", f"https://www.tiktok.com/@{username}")
            
            usuarios.append({
                "username": username,
                "url": url
            })
        
        if limite is not None:
            print(f"[OK] {len(usuarios)} usuarios cargados desde Excel (head({limite}))")
        else:
            print(f"[OK] {len(usuarios)} usuarios cargados desde Excel (TODOS)")
        return usuarios
        
    except Exception as e:
        print(f"[ERROR] Error leyendo archivo Excel: {e}")
        return []


async def main_simple():
    """Función principal del scraper simple uno por uno"""
    print("SIMPLE TIKTOK PROFILE SCRAPER - VERSIÓN OPTIMIZADA 🚀")
    print("=" * 75)
    print(" [INFO] ⚡ Procesamiento SECUENCIAL optimizado")
    print(" [INFO] 👻 Navegador INVISIBLE (headless=True)")
    print(" [INFO] 🏃 RÁPIDO y SEGURO - ~6-12 segundos por perfil")
    print(" [INFO] 📊 Guardado incremental progresivo")
    print(" [INFO] 📋 CSV: URL,username,followers_count,following_count,likes_count,bio,is_verified,is_private")
    print(" [INFO] 🎯 Balance: VELOCIDAD + ESTABILIDAD")
    print(" [INFO] 🔥 PROCESANDO TODOS LOS USUARIOS DEL EXCEL")
    print(" [INFO] ⏱️ Delays adaptativos: 2-5s (éxito) / 5-8s (errores)")
    print("=" * 75)
    
    # Cargar TODOS los usuarios desde Excel (sin límite)
    usuarios = cargar_usuarios_desde_excel(limite=None)
    
    if not usuarios:
        print("[ERROR] No se pudieron cargar usuarios. Terminando.")
        return
    
    # Crear directorio de salida si no existe
    output_dir = "data/generated_input"
    os.makedirs(output_dir, exist_ok=True)
    
    # Archivo CSV incremental
    archivo_csv_incremental = "data/generated_input/stats_progressive.csv"
    
    # Eliminar archivo CSV previo si existe
    if os.path.exists(archivo_csv_incremental):
        os.remove(archivo_csv_incremental)
        print(f"[INFO] Archivo CSV previo eliminado: {archivo_csv_incremental}")
    
    # Configurar scraper simple
    scraper = TikTokScraperSimple()
    await scraper.inicializar_navegador()
    
    print(f"\n[INFO] 🚀 Navegador invisible inicializado")
    print(f"[INFO] ⚙️ Configuración: Uno por uno, lento pero seguro")
    print(f"[INFO] 📊 Total a procesar: {len(usuarios)} usuarios")
    
    resultados_data = []
    exitosos = 0
    errores = 0
    
    # Configurar barra de progreso
    with tqdm(total=len(usuarios), desc="Procesando perfiles", unit="perfil") as pbar:
        
        for i, usuario in enumerate(usuarios, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(usuarios)}] Procesando: {usuario['username']}")
            print(f"{'='*60}")
            
            try:
                # Procesar usuario
                start_time = time.time()
                resultado_data = await scraper.extraer_perfil_simple(usuario["url"])
                end_time = time.time()
                tiempo_usuario = end_time - start_time
                
                if resultado_data["extraction_metadata"]["status"] == "success":
                    exitosos += 1
                    status = "success"
                    profile_info = resultado_data.get("profile_info", {})
                    print(f"[RESULTADO] ✅ ÉXITO - {profile_info.get('username', 'N/A')}")
                    print(f"[DATOS] Followers: {profile_info.get('follower_count', 'N/A')}")
                    print(f"[DATOS] Following: {profile_info.get('following_count', 'N/A')}")
                    print(f"[DATOS] Likes: {profile_info.get('likes_count', 'N/A')}")
                    print(f"[DATOS] Bio: {profile_info.get('bio', 'N/A')[:30]}...")
                else:
                    errores += 1
                    status = "error"
                    print(f"[RESULTADO] ❌ ERROR")
                
                resultado_final = {
                    "username": usuario["username"],
                    "url": usuario["url"],
                    "status": status,
                    "profile_data": resultado_data,
                    "json_file": None
                }
                
            except Exception as e:
                print(f"[ERROR] ❌ Excepción procesando {usuario['username']}: {e}")
                errores += 1
                resultado_final = {
                    "username": usuario["username"],
                    "url": usuario["url"],
                    "status": "error",
                    "profile_data": None,
                    "json_file": None
                }
                tiempo_usuario = 0
            
            resultados_data.append(resultado_final)
            
            # Guardar inmediatamente al CSV incremental
            guardado_ok = guardar_perfil_incremental_csv(resultado_final, archivo_csv_incremental)
            
            # Actualizar barra de progreso
            pbar.update(1)
            pbar.set_postfix({
                "Exitosos": exitosos, 
                "Errores": errores,
                "Tiempo": f"{tiempo_usuario:.1f}s",
                "CSV": "✅" if guardado_ok else "❌"
            })
            
            # Pausa optimizada entre usuarios
            if i < len(usuarios):
                # Delay adaptativo basado en éxitos/errores
                if errores == 0 or (exitosos / (exitosos + errores)) > 0.8:
                    espera = random.randint(2, 5)  # Si va bien, delay corto
                else:
                    espera = random.randint(5, 8)  # Si hay errores, delay medio
                
                print(f"[PAUSA] Esperando {espera}s antes del siguiente usuario...")
                await asyncio.sleep(espera)
    
    # Cerrar scraper
    await scraper.cerrar_navegador()
    
    # Resumen final
    print(f"\n{'='*75}")
    print(f"[SUMMARY] RESUMEN FINAL")
    print(f"{'='*75}")
    
    print(f"[INFO] Total perfiles procesados: {len(resultados_data)}")
    print(f"[INFO] Perfiles exitosos: {exitosos}")
    print(f"[INFO] Perfiles con error: {errores}")
    print(f"[INFO] Tasa de éxito: {(exitosos/len(usuarios)*100):.1f}%")
    
    # Verificar archivo CSV
    if os.path.exists(archivo_csv_incremental):
        # Contar líneas en CSV
        with open(archivo_csv_incremental, 'r', encoding='utf-8') as f:
            lineas_csv = sum(1 for line in f) - 1  # -1 para el header
        
        print(f"[SUCCESS] ✅ Archivo CSV incremental: {archivo_csv_incremental}")
        print(f"[INFO] Filas en CSV: {lineas_csv}")
        
        # Crear también un CSV final con todos los datos (backup)
        archivo_csv_final = guardar_stats_csv(resultados_data)
        if archivo_csv_final:
            print(f"[SUCCESS] ✅ Archivo CSV final (backup): {archivo_csv_final}")
        
    else:
        print(f"[ERROR] ❌ No se encontró el archivo CSV incremental")
    
    # Mostrar algunos ejemplos
    print(f"\n[INFO] EJEMPLOS DE RESULTADOS:")
    for resultado in resultados_data[:5]:  # Mostrar primeros 5
        status_emoji = "✅" if resultado["status"] == "success" else "❌"
        print(f"{status_emoji} {resultado['username']} - {resultado['status']}")
    
    if len(resultados_data) > 5:
        print(f"    ... y {len(resultados_data) - 5} más")
    
    print(f"\n[INFO] 🎉 Proceso completado. Datos guardados en: {archivo_csv_incremental}")
    print(f"[INFO] 📋 Columnas CSV: URL,username,followers_count,following_count,likes_count,bio,is_verified,is_private")


def main():
    """Wrapper para ejecutar la función principal asíncrona"""
    asyncio.run(main_simple())


if __name__ == "__main__":
    main() 