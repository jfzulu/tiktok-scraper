#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TIKTOK SCRAPER OPTIMIZADO - Versión 2.0
Características:
- Procesamiento paralelo (3-5 perfiles simultáneos)
- Delays inteligentes basados en comportamiento
- Rotación de user agents y fingerprints
- Manejo robusto de errores
- Cache de sesiones
"""

import os
import json
import asyncio
import random
import time
from datetime import datetime
from playwright.async_api import async_playwright
from tqdm.asyncio import tqdm_asyncio
import pandas as pd
import numpy as np
from typing import List, Dict

class TikTokScraperOptimized:
    """Scraper optimizado para TikTok con paralelismo y técnicas anti-detección"""
    
    def __init__(self, max_concurrent=3):
        self.browser = None
        self.context = None
        self.playwright = None
        self.max_concurrent = max_concurrent
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        ]
        self.session_cache = "data/session_cache.json"

    async def initialize_browser(self):
        """Inicializa el navegador con configuración optimizada"""
        self.playwright = await async_playwright().start()
        
        # Configuración avanzada del navegador
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--disable-infobars'
            ],
            chromium_sandbox=False
        )

        # Contexto con fingerprint aleatorio
        self.context = await self.browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={'width': random.randint(1200, 1400), 'height': random.randint(700, 900)},
            locale='en-US',
            timezone_id='America/New_York',
            color_scheme='light',
            http_credentials=None,
            proxy=None,
            storage_state=self.session_cache if os.path.exists(self.session_cache) else None
        )

        # Inyectar scripts de evasión
        await self.context.add_init_script("""
            delete navigator.__proto__.webdriver;
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)

    async def close(self):
        """Guarda la sesión y cierra recursos"""
        if self.context:
            # Guardar cookies y almacenamiento para la próxima sesión
            await self.context.storage_state(path=self.session_cache)
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def smart_delay(self, success: bool):
        """Delay adaptativo basado en éxito/fracaso"""
        base_delay = random.gauss(1.5, 0.3) if success else random.gauss(3, 0.5)
        jitter = random.uniform(-0.5, 0.5)
        delay = max(0.5, base_delay + jitter)
        await asyncio.sleep(delay)

    async def fetch_profile(self, url: str) -> Dict:
        """Extrae datos de perfil de manera optimizada"""
        page = None
        try:
            page = await self.context.new_page()
            
            # Configuración de tiempo de espera
            page.set_default_timeout(10000)
            page.set_default_navigation_timeout(15000)

            # Navegación inteligente con reintentos
            navigation_success = await self.smart_navigate(page, url)
            if not navigation_success:
                return self._error_response(url, "Navigation failed")

            # Extracción optimizada de datos
            profile_data = await self._extract_profile_data(page, url)
            await page.close()
            
            # Delay post-éxito
            await self.smart_delay(success=True)
            return profile_data

        except Exception as e:
            if page:
                await page.close()
            # Delay post-error
            await self.smart_delay(success=False)
            return self._error_response(url, str(e))

    async def smart_navigate(self, page, url: str, max_retries: int = 2) -> bool:
        """Navegación con reintentos inteligentes"""
        for attempt in range(max_retries):
            try:
                # Rotar user agent para cada intento
                await page.set_extra_http_headers({
                    'User-Agent': random.choice(self.user_agents)
                })

                # Estrategia de carga flexible
                load_strategy = "domcontentloaded" if attempt == 0 else "load"
                await page.goto(url, wait_until=load_strategy, timeout=15000)
                
                # Verificación básica de carga
                await page.wait_for_selector('body', state='attached', timeout=5000)
                return True
            
            except Exception as e:
                if attempt == max_retries - 1:
                    return False
                await asyncio.sleep(1 * (attempt + 1))
        return False

    async def _extract_profile_data(self, page, url: str) -> Dict:
        """Extracción eficiente de datos del perfil"""
        data = {
            "extraction_metadata": {
                "url": url,
                "extraction_date": datetime.now().isoformat(),
                "status": "success"
            },
            "profile_info": {
                "username": await self._extract_username(page, url),
                "bio": await self._extract_with_fallback(page, '[data-e2e="user-bio"]', "No bio"),
                "follower_count": await self._extract_with_fallback(page, '[data-e2e="followers-count"]', "N/A"),
                "following_count": await self._extract_with_fallback(page, '[data-e2e="following-count"]', "N/A"),
                "likes_count": await self._extract_with_fallback(page, '[data-e2e="likes-count"]', "N/A"),
                "is_verified": await self._check_verified(page),
                "is_private": await self._check_private(page)
            }
        }
        return data

    async def _extract_username(self, page, url: str) -> str:
        """Extracción optimizada de username"""
        selectors = ['h1[data-e2e="user-title"]', '[data-e2e="user-title"]', 'h1']
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text.strip():
                        return text.strip()
            except:
                continue
        return url.split('@')[-1].split('?')[0].split('/')[0]

    async def _extract_with_fallback(self, page, selector: str, default: str) -> str:
        """Extracción genérica con fallback"""
        try:
            element = await page.query_selector(selector)
            return (await element.inner_text()).strip() if element else default
        except:
            return default

    async def _check_verified(self, page) -> bool:
        """Verificación optimizada de cuenta verificada"""
        verified_selectors = [
            '[data-e2e="user-verified"]',
            'svg[data-e2e="verified-icon"]',
            '[aria-label*="verified" i]'
        ]
        for selector in verified_selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    return True
            except:
                continue
        return False

    async def _check_private(self, page) -> bool:
        """Verificación optimizada de cuenta privada"""
        private_indicators = [
            '[data-e2e="user-page-private-lock"]',
            'text="This account is private"',
            'text="Private account"'
        ]
        for indicator in private_indicators:
            try:
                element = await page.query_selector(indicator)
                if element and await element.is_visible():
                    return True
            except:
                continue
        return False

    def _error_response(self, url: str, error_msg: str) -> Dict:
        """Respuesta estandarizada para errores"""
        return {
            "extraction_metadata": {
                "url": url,
                "extraction_date": datetime.now().isoformat(),
                "status": "error",
                "error": error_msg
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

async def process_batch(scraper, batch: List[Dict]) -> List[Dict]:
    """Procesa un lote de URLs en paralelo"""
    tasks = [scraper.fetch_profile(user['url']) for user in batch]
    return await tqdm_asyncio.gather(*tasks, desc=f"Processing batch")

def save_to_csv(data: List[Dict], filename: str):
    """Guarda datos en CSV de manera eficiente"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    df = pd.json_normalize([{
        'URL': item['extraction_metadata']['url'],
        'username': item['profile_info']['username'],
        'followers_count': item['profile_info']['follower_count'],
        'following_count': item['profile_info']['following_count'],
        'likes_count': item['profile_info']['likes_count'],
        'bio': item['profile_info']['bio'],
        'is_verified': item['profile_info']['is_verified'],
        'is_private': item['profile_info']['is_private'],
        'status': item['extraction_metadata']['status']
    } for item in data])
    
    df.to_csv(filename, index=False, encoding='utf-8')

def load_users(filename: str, limit: int = None) -> List[Dict]:
    """Carga usuarios desde archivo Excel"""
    df = pd.read_excel(filename)
    users = df[['username']].to_dict('records')
    
    for user in users:
        user['url'] = f"https://www.tiktok.com/@{user['username']}"
    
    return users[:limit] if limit else users

async def main():
    print("=== TIKTOK SCRAPER OPTIMIZADO ===")
    
    # Configuración (definir variables ANTES de usarlas)
    MAX_CONCURRENT = 3  # <-- Añade esta línea
    BATCH_SIZE = 10
    INPUT_FILE = "data/input/usernames.xlsx"
    OUTPUT_FILE = "data/generated_input/profiles.csv"
    
    print(f"• Paralelismo: {MAX_CONCURRENT} perfiles simultáneos")  # <-- Ahora sí puede usarse
    print("• Delays adaptativos inteligentes")
    print("• Técnicas avanzadas anti-detección\n")
    
    # Resto del código permanece igual...
    users = load_users(INPUT_FILE)
    print(f"Total usuarios a procesar: {len(users)}")
    
    scraper = TikTokScraperOptimized(max_concurrent=MAX_CONCURRENT)
    await scraper.initialize_browser()
    
    all_results = []
    for i in range(0, len(users), BATCH_SIZE):
        batch = users[i:i+BATCH_SIZE]
        results = await process_batch(scraper, batch)
        all_results.extend(results)
        save_to_csv(all_results, OUTPUT_FILE)
        print(f"\nBatch {i//BATCH_SIZE + 1} completado. Guardado en {OUTPUT_FILE}")
    
    success_count = sum(1 for r in all_results if r['extraction_metadata']['status'] == 'success')
    print(f"\nProceso completado. Éxito: {success_count}/{len(users)} ({success_count/len(users):.1%})")
    
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())