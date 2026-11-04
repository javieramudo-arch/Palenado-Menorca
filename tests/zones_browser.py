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
def constant_weather(url,marine=False):
 data=weather(url,marine)
 for row in data if isinstance(data,list) else [data]:
  row['hourly']['wind_direction_10m']=[45]*len(row['hourly']['time']);row['hourly']['wave_direction']=[270]*len(row['hourly']['time'])
 return data
def zones_weather(url,marine=False):
 from urllib.parse import urlparse,parse_qs
 import time
 q=parse_qs(urlparse(url).query);lats=q.get('latitude',['40'])[0].split(',');lngs=q.get('longitude',['4'])[0].split(',');start=int(time.time())//3600*3600;times=[start+i*3600 for i in range(96)]
 rows=[]
 for lat,lng in zip(lats,lngs):
  rows.append({'latitude':float(lat),'longitude':float(lng),'hourly':{'time':times,'wind_speed_10m':[8]*96,'wind_gusts_10m':[12]*96,'wind_direction_10m':[90]*96,'temperature_2m':[20]*96,'wave_height':[.3]*96,'wave_direction':[90]*96,'wave_period':[5]*96}})
 return rows if len(rows)>1 else rows[0]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch()
  for width in [393,1280]:
   context=browser.new_context(viewport={'width':width,'height':900},service_workers='block',reduced_motion='reduce');page=context.new_page();errors=[]
   page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',e,flush=True)));page.on('dialog',lambda d:d.accept())
   page.route('**/app.js*',lambda r:r.fulfill(body=(ROOT/'app.js').read_text()+'\nwindow.zonesTest={map:()=>map,state:()=>({draft:structuredClone(draft),mode,entries:structuredClone(entries)})};',content_type='text/javascript'))
   page.route('**/backend.js*',lambda r:r.fulfill(body=backend,content_type='text/javascript'))
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json=zones_weather(r.request.url)))
   page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(json=zones_weather(r.request.url,True)))
   page.goto('http://127.0.0.1:8083/',wait_until='networkidle');page.wait_for_function("!document.querySelector('#meteo-map-hours').disabled")
   before=page.evaluate('zonesTest.state().entries');page.locator('[data-map=layers]').click();page.locator('#zones-layer').check();assert page.locator('#zones-panel').is_visible();assert page.locator('#layers').is_hidden()
   page.locator('#zones-run').click();page.wait_for_function("document.querySelector('#zones-state').textContent.includes('propuestas comparativas')");assert page.locator('#zones-results .card').count()>0;assert page.locator('#zones-results .card').count()<=3;assert page.evaluate('zonesTest.state().entries')==before
   panel=page.locator('#zones-panel').bounding_box();mapbox=page.locator('#map').bounding_box();assert panel['y']>=mapbox['y']+mapbox['height']
   page.locator('#zones-results [data-zone-view]').first.click();assert page.locator('#zones-detail').is_visible();assert 'Máximos' in page.locator('#zones-detail').inner_text();assert 'seguro' not in page.locator('#zones-detail').inner_text().lower()
   page.locator('#zones-results [data-zone-plan]').first.click();page.wait_for_selector('#editor-dialog[open]');assert page.locator('#editor-type').inner_text()=='RUTA PENDIENTE';draft=page.evaluate('zonesTest.state().draft');assert len(draft['data']['points'])>2;assert page.evaluate('zonesTest.state().entries')==before
   page.locator('#close-editor').click();page.locator('#zones-results [data-zone-plan]').first.click();assert page.evaluate('zonesTest.state().draft.id')==draft['id'];page.locator('#close-editor').click()
   page.locator('#meteo-map-hours').focus();page.locator('#meteo-map-hours').press('ArrowRight');assert page.locator('#zones-results .card').count()==0;assert 'Hora del mapa cambiada' in page.locator('#zones-state').inner_text();assert page.evaluate('zonesTest.state().draft.id')==draft['id']
   page.locator('#zones-panel summary').first.click();page.locator('#zones-gust').fill('0');page.locator('#zones-run').click();page.wait_for_function("document.querySelector('#zones-state').textContent.includes('propuestas comparativas')");assert page.locator('#zones-results .card').count()==0;assert 'No hay sectores' in page.locator('#zones-results').inner_text()
   page.locator('#zones-gust').fill('');page.locator('#zones-run').click();page.wait_for_function("document.querySelector('#zones-state').textContent.includes('propuestas comparativas')");page.screenshot(path=str(ROOT/f'tests/zones-{width}.png'))
   page.locator('[data-map=layers]').click();page.locator('#zones-layer').uncheck();assert page.locator('#zones-panel').is_hidden();assert page.evaluate('zonesTest.state().draft.id')==draft['id']
   assert not errors,errors;context.close()
  browser.close();print('ZONES_BROWSER_PASS mobile/desktop: enable in Layers, 1–3 proposals, inline detail/cards below map, coastal plan draft/new ID, existing draft protected, timeline invalidation, limits, toggle, no diary writes. Providers simulated.')
finally:server.shutdown()
