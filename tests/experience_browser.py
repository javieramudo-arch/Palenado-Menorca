"""Affected experience flows. Chromium real, meteorology and account simulated."""
import functools,http.server,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=http.server.ThreadingHTTPServer(('127.0.0.1',8083),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
backend="""let rows=SEED;window.testRows=()=>structuredClone(rows);const user={id:'test',email:'test@example.invalid'};export async function getClient(){return {auth:{getSession:async()=>({data:{session:{user}}}),onAuthStateChange(){}}};}export async function loadEntries(){return structuredClone(rows);}export async function saveEntry(e){e={...structuredClone(e),revision:(e.revision||0)+1};const i=rows.findIndex(r=>r.id===e.id);if(i<0)rows.push(e);else rows[i]=e;return e;}export async function signedPhoto(){return './guide-photo.svg';}export async function uploadPhoto(){throw Error('unused');}"""
rows=[dict(id=id,revision=1,kind=kind,title='Ruta '+id,data=dict(date='2026-11-03',points=[[39.93805,3.93665],[39.93168,3.91459]],source='gpx',zone='Sur',duration=45,estimatedMinutes=60,wind='fuerte',photos=[],markers=[])) for id,kind in [('trip','trip'),('plan1','plan'),('plan2','plan')]]
backend=backend.replace('SEED',json.dumps(rows))
def weather(url,marine=False):
 from urllib.parse import urlparse,parse_qs
 import time
 q=parse_qs(urlparse(url).query);start=int(time.time())//3600*3600;times=[start+i*3600 for i in range(96)]
 def row():
  h={'time':times}
  for key,val in [('wind_speed_10m',18),('wind_direction_10m',45),('wind_gusts_10m',28),('temperature_2m',20),('wave_height',.5),('wave_direction',90)]:h[key]=[val]*96
  return {'latitude':40,'longitude':4,'hourly':h}
 return [row() for _ in range(20)] if len(q.get('latitude',[''])[0].split(','))==20 else row()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch()
  for width in [393,1280]:
   context=browser.new_context(viewport={'width':width,'height':900},service_workers='block');page=context.new_page();errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',e,flush=True)));page.on('dialog',lambda d:d.accept())
   page.route('**/app.js*',lambda r:r.fulfill(body=(ROOT/'app.js').read_text()+'\nwindow.experienceTest={map:()=>map,pending:()=>pendingLayer,startPractice,endPractice};',content_type='text/javascript'))
   page.route('**/backend.js*',lambda r:r.fulfill(body=backend,content_type='text/javascript'))
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json=weather(r.request.url)))
   page.route('**/embed.windy.com/**',lambda r:r.fulfill(body='<html>Windy simulado</html>',content_type='text/html'))
   page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(json=weather(r.request.url,True)))
   page.goto('http://127.0.0.1:8083/',wait_until='networkidle');page.wait_for_function("document.querySelector('#wind-day').options.length>1");assert not page.locator('#wind-panel').is_visible();page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':90});page.wait_for_selector('#meteo-dialog[open]')
   assert 'Previsión para' in page.locator('#wind-status').inner_text();page.locator('#wind-day').select_option(index=2);page.locator('#wind-hour').select_option(index=4);assert page.locator('#wind-hour').input_value();page.locator('#wind-now').click();assert page.locator('#wind-day').input_value();page.locator('#wind-motion').uncheck();page.locator('#wind-visible').uncheck();page.locator('#wind-visible').check();page.locator('#wind-play').click();page.wait_for_timeout(1000);page.locator('#wind-play').click()
   page.locator('#wind-full').click();page.wait_for_selector('.hour-strip',state='attached');page.locator('.hour-strip').locator('..').locator('summary').click();page.locator('.hour-strip button').nth(1).click();assert page.locator('.hour-strip [aria-pressed=true]').count()==1;page.locator('#content-dialog [data-close]').click();page.locator('#meteo-details').click();page.locator('#wind-point').click();page.locator('#map').click(position={'x':100,'y':100});assert 'Punto seleccionado' in page.locator('#wind-point-data').inner_text();assert page.locator('#draw-bar').is_hidden();page.locator('#meteo-dialog [data-close]').click();page.screenshot(path=str(ROOT/f'tests/wind-{width}.png'))
   page.locator('[data-tab=diario]').click();page.locator('.advanced-filters summary').click();page.locator('#filter-zone').fill('Norte');page.evaluate('experienceTest.startPractice()');assert page.locator('#filter-zone').input_value()=='';page.evaluate('experienceTest.endPractice()');assert page.locator('#filter-zone').input_value()=='Norte';assert page.locator('#trip-list .card').count()==0;page.locator('#reset-filters').click();page.locator('#trip-list [data-action=repeat]').click();assert page.locator('[name=wind]').input_value()=='';assert page.locator('[name=duration]').input_value()=='';assert page.locator('[name=zone]').input_value()=='Sur';page.locator('[name=title]').fill('Repetida');page.locator('[name=parkingCoordinates]').fill('39.938,3.936');page.locator('[name=accessCoordinates]').fill('39.932,3.915');page.locator('#save-entry').click();assert page.evaluate("testRows().filter(e=>e.kind==='trip').length")==2;assert page.evaluate("testRows().find(e=>e.id==='trip').data.wind")=='fuerte'
   page.locator('#trip-list .card').filter(has_text='Repetida').locator('[data-action=view-adventure]').click();assert page.locator('#adventure-sheet a').filter(has_text='Ir al aparcamiento').count()==1;assert page.locator('#adventure-sheet a').filter(has_text='Ir al acceso').count()==1;page.locator('#adventure-sheet [data-action=route-profile]').click();page.locator('#profile-run').click();page.wait_for_function("document.querySelector('#profile-result').textContent.includes('Llegada')");assert 'Punto intermedio' in page.locator('#profile-result').inner_text();page.locator('#content-dialog [data-close]').click()
   page.locator('[data-tab=progreso]').click();page.wait_for_selector('#period-result');assert 'costa nueva' in page.locator('#period-result').inner_text();page.locator('#period-month').select_option('11')
   # Invoke menu routes through their existing user control.
   page.locator('#menu-button').click();page.locator('[data-menu=plans]').click();page.locator('[data-action=compare]').click();page.locator('#compare-selection input').nth(0).check();page.locator('#compare-selection input').nth(1).check();page.locator('#compare-run').click();page.wait_for_function("!document.querySelector('#compare-results').textContent.includes('Consultando')");assert page.locator('#compare-results .card').count()==2,{'result':page.locator('#compare-results').inner_text(),'time':page.locator('#compare-time').input_value(),'checked':page.locator('#compare-selection input:checked').count(),'errors':errors}
   page.locator('#content-dialog [data-close]').click();page.locator('[data-tab=mapa]').click();page.locator('[data-map=layers]').click();page.locator('#pending-coast').check();page.locator('[data-map=layers]').click();assert page.locator('#pending-coast').is_checked()
   point=page.evaluate('''()=>{const m=experienceTest.map(),segments=experienceTest.pending().getLayers()[0].getLatLngs(),s=segments.find(s=>s[0].lng>4.1);m.setView(s[0],15,{animate:false});const p=m.latLngToContainerPoint(s[0]);return {x:p.x,y:p.y};}''');page.locator('#map').click(position=point);page.wait_for_selector('#editor-dialog[open]');assert 'PENDIENTE' in page.locator('#editor-type').inner_text();assert 'Tramo de costa pendiente'==page.locator('[name=title]').input_value();page.locator('#discard-draft').click()
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(status=503,body='unavailable'));page.locator('#meteo-details').click();page.locator('#wind-retry').click();page.wait_for_function("document.querySelector('#wind-status').textContent.includes('no disponible')");assert page.locator('#wind-day').is_disabled();assert 'Viento no disponible' in page.locator('#wind-point-data').inner_text()
   assert not errors,errors;page.screenshot(path=str(ROOT/f'tests/experience-{width}.png'));context.close()
  browser.close();print('EXPERIENCE_BROWSER_PASS mobile/desktop wind/time/play/pick, repeat identity, combined filters, profile, period and comparison. Providers simulated.')
finally:server.shutdown()
