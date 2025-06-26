#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TIKTOK SCRAPER - VERSIÓN EQUILIBRADA
• Velocidad moderada (3-5 segundos por perfil)
• Alta tasa de éxito (>90%)
• Anti-detección mejorado
"""

import os
import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright
from tqdm.asyncio import tqdm_asyncio
import pandas as pd

class BalancedTikTokScraper:
    def __init__(self, max_concurrent=2):  # Reducido a 2 conexiones
        self.max_concurrent = max_concurrent
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.min_delay = 3.0  # Aumentado de 1.5 a 3.0 segundos
        self.max_delay = 6.0  # Aumentado de 3.0 a 6.0 segundos

    async def initialize(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            slow_mo=500,  # Añadido delay artificial entre acciones
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        self.context = await self.browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={'width': 1280, 'height': 720},
            locale='en-US'
        )

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def random_delay(self):
        """Delay aleatorio entre min_delay y max_delay"""
        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

    async def fetch_profile(self, url, retries=3):
        """Extrae datos con reintentos y delays mejorados"""
        for attempt in range(retries):
            try:
                page = await self.context.new_page()
                await page.set_default_timeout(15000)  # Timeout aumentado

                # Navegación con espera inteligente
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_selector('body', state='attached', timeout=10000)

                # Scroll suave para activar contenido
                for _ in range(2):
                    await page.mouse.wheel(0, random.randint(200, 400))
                    await asyncio.sleep(1)

                # Extracción con validación
                data = {
                    "username": await self._safe_extract(page, 'h1[data-e2e="user-title"]', url.split('@')[-1]),
                    "bio": await self._safe_extract(page, '[data-e2e="user-bio"]', "No bio"),
                    "followers": await self._safe_extract(page, '[data-e2e="followers-count"]', "N/A"),
                    "following": await self._safe_extract(page, '[data-e2e="following-count"]', "N/A"),
                    "likes": await self._safe_extract(page, '[data-e2e="likes-count"]', "N/A"),
                    "is_verified": await self._is_verified(page),
                    "status": "success"
                }

                await page.close()
                await self.random_delay()  # Delay post-extracción
                return data

            except Exception as e:
                await page.close()
                if attempt == retries - 1:
                    return {
                        "username": "error",
                        "bio": f"Error: {str(e)}",
                        "followers": "Error",
                        "following": "Error",
                        "likes": "Error",
                        "is_verified": False,
                        "status": "failed"
                    }
                await asyncio.sleep(2 * (attempt + 1))  # Delay entre reintentos

    async def _safe_extract(self, page, selector, default):
        """Extracción con validación robusta"""
        try:
            element = await page.wait_for_selector(selector, timeout=8000)  # Timeout aumentado
            text = await element.inner_text()
            return text.strip() if text else default
        except:
            return default

    async def _is_verified(self, page):
        """Verificación mejorada de cuenta verificada"""
        try:
            return await page.evaluate('''() => {
                const elements = [
                    ...document.querySelectorAll('[data-e2e="user-verified"]'),
                    ...document.querySelectorAll('svg[data-e2e="verified-icon"]')
                ];
                return elements.some(el => el.offsetParent !== null);
            }''')
        except:
            return False

async def process_profiles(scraper, profiles):
    """Procesamiento con gestión de tasa de éxito"""
    results = []
    success_rate = 0
    
    with tqdm_asyncio(total=len(profiles)) as pbar:
        for i in range(0, len(profiles), scraper.max_concurrent):
            batch = profiles[i:i+scraper.max_concurrent]
            tasks = [scraper.fetch_profile(p['url']) for p in batch]
            batch_results = await asyncio.gather(*tasks)
            
            # Ajustar delays basado en tasa de éxito
            batch_success = sum(1 for r in batch_results if r['status'] == 'success')
            current_rate = batch_success / len(batch_results)
            
            if current_rate < 0.7:  # Si tasa <70%, aumentar delays
                scraper.min_delay = min(6.0, scraper.min_delay + 0.5)
                scraper.max_delay = min(10.0, scraper.max_delay + 0.5)
                print(f"\n⚠️ Ajustando delays (+0.5s) por baja tasa de éxito: {current_rate:.0%}")
            
            results.extend(batch_results)
            pbar.update(len(batch_results))
    
    return results

def save_results(results, filename):
    """Guardado robusto de resultados"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(filename, index=False, encoding='utf-8-sig')

async def main():
    print("=== TIKTOK SCRAPER - VERSIÓN ESTABLE ===")
    print("• 2-3 segundos entre requests")
    print("• 2 conexiones concurrentes")
    print("• 3 reintentos por perfil\n")
    
    # Configuración
    INPUT_FILE = "data/input/usernames.xlsx"
    OUTPUT_FILE = "data/generated_input/profiles_stable.csv"
    
    # Cargar perfiles
    df = pd.read_excel(INPUT_FILE)
    profiles = [{"username": row['username'], "url": f"https://www.tiktok.com/@{row['username']}"} 
               for _, row in df.iterrows()]
    
    # Inicializar scraper
    scraper = BalancedTikTokScraper(max_concurrent=2)
    await scraper.initialize()
    
    # Procesar
    results = await process_profiles(scraper, profiles)
    
    # Guardar y mostrar stats
    save_results(results, OUTPUT_FILE)
    success = sum(1 for r in results if r['status'] == 'success')
    print(f"\n✅ Proceso completado: {success}/{len(results)} exitosos ({success/len(results):.1%})")
    
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())