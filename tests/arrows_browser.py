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
  for key,val in [('wind_speed_10m',18),('wind_direction_10m',45),('wind_gusts_10m',28),('temperature_2m',20),('wave_height',.5),('wave_direction',270)]:h[key]=[(val+i*17)%360 for i in range(96)] if key=='wind_direction_10m' else [val+i%9 for i in range(96)] if key=='wind_speed_10m' else [(val+i*15)%360 for i in range(96)] if key=='wave_direction' else [val]*96
  return {'latitude':40,'longitude':4,'hourly':h}
 return [row() for _ in range(20)] if len(q.get('latitude',[''])[0].split(','))==20 else row()
def constant_weather(url,marine=False):
 data=weather(url,marine)
 for row in data if isinstance(data,list) else [data]:
  row['hourly']['wind_direction_10m']=[45]*len(row['hourly']['time']);row['hourly']['wave_direction']=[270]*len(row['hourly']['time'])
 return data
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width in [393,1280]:
   context=browser.new_context(viewport={'width':width,'height':900},service_workers='block',reduced_motion='no-preference');page=context.new_page();errors=[]
   page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',e,flush=True)))
   page.add_init_script("""window.arrowAngles={};const nativeRotate=CanvasRenderingContext2D.prototype.rotate;CanvasRenderingContext2D.prototype.rotate=function(a){if(this.canvas.className==='wind-canvas'||this.canvas.className==='wave-canvas')window.arrowAngles[this.canvas.className]=a;return nativeRotate.call(this,a);};""")
   page.route('**/app.js*',lambda r:r.fulfill(body=(ROOT/'app.js').read_text()+'\nwindow.animationMap=map;',content_type='text/javascript'))
   page.route('**/backend.js*',lambda r:r.fulfill(body=backend,content_type='text/javascript'))
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json=constant_weather(r.request.url)))
   page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(json=constant_weather(r.request.url,True)))
   page.goto('http://127.0.0.1:8083/',wait_until='networkidle');page.wait_for_function("document.querySelector('#wave-status').textContent.includes('Oleaje azul')");page.evaluate('animationMap.setView([40.14,4.1],13,{animate:false})');page.wait_for_timeout(200)
   def images():return page.evaluate("[...document.querySelectorAll('.wind-canvas,.wave-canvas')].map(c=>c.toDataURL())")
   # Both layers animate even before playing the timeline.
   t=page.locator('#meteo-map-hours').get_attribute('data-time');a=images();page.wait_for_timeout(350);b=images();assert a[0]!=b[0] and a[1]!=b[1];assert page.locator('#meteo-map-hours').get_attribute('data-time')==t
   angles=page.evaluate('arrowAngles');import math
   assert abs(angles['wind-canvas']-math.pi/4)<.00001;assert abs(angles['wave-canvas']-3*math.pi/2)<.00001
   page.locator('#meteo-map-play').click();page.wait_for_timeout(1100);page.locator('#meteo-map-pause').click();t=page.locator('#meteo-map-hours').get_attribute('data-time');a=images();page.wait_for_timeout(350);b=images();assert a[0]!=b[0] and a[1]!=b[1];page.wait_for_timeout(900);assert page.locator('#meteo-map-hours').get_attribute('data-time')==t
   # Selecting an hour leaves it fixed while animation keeps running.
   page.locator('#meteo-map-hours').focus();page.locator('#meteo-map-hours').press('ArrowRight');t=page.locator('#meteo-map-hours').get_attribute('data-time');a=images();page.wait_for_timeout(350);b=images();assert a[0]!=b[0] and a[1]!=b[1];assert page.locator('#meteo-map-hours').get_attribute('data-time')==t
   assert not errors,errors;context.close()
  browser.close();print('ARROWS_BROWSER_PASS desktop/mobile: wind and blue waves animate before play, after pause and after scrubbing while forecast hour stays fixed; arrowheads match source bearings NE and W. Services simulated.')
finally:server.shutdown()
