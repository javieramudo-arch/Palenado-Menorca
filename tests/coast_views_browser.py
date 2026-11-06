import os
"""Affected experience flows. Chromium real, meteorology and account simulated."""
import functools,http.server,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=http.server.ThreadingHTTPServer(('127.0.0.1',8083),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
backend="""let rows=SEED;window.testRows=()=>structuredClone(rows);const user={id:'test',email:'test@example.invalid'};export async function getClient(){return {auth:{getSession:async()=>({data:{session:{user}}}),onAuthStateChange(){}}};}export async function loadEntries(){return structuredClone(rows);}export async function saveEntry(e){e={...structuredClone(e),revision:(e.revision||0)+1};const i=rows.findIndex(r=>r.id===e.id);if(i<0)rows.push(e);else rows[i]=e;return e;}export async function signedPhoto(){return './guide-photo.svg';}export async function uploadPhoto(){throw Error('unused');}"""
rows=[dict(id=id,revision=1,kind=kind,title='Nombre repetido',data=dict(date='2026-11-03',points=[[39.93805,3.93665],[39.93168,3.91459]],source='gpx',zone='Sur',duration=45,estimatedMinutes=60,wind='fuerte',photos=[],markers=[])) for id,kind in [('trip','trip'),('trip2','trip'),('plan1','plan')]]
rows[1]['data']['roundtrip']=True
rows[0]['data']['markers']=[dict(id='access-marker',category='access',title='Acceso',point=[39.93805,3.93665])]
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
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width in [393,1280]:
   context=browser.new_context(viewport={'width':width,'height':900},service_workers='block',reduced_motion='reduce');page=context.new_page();errors=[]
   page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',e,flush=True)));page.on('dialog',lambda d:d.accept())
   hook="""
window.coastTest={map:()=>map,show:viewAdventure,state:()=>({view:coastViews.current,previous:coastViews.previous,selected:selectedRouteId,draft:structuredClone(draft),entries:structuredClone(entries),visible:Object.fromEntries(Object.entries({...groups,pending:pendingLayer,selected:selectionLayer,draft:drawLayer}).map(([k,v])=>[k,map.hasLayer(v)])),styles:Object.fromEntries(['trips','plans','selected','pending'].map(k=>[k,(k==='selected'?selectionLayer:k==='pending'?pendingLayer:groups[k]).getLayers().map(x=>({color:x.options.color,dash:x.options.dashArray}))]))})};"""
   page.route('**/app.js*',lambda r:r.fulfill(body=(ROOT/'app.js').read_text()+hook,content_type='text/javascript'))
   page.route('**/backend.js*',lambda r:r.fulfill(body=backend,content_type='text/javascript'))
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json=zones_weather(r.request.url)))
   page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(json=zones_weather(r.request.url,True)))
   page.goto('http://127.0.0.1:8083/',wait_until='networkidle');page.wait_for_function("!document.querySelector('#meteo-map-hours').disabled")
   state=lambda:page.evaluate('coastTest.state()')
   def layers():
    if page.locator('#layers').is_hidden():page.locator('[data-map=layers]').click()
   original=state()['entries'];assert state()['view']=='routes';assert {x['color'] for x in state()['styles']['trips']}=={'#11796f','#ad5c28'};assert all(x['dash']=='6 6' for x in state()['styles']['plans'])
   # Reproduces the complaint with overlapping saved trip/plan geometry.
   assert not state()['visible']['plans'] and not state()['visible']['pending'];assert not page.locator('[data-layer=plans]').is_checked()
   layers();page.locator('[data-layer=plans]').check();assert state()['view']=='plans';assert state()['visible']['plans'] and not state()['visible']['trips'] and not state()['visible']['pending'];assert state()['visible']['access'];assert page.locator('#coast-view-name').inner_text()=='Rutas pendientes'
   page.locator('#pending-coast').check();assert not state()['visible']['plans'];page.locator('[data-map=layers]').click();page.locator('#coast-view-back').click();assert state()['view']=='plans' and state()['visible']['plans'];assert not state()['visible']['trips']
   layers();page.locator('[data-layer=plans]').uncheck();assert state()['view']=='routes';assert state()['visible']['trips'] and not state()['visible']['plans']
   # Opening one planned adventure is an explicit isolated display, and closing hides it again.
   page.locator('[data-map=layers]').click()
   page.evaluate("coastTest.show('plan1')");assert state()['view']=='adventure' and state()['selected']=='plan1';assert state()['visible']['selected'] and not state()['visible']['plans'];page.locator('#clear-selection').click();assert state()['view']=='routes' and not state()['visible']['plans']
   layers();page.locator('[data-layer=trips]').uncheck();page.locator('[data-layer=plans]').check();page.locator('[data-layer=plans]').uncheck();assert not state()['visible']['trips'];assert not page.locator('[data-layer=trips]').is_checked();page.locator('[data-layer=trips]').check();page.locator('#pending-coast').check();s=state();assert s['view']=='pending';assert s['visible']['pending'] and not s['visible']['trips'] and not s['visible']['plans'];assert s['visible']['access'];assert page.locator('[data-layer=plans]').is_enabled();assert s['styles']['pending'][0]['dash']=='2 8'
   page.locator('[data-map=layers]').click();page.locator('#coast-view-back').click();assert state()['visible']['trips'] and not state()['visible']['plans'];assert not page.locator('[data-layer=plans]').is_checked();assert page.locator('[data-layer=plans]').is_enabled()
   layers();page.locator('#zones-layer').check();page.locator('#zones-run').click();page.wait_for_function("document.querySelector('#zones-state').textContent.includes('propuestas comparativas')");count=page.locator('#zones-results .card').count();assert count>0;assert page.locator('.legend-sectors').is_visible();assert page.locator('.legend-sectors span').count()==4
   assert not state()['visible']['trips'] and not state()['visible']['pending'];assert state()['visible']['access'];assert page.locator('.coast-sea-bands').evaluate("e=>getComputedStyle(e).pointerEvents")=='none'
   # Raster pixels are only on the sea side; the coast itself has a transparent channel.
   band=page.evaluate("""async()=>{const {landMask}=await import('./wave-field.js?v=0.10.1'),mask=landMask(),c=document.querySelector('.coast-sea-bands'),m=coastTest.map(),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let sea=0,land=0;for(let y=0;y<c.height;y+=2)for(let x=0;x<c.width;x+=2)if(d[(y*c.width+x)*4+3]){const p=m.containerPointToLatLng([x+.5,y+.5]);if(mask([p.lat,p.lng]))land++;else sea++;}return {sea,land};}""");assert band['sea']>30,band;assert band['land']==0,band
   page.screenshot(path=str(ROOT/f'tests/coast-zones-{width}.png'))
   if width==393:
    import base64
    print('COAST_PREVIEW_393 '+base64.b64encode(page.locator('#map-wrap').screenshot()).decode(),flush=True)
   gap=page.evaluate("""async()=>{const {coastSectors}=await import('./zone-analysis.js?v=0.12.0'),m=coastTest.map(),c=document.querySelector('.coast-sea-bands'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0,painted=0;for(const s of coastSectors())for(const[a,b]of s.segments){const p=m.latLngToContainerPoint([(a[0]+b[0])/2,(a[1]+b[1])/2]),x=Math.round(p.x),y=Math.round(p.y);if(x<0||y<0||x>=c.width||y>=c.height)continue;n++;if(d[(y*c.width+x)*4+3])painted++;}return {n,painted};}""");assert gap['n']>20 and gap['painted']==0,gap
   layers();page.locator('#pending-coast').check();assert state()['view']=='pending';assert page.locator('#zones-panel').is_hidden();assert page.locator('.coast-sea-bands').is_hidden()
   page.locator('[data-map=layers]').click();page.locator('[data-tab=diario]').click();page.locator('[data-action=view-adventure][data-id=trip2]').click();assert state()['view']=='adventure';assert state()['selected']=='trip2';assert state()['visible']['selected'] and not state()['visible']['pending'] and not state()['visible']['trips'];assert page.locator('#selected-route').get_attribute('data-route-id')=='trip2';assert 'ida y vuelta' in page.locator('#selected-route-type').inner_text().lower()
   page.wait_for_timeout(250)
   fits=page.evaluate("""()=>{const m=coastTest.map(),e=coastTest.state().entries.find(e=>e.id==='trip2'),sz=m.getSize();return e.data.points.every(p=>{const a=m.latLngToContainerPoint(p);return a.x>=15&&a.x<=sz.x-15&&a.y>=document.querySelector('.map-color-legend').getBoundingClientRect().bottom-m.getContainer().getBoundingClientRect().top+8&&a.y<=document.querySelector('.meteo-map-control').getBoundingClientRect().top-m.getContainer().getBoundingClientRect().top-8;});}""");assert fits
   sheet=page.locator('#adventure-sheet').bounding_box();mb=page.locator('#map').bounding_box();assert sheet['y']+sheet['height']<=mb['y'];page.locator('#clear-selection').click();assert state()['view']=='pending';assert state()['visible']['pending'];page.locator('#coast-view-back').click();assert state()['view']=='zones';assert page.locator('#zones-results .card').count()==count;assert page.locator('.coast-sea-bands').is_visible()
   page.locator('#coast-view-back').click();assert state()['view']=='routes';assert state()['visible']['trips'] and not state()['visible']['plans'];assert state()['entries']==original
   layers();page.locator('#zones-layer').check();page.locator('#zones-results [data-zone-plan]').first.click();page.wait_for_selector('#editor-dialog[open]');page.locator('[name=notes]').fill('Conservar borrador');draft_id=state()['draft']['id'];assert state()['visible']['draft'] and not state()['visible']['trips'];assert page.locator('.coast-sea-bands').is_hidden();page.locator('#close-editor').click();assert state()['view']=='zones';assert page.locator('.coast-sea-bands').is_visible();assert state()['draft']['id']==draft_id;assert state()['draft']['data']['notes']=='Conservar borrador';assert state()['entries']==original
   assert page.locator('.wind-canvas').is_visible();assert page.locator('.wave-canvas').is_visible();assert page.evaluate('document.documentElement.scrollWidth')<=width+1
   assert state()['entries']==original
   page.reload(wait_until='networkidle');page.wait_for_function("window.coastTest&&coastTest.state().entries.length===3");assert state()['view']=='routes';assert not state()['visible']['plans'] and not state()['visible']['pending'];assert not page.locator('[data-layer=plans]').is_checked();assert state()['entries']==original
   assert not errors,errors;context.close()
  browser.close();print('COAST_VIEWS_PASS mobile/desktop: blue plans hidden on load/reload, explicit plans-only toggle/back, saved route filters, markers and weather preserved, ID-based adventure isolation/full bounds, nested restoration, sea-only passive ribbon, preserved analysis/draft/data. Account and providers simulated.')
finally:server.shutdown()
