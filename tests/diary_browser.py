"""Real Chromium UI; isolated fixture account, private-photo service and weather providers."""
import os,json,time,base64,traceback
from datetime import datetime,timedelta,timezone
import sea_browser as h
from playwright.sync_api import sync_playwright

today=datetime.now(timezone.utc).date()
trips=[]
for i in range(36):
 date=str(today-timedelta(days=max(0,i-1))) if i<35 else '2025-06-01'
 trips.append({'id':f'diary-{i:02}','kind':'trip','title':'Mismo nombre' if i<2 else f'Aventura {i:02}','revision':1,'data':{'date':date,'points':h.points,'source':'gpx' if i==1 else 'coastal','roundtrip':i%2==1,'duration':'' if i%3==0 else 45+i,'estimatedMinutes':999,'departure':'Ciutadella' if i<2 else f'Acceso {i}','arrival':'Cala Galdana','zone':'Sur' if i%2==0 else 'Norte','favorite':i%6==0,'rating':4 if i%2==0 else '', 'notes':'Última palada, notas íntegras '+str(i),'customField':'Conservar siempre','markers':[],'photos':[{'id':'one','path':'test/first','name':'Primera foto'},{'id':'two','path':'test/broken','name':'Segunda foto'}] if i==0 else [{'id':'p','path':'test/third','name':'Tercera foto'}] if i==1 else []}})
seed=trips+[h.seed[0],h.seed[-1]]
h.backend=h.backend.replace(json.dumps(h.seed),json.dumps(seed)).replace("export async function signedPhoto(){return './guide-photo.svg';}","window.diaryPhotoCalls=[];window.diaryPhotoFail=true;export async function signedPhoto(path){window.diaryPhotoCalls.push(path);if(window.diaryPhotoDelay)await new Promise(r=>setTimeout(r,700));if(path==='test/broken'&&window.diaryPhotoFail)throw Error('Foto privada no disponible');return './guide-photo.svg?path='+encodeURIComponent(path);}")

def open_diary(page):
 page.locator('[data-tab=diario]').click();page.wait_for_selector('#trip-list .diary-card')
def all_filter(page):page.locator('#view-diario [data-diary-chip=all]').first.click()
def menu(page,id):page.locator(f'[data-diary-more={id}]').click();page.wait_for_selector('#content-dialog.diary-action-sheet[open]')
def shot(page,name):
 page.screenshot(path=str(h.ROOT/f'tests/diary-{name}.png'))
 print('DIARY_PREVIEW_'+name,base64.b64encode(page.screenshot()).decode(),flush=True)
def intact(page):
 assert not page.evaluate("testRows().some(e=>e.kind==='trip'&&e.data.customField!=='Conservar siempre')")

def filters_and_layout(page,errors,width):
 original=page.evaluate('testRows()');open_diary(page)
 assert page.locator('#trip-list .diary-card').count()==12
 assert '36 aventuras' in page.locator('#diary-results').inner_text()
 assert '12 sin duración' in page.locator('#diary-summary').inner_text()
 assert '999' not in page.locator('#diary-summary').inner_text()
 page.locator('#trip-search').fill('ciutadella');assert page.locator('#trip-list .diary-card').count()==2
 page.locator('#trip-search').fill('ultima');assert '36 aventuras' in page.locator('#diary-results').inner_text()
 page.locator('[data-diary-chip=favorite]').click();assert page.locator('#trip-list .diary-card').count()==6
 page.locator('[data-diary-chip=photos]').click();assert page.locator('#trip-list .diary-card').count()==1
 assert page.locator('[data-diary-clear=query]').is_visible();page.locator('[data-diary-clear=query]').click()
 all_filter(page);page.locator('[data-diary-chip=zone]').click();assert page.locator('.advanced-filters').evaluate('el=>el.open')
 page.locator('#filter-zone').fill('Norte');assert '18 aventuras' in page.locator('#diary-results').inner_text()
 page.locator('#filter-rating').select_option('4');assert page.locator('#trip-list .diary-card').count()==0
 page.locator('#reset-filters').click();assert '36 aventuras' in page.locator('#diary-results').inner_text();page.locator('.advanced-filters summary').click()
 page.locator('.advanced-filters summary').click();page.locator('#year-filter').select_option('2025');page.locator('.advanced-filters summary').click();assert page.locator('#trip-list .diary-card').count()==1;assert 'junio de 2025' in page.locator('.diary-month-heading').inner_text().lower()
 all_filter(page);page.locator('#diary-period').select_option('2025-06');assert page.locator('#trip-list .diary-card').count()==1
 all_filter(page);page.locator('[data-diary-chip=month]').click();current=str(today)[:7];expected=sum(t['data']['date'].startswith(current) for t in trips);assert str(expected)+' aventuras' in page.locator('#diary-results').inner_text()
 all_filter(page);page.locator('[data-diary-view=list]').click();assert page.locator('#trip-list').get_attribute('data-view')=='list';assert page.locator('.diary-gallery').first.is_hidden()
 page.locator('[data-diary-view=cards]').click();assert page.locator('.diary-gallery').first.is_visible()
 assert page.evaluate('testRows()')==original
 page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(100);shot(page,str(width));assert page.locator('#trip-list .diary-card').first.bounding_box()['y']<(700 if width<=700 else 820)
 page.locator('[data-diary-id=diary-00]').scroll_into_view_if_needed();shot(page,'card-'+str(width))
 # Enlarged text and short mobile viewport: content scrolls, actions retain their own space.
 if width==393:
  page.add_style_tag(content='#view-diario{font-size:20px} #view-diario button{font-size:16px} #view-diario h3{font-size:26px!important}')
  page.set_viewport_size({'width':393,'height':600});page.locator('[data-diary-id=diary-00] [data-action=view-adventure]').scroll_into_view_if_needed()
  assert page.locator('[data-diary-id=diary-00] [data-action=view-adventure]').is_visible()
 h.check(page,errors,width)

