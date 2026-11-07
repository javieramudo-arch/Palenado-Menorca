import sys,os
from pathlib import Path
sys.path.insert(0,'tests')
import sea_browser as h
from playwright.sync_api import sync_playwright
out=Path('review');out.mkdir(exist_ok=True)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width in [393,1280]:
   context,page,errors=h.setup(browser,width)
   page.locator('[data-tab=diario]').click()
   page.locator('[data-diary-more=trip-one]').click();page.locator('#content-body [data-action=edit]').click()
   page.locator('[name=notes]').fill('BORRADOR SIN GUARDAR');page.locator('#close-editor').click()
   page.locator('[data-diary-favorite=trip-one]').click()
   page.wait_for_function("testRows().find(e=>e.id==='trip-one').data.favorite===true")
   assert not page.locator('#editor-dialog').is_visible()
   assert page.evaluate('seaTest.state().draft.data.notes')=='BORRADOR SIN GUARDAR'
   assert page.evaluate("testRows().find(e=>e.id==='trip-one').data.notes")!='BORRADOR SIN GUARDAR'
   page.locator('[data-diary-more=trip-one]').click();page.locator('#content-body [data-action=delete]').click()
   page.wait_for_function("!!testRows().find(e=>e.id==='trip-one').deleted_at")
   assert page.locator('[data-diary-id=trip-one]').count()==0
   assert page.evaluate('seaTest.state().draft') is None
   page.locator('#undo').click()
   page.wait_for_function("!testRows().find(e=>e.id==='trip-one').deleted_at")
   assert page.evaluate('seaTest.state().draft.data.notes')=='BORRADOR SIN GUARDAR'
   page.locator('[data-diary-more=trip-one]').click();page.locator('#content-body [data-action=edit]').click()
   assert page.locator('[name=notes]').input_value()=='BORRADOR SIN GUARDAR'
   assert page.locator('[name=favorite]').is_checked()
   page.locator('#discard-draft').click();page.locator('[data-tab=mapa]').click()
   page.screenshot(path=str(out/f'weather-flow-{width}.png'),full_page=True)
   assert 'Estelas' in page.locator('.legend-weather').get_attribute('aria-label')
   page.emulate_media(reduced_motion='no-preference')
   page.evaluate("const e=document.querySelector('#wind-motion');e.checked=true;e.dispatchEvent(new Event('change'))")
   page.wait_for_timeout(200)
   def canvas():return page.locator('.wind-canvas').evaluate('(c)=>c.toDataURL()')
   before=canvas();page.wait_for_timeout(300);assert canvas()!=before,'Wind should move'
   page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(200)
   before=canvas();page.wait_for_timeout(300);assert canvas()==before,'Reduced motion should freeze'
   assert not errors,errors
   print('PASS controls and saved-draft restoration, flowing particles and reduced motion',width,flush=True)
   context.close()
  browser.close()
finally:h.server.shutdown()
