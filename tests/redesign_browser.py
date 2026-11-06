"""Real Chromium layout/gesture checks; account, photos and providers are simulated."""
import os,json,base64,traceback,time,math
from pathlib import Path
import sea_browser as h
from playwright.sync_api import sync_playwright

original_seed=json.dumps(h.seed)
seed=json.loads(original_seed)
prefs=next(e for e in seed if e['kind']=='preferences')['data']
prefs['weatherLimits']={'wind':3,'gust':3}
prefs['weatherFavorites']=[{'id':'favorite-'+str(i),'title':'Cala de prueba '+str(i+1),'point':[40.02+i*.005,4.02]} for i in range(7)]
later=json.loads(json.dumps(seed[0]));later['id']='plan-later';later['data']['plannedStart']=h.iso(h.future+7200)
seed.insert(0,later)
h.backend=h.backend.replace(original_seed,json.dumps(seed))

def visible_bounds(page,selector,width,height=None):
 box=page.locator(selector).bounding_box();assert box and box['x']>=-1 and box['x']+box['width']<=width+1,(selector,box)
 if height:assert box['y']>=-1 and box['y']+box['height']<=height+1,(selector,box,height)
 return box

def go_card(page,index):
 page.locator('#summary-track').focus();page.locator('#summary-track').press('Home')
 for _ in range(index):page.locator('#summary-track').press('ArrowRight')
 page.wait_for_timeout(100)