def photos_and_return(page,errors,width):
 open_diary(page);first=page.locator('[data-diary-id=diary-00]');first.scroll_into_view_if_needed();page.wait_for_function("document.querySelector('[data-diary-id=diary-00] img').getAttribute('src')")
 assert len(page.evaluate('diaryPhotoCalls'))<=3
 gallery=first.locator('.diary-gallery');gallery.focus();gallery.press('ArrowRight')
 page.wait_for_function("document.querySelector('[data-diary-id=diary-00] .diary-photo-count').textContent==='2 / 2'")
 retry=first.locator('.diary-photo-retry').nth(1);page.wait_for_function("!document.querySelectorAll('[data-diary-id=diary-00] .diary-photo-retry')[1].hidden")
 assert first.locator('.diary-photo-status').nth(1).inner_text()=='No se pudo cargar la fotografía privada.'
 page.evaluate('window.diaryPhotoFail=false');retry.click();page.wait_for_function("!document.querySelectorAll('[data-diary-id=diary-00] .diary-slide img')[1].hidden")
 first.locator('.diary-open-photo').nth(1).click();assert page.locator('#content-title').inner_text()=='Segunda foto';h.close(page)
 # Account reset while a private signed URL is in flight must not populate the next diary.
 page.locator('[data-tab=mapa]').click();page.locator('[data-tab=diario]').click();assert first.locator('.diary-photo-count').inner_text()=='2 / 2'
 page.locator('#trip-search').fill('ultima');page.locator('[data-diary-view=list]').click()
 page.locator('#diary-load-more').click();assert page.locator('#trip-list .diary-card').count()>=24
 target=page.locator('[data-diary-id=diary-18] [data-action=view-adventure]');target.scroll_into_view_if_needed();before=page.locator('[data-diary-id=diary-18]').bounding_box()['y']
 target.click();assert page.locator('#adventure-sheet').get_attribute('data-unused') is None
 assert page.locator('#adventure-panel').get_attribute('data-route-id')=='diary-18'
 page.locator('[data-tab=diario]').click();page.wait_for_timeout(150)
 assert page.locator('#trip-search').input_value()=='ultima';assert page.locator('#trip-list').get_attribute('data-view')=='list'
 assert page.locator('#trip-list .diary-card').count()>=24
 assert abs(page.locator('[data-diary-id=diary-18]').bounding_box()['y']-before)<3
 ids=page.locator('#trip-list .diary-card').evaluate_all('els=>els.map(e=>e.dataset.diaryId)');assert len(ids)==len(set(ids))
 page.locator('#diary-load-more').click() if page.locator('#diary-load-more').is_visible() else None
 assert page.locator('#trip-list .diary-card').count()==36
 assert page.locator('#diary-feed-end').is_visible()
 # Reset account-local state, clear private DOM, retain no signed URLs in browser storage.
 page.evaluate("window.diaryPhotoDelay=true;testSwitch('other')");page.wait_for_function("seaTest.state().entries.length===0&&seaTest.state().account==='other'");page.wait_for_timeout(800)
 assert page.locator('#trip-list .diary-card').count()==0;assert page.locator('#trip-list img').count()==0
 assert page.locator('#trip-search').input_value()=='';assert page.locator('[data-diary-view=cards]').get_attribute('aria-pressed')=='true'
 assert not page.evaluate("Object.values({...localStorage}).some(v=>v.includes('guide-photo.svg?path='))")
 h.check(page,errors,width)

