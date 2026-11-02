"""Functional browser checks with real Leaflet and a simulated private backend.
These do not validate production login, GPS, private storage, or Android touch.
"""
import functools
import http.server
import json
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 8081), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
BACKEND = '''
let records=[];
export async function getClient(){return {auth:{getSession:async()=>({data:{session:{user:{id:'test-user',email:'test@example.invalid'}}}}),onAuthStateChange:()=>{},signOut:async()=>({})}};}
export async function loadEntries(){return structuredClone(records);}
export async function saveEntry(e,userId){const row={...structuredClone(e),user_id:userId,revision:(e.revision||0)+1};const i=records.findIndex(x=>x.id===e.id);if(i<0)records.push(row);else records[i]=row;return row;}
export async function signedPhoto(){throw Error('Fotografía simulada no disponible');}
export async function uploadPhoto(){throw Error('Almacenamiento simulado no disponible');}
'''
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1280,'height':1000})
        errors=[]
        page.on('pageerror', lambda error: (errors.append(str(error)),print('PAGE ERROR:',str(error),flush=True)))
        page.route('**/backend.js*',lambda route:route.fulfill(body=BACKEND,content_type='text/javascript'))
        page.goto('http://127.0.0.1:8081/',wait_until='networkidle')
        page.wait_for_selector('#map.leaflet-container')
        page.get_by_role('button',name='Capas',exact=True).click()
        assert page.locator('#layers').is_visible()
        assert page.locator('#layers input[data-layer]').count()==7
        page.get_by_role('button',name='Capas',exact=True).click()
        assert not page.locator('#layers').is_visible()
        page.get_by_role('button',name='Ver Menorca',exact=True).click()
        assert not page.locator('#layers').is_visible()
        page.get_by_role('button',name='Pantalla completa',exact=True).click()
        assert 'fullscreen-map' in page.locator('#map-wrap').get_attribute('class')
        page.get_by_role('button',name='Restaurar mapa',exact=True).click()
        page.locator('#new-button').click()
        page.locator('#map').click(position={'x':340,'y':210})
        page.locator('#map').click(position={'x':420,'y':230})
        page.locator('#finish-draw').click()
        page.locator('#entry-form [name=title]').fill('Salida <segura>')
        page.locator('#entry-form [name=roundtrip]').check()
        page.locator('#entry-form [name=duration]').fill('75')
        page.locator('#entry-form [name=notes]').fill('Mar tranquilo y muy buena compañía.')
        page.locator('#save-entry').click()
        page.wait_for_selector('#trip-list .card')
        assert page.locator('#trip-list h3').inner_text()=='Salida <segura>'
        assert not page.locator('#trip-list segura').count()
        initial=page.locator('#total-km').inner_text()
        assert initial!='0'
        page.locator('#trip-list [data-action=edit]').click()
        page.locator('#entry-form [name=title]').fill('Macarella al amanecer')
        page.locator('#close-editor').click()
        page.locator('#menu-button').click()
        page.locator('#continue-draft').click()
        assert page.locator('#entry-form [name=title]').input_value()=='Macarella al amanecer'
        page.locator('#save-entry').click()
        page.locator('#trip-list [data-action=detail]').click()
        page.on('dialog',lambda dialog:dialog.accept())
        page.locator('#content-dialog [data-action=delete]').click()
        assert page.locator('#total-km').inner_text()=='0'
        page.locator('#undo').click()
        assert page.locator('#total-km').inner_text()==initial
        page.locator('[data-tab=mapa]').click()
        page.locator('#plan-button').click()
        page.locator('#map').click(position={'x':360,'y':220})
        page.locator('#map').click(position={'x':430,'y':250})
        page.locator('#finish-draw').click()
        page.locator('#entry-form [name=title]').fill('Ruta para mañana')
        page.locator('#save-entry').click()
        assert page.locator('#total-km').inner_text()==initial
        page.locator('[data-tab=mapa]').click()
        page.locator('#guide-button').click()
        page.locator('[data-action=practice]').click()
        assert page.locator('#total-km').inner_text()==initial
        page.locator('#exit-practice').click()
        assert page.locator('#total-km').inner_text()==initial
        # Exercise every guided action in a real rendering engine at desktop and mobile sizes.
        page.route('https://api.open-meteo.com/**',lambda route:route.fulfill(content_type='application/json',body=json.dumps({'daily':{'time':['2026-11-03'],'temperature_2m_min':[15],'temperature_2m_max':[21],'wind_speed_10m_max':[12],'wind_gusts_10m_max':[18]}})))
        for viewport in [{'width':1280,'height':1000},{'width':393,'height':851}]:
            page.set_viewport_size(viewport)
            page.locator('#guide-button').click()
            page.locator('[data-action=practice]').click()
            page.locator('#new-button').click()
            page.locator('#map').click(position={'x':100,'y':130})
            page.locator('#map').click(position={'x':170,'y':180})
            page.locator('#finish-draw').click()
            page.locator('#entry-form [name=roundtrip]').check()
            page.locator('#add-route-marker').click()
            page.locator('#map').click(position={'x':130,'y':150})
            page.locator('#place-form [name=title]').fill('Acceso de práctica')
            page.locator('#place-form button').click()
            page.locator('#photo-input').click()
            select=page.locator('[data-marker-photo]')
            photo_id=select.locator('option').nth(1).get_attribute('value')
            select.select_option(photo_id)
            page.locator('#close-editor').click()
            page.locator('#weather-button').click()
            page.locator('#content-dialog [data-close]').click()
            page.locator('#menu-button').click()
            page.locator('[data-menu=places]').click()
            page.locator('#content-dialog [data-close]').click()
            page.locator('#menu-button').click()
            page.locator('[data-menu=plans]').click()
            page.locator('#content-dialog [data-close]').click()
            page.locator('#menu-button').click()
            page.locator('[data-menu=preferences]').click()
            page.locator('#content-dialog [data-close]').click()
            page.locator('#resume-draft').click()
            page.locator('#entry-form [name=title]').fill('Práctica completa')
            page.locator('#save-entry').click()
            page.locator('#trip-list [data-action=edit]').click()
            page.locator('#entry-form [name=notes]').fill('He aprendido a editar.')
            page.locator('#save-entry').click()
            page.locator('#trip-list [data-action=detail]').click()
            page.locator('#content-dialog [data-action=delete]').click()
            page.locator('#undo').click()
            page.wait_for_selector('#practice-finish')
            assert page.locator('#total-km').inner_text()==initial
            page.locator('#practice-discard').click()
            assert page.locator('#total-km').inner_text()==initial
            assert not page.locator('#practice-banner').is_visible()
        assert not errors, errors
        page.screenshot(path=str(ROOT/'tests'/'desktop.png'),full_page=True)
        page.set_viewport_size({'width':393,'height':851})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(ROOT/'tests'/'mobile.png'),full_page=True)
        print(json.dumps({'status':'passed','scope':'browser with simulated backend','checks':['independent map controls','save','edit','draft','delete','undo','plans excluded from totals','practice isolation','mobile width'],'pageErrors':errors}))
        browser.close()
finally:
    server.shutdown()
