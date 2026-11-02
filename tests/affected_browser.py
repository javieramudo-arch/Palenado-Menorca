"""Only the five requested flows. Real Chromium/Leaflet; simulated account and forecast."""
import functools,http.server,json,threading,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=http.server.ThreadingHTTPServer(('127.0.0.1',8081),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
rows=[{'id':'a','kind':'trip','title':'Mismo nombre','revision':1,'data':{'date':'2026-11-01','points':[[39.93805,3.93665],[39.93168,3.91459]],'source':'gpx','roundtrip':False,'photos':[],'markers':[]}},
 {'id':'b','kind':'trip','title':'Mismo nombre','revision':1,'data':{'date':'2026-11-01','points':[[40.05,4.05],[40.07,4.12]],'source':'gpx','roundtrip':True,'photos':[],'markers':[]}},
 {'id':'bad','kind':'trip','title':'Sin geometría','revision':1,'data':{'date':'2026-11-01','points':[],'photos':[],'markers':[]}},
 {'id':'prefs','kind':'preferences','title':'Preferencias','data':{'paceMinutesPerKm':18}}]
BACKEND='''let rows=SEED;
export async function getClient(){return {auth:{getSession:async()=>({data:{session:{user:{id:'test-user',email:'test@example.invalid'}}}}),onAuthStateChange(){}}};}
export async function loadEntries(){return structuredClone(rows);}
export async function saveEntry(e){const saved={...structuredClone(e),revision:(e.revision||0)+1};const i=rows.findIndex(x=>x.id===e.id);if(i<0)rows.push(saved);else rows[i]=saved;return saved;}
export async function signedPhoto(){throw Error('not used');} export async function uploadPhoto(){throw Error('not used');}
'''.replace('SEED',json.dumps(rows))
try:
 with sync_playwright() as p:
  browser=p.chromium.launch()
  page=browser.new_page(viewport={'width':1280,'height':1000})
  errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',str(e),flush=True)))
  page.route('**/backend.js*',lambda r:r.fulfill(body=BACKEND,content_type='text/javascript'))
  page.add_init_script("""let leaflet;Object.defineProperty(window,'L',{configurable:true,get:()=>leaflet,set:v=>{leaflet=v;v.Map.addInitHook(function(){window.testMap=this;});}});""")
  page.goto('http://127.0.0.1:8081/',wait_until='networkidle')
  page.wait_for_selector('#map.leaflet-container')
  def map_click(lat,lng):
   pos=page.evaluate('([a,b])=>{const p=testMap.latLngToContainerPoint([a,b]);return {x:p.x,y:p.y}}',[lat,lng]);page.locator('#map').click(position=pos)
  for viewport,entry in [({'width':1280,'height':1000},'a'),({'width':393,'height':851},'b')]:
   page.set_viewport_size(viewport);page.locator('[data-tab=diario]').click()
   page.locator(f'[data-action=view-adventure][data-id="{entry}"]').click()
   assert page.locator('#view-mapa').is_visible()
   assert page.locator('#selected-route').get_attribute('data-route-id')==entry
   assert page.locator('#selected-route-name').inner_text()=='Mismo nombre'
   points=rows[0 if entry=='a' else 1]['data']['points']
   projected=page.evaluate('(points)=>points.map(x=>{const p=testMap.latLngToContainerPoint(x);return [p.x,p.y,testMap.getSize().x,testMap.getSize().y]})',points)
   for x,y,w,h in projected: assert 20<=x<=w-75 and 125<=y<=h-35,(x,y,w,h)
   assert not page.locator('dialog[open]').count()
  page.locator('[data-tab=diario]').click();page.locator('[data-action=view-adventure][data-id=bad]').click()
  assert 'no tiene un recorrido válido' in page.locator('#toast').inner_text()
  page.locator('[data-tab=mapa]').click();page.locator('#clear-selection').click()
  page.locator('[data-map=island]').click();page.wait_for_timeout(400)
  page.locator('#plan-button').click();map_click(39.93805,3.93665);map_click(39.93168,3.91459);page.locator('#finish-draw').click()
  assert page.locator('#plan-estimate').is_visible() and not page.locator('#real-duration').is_visible()
  assert page.locator('[name=pace]').input_value()=='18'
  original=int(page.locator('[name=estimate]').input_value());assert original>0
  page.locator('[name=stops]').fill('10');assert int(page.locator('[name=estimate]').input_value())==original+10
  page.locator('[name=roundtrip]').check();assert abs(int(page.locator('[name=estimate]').input_value())-(2*original+10))<=1
  page.locator('#estimate-manual').check();page.locator('[name=estimate]').fill('177');page.locator('[name=pace]').fill('25');assert page.locator('[name=estimate]').input_value()=='177'
  page.locator('#estimate-manual').uncheck();assert page.locator('[name=estimate]').input_value()!='177'
  page.locator('[name=title]').fill('Pendiente azul');estimated=page.locator('[name=estimate]').input_value()
  assert 'pendiente' in page.locator('#route-type').inner_text()
  page.locator('#edit-track').click()
  before=page.evaluate("localStorage.getItem('paleando:0.1:draft:test-user')")
  weather_calls=[]
  fail_marine=[False]
  def forecast(route):
   weather_calls.append(route.request.url);marine='marine-api' in route.request.url
   if marine and fail_marine[0]:
    route.fulfill(status=503,body='unavailable');return
   t=(int(time.time())//3600+1)*3600
   data={'latitude':39.93,'longitude':3.91,'hourly':{'time':[t],**({'wave_height':[0.6],'wave_direction':[90]} if marine else {'temperature_2m':[19],'wind_speed_10m':[12],'wind_direction_10m':[0]})}}
   route.fulfill(body=json.dumps(data),content_type='application/json')
  page.route('https://api.open-meteo.com/**',forecast);page.route('https://marine-api.open-meteo.com/**',forecast)
  page.locator('#weather-button').click();assert 'Toca el mapa donde quieras consultar la previsión'==page.locator('#map-hint').inner_text();assert len(weather_calls)==0
  page.locator('#cancel-draw').click();assert page.locator('#draw-bar').is_visible();assert page.evaluate("localStorage.getItem('paleando:0.1:draft:test-user')")==before
  page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':250})
  page.wait_for_function("document.querySelector('#weather-result')?.textContent.includes('19 °C')")
  result=page.locator('#weather-result').inner_text();assert '12 km/h' in result and '0.6 m' in result and 'Viene del N' in result and 'Viene del E' in result and 'Europe/Madrid' in result and 'Punto marítimo' in result
  assert page.evaluate("localStorage.getItem('paleando:0.1:draft:test-user')")==before
  page.locator('#content-dialog [data-close]').click();assert page.locator('#draw-bar').is_visible()
  fail_marine[0]=True;page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':250})
  page.get_by_role('button',name='Reintentar previsión').wait_for()
  assert 'No disponible' in page.locator('#weather-result').inner_text() and '0.6 m' not in page.locator('#weather-result').inner_text()
  fail_marine[0]=False;page.get_by_role('button',name='Reintentar previsión').click();page.wait_for_function("document.querySelector('#weather-result')?.textContent.includes('0.6 m')")
  page.locator('#content-dialog [data-close]').click()
  page.locator('#finish-draw').click();assert page.locator('[name=estimate]').input_value()==estimated
  page.locator('#save-entry').click();page.locator('#menu-button').click();page.locator('[data-menu=plans]').click();page.locator('#content-dialog [data-action=edit]').click()
  assert page.locator('[name=estimate]').input_value()==estimated
  page.locator('#close-editor').click();page.locator('[data-tab=mapa]').click();page.locator('#resume-draft').click();page.on('dialog',lambda d:d.accept());page.locator('#discard-draft').click()
  page.locator('#menu-button').click();page.locator('[data-menu=plans]').click();page.locator('#content-dialog [data-action=detail]').click();page.locator('[data-action=complete]').click()
  assert not page.locator('#plan-estimate').is_visible();assert page.locator('#real-duration').is_visible();assert page.locator('[name=duration]').input_value()=='';assert 'ida y vuelta' in page.locator('#route-type').inner_text()
  assert '#ad5c28' in page.locator('#route-type').get_attribute('style')
  page.locator('[name=duration]').fill('80');page.locator('#save-entry').click()
  assert page.locator('#trip-list .route-badge').filter(has_text='ida y vuelta').count()>=1
  page.locator('#menu-button').click();page.locator('[data-menu=plans]').click();assert not page.locator('#content-dialog .card').count();page.locator('#content-dialog [data-close]').click()
  assert page.locator('#install-app').is_visible();page.locator('#install-app').click();assert 'Chrome' in page.locator('#content-body').inner_text() or 'Edge' in page.locator('#content-body').inner_text()
  page.locator('#content-dialog [data-close]').click()
  page.wait_for_function("navigator.serviceWorker.controller!==null")
  assert page.evaluate("fetch('./manifest.webmanifest').then(r=>r.json()).then(m=>m.icons.some(i=>i.sizes==='192x192')&&m.icons.some(i=>i.sizes==='512x512'))")
  assert not errors,errors
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=str(ROOT/'tests'/'affected-mobile.png'),full_page=True)
  page.set_viewport_size({'width':1280,'height':1000});page.screenshot(path=str(ROOT/'tests'/'affected-desktop.png'),full_page=True)
  print('AFFECTED_BROWSER_PASS: route ID and framing desktop/mobile, weather selection/cancel/no route mutation, units/time/directions/sea adjustment, PWA manifest/service worker/manual flow, plan auto/manual persistence and conversion colors; account/weather simulated',flush=True)
  browser.close()
finally: server.shutdown()
