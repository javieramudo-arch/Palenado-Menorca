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
        page.add_init_script("""let leaflet;Object.defineProperty(window,'L',{configurable:true,get:()=>leaflet,set:v=>{leaflet=v;if(v?.Map)v.Map.addInitHook(function(){window.__routingTestMap=this;});}});""")
        def coastal_click(lat,lng):
            pos=page.evaluate("([lat,lng])=>{const p=window.__routingTestMap.latLngToContainerPoint([lat,lng]);return {x:p.x,y:p.y};}",[lat,lng])
            page.locator('#map').click(position=pos)
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
        coastal_click(39.93805,3.93665)
        coastal_click(39.93168,3.91459)
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
        coastal_click(39.93805,3.93665)
        coastal_click(39.93168,3.91459)
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
            def wait_step(n):
                page.locator('.guide-card .eyebrow').filter(has_text=f'PRÁCTICA {n} /').wait_for()
            def guide_click(selector,n):
                page.locator(selector).click()
                wait_step(n)
            menu_index=0
            wait_step(1)
            guide_click('#new-button',2)
            coastal_click(39.93805,3.93665)
            coastal_click(39.93168,3.91459)
            wait_step(3)
            guide_click('#finish-draw',4)
            page.locator('#entry-form [name=roundtrip]').check()
            wait_step(5)
            guide_click('#add-route-marker',6)
            coastal_click(39.93805,3.93665)
            wait_step(7)
            page.locator('#place-form [name=title]').fill('Acceso de práctica')
            guide_click('#place-form button',8)
            guide_click('#photo-input',9)
            select=page.locator('[data-marker-photo]')
            photo_id=select.locator('option').nth(1).get_attribute('value')
            select.select_option(photo_id)
            wait_step(10)
            guide_click('#close-editor',11)
            guide_click('#weather-button',12)
            guide_click('#content-dialog [data-close]',13)
            guide_click('#menu-button',{0:14,1:17,2:20}[menu_index])
            menu_index+=1
            guide_click('[data-menu=places]',15)
            guide_click('#content-dialog [data-close]',16)
            guide_click('#menu-button',{0:14,1:17,2:20}[menu_index])
            menu_index+=1
            guide_click('[data-menu=plans]',18)
            guide_click('#content-dialog [data-close]',19)
            guide_click('#menu-button',{0:14,1:17,2:20}[menu_index])
            menu_index+=1
            guide_click('[data-menu=preferences]',21)
            guide_click('#content-dialog [data-close]',22)
            guide_click('#resume-draft',23)
            page.locator('#entry-form [name=title]').fill('Práctica completa')
            guide_click('#save-entry',24)
            guide_click('#trip-list [data-action=edit]',25)
            page.locator('#entry-form [name=notes]').fill('He aprendido a editar.')
            guide_click('#save-entry',26)
            guide_click('#trip-list [data-action=detail]',27)
            guide_click('#content-dialog [data-action=delete]',28)
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
except Exception:
    try:
        page.screenshot(path=str(ROOT/'tests'/'failure.png'),full_page=True)
    except Exception:
        pass
    raise
finally:
    server.shutdown()
