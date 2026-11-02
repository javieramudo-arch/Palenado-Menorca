"""The four audit fixes only. Real Chromium; account/storage simulated."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=http.server.ThreadingHTTPServer(('127.0.0.1',8081),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
rows=[{'id':'good','revision':1,'kind':'trip','title':'Salida válida','data':{'date':'2026-11-02','points':[[39.93805,3.93665],[39.93168,3.91459]],'source':'gpx','notes':'Original','photos':[{'id':'p1','path':'private/one','name':'Primera'},{'id':'p2','path':'private/two','name':'Segunda'}],'markers':[{'id':'m1','title':'Acceso','category':'access','point':[39.93805,3.93665],'photoId':'p1'}]}},
 {'id':'bad','revision':1,'kind':'trip','title':'Trazado dañado','data':{'date':'2026-11-02','points':[[39.9,4],[None,4]],'source':'manual','notes':'No perder estas notas','photos':[],'markers':[]}}]
BACKEND='''let rows=SEED;window.auditRows=()=>structuredClone(rows);window.auditBump=id=>{const e=rows.find(e=>e.id===id);e.revision++;e.data.notes='Servidor '+e.revision;e.data.conditions='Condiciones del servidor';};
export async function getClient(){return {auth:{getSession:async()=>({data:{session:{user:{id:'test-user',email:'test@example.invalid'}}}}),onAuthStateChange(){}}};}
export async function loadEntries(){return structuredClone(rows);}
export async function saveEntry(e){const i=rows.findIndex(x=>x.id===e.id);if(i>=0&&rows[i].revision!==e.revision){const error=Error('Conflicto');error.code='VERSION_CONFLICT';throw error;}const saved={...structuredClone(e),revision:(e.revision||0)+1};if(i<0)rows.push(saved);else rows[i]=saved;return saved;}
export async function signedPhoto(){return './guide-photo.svg';}export async function uploadPhoto(){throw Error('unused');}
'''.replace('SEED',json.dumps(rows))
HOOK='''\nwindow.auditApp={startPractice,weather,endPractice,state:()=>({mode,practice:!!practice,weatherSelection,weatherReturn,draft:structuredClone(draft)})};'''
try:
 with sync_playwright() as p:
  browser=p.chromium.launch();page=browser.new_page(viewport={'width':393,'height':851});errors=[]
  page.on('pageerror',lambda e:(errors.append(str(e)),print('PAGE_ERROR',str(e),flush=True)));page.on('dialog',lambda d:d.accept())
  page.route('**/backend.js*',lambda r:r.fulfill(body=BACKEND,content_type='text/javascript'))
  page.route('**/app.js*',lambda r:r.fulfill(body=(ROOT/'app.js').read_text()+HOOK,content_type='text/javascript'))
  page.add_init_script("""let leaflet;Object.defineProperty(window,'L',{configurable:true,get:()=>leaflet,set:v=>{leaflet=v;v.Map.addInitHook(function(){window.testMap=this;});}});""")
  page.goto('http://127.0.0.1:8081/',wait_until='networkidle');page.wait_for_selector('#map.leaflet-container')
  def edit(identifier):
   page.locator('[data-tab=diario]').click();page.locator(f'#trip-list [data-action=edit][data-id="{identifier}"]').click()
  def map_click(lat,lng):
   point=page.evaluate('([a,b])=>{const p=testMap.latLngToContainerPoint([a,b]);return {x:p.x,y:p.y}}',[lat,lng]);page.locator('#map').click(position=point)
  assert 'revisar su trazado' in page.locator('#coast-status').inner_text();page.locator('[data-tab=diario]').click();assert page.locator('#trip-list .card').count()==2
  assert 'No disponible' in page.locator('#trip-list .card').filter(has_text='Trazado dañado').inner_text()
  edit('bad');assert page.locator('[name=notes]').input_value()=='No perder estas notas';page.locator('#edit-track').click();map_click(39.93805,3.93665);map_click(39.93168,3.91459);assert page.evaluate('auditApp.state().draft.data.points.length')>2;page.locator('#finish-draw').click();page.locator('#save-entry').click()
  assert page.evaluate("auditRows().find(e=>e.id==='bad').data.notes")=='No perder estas notas';assert page.evaluate("auditRows().find(e=>e.id==='bad').data.points.every(p=>p.every(Number.isFinite))")
  edit('good');page.locator('[data-remove-photo=p1]').click();page.locator('[name=notes]').fill('Cambios posteriores que conservar');page.locator('[name=roundtrip]').check();page.locator('[data-marker-photo=m1]').select_option('p2');page.locator('[data-undo-draft-item]').click()
  assert page.locator('[name=notes]').input_value()=='Cambios posteriores que conservar';assert page.locator('[name=roundtrip]').is_checked();assert page.locator('[data-marker-photo=m1]').input_value()=='p2';assert page.locator('[data-remove-photo=p1]').count()==1;page.locator('#save-entry').click()
  edit('good');page.locator('[name=notes]').fill('Mi edición en conflicto');page.evaluate("auditBump('good')");page.locator('#save-entry').click();page.wait_for_selector('#conflict-form')
  assert page.evaluate("auditApp.state().draft.data.notes")=='Mi edición en conflicto'
  for select in page.locator('#conflict-form select').all():select.select_option('local')
  page.locator('#conflict-form fieldset').filter(has_text='conditions').locator('select').select_option('server')
  page.locator('#conflict-form button').click();page.locator('#save-entry').click();assert page.evaluate("auditRows().find(e=>e.id==='good').data.notes")=='Mi edición en conflicto';assert page.evaluate("auditRows().find(e=>e.id==='good').data.conditions")=='Condiciones del servidor'
  edit('good');page.locator('[name=notes]').fill('Guardar como copia');page.evaluate("auditBump('good')");server_notes=page.evaluate("auditRows().find(e=>e.id==='good').data.notes");page.locator('#save-entry').click();page.locator('#conflict-copy').click();page.locator('#save-entry').click();assert page.evaluate("auditRows().find(e=>e.id==='good').data.notes")==server_notes;assert page.evaluate("auditRows().filter(e=>e.data.notes==='Guardar como copia').length")==1
  edit('good');page.locator('[name=notes]').fill('No conservar esto');page.evaluate("auditBump('good')");page.locator('#save-entry').click();page.locator('#conflict-server').click();assert page.locator('[name=notes]').input_value()==page.evaluate("auditRows().find(e=>e.id==='good').data.notes");page.locator('#discard-draft').click()
  # Enter the actual practice, then exercise only its weather-exit state.
  page.locator('[data-tab=mapa]').click();page.evaluate('auditApp.startPractice();auditApp.weather()');assert page.evaluate('auditApp.state().practice');page.locator('#exit-practice').click();state=page.evaluate('auditApp.state()');assert state['weatherSelection'] is None and state['weatherReturn'] is None and not state['practice']
  page.locator('#weather-button').click();assert 'Toca el mapa' in page.locator('#map-hint').inner_text();page.locator('#cancel-draw').click();assert page.evaluate('auditApp.state().weatherSelection') is None
  assert not errors,errors;print('AUDIT_STAGE1_BROWSER_PASS: damaged record isolated/repaired without loss; granular local recovery; merge/copy/server conflicts; practice weather exit and next query; backend simulated',flush=True);browser.close()
finally:server.shutdown()
