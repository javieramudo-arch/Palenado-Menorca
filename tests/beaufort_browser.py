import os
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
  for key,val in [('wind_speed_10m',18),('wind_direction_10m',45),('wind_gusts_10m',28),('temperature_2m',20),('wave_height',.5),('wave_direction',90)]:h[key]=[(val+i*17)%360 for i in range(96)] if key=='wind_direction_10m' else [val+i%9 for i in range(96)] if key=='wind_speed_10m' else [val]*96
  return {'latitude':40,'longitude':4,'hourly':h}
 return [row() for _ in range(20)] if len(q.get('latitude',[''])[0].split(','))==20 else row()
scenario={'wind':12,'gust':36,'fail':False}
def dataset(url):
 from urllib.parse import urlparse,parse_qs
 import time
 q=parse_qs(urlparse(url).query);start=int(time.time())//3600*3600;times=[start+i*3600 for i in range(96)];lat=q.get('latitude',['40'])[0].split(',');lon=q.get('longitude',['4'])[0].split(',')
 def row(a,b):return {'latitude':float(a),'longitude':float(b),'hourly':{'time':times,'wind_speed_10m':[scenario['wind']]*96,'wind_gusts_10m':[scenario['gust']]*96,'wind_direction_10m':[45]*96,'temperature_2m':[20]*96,'wave_height':[.5]*96,'wave_direction':[90]*96}}
 rows=[row(a,b) for a,b in zip(lat,lon)];return rows if len(rows)>1 else rows[0]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width in [393,1280]:
   scenario.update(wind=12,gust=36,fail=False);context=browser.new_context(viewport={'width':width,'height':900},service_workers='block',reduced_motion='reduce');page=context.new_page();errors=[]
   page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',e,flush=True)))
   page.add_init_script("""window.windPaint=new Set();const stroke=CanvasRenderingContext2D.prototype.stroke;CanvasRenderingContext2D.prototype.stroke=function(...args){if(this.canvas.className==='wind-canvas')windPaint.add(this.strokeStyle);return stroke.apply(this,args);};""")
   page.route('**/backend.js*',lambda r:r.fulfill(body=backend,content_type='text/javascript'))
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(status=503,body='unavailable') if scenario['fail'] else r.fulfill(json=dataset(r.request.url)))
   page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(json=dataset(r.request.url)))
   page.route('**/embed.windy.com/**',lambda r:r.fulfill(body='<html>Windy simulado</html>',content_type='text/html'))
   page.goto('http://127.0.0.1:8083/',wait_until='networkidle');page.wait_for_selector('#meteo-mini-data [data-kind=wind][data-force="2"]')
   assert page.locator('#meteo-mini-data [data-kind=gust]').get_attribute('data-force')=='5';paint=page.evaluate('[...windPaint]');assert '#7cff00' in paint and '#ff6347' not in paint,paint
   assert page.locator('#meteo-mini-data [data-kind=wind]').evaluate("e=>getComputedStyle(e).color")=='rgb(124, 255, 0)';assert page.locator('#meteo-mini-data [data-kind=gust]').evaluate("e=>getComputedStyle(e).color")=='rgb(255, 99, 71)'
   def bounds():
    wind=page.locator('.mini-wind').bounding_box();gust=page.locator('.mini-gust').bounding_box();pill=page.locator('#meteo-map-date').bounding_box();assert wind['x']+wind['width']<=pill['x']-2,(wind,pill);assert gust['x']>=pill['x']+pill['width']+2,(gust,pill)
   bounds();page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':100});page.wait_for_selector('#meteo-dialog[open]');assert page.locator('#wind-point-data [data-kind=wind]').get_attribute('data-force')=='2';assert page.locator('#wind-point-data [data-kind=gust]').get_attribute('data-force')=='5';page.locator('#wind-panel .meteo-explanation > summary').click();assert 'equivalencia' in page.locator('#wind-panel').inner_text();assert 'km/h' not in page.locator('#wind-panel').inner_text();page.locator('#wind-panel .meteo-explanation > summary').click()
   page.locator('#wind-full').click();page.wait_for_selector('#weather-result [data-kind=gust]');assert page.locator('#weather-result .forecast-grid [data-kind=wind]').get_attribute('data-force')=='2';assert page.locator('#weather-result .forecast-grid [data-kind=gust]').get_attribute('data-force')=='5';assert 'equivalencia' in page.locator('#weather-result').inner_text();assert 'km/h' not in page.locator('#weather-result').inner_text();assert 'metricWind=bft' in page.locator('.windy-frame').get_attribute('src')
   current=page.locator('#weather-result').get_attribute('data-day');page.locator('#forecast-next').click();page.wait_for_function("old=>document.querySelector('#weather-result').dataset.day!==old&&!!document.querySelector('#weather-result .forecast-grid')",arg=current);assert page.locator('#weather-result').get_attribute('data-day')!=current;assert page.locator('#weather-result .forecast-grid [data-kind=wind]').get_attribute('data-force')=='2';page.locator('#content-dialog [data-close]').click()
   for speed,gust,force,gforce,color in [(27,45,'4','6','#ff7900'),(36,None,'5',None,'#ff6347'),(None,36,None,'5',None),(0,0,'0','0','#7cff00'),(12,18,'2','3','#7cff00')]:
    scenario.update(wind=speed,gust=gust);page.evaluate('windPaint.clear()');page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':100});page.wait_for_selector('#meteo-dialog[open]');page.locator('#wind-retry').click();page.wait_for_function("!document.querySelector('#wind-retry').disabled");actual=page.locator('#meteo-mini-data [data-kind=wind]').get_attribute('data-force');gactual=page.locator('#meteo-mini-data [data-kind=gust]').get_attribute('data-force');print('BFT_CASE',width,speed,gust,actual,gactual,flush=True);assert actual==force,(speed,actual,force);assert gactual==gforce,(gust,gactual,gforce);assert color is None or speed==0 or color in page.evaluate('[...windPaint]');assert 'km/h' not in page.locator('#wind-point-data').inner_text()
    if force is None or speed==0:assert page.locator('.wind-canvas').evaluate("c=>!c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)")
    if gforce is None:assert page.locator('#meteo-mini-data [data-kind=gust]').inner_text()=='No disponible'
    page.locator('#meteo-dialog [data-close]').click();bounds()
   page.locator('#meteo-map-hours').focus();page.locator('#meteo-map-hours').press('ArrowRight');assert page.locator('#meteo-mini-data [data-kind=gust]').get_attribute('data-force')=='3'
   import base64
   box=page.locator('.map-color-legend').bounding_box();bar=page.locator('.meteo-map-control').bounding_box();print('BEAUFORT_PREVIEW_'+str(width)+' '+base64.b64encode(page.screenshot(clip={'x':bar['x'],'y':box['y']-3,'width':bar['width'],'height':bar['y']+bar['height']-box['y']+6})).decode(),flush=True)
   scenario['fail']=True;page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':100});page.wait_for_selector('#meteo-dialog[open]');page.locator('#wind-retry').click();page.wait_for_function("!document.querySelector('#wind-retry').disabled");assert page.locator('#meteo-mini-data .is-missing').count()==2;assert page.locator('#meteo-mini-data [data-force]').count()==0
   assert not errors,errors;context.close()
  browser.close();print('BEAUFORT_BROWSER_PASS mobile/desktop: independent wind/gust force and color; arrow paint follows mean only; true calm, missing gust, provider failure clears data, details/hour/day, Windy bft URL, compact nonoverlapping mini readings. Providers and account simulated.')
finally:server.shutdown()
