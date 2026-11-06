"""Real native overflow/keyboard checks; no real account or diary writes."""
import os,base64,traceback
import sea_browser as h
from playwright.sync_api import sync_playwright

def selected(page,index):
 page.wait_for_function("""i=>{const cards=[...document.querySelectorAll('.summary-card')],track=document.querySelector('#summary-track'),a=cards[i].getBoundingClientRect(),b=track.getBoundingClientRect();return document.querySelector('#summary-position').textContent===(i+1)+' de 4'&&Math.abs(a.left+a.width/2-b.left-b.width/2)<2;}""",arg=index)

def wheel(page,direction,index):
 track=page.locator('#summary-track');box=track.bounding_box();step=page.locator('.summary-card').first.bounding_box()['width']+8
 page.mouse.move(box['x']+box['width']/2,box['y']+50);page.mouse.wheel(direction*step,0);selected(page,index)
 page.wait_for_timeout(160)

failures=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width,height in [(393,640),(360,568)]:
   context,page,errors=h.setup(browser,width);page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
   try:
    before=page.evaluate('testRows()');requests=[];page.on('request',lambda r:requests.append(r.url) if 'open-meteo.com/' in r.url else None)
    track=page.locator('#summary-track');selected(page,0)
    assert page.locator('.summary-card').count()==4 and page.locator('[data-carousel-copy]').count()==8
    assert page.locator('[data-carousel-copy]').evaluate_all("nodes=>nodes.every(n=>n.inert&&n.getAttribute('aria-hidden')==='true'&&[...n.querySelectorAll('button')].every(b=>b.tabIndex===-1))")
    assert page.evaluate("(()=>{const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return ids.length===new Set(ids).size;})()")
    # Wheel goes through both physical boundaries; wait for the ORIGINAL to centre.
    for direction,count in [(1,12),(-1,12)]:
     index=0
     for _ in range(count):index=(index+direction)%4;wheel(page,direction,index)
    track.focus();track.press('Home');selected(page,0);track.press('ArrowLeft');selected(page,3);track.press('ArrowRight');selected(page,0)
    track.press('End');selected(page,3);track.press('ArrowRight');selected(page,0)
    for _ in range(18):track.press('ArrowRight')
    selected(page,2)
    # Copies mirror later display/state updates, including dynamic action IDs.
    page.locator('#summary-next-title').evaluate("e=>e.textContent='Título actualizado de prueba'")
    page.wait_for_function("[...document.querySelectorAll('[data-summary-origin=summary-next-title]')].every(e=>e.textContent==='Título actualizado de prueba')")
    page.locator('#summary-next-edit').evaluate('e=>e.disabled=true')
    page.wait_for_function("[...document.querySelectorAll('[data-summary-origin=summary-next-edit]')].every(e=>e.disabled)")
    page.locator('#summary-next-edit').evaluate('e=>e.disabled=false')
    assert not requests,requests
    assert page.evaluate('testRows()')==before
    # Repeated first/last crossings still resolve to one original action.
    track.press('Home');wheel(page,-1,3);wheel(page,1,0);page.locator('#summary-coast').click();assert page.locator('#pending-coast').is_checked();page.locator('#summary-coast').click();assert not page.locator('#pending-coast').is_checked()
    track.focus();track.press('End');track.press('ArrowLeft');selected(page,2);page.locator('#summary-next-view').click();assert page.locator('#adventure-sheet [data-action=edit]').get_attribute('data-id')=='plan-one'
    track.focus();selected(page,2)
    page.locator('[data-tab=diario]').click();page.locator('[data-tab=mapa]').click();selected(page,2)
    # Wide layout contains only the four originals; narrowing restores selection.
    page.set_viewport_size({'width':1280,'height':900});page.wait_for_timeout(160)
    assert page.locator('[data-carousel-copy]').evaluate_all("nodes=>nodes.every(n=>getComputedStyle(n).display==='none')")
    assert track.evaluate('e=>e.scrollWidth<=e.clientWidth+2')
    page.set_viewport_size({'width':width,'height':height});selected(page,2)
    page.locator('#clear-selection').click();track.focus();track.press('Home');selected(page,0);page.evaluate('document.activeElement?.blur();window.scrollTo(0,0)');page.wait_for_timeout(100)
    assert page.evaluate('testRows()')==before
    assert page.locator('#energy').evaluate("e=>Number(e.closest('.energy-track').getAttribute('aria-valuenow'))")>0
    assert not errors,errors
    print('CIRCULAR_PREVIEW_'+str(width),base64.b64encode(page.screenshot()).decode(),flush=True)
    print('CIRCULAR_CASE_PASS',width,height,flush=True)
   except Exception as error:
    failures.append((width,str(error)));traceback.print_exc();print('CIRCULAR_CASE_FAIL',width,repr(error),flush=True);print('CIRCULAR_STATE',page.locator('#summary-track').evaluate("e=>({scroll:e.scrollLeft,width:e.clientWidth,total:e.scrollWidth,status:document.querySelector('#summary-position').textContent,cards:[...e.children].map(n=>({kind:n.className,index:n.dataset.carouselIndex,left:n.offsetLeft,width:n.offsetWidth}))})"),flush=True);page.screenshot(path=str(h.ROOT/f'tests/circular-fail-{width}.png'))
   finally:context.close()
  browser.close()
 assert not failures,failures
 print('CIRCULAR_BROWSER_PASS: native wheel crosses both boundaries for multiple cycles; keyboard and rapid repeats wrap; neighbours shown on both sides; current copies, unique IDs, inert duplicates; correct original actions, no requests/writes; selection restored across modal/tab/desktop layout. Real Chromium, simulated account/services; physical touch remains unverified.',flush=True)
finally:h.server.shutdown()