def check_case(page,errors,width):
 rows=page.evaluate('testRows()');requests=[];page.evaluate('document.activeElement?.blur()');print('DESIGN_INITIAL_'+str(width),base64.b64encode(page.screenshot()).decode(),flush=True)
 page.on('request',lambda r:requests.append(r.url) if 'open-meteo.com/' in r.url else None)
 assert page.locator('.summary-card').count()==4
 assert page.locator('#summary-favorites-count').inner_text()=='7 calas favoritas'
 assert page.locator('#summary-next-view').get_attribute('data-id')=='plan-one'
 assert page.locator('#summary-next-edit').get_attribute('data-id')=='plan-one'
 assert page.locator('#summary-next-metrics').inner_text().endswith('2 h 00 min')
 assert not page.locator('#pending-coast').is_checked()
 for selector in ['#refresh','#menu-button','#goal-button','#summary-coast','#summary-next-view','#summary-next-edit','#summary-favorites','#meteo-map-play','#meteo-map-pause','#meteo-ruler']:
  box=page.locator(selector).bounding_box();assert box['width']>=44 and box['height']>=44,(selector,box)
 sizes=page.locator('.summary-card').evaluate_all('cards=>cards.map(c=>c.getBoundingClientRect().height)');assert max(sizes)-min(sizes)<2,sizes
 track=page.locator('#summary-track').bounding_box();first=page.locator('.summary-card').first.bounding_box()
 if width<700:
  assert track['width']-first['width']>=20
  assert page.locator('#summary-prev,#summary-next,.summary-pagination').count()==0
  go_card(page,3);assert page.locator('#summary-position').inner_text()=='4 de 4'
  page.locator('#summary-track').press('ArrowRight');assert page.locator('#summary-position').inner_text()=='4 de 4'
  # Real pointer drag on the dedicated carousel; the Leaflet view remains fixed.
  before=page.evaluate('seaTest.map().getCenter()');go_card(page,0);box=page.locator('#summary-track').bounding_box()
  page.locator('#summary-track').dispatch_event('pointerdown',{'pointerType':'touch','pointerId':41,'clientX':box['x']+250,'clientY':box['y']+70,'bubbles':True})
  # Browser wheel horizontal scroll follows the native overflow path.
  page.mouse.move(box['x']+box['width']/2,box['y']+60);page.mouse.wheel(280,0);page.wait_for_timeout(120)
  assert page.locator('#summary-track').evaluate('e=>e.scrollLeft')>0
  assert page.evaluate('seaTest.map().getCenter()')==before
  nav=visible_bounds(page,'.tabs',width,900);assert nav['y']>800
 else:
  assert page.locator('#summary-track').evaluate('e=>e.scrollWidth<=e.clientWidth+2')
 go_card(page,0) if width<700 else None
 page.locator('#goal-button').click();assert 'costa de referencia' in page.locator('#content-body').inner_text();h.close(page)
 assert not page.locator('#pending-coast').is_checked()
 page.locator('#summary-coast').click();assert page.locator('#pending-coast').is_checked();page.locator('#summary-coast').click();assert not page.locator('#pending-coast').is_checked()
 # ID-based card actions preserve a live draft, including when re-editing the same route.
 page.locator('#summary-next-edit').click();page.locator('#entry-form [name=notes]').fill('Conservar durante el rediseño');page.locator('#close-editor').click()
 draft=page.evaluate('seaTest.state().draft');assert draft['id']=='plan-one'
 page.locator('#summary-next-edit').click();assert page.locator('#entry-form [name=notes]').input_value()=='Conservar durante el rediseño';page.locator('#close-editor').click()
 page.locator('#summary-next-view').click();assert page.locator('#adventure-sheet [data-action=edit]').get_attribute('data-id')=='plan-one'
 image=page.locator('#adventure-image');close_box=page.locator('#clear-selection').bounding_box();assert close_box['width']>=44 and close_box['height']>=44;sheet=page.locator('#adventure-sheet').bounding_box();map_box=page.locator('#map-wrap').bounding_box();assert sheet['y']+sheet['height']<=map_box['y']
 if image.is_visible():assert image.bounding_box()['y']+image.bounding_box()['height']<=sheet['y']
 if width<700:assert page.locator('#summary-position').inner_text()=='3 de 4'
 page.locator('#summary-next-view').click();assert page.evaluate('seaTest.state().draft.data.notes')==draft['data']['notes']
 page.locator('[data-tab=diario]').click();assert page.locator('#summary-carousel').is_hidden();assert page.locator('[data-tab=diario]').get_attribute('aria-current')=='page'
 page.locator('[data-tab=mapa]').click();assert page.locator('#summary-carousel').is_visible()
 if width<700:assert page.locator('#summary-position').inner_text()=='3 de 4'
 assert not requests,requests
 assert page.evaluate('testRows()')==rows
 # Existing Meteo still consumes a dedicated map touch and restores the draft.
 page.locator('#weather-button').click();assert 'Toca el mapa' in page.locator('#map-hint').inner_text();page.locator('#map').click(position={'x':110,'y':120});page.wait_for_selector('#meteo-dialog[open]')
 visible_bounds(page,'#meteo-dialog',width,900);visible_bounds(page,'#meteo-dialog .dialog-heading',width,900)
 if width<700:assert abs(page.locator('#meteo-dialog').bounding_box()['y']+page.locator('#meteo-dialog').bounding_box()['height']-900)<3
 assert page.locator('.meteo-explanation').count()==1
 page.locator('#wind-full').click();page.wait_for_selector('svg[data-weather-chart]');visible_bounds(page,'#content-dialog',width,900);assert page.locator('#windy-map iframe').count()==1
 h.close(page);assert page.evaluate('seaTest.state().draft.data.notes')==draft['data']['notes']
 # Favorite summary reuses the exact consulted time/source without new network calls.
 page.locator('#summary-favorites').click();page.locator('#sea-favorites-form [name=time]').fill(page.evaluate('(t)=>seaTest.format(t)',math.ceil(time.time()/60)*60+60));page.locator('#sea-favorites-form button').click();page.wait_for_function("document.querySelectorAll('#sea-favorites-results .card').length===7")
 visible_bounds(page,'#content-dialog .dialog-heading',width,900);h.close(page)
 assert 'Cala de prueba' in page.locator('#summary-weather').inner_text();assert 'Open-Meteo' in page.locator('#summary-weather').inner_text()
 count=len(requests)
 if width<700:go_card(page,0);go_card(page,3)
 page.wait_for_timeout(200);assert len(requests)==count
 assert page.evaluate('testRows()')==rows
 # Fixed bottom navigation never steals touches from fullscreen map.
 page.locator('[data-map=fullscreen]').click();page.wait_for_timeout(180)
 if width<700:assert page.evaluate("!document.elementFromPoint(innerWidth/2,innerHeight-20)?.closest('.tabs')")
 page.locator('[data-map=fullscreen]').click();page.wait_for_timeout(180)
 # Short viewport/focused form: closing and saving remain reachable, no keyboard claim.
 page.set_viewport_size({'width':width,'height':600});page.locator('#summary-next-edit').click();page.locator('#entry-form [name=notes]').focus();visible_bounds(page,'#editor-dialog',width,600)
 page.locator('#save-entry').scroll_into_view_if_needed();visible_bounds(page,'#save-entry',width,600);visible_bounds(page,'#close-editor',width,600);page.locator('#close-editor').click();page.set_viewport_size({'width':width,'height':900})
 assert page.evaluate('document.documentElement.scrollWidth')<=width+1
 assert page.evaluate('testRows()')==rows
 # Capture actual browser rendering, with only fixture data.
 page.locator('#clear-selection').click();page.evaluate('window.scrollTo(0,0)')
 if width<700:go_card(page,0)
 page.evaluate('document.activeElement?.blur();window.scrollTo(0,0)');page.wait_for_timeout(100)
 print('DESIGN_PREVIEW_'+str(width),base64.b64encode(page.screenshot()).decode(),flush=True)
 if width<700:go_card(page,3);print('DESIGN_CALAS_'+str(width),base64.b64encode(page.locator('.favorites-card').screenshot()).decode(),flush=True)
 assert not errors,errors

