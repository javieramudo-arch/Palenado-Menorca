"""Actual Chromium; simulated account/providers, never production diary data."""
import os,base64,traceback
import sea_browser as h
from playwright.sync_api import sync_playwright

def settle(page):
 page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(180)

def fold(page,height):
 settle(page)
 nav=page.locator('.tabs').bounding_box()
 for selector in ['#plan-button','#new-button','#weather-button']:
  r=page.locator(selector).bounding_box()
  assert r and r['y']>=0 and r['y']+r['height']<=nav['y']-2,(selector,r,nav,height)
  assert r['height']>=44
  assert page.locator(selector).evaluate("e=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}"),(selector,page.locator(selector).evaluate("e=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.outerHTML.slice(0,240);}"))
 return page.locator('#map').bounding_box()

def legend_bounds(page):
 m=page.locator('#map').bounding_box();key=page.locator('.map-color-legend').bounding_box();buttons=page.locator('.map-actions').bounding_box();bar=page.locator('.meteo-map-control').bounding_box()
 assert key['x']>=m['x'] and key['x']<=m['x']+12
 assert key['y']>=m['y'] and key['y']<=m['y']+12
 assert key['x']+key['width']<=buttons['x']-2,(key,buttons)
 assert buttons['y']>=m['y']+18
 assert buttons['y']+buttons['height']<=bar['y']-3,(buttons,bar,m)
 assert key['y']+key['height']<=bar['y']-8,(key,bar)
 assert page.locator('.map-title').count()==0
 assert page.locator('.map-color-legend input,.map-color-legend button').count()==0
 assert page.locator('.legend-tracks span').count()==4
 assert page.locator('.legend-weather svg').evaluate_all('els=>els.map(e=>e.style.color)')==['rgb(124, 255, 0)','rgb(255, 121, 0)','rgb(255, 99, 71)','rgb(8, 126, 213)']
 assert page.locator('.leaflet-control-attribution').is_visible()

def carousel(page):
 track=page.locator('#summary-track');track.focus();track.press('Home')
 assert page.locator('#summary-prev,#summary-next,.summary-pagination').count()==0
 for index in [1,2]:
  track.press('ArrowRight');page.wait_for_timeout(100)
  bounds=page.locator('.summary-card').evaluate_all('els=>els.map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width};})');box=track.bounding_box();r=bounds[index]
  assert abs((r['left']+r['right'])/2-(box['x']+box['width']/2))<=2,(r,box)
  assert bounds[index-1]['right']>=box['x']+8
  assert bounds[index+1]['left']<=box['x']+box['width']-8
 track.press('End');page.wait_for_timeout(60);last=track.evaluate('e=>e.scrollLeft');track.press('ArrowRight');assert track.evaluate('e=>e.scrollLeft')==last
 track.press('Home');page.evaluate('document.activeElement?.blur()')

failures=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width,height in [(393,720),(393,640),(393,600),(360,568),(1280,900)]:
   context,page,errors=h.setup(browser,width);page.set_viewport_size({'width':width,'height':height});page.evaluate('document.fonts.ready');page.wait_for_timeout(180)
   try:
    original=page.evaluate('testRows()');requests=[];page.on('request',lambda r:requests.append(r.url) if 'open-meteo.com/' in r.url else None)
    if width<700:fold(page,height);carousel(page);fold(page,height)
    legend_bounds(page)
    # Saved data/draft remain intact while the continuation strip sits below the actions.
    page.evaluate("seaTest.view('plan-one')");page.locator('#adventure-sheet [data-action=edit]').click();page.locator('#entry-form [name=notes]').fill('Borrador conservado');page.locator('#close-editor').click();page.locator('#clear-selection').click()
    if width<700:
     fold(page,height);resume=page.locator('#resume-draft').bounding_box();actions=page.locator('.map-bottom').bounding_box();assert resume['y']>=actions['y']+actions['height']
    legend_bounds(page)
    if (width,height) in [(393,640),(360,568),(1280,900)]:
     settle(page);page.wait_for_timeout(350);page.evaluate('document.activeElement?.blur()');print('COMPACT_PREVIEW_'+str(width)+'_'+str(height),base64.b64encode(page.screenshot()).decode(),flush=True)
    # Legend is passive even during real route editing.
    page.locator('#resume-draft').click();page.locator('#edit-track').click();before=page.evaluate('seaTest.state().draft');page.locator('.map-color-legend').click();assert page.evaluate('seaTest.state().draft')==before
    legend_bounds(page);page.locator('#finish-draw').click();page.locator('#close-editor').click()
    if width<700:fold(page,height)
    assert not requests,requests
    assert page.evaluate('testRows()')==original
    # Real fit pixels must be below the upper legend and above the time control.
    page.evaluate("seaTest.view('plan-one')");page.wait_for_timeout(180)
    assert page.evaluate("""()=>{const m=seaTest.map(),box=m.getContainer().getBoundingClientRect(),key=document.querySelector('.map-color-legend').getBoundingClientRect(),bar=document.querySelector('.meteo-map-control').getBoundingClientRect(),actions=document.querySelector('.map-actions').getBoundingClientRect();return seaTest.state().entries.find(e=>e.id==='plan-one').data.points.every(p=>{const q=m.latLngToContainerPoint(p);return q.y>=key.bottom-box.top+7&&q.y<=bar.top-box.top-7&&q.x<=actions.left-box.left-7&&q.x>=15;});}""")
    page.locator('#clear-selection').click()
    if width<700:fold(page,height)
    page.locator('#sea-sun').click();page.wait_for_timeout(160);legend_bounds(page)
    # The existing six-second status toast is transient; verify the steady initial layout.
    page.wait_for_function("document.querySelector('#toast').hidden")
    if width<700 and height>=600:fold(page,height)
    page.locator('[data-map=fullscreen]').click();page.wait_for_timeout(160);legend_bounds(page);page.locator('[data-map=fullscreen]').click();page.wait_for_timeout(160);legend_bounds(page)
    assert page.evaluate('document.documentElement.scrollWidth')<=width
    assert page.evaluate('testRows().filter(e=>e.kind!=="preferences")')==[e for e in original if e['kind']!='preferences']
    assert page.evaluate('seaTest.state().draft.data.notes')=='Borrador conservado'
    assert not errors,errors
    print('COMPACT_CASE_PASS',width,height,flush=True)
   except Exception as error:
    failures.append((width,height,str(error)));traceback.print_exc();print('COMPACT_CASE_FAIL',width,height,repr(error),flush=True);print('COMPACT_GEOMETRY',page.evaluate("Object.fromEntries(['.topbar','.sync-line','#summary-track','#map','.map-actions','.map-color-legend','.meteo-map-control','.map-bottom','.tabs'].map(s=>[s,document.querySelector(s)?.getBoundingClientRect().toJSON()]))"),flush=True);page.screenshot(path=str(h.ROOT/f'tests/compact-fail-{width}-{height}.png'))
   finally:context.close()
  browser.close()
 assert not failures,failures
 print('COMPACT_BROWSER_PASS: centred adjacent cards, no dots/arrows, finite scrolling unchanged; first-screen actions including draft; light upper-left legend with preserved colour keys; separate right controls/timeline in small and sun/fullscreen layouts; actual route fit pixels; unchanged data and saved draft. Real Chromium, account/providers simulated; physical Android/browser chrome not claimed.',flush=True)
finally:h.server.shutdown()
