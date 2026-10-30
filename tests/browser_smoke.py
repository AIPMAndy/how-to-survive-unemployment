#!/usr/bin/env python3
"""Optional end-to-end smoke test requiring playwright + Chromium."""
import asyncio
import os
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=f'http://127.0.0.1:{server.server_address[1]}/'

async def main():
    async with async_playwright() as p:
        browser_options={'headless':True}
        if os.environ.get('CHROMIUM_EXECUTABLE_PATH'):
            browser_options['executable_path']=os.environ['CHROMIUM_EXECUTABLE_PATH']
        b=await p.chromium.launch(**browser_options)
        page=await b.new_page(viewport={'width':1440,'height':1000}, accept_downloads=True)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.goto(BASE)
        assert await page.locator('h1').count()==1
        assert await page.locator('.task').count()==53
        await page.locator('input[type="checkbox"]').first.check()
        assert await page.locator('#done-count').inner_text()=='1'
        await page.reload()
        assert await page.locator('#done-count').inner_text()=='1'
        assert await page.locator('#route-result li').count()>=3
        await page.locator('#status-select').select_option('longtime')
        assert await page.locator('#route-result').get_by_text('30个岗位',exact=False).count()>=1
        await page.locator('#work-years').fill('3')
        await page.locator('#work-months').fill('8')
        await page.locator('#avg-wage').fill('15000')
        assert '60,000' in await page.locator('#n-result').inner_text()
        await page.locator('#search').fill('医保')
        assert 0<await page.locator('.task').count()<53
        await page.locator('#search').fill('')
        await page.locator('#city').select_option('beijing')
        assert await page.locator('.task').count()<53
        await page.locator('#city').select_option('all')
        await page.locator('#cash').fill('80000')
        await page.locator('#due').fill('0')
        await page.locator('#expense').fill('10000')
        await page.locator('#income').fill('0')
        assert await page.locator('#runway').inner_text()=='8.0个月'
        await page.locator('#theme').click()
        assert 'dark' in (await page.locator('body').get_attribute('class') or '')
        await page.locator('#theme').click()
        await page.screenshot(path=str(ROOT.parent/'unemployment-desktop-preview.png'),full_page=False)
        async with page.expect_download() as obj:
            await page.locator('#download').click()
        assert (await obj.value).suggested_filename=='失业自救行动清单.txt'
        mobile=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
        await mobile.goto(BASE)
        assert await mobile.locator('.task').count()==53
        await mobile.screenshot(path=str(ROOT.parent/'unemployment-mobile-preview.png'),full_page=False)
        assert not errors,errors
        print('BROWSER SMOKE PASS: 53 tasks, checklist persistence, search, city filter, 8.0 months, theme, download, mobile, zero JS errors')
        await b.close()
        server.shutdown()

asyncio.run(main())