failures=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width in [393,1280]:
   context,page,errors=h.setup(browser,width,expected_entries=5)
   try:check_case(page,errors,width);print('DESIGN_CASE_PASS',width,flush=True)
   except Exception as error:
    failures.append((width,str(error)));traceback.print_exc();print('DESIGN_CASE_FAIL',width,repr(error),flush=True);print('DESIGN_FAILURE_BODY',page.locator('body').inner_text()[-6500:],flush=True);page.screenshot(path=str(h.ROOT/f'tests/design-fail-{width}.png'))
   finally:context.close()
  # Empty/loading states retain working actions, no invented next route or weather.
  context,page,errors=h.setup(browser,393,expected_entries=5)
  page.evaluate("testSwitch('other')");page.wait_for_function("seaTest.state().account==='other'&&seaTest.state().entries.length===0")
  assert page.locator('#summary-next-view').inner_text()=='Ver rutas pendientes';assert page.locator('#summary-next-edit').is_hidden();assert '0 calas' in page.locator('#summary-favorites-count').inner_text();assert 'Open-Meteo' not in page.locator('#summary-weather').inner_text()
  page.locator('#summary-next-view').click();assert page.locator('#content-dialog [data-action=plan]').count()>0;h.close(page)
  page.locator('#summary-track').focus();page.locator('#summary-track').press('Home');page.evaluate("document.documentElement.style.fontSize='24px'");page.wait_for_timeout(120)
  assert page.evaluate('document.documentElement.scrollWidth')<=393
  assert page.locator('#summary-coast').is_visible();assert not errors;context.close();browser.close()
 assert not failures,failures
 print('DESIGN_BROWSER_PASS mobile/desktop: finite accessible carousel; correct IDs, totals, estimates and empty states; no automatic queries or layer changes; protected drafts/preferences; fixed navigation; map/legend/fullscreen; sheets/forecast/Windy; consulted favorite summary; short viewport and text enlargement. Real Chromium, simulated account/services; physical Android keyboard/touch not claimed.',flush=True)
finally:h.server.shutdown()