def actions_and_practice(page,errors,width):
 open_diary(page);first=page.locator('[data-diary-id=diary-00]');original=page.evaluate('testRows()')
 first.locator('[data-diary-favorite]').click();page.wait_for_function("testRows().find(e=>e.id==='diary-00').data.favorite===false")
 saved=page.evaluate("testRows().find(e=>e.id==='diary-00')");expected=original[0];expected['data']['favorite']=False;expected['revision']=2;assert saved==expected
 menu(page,'diary-00')
 with page.expect_download() as download:page.locator('#content-body [data-action=export]').click()
 assert download.value.suggested_filename=='paleando-diary-00.gpx';h.close(page)
 menu(page,'diary-00');page.locator('#content-body [data-action=edit]').click();page.locator('[name=notes]').fill('Borrador a proteger');page.locator('#close-editor').click()
 menu(page,'diary-00');page.locator('#content-body [data-action=edit]').click();assert page.locator('[name=notes]').input_value()=='Borrador a proteger';page.locator('#close-editor').click()
 first.locator('[data-diary-favorite]').click();assert page.locator('#editor-dialog').is_visible();assert page.locator('[name=notes]').input_value()=='Borrador a proteger';assert page.evaluate("testRows().find(e=>e.id==='diary-00').data.favorite") is False
 page.locator('#discard-draft').click();menu(page,'diary-00');page.locator('#content-body [data-action=repeat]').click();assert page.locator('[name=duration]').input_value()=='';assert page.evaluate('seaTest.state().draft.id')!='diary-00';assert page.evaluate("seaTest.state().draft.data.customField")=='Conservar siempre';page.locator('#discard-draft').click()
 menu(page,'diary-01');page.locator('#content-body [data-action=delete]').click();page.wait_for_function("!!testRows().find(e=>e.id==='diary-01').deleted_at");assert page.locator('[data-diary-id=diary-01]').count()==0
 page.locator('#undo').click();page.wait_for_function("!testRows().find(e=>e.id==='diary-01').deleted_at");assert page.locator('[data-diary-id=diary-01]').count()==1
 all_filter(page);page.locator('[data-diary-chip=photos]').click();page.locator('[data-diary-view=list]').click();before=page.evaluate('testRows()')
 page.evaluate('seaTest.startPractice()');assert page.evaluate('seaTest.state().practice');assert page.locator('[data-diary-chip=photos]').get_attribute('aria-pressed')=='false'
 page.evaluate('seaTest.endPractice()');assert page.locator('[data-diary-chip=photos]').get_attribute('aria-pressed')=='true';assert page.locator('[data-diary-view=list]').get_attribute('aria-pressed')=='true';assert page.locator('#trip-list .diary-card').count()==2
 assert page.evaluate('testRows()')==before
 intact(page);h.check(page,errors,width)

failures=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width in [393,1280]:
   for case in [filters_and_layout,photos_and_return,actions_and_practice]:
    context,page,errors=h.setup(browser,width,len(seed))
    try:case(page,errors,width);print('DIARY_CASE_PASS',width,case.__name__,flush=True)
    except Exception as error:
     failures.append((width,case.__name__,repr(error)));traceback.print_exc();print('DIARY_CASE_FAIL',width,case.__name__,repr(error),flush=True);print('DIARY_FAILURE_BODY',page.locator('body').inner_text()[-6000:],flush=True);page.screenshot(path=str(h.ROOT/f'tests/diary-fail-{width}-{case.__name__}.png'))
    finally:context.close()
  browser.close()
 assert not failures,failures
 print('DIARY_BROWSER_PASS: filters/date selection/two views, missing real duration, lazy private galleries/error retry, exact scroll and photo restoration, unique progressive feed, favorite/revision/metadata, GPX/edit/repeat/delete/undo, draft and practice/account isolation. Real Chrome mobile/desktop; account/photos/weather simulated, not physical Android.',flush=True)
finally:h.server.shutdown()
