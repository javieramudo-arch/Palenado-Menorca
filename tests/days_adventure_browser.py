"""Only day navigation, official iframe lifecycle and inline adventure/actions.
Chromium and Leaflet real; diary, photos, forecast and Windy iframe simulated.
"""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=http.server.ThreadingHTTPServer(('127.0.0.1',8081),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
rows=[{'id':'one','kind':'trip','title':'Nombre repetido','revision':1,'data':{'date':'2026-11-01','points':[[39.93805,3.93665],[39.93168,3.91459]],'source':'gpx','roundtrip':False,'photos':[{'id':'p','path':'private/test','name':'Mi fotografía'}],'markers':[],'duration':75,'estimatedMinutes':90,'notes':'Notas completas','conditions':'Mar tranquilo','rating':4,'parking':'Junto al acceso','customDetail':'Información adicional'}},
 {'id':'two','kind':'plan','title':'Nombre repetido','revision':1,'data':{'date':'2026-11-01','points':[[40.05,4.05],[40.07,4.12]],'source':'gpx','roundtrip':True,'photos':[],'markers':[],'estimatedMinutes':130,'notes':'Pendiente conservada'}},
 {'id':'invalid','kind':'trip','title':'Sin trazado','revision':1,'data':{'date':'2026-11-01','points':[],'photos':[],'markers':[],'notes':'Conservar la ficha sin geometría'}}]
BACKEND='''let rows=SEED;
export async function getClient(){return {auth:{getSession:async()=>({data:{session:{user:{id:'test-user',email:'test@example.invalid'}}}}),onAuthStateChange(){}}};}
export async function loadEntries(){return structuredClone(rows);}
export async function saveEntry(e){const saved={...structuredClone(e),revision:(e.revision||0)+1};const i=rows.findIndex(x=>x.id===e.id);if(i<0)rows.push(saved);else rows[i]=saved;return saved;}
export async function signedPhoto(){return './guide-photo.svg';}export async function uploadPhoto(){throw Error('unused');}
'''.replace('SEED',json.dumps(rows))
try:
 with sync_playwright() as p:
  browser=p.chromium.launch();page=browser.new_page(viewport={'width':1280,'height':1000},accept_downloads=True)
  errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',str(e),flush=True)))
  page.route('**/backend.js*',lambda r:r.fulfill(body=BACKEND,content_type='text/javascript'))
  page.add_init_script("""Date.now=()=>Date.UTC(2026,10,2,8);let leaflet;Object.defineProperty(window,'L',{configurable:true,get:()=>leaflet,set:v=>{leaflet=v;v.Map.addInitHook(function(){window.testMap=this;});}});""")
  requests=[];fail=[False]
  from datetime import datetime,timezone
  times=[int(datetime(2026,11,day,hour,tzinfo=timezone.utc).timestamp()) for day in [2,3,4,5] for hour in [10,14]]
  def forecast(route):
   requests.append(route.request.url)
   if fail[0]:route.fulfill(status=503,body='unavailable');return
   marine='marine-api' in route.request.url
   hourly={'time':times,**({'wave_height':[.2,.21,.3,.31,None,None,.5,.51],'wave_direction':[0,0,90,90,None,None,270,270]} if marine else {'temperature_2m':[11,12,21,22,31,32,41,42],'wind_speed_10m':[2,3,4,5,6,7,8,9],'wind_direction_10m':[0,0,90,90,180,180,270,270]})}
   route.fulfill(body=json.dumps({'latitude':39.93,'longitude':3.91,'hourly':hourly}),content_type='application/json')
  page.route('https://api.open-meteo.com/**',forecast);page.route('https://marine-api.open-meteo.com/**',forecast)
  page.route('https://embed.windy.com/**',lambda r:r.fulfill(body='<html><body><p>Windy iframe simulated</p></body></html>',content_type='text/html'))
  page.goto('http://127.0.0.1:8081/',wait_until='networkidle');page.wait_for_selector('#map.leaflet-container')
  def open_adventure(identifier):
   page.locator('[data-tab=diario]').click()
   button=page.locator(f'#trip-list [data-action=view-adventure][data-id="{identifier}"]')
   if button.count():button.click()
   else:
    page.locator('#menu-button').click();page.locator('[data-menu=plans]').click();page.locator(f'#content-dialog [data-action=view-adventure][data-id="{identifier}"]').click()
  for viewport in [{'width':1280,'height':1000},{'width':393,'height':851}]:
   page.set_viewport_size(viewport);open_adventure('one')
   assert page.locator('#adventure-panel').get_attribute('data-route-id')=='one';assert page.locator('#adventure-image').is_visible()
   page.wait_for_function("document.querySelector('#adventure-image img').naturalWidth>0")
   text=page.locator('#adventure-sheet').inner_text();assert all(s in text for s in ['Notas completas','Mar tranquilo','Aparcamiento','Información adicional','Duración real','Duración estimada','1 h 15 min','1 h 30 min'])
   boxes=page.evaluate("()=>{const a=document.querySelector('#adventure-image').getBoundingClientRect(),b=document.querySelector('#adventure-sheet').getBoundingClientRect(),c=document.querySelector('#map-wrap').getBoundingClientRect();return [a.bottom,b.top,b.bottom,c.top]}")
   assert boxes[0]<=boxes[1]+1 and boxes[2]<=boxes[3]
   page.locator('#adventure-sheet [data-action=focus-adventure-map]').click()
   bounds=page.evaluate('(points)=>points.map(x=>{const p=testMap.latLngToContainerPoint(x);return [p.x,p.y,testMap.getSize().x,testMap.getSize().y]})',rows[0]['data']['points'])
   for x,y,w,h in bounds:assert 20<=x<=w-75 and 40<=y<=h-40,(x,y,w,h)
   action=page.locator('#adventure-sheet .adventure-actions').bounding_box();map_box=page.locator('#map-wrap').bounding_box();assert action['y']+action['height']<=map_box['y']
   open_adventure('two');assert page.locator('#adventure-panel').get_attribute('data-route-id')=='two';assert not page.locator('#adventure-image').is_visible();assert 'Pendiente conservada' in page.locator('#adventure-sheet').inner_text()
   open_adventure('invalid');assert 'Conservar la ficha' in page.locator('#adventure-sheet').inner_text();assert page.locator('#adventure-map-notice').is_visible()
   page.locator('#clear-selection').click();page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':230})
   page.wait_for_function("document.querySelector('#weather-result')?.textContent.includes('12 °C')")
   original_calls=len(requests);point=page.locator('.forecast-location').inner_text()
   assert page.locator('#forecast-prev').is_disabled();assert not page.locator('#forecast-next').is_disabled()
   page.locator('#forecast-next').click();page.wait_for_function("document.querySelector('#weather-result').textContent.includes('22 °C')")
   assert page.locator('#forecast-day-label').get_attribute('data-day')=='2026-11-03'
   page.locator('#forecast-hour').select_option(str(times[2]));assert '21 °C' in page.locator('#weather-result').inner_text()
   page.locator('#forecast-next').click();page.wait_for_function("document.querySelector('#weather-result').textContent.includes('32 °C')");assert 'No disponible' in page.locator('#weather-result').inner_text();assert '.31 m' not in page.locator('#weather-result').inner_text()
   page.locator('#forecast-next').click();page.wait_for_function("document.querySelector('#weather-result').textContent.includes('42 °C')");assert page.locator('#forecast-next').is_disabled()
   page.locator('#forecast-prev').click();page.locator('#forecast-today').click();page.wait_for_function("document.querySelector('#weather-result').textContent.includes('12 °C')");assert page.locator('#forecast-prev').is_disabled()
   page.evaluate("()=>{document.querySelector('#forecast-next').click();document.querySelector('#forecast-next').click();document.querySelector('#forecast-prev').click();}")
   page.wait_for_function("document.querySelector('#weather-result').textContent.includes('22 °C')");assert page.locator('#weather-result').get_attribute('data-day')=='2026-11-03';assert page.locator('.forecast-location').inner_text()==point;assert len(requests)==original_calls
   frame=page.locator('iframe.windy-frame');assert 'embed.windy.com/embed2.html' in frame.get_attribute('src');page.frame_locator('iframe.windy-frame').get_by_text('Windy iframe simulated').wait_for();assert 'propio selector temporal' in page.locator('.windy-time-note').inner_text()
   page.evaluate("document.querySelector('iframe.windy-frame').dispatchEvent(new Event('error'))");assert not page.locator('iframe.windy-frame').count();assert 'bloqueado' in page.locator('#windy-map').inner_text();assert page.get_by_role('link',name='Abrir en Windy').is_visible();page.get_by_role('button',name='Reintentar mapa').click();page.frame_locator('iframe.windy-frame').get_by_text('Windy iframe simulated').wait_for()
   # The close button and day toolbar remain above the iframe while scrolling.
   page.locator('iframe.windy-frame').scroll_into_view_if_needed();close=page.locator('#content-dialog [data-close]').bounding_box();assert close['y']>=0 and close['y']<viewport['height']
   page.locator('#content-dialog [data-close]').click()
  # Error/retry resets data and retains the selected coordinates.
  fail[0]=True;page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':230});page.get_by_role('button',name='Reintentar previsión').wait_for();assert '12 °C' not in page.locator('#weather-result').inner_text();fail[0]=False;page.get_by_role('button',name='Reintentar previsión').click();page.wait_for_function("document.querySelector('#weather-result').textContent.includes('12 °C')");page.locator('#content-dialog [data-close]').click()
  # Existing sheet actions use the original ID and normal handlers.
  open_adventure('one')
  page.locator('#adventure-sheet [data-photo]').click();page.wait_for_selector('.photo-view');page.locator('#content-dialog [data-close]').click()
  with page.expect_download() as event:page.locator('#adventure-sheet [data-action=export]').click()
  assert 'one' in event.value.suggested_filename
  page.locator('#adventure-sheet [data-action=edit]').click();page.locator('[name=title]').fill('Nombre editado');page.locator('#save-entry').click();page.locator('[data-action=view-adventure][data-id=one]').click();assert 'Nombre editado' in page.locator('#adventure-sheet h2').inner_text()
  page.on('dialog',lambda d:d.accept());page.locator('#adventure-sheet [data-action=delete]').click();assert not page.locator('#adventure-panel').is_visible();page.locator('#undo').click();open_adventure('one');assert 'Nombre editado' in page.locator('#adventure-sheet h2').inner_text()
  open_adventure('two');page.locator('#adventure-sheet [data-action=complete]').click();page.locator('[name=duration]').fill('110');page.locator('#save-entry').click();page.locator('[data-action=view-adventure][data-id=two]').click();assert 'Realizada' in page.locator('#adventure-sheet').inner_text();assert '1 h 50 min' in page.locator('#adventure-sheet').inner_text()
  open_adventure('invalid');page.locator('#adventure-sheet [data-action=delete]').click();assert not page.locator('#adventure-panel').is_visible();page.locator('#undo').click();open_adventure('invalid');assert 'Conservar la ficha sin geometría' in page.locator('#adventure-sheet').inner_text()
  assert not errors,errors;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(ROOT/'tests'/'days-adventure-mobile.png'),full_page=True)
  print('DAYS_ADVENTURE_BROWSER_PASS: day/hour/limits/Today/rapid navigation, point retained, missing values and retry; official iframe rendering simulated plus error fallback; ID/photo-sheet-map flow, framing and sheet actions desktop/mobile; account/photo/forecast/Windy simulated',flush=True)
  browser.close()
finally:server.shutdown()
