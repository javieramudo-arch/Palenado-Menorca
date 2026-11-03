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
  for key,val in [('wind_speed_10m',18),('wind_direction_10m',45),('wind_gusts_10m',28),('temperature_2m',20),('wave_height',.5),('wave_direction',270)]:h[key]=[(val+i*17)%360 for i in range(96)] if key=='wind_direction_10m' else [val+i%9 for i in range(96)] if key=='wind_speed_10m' else [(val+i*15)%360 for i in range(96)] if key=='wave_direction' else [val]*96
  return {'latitude':40,'longitude':4,'hourly':h}
 return [row() for _ in range(20)] if len(q.get('latitude',[''])[0].split(','))==20 else row()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch()
  for width in [393,1280]:
   context=browser.new_context(viewport={'width':width,'height':900},service_workers='block',reduced_motion='reduce');page=context.new_page();errors=[]
   page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',e,flush=True)));page.on('dialog',lambda d:d.accept())
   page.route('**/app.js*',lambda r:r.fulfill(body=(ROOT/'app.js').read_text()+'\nwindow.waveTest={map:()=>map,state:()=>({mode,draft:structuredClone(draft)})};',content_type='text/javascript'))
   page.route('**/backend.js*',lambda r:r.fulfill(body=backend,content_type='text/javascript'))
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json=weather(r.request.url)))
   page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(json=weather(r.request.url,True)))
   page.goto('http://127.0.0.1:8083/',wait_until='networkidle');page.wait_for_function("document.querySelector('#wave-status').textContent.includes('Oleaje azul')")
   assert page.locator('.wave-canvas').evaluate("e=>getComputedStyle(e).pointerEvents")=='none'
   page.evaluate('waveTest.map().setView([40.14,4.1],13,{animate:false})');page.wait_for_timeout(150)
   blue=page.locator('.wave-canvas').evaluate("c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i+2]>150&&d[i+2]>d[i]*2&&d[i+2]>d[i+1]*1.1)n++;return n;}");assert blue>50,blue
   image=page.locator('.wave-canvas').evaluate('(c)=>c.toDataURL()');page.locator('#meteo-map-hours').focus();page.locator('#meteo-map-hours').press('ArrowRight');page.locator('#meteo-map-hours').press('ArrowRight');assert page.locator('.wave-canvas').evaluate('(c)=>c.toDataURL()')!=image
   page.screenshot(path=str(ROOT/f'tests/waves-{width}.png'))
   # All arrows are passive: choosing weather still reaches the map through the canvases.
   page.locator('#weather-button').click();page.locator('#map').click(position={'x':180,'y':160});page.wait_for_selector('#meteo-dialog[open]');page.locator('#meteo-dialog [data-close]').click();assert page.locator('.wave-canvas').evaluate("e=>getComputedStyle(e).pointerEvents")=='none'
   page.evaluate('waveTest.map().setView([39.98,4.08],15,{animate:false})');page.wait_for_timeout(150);assert page.locator('.wave-canvas').evaluate("c=>c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)")==False
   page.evaluate('waveTest.map().setView([40.14,4.1],13,{animate:false})');page.locator('#weather-button').click();page.locator('#map').click(position={'x':180,'y':160});page.wait_for_selector('#meteo-dialog[open]');page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(status=503,body='no marine'));page.locator('#wind-retry').click();page.wait_for_function("document.querySelector('#wave-status').textContent.includes('no disponible')");page.wait_for_function("!document.querySelector('#meteo-map-hours').disabled");assert 'km/h' in page.locator('#meteo-mini-data').inner_text();assert page.locator('.wave-canvas').evaluate("c=>c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)")==False
   assert not errors,errors;context.close()
  browser.close();print('WAVES_BROWSER_PASS mobile/desktop: blue marine arrows, independent directions, selected-hour update, sea-only mask, pointer-events none, marine failure does not break wind. Providers simulated.')
finally:server.shutdown()
