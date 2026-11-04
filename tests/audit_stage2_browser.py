import os
"""Unified adventure and password flows. Real Chromium, simulated account and emails."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=http.server.ThreadingHTTPServer(('127.0.0.1',8082),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
BACKEND='''let listener;const user={id:'test-user',email:'test@example.invalid'};window.resetRequests=[];window.passwordUpdates=[];window.failReset=false;window.failUpdate=false;window.emitRecovery=()=>listener('PASSWORD_RECOVERY',{user});window.emitLogout=()=>listener('SIGNED_OUT',null);
const client={auth:{getSession:async()=>({data:{session:{user}}}),onAuthStateChange:f=>{listener=f;},resetPasswordForEmail:async(...a)=>{window.resetRequests.push(a);return {error:window.failReset?Error('Sin conexión'):null};},updateUser:async data=>{window.passwordUpdates.push(data);return {error:window.failUpdate?Error('Reintenta'):null};}}};
export async function getClient(){return client;}
export async function loadEntries(){return ['one','two'].map(id=>({id,revision:1,kind:'trip',title:'Mismo nombre',data:{date:'2026-11-02',points:[[39.93805,3.93665],[39.93168,3.91459]],source:'gpx',notes:'Notas '+id,photos:[],markers:[]}}));}
export async function saveEntry(e){return e;}export async function signedPhoto(){return './guide-photo.svg';}export async function uploadPhoto(){throw Error('unused');}
'''
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel=os.environ.get('PALEANDO_BROWSER_CHANNEL'))
  for width in [393,1280]:
   context=browser.new_context(viewport={'width':width,'height':900},service_workers='block');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.route('**/backend.js*',lambda r:r.fulfill(body=BACKEND,content_type='text/javascript'))
   page.goto('http://127.0.0.1:8082/',wait_until='networkidle');page.wait_for_selector('#map.leaflet-container')
   page.locator('[data-tab=diario]').click();assert page.locator('#trip-list [data-action=detail]').count()==0
   page.locator('#trip-list [data-action=view-adventure][data-id=two]').click();assert 'Notas two' in page.locator('#adventure-sheet').inner_text();assert 'Notas one' not in page.locator('#adventure-sheet').inner_text()
   page.evaluate("document.querySelector('#auth-dialog').showModal()");page.locator('#forgot-password').click();page.locator('#request-password-form [name=email]').fill('test@example.invalid');page.evaluate('failReset=true');page.locator('#request-password-form button').click();page.wait_for_function("document.querySelector('#request-password-message').textContent.includes('No se pudo')")
   page.evaluate('failReset=false');page.locator('#request-password-form button').click();page.wait_for_function("document.querySelector('#request-password-message').textContent.includes('Si existe')");assert page.evaluate('resetRequests.at(-1)[1].redirectTo')=='http://127.0.0.1:8082/'
   page.evaluate('emitRecovery()');page.wait_for_selector('#new-password-dialog[open]');page.locator('#new-password-form [name=password]').fill('sample-password-long');page.locator('#new-password-form [name=confirmation]').fill('different-password-long');page.locator('#new-password-form button').click();page.wait_for_function("document.querySelector('#new-password-message').textContent.includes('coinciden')");assert page.evaluate('passwordUpdates.length')==0
   page.locator('#new-password-form [name=confirmation]').fill('sample-password-long');page.evaluate('failUpdate=true');page.locator('#new-password-form button').click();page.wait_for_function("document.querySelector('#new-password-message').textContent.includes('Reintenta')");assert page.locator('#new-password-form [name=password]').input_value()=='sample-password-long'
   page.evaluate('failUpdate=false');page.locator('#new-password-form button').click();page.wait_for_function("!document.querySelector('#new-password-dialog').open");assert page.locator('#new-password-form [name=password]').input_value()==''
   page.goto('http://127.0.0.1:8082/?case=expired#error=access_denied&error_code=otp_expired',wait_until='networkidle');page.wait_for_selector('#retry-password-recovery');assert not page.locator('#new-password-dialog').is_visible();page.locator('#retry-password-recovery').click();assert page.locator('#request-password-dialog').is_visible()
   page.goto('http://127.0.0.1:8082/?case=recovery#type=recovery&access_token=simulated-token',wait_until='networkidle');page.wait_for_selector('#new-password-dialog[open]');page.evaluate('emitLogout()');assert not page.locator('#new-password-dialog').is_visible()
   assert not errors,errors;context.close()
  browser.close();print('AUDIT_STAGE2_PASS: unified ID-based adventure, mobile/desktop; recovery request/error/retry, same-user recovery, password mismatch/update failure/retry, expired link. Auth/email simulated.',flush=True)
finally:server.shutdown()
