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
   context=browser.new_context(viewport={'width':width,'height':900},service_workers='block');page=context.new_page();errors=[]
   page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',e,flush=True)));page.on('dialog',lambda d:d.accept())
   page.route('**/app.js*',lambda r:r.fulfill(body=(ROOT/'app.js').read_text()+'\nwindow.meteoTest={map:()=>map,state:()=>({mode,draft:structuredClone(draft),weatherSelection,weatherReturn})};',content_type='text/javascript'))
   page.route('**/backend.js*',lambda r:r.fulfill(body=backend,content_type='text/javascript'))
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json=weather(r.request.url)))
   page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(json=weather(r.request.url,True)))
   page.route('**/embed.windy.com/**',lambda r:r.fulfill(body='<html>Windy simulado</html>',content_type='text/html'))
   page.goto('http://127.0.0.1:8083/',wait_until='networkidle');page.wait_for_function("document.querySelector('#wind-day').options.length>1")
   assert page.locator('#weather-button').inner_text().strip().endswith('Meteo');assert not page.locator('#wind-panel').is_visible();assert not page.locator('.meteo-map-control').is_visible()
   page.locator('#weather-button').click();assert 'Toca el mapa' in page.locator('#map-hint').inner_text();page.locator('#cancel-draw').click();assert not page.locator('#meteo-dialog').is_visible();assert not page.locator('.meteo-map-control').is_visible()
   page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':100});page.wait_for_selector('#meteo-dialog[open]');assert 'Punto seleccionado' in page.locator('#wind-point-data').inner_text();page.locator('#wind-day').select_option(index=2);page.locator('#wind-hour').select_option(index=3);time=page.locator('#wind-hour').input_value();page.locator('#meteo-dialog [data-close]').click();assert page.locator('#meteo-map-hours').get_attribute('data-time')==time
   assert page.locator('.meteo-map-control').is_visible();assert 'Viene del NE' in page.locator('#meteo-mini-data').inner_text();assert 'Rachas: 28 km/h' in page.locator('#meteo-mini-data').inner_text()
   bounds=page.locator('.meteo-map-control').bounding_box();mapbox=page.locator('#map').bounding_box();assert bounds['x']>=mapbox['x'];assert bounds['y']+bounds['height']<=mapbox['y']+mapbox['height']+1;assert bounds['x']+bounds['width']<=mapbox['x']+mapbox['width']
   before=page.evaluate('JSON.stringify(meteoTest.state())');page.locator('#meteo-map-hours').fill('4');page.locator('#meteo-map-hours').dispatch_event('input');assert page.evaluate('JSON.stringify(meteoTest.state())')==before
   page.locator('#meteo-map-play').click();page.wait_for_timeout(1100);assert page.locator('#meteo-map-hours').input_value()!='4';page.locator('#meteo-map-play').click();stopped=page.locator('#meteo-map-hours').input_value();page.wait_for_timeout(1000);assert page.locator('#meteo-map-hours').input_value()==stopped
   page.locator('#meteo-details').click();assert page.locator('#wind-hour').input_value()==page.locator('#meteo-map-hours').get_attribute('data-time');page.locator('#wind-full').click();page.wait_for_selector('#forecast-hour:not([disabled])');page.locator('#content-dialog [data-close]').click();assert not page.locator('#meteo-dialog').is_visible()
   # Selecting Meteo in the middle of a real route draft never changes the track.
   page.locator('#new-button').click();page.locator('#map').click(position={'x':150,'y':100});previous=page.evaluate('meteoTest.state().draft');page.locator('#weather-button').click();page.locator('#map').click(position={'x':180,'y':110});page.wait_for_selector('#meteo-dialog[open]');assert page.evaluate('meteoTest.state().draft')==previous;page.locator('#meteo-dialog [data-close]').click();assert page.evaluate('meteoTest.state().mode')!='weather';assert page.evaluate('meteoTest.state().draft')==previous
   page.locator('#meteo-details').click();page.locator('#wind-point').click();page.locator('#cancel-draw').click();assert page.evaluate('meteoTest.state().draft')==previous
   page.locator('#meteo-details').click();page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(status=503,body='unavailable'));page.locator('#wind-retry').click();page.wait_for_function("document.querySelector('#wind-status').textContent.includes('no disponible')");page.locator('#meteo-dialog [data-close]').click();assert page.locator('#meteo-map-hours').is_disabled();assert 'Viento no disponible' in page.locator('#meteo-mini-data').inner_text()
   assert not errors,errors;page.screenshot(path=str(ROOT/f'tests/meteo-{width}.png'));context.close()
  browser.close();print('METEO_BROWSER_PASS: hidden initial panel, choose/cancel point, shared hours/play/pause, lower-left bounds, details/full forecast, draft isolation and errors; desktop/mobile; providers simulated.')
finally:server.shutdown()
