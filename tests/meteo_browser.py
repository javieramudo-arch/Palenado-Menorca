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
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width in [393,1280]:
   context=browser.new_context(viewport={'width':width,'height':900},service_workers='block',reduced_motion='reduce');page=context.new_page();errors=[]
   page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',e,flush=True)));page.on('dialog',lambda d:d.accept())
   page.route('**/app.js*',lambda r:r.fulfill(body=(ROOT/'app.js').read_text()+'\nwindow.meteoTest={map:()=>map,state:()=>({mode,draft:structuredClone(draft),weatherSelection,weatherReturn})};',content_type='text/javascript'))
   page.route('**/backend.js*',lambda r:r.fulfill(body=backend,content_type='text/javascript'))
   page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(json=weather(r.request.url)))
   page.route('**/marine-api.open-meteo.com/**',lambda r:r.fulfill(json=weather(r.request.url,True)))
   page.route('**/embed.windy.com/**',lambda r:r.fulfill(body='<html>Windy simulado</html>',content_type='text/html'))
   page.goto('http://127.0.0.1:8083/',wait_until='networkidle');page.wait_for_function("!document.querySelector('#meteo-map-hours').disabled")
   assert page.locator('.meteo-map-control').is_visible();assert not page.locator('#wind-panel').is_visible();assert page.locator('.meteo-map-control button').count()==2
   assert page.locator('.meteo-map-control .windsock,.meteo-map-control .wind-compass,#meteo-details,#meteo-hide').count()==0
   assert 'km/h' in page.locator('#meteo-mini-data').inner_text();assert 'Rachas' not in page.locator('.meteo-map-control').inner_text()
   first=int(page.locator('#meteo-map-hours').get_attribute('data-time'));page.locator('#meteo-map-hours').focus();page.locator('#meteo-map-hours').press('End');last=int(page.locator('#meteo-map-hours').get_attribute('data-time'));assert last-first==48*3600;page.locator('#meteo-map-hours').press('Home')
   initial_image=page.locator('.wind-canvas').evaluate('(c)=>c.toDataURL()');initial_text=page.locator('#meteo-mini-data').inner_text();page.locator('#meteo-map-hours').press('ArrowRight');page.locator('#meteo-map-hours').press('ArrowRight');assert page.locator('.wind-canvas').evaluate('(c)=>c.toDataURL()')!=initial_image
   assert page.locator('#meteo-mini-data').inner_text()!=initial_text
   play_start=int(page.locator('#meteo-map-hours').input_value());page.locator('#meteo-map-play').click();page.locator('#meteo-map-play').click();page.wait_for_timeout(1100);page.locator('#meteo-map-pause').click();stopped=page.locator('#meteo-map-hours').input_value();assert int(stopped)>play_start;page.wait_for_timeout(1000);assert page.locator('#meteo-map-hours').input_value()==stopped
   def bounds():
    box=page.locator('.meteo-map-control').bounding_box();m=page.locator('#map').bounding_box();assert box['height']<=64,box;assert box['width']>=m['width']-24;assert box['x']>=m['x'];assert box['x']+box['width']<=m['x']+m['width']+1;assert box['y']+box['height']<=m['y']+m['height']+1;key=page.locator('.map-color-legend').bounding_box();pill=page.locator('#meteo-map-date').bounding_box();assert key['height']<=52,key;assert key['x']>=m['x'] and key['x']+key['width']<=m['x']+m['width']+1;assert key['y']>=m['y'];assert key['y']+key['height']<=pill['y']-2;assert page.locator('.map-color-legend button,.map-color-legend input').count()==0
   bounds()
   assert '15–<30' in page.locator('.legend-weather').inner_text();assert 'km/h' in page.locator('.legend-weather').inner_text();assert page.locator('.legend-weather svg').count()==4
   assert page.locator('.legend-tracks span').count()==4;assert page.locator('.legend-tracks .dash').count()==1;assert page.locator('.legend-tracks .dots').count()==1;assert page.locator('.legend-sectors').is_hidden()
   assert page.locator('.legend-tracks i').evaluate_all("els=>els.map(e=>e.style.getPropertyValue('--legend-color'))")==['#11796f','#ad5c28','#2678c8','#8650ad']
   assert page.locator('.legend-weather svg').evaluate_all("els=>els.map(e=>e.style.color)")==['rgb(17, 137, 128)','rgb(36, 124, 115)','rgb(134, 80, 173)','rgb(8, 126, 213)']
   import base64
   key=page.locator('.map-color-legend').bounding_box();bar=page.locator('.meteo-map-control').bounding_box();preview=page.screenshot(clip={'x':bar['x'],'y':key['y']-3,'width':bar['width'],'height':bar['y']+bar['height']-key['y']+6});print('LEGEND_PREVIEW_'+str(width)+' '+base64.b64encode(preview).decode(),flush=True)
   # Fixed hour marker; moving ruler responds to actual touch/mouse drag and pauses playback.
   pill=page.locator('#meteo-map-date').bounding_box();m=page.locator('#map').bounding_box();assert abs(pill['x']+pill['width']/2-(m['x']+m['width']/2))<=3
   assert page.locator('.ruler-day-name').count()>2;assert page.locator('.ruler-hour').count()>8
   viewport=page.locator('#meteo-ruler').bounding_box();x=viewport['x']+viewport['width']*.65;y=viewport['y']+viewport['height']*.5
   before=int(page.locator('#meteo-map-hours').input_value());page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-65,y,steps=8);page.mouse.up();assert int(page.locator('#meteo-map-hours').input_value())>before
   after=page.locator('#meteo-map-hours').input_value();page.wait_for_timeout(1000);assert page.locator('#meteo-map-hours').input_value()==after
   pill_after=page.locator('#meteo-map-date').bounding_box();assert abs(pill_after['x']+pill_after['width']/2-(pill['x']+pill['width']/2))<=1
   page.emulate_media(reduced_motion='no-preference');page.locator('#meteo-map-play').click();page.wait_for_timeout(1050);assert page.locator('#meteo-ruler-track').evaluate("e=>getComputedStyle(e).transitionDuration")=='0.85s';page.locator('#meteo-map-pause').click();assert page.locator('#meteo-ruler-track').evaluate("e=>getComputedStyle(e).transitionDuration")=='0s';page.emulate_media(reduced_motion='reduce')
   # Day boundary renders a new date; keyboard and fixed cursor use the same selection.
   page.locator('#meteo-map-hours').focus();page.locator('#meteo-map-hours').press('End');assert int(page.locator('#meteo-map-hours').get_attribute('data-time'))==last
   page.locator('#meteo-map-hours').press('Home')
   bounds();page.locator('[data-map=fullscreen]').click();page.wait_for_timeout(200);bounds();page.locator('[data-map=fullscreen]').click();page.wait_for_timeout(200)
   general=page.locator('#meteo-map-hours').get_attribute('data-time');page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':100});page.wait_for_selector('#meteo-dialog[open]');page.locator('#wind-day').select_option(index=3);assert page.locator('#meteo-map-hours').get_attribute('data-time')==general;page.locator('#meteo-dialog [data-close]').click();page.wait_for_function('meteoTest.state().weatherReturn===null');assert page.locator('.meteo-map-control').is_visible()
   page.locator('#new-button').click();previous=page.evaluate('meteoTest.state()');page.locator('.legend-tracks span').first.click();assert page.evaluate('meteoTest.state()')==previous;page.locator('#meteo-map-hours').focus();page.locator('#meteo-map-hours').press('ArrowRight');assert page.evaluate('meteoTest.state()')==previous
   page.locator('#weather-button').click();page.locator('#cancel-draw').click();assert page.evaluate('meteoTest.state().draft')==previous['draft'];assert page.locator('.meteo-map-control').is_visible()
   hint=page.locator('#map-hint').bounding_box();pill=page.locator('#meteo-map-date').bounding_box();assert hint['y']+hint['height']<page.locator('.map-color-legend').bounding_box()['y']
   page.screenshot(path=str(ROOT/f'tests/timeline-{width}.png'));page.locator('.meteo-map-control').screenshot(path=str(ROOT/f'tests/ruler-{width}.png'));
   if width==393:
    import base64
    box=page.locator('.meteo-map-control').bounding_box();preview=page.screenshot(clip={'x':box['x'],'y':box['y']-16,'width':box['width'],'height':box['height']+18});print('RULER_PREVIEW_393 '+base64.b64encode(preview).decode(),flush=True)
   page.locator('#weather-button').click();page.locator('#map').click(position={'x':140,'y':100});page.wait_for_selector('#meteo-dialog[open]');page.route('**/api.open-meteo.com/**',lambda r:r.fulfill(status=503,body='unavailable'));page.locator('#wind-retry').click();page.wait_for_function("document.querySelector('#wind-status').textContent.includes('no disponible')");page.locator('#meteo-dialog [data-close]').click();assert page.locator('#meteo-map-hours').is_disabled();assert page.locator('#meteo-mini-data').inner_text()=='No disponible'
   assert not errors,errors;context.close()
  browser.close();print('RULER_BROWSER_PASS mobile/desktop compact horizontal legend above ruler/hour, exact arrow/route colors and patterns, passive legend during draft, fullscreen/mobile bounds; fixed central hour, real drag, date/hour ticks, keyboard, narrow/fullscreen: always visible, <=64px, full bottom width/fullscreen, now to 48h, separate play/pause, arrow field redraw, independent Meteo, draft isolation, missing data. Services simulated.')
finally:server.shutdown()
