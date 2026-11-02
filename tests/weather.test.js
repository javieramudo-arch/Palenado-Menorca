import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {parseHTML} from 'linkedom';
const app=readFileSync(new URL('../app.js',import.meta.url),'utf8');
const source=app.slice(app.indexOf('async function weather(){'),app.indexOf('async function showPhoto'));
function harness(fetch){
 const {document}=parseHTML('<html><body><div id="map-wrap" class="fullscreen-map"></div><button data-map="fullscreen"></button><div id="content-dialog"></div><div id="content-body"></div></body></html>');let timeout,cleared=false;
 const ctx=vm.createContext({document,$:s=>document.querySelector(s),practice:null,draft:null,map:{getCenter:()=>({lat:39.98,lng:4.08}),invalidateSize(){}},weatherRequest:0,AbortController,fetch,navigator:{onLine:true},setTimeout:f=>{timeout=f;return 1},clearTimeout:()=>cleared=true,readFormIfOpen(){},closeDialogs(){},content(title,html){ctx.weatherRequest++;document.querySelector('#content-body').innerHTML=html;},esc:x=>String(x),guideAdvance(){},toast(){}});
 vm.runInContext(source,ctx);return {ctx,document,run:()=>ctx.weather(),expire:()=>timeout(),get cleared(){return cleared}};
}
const daily={time:['2026-11-02'],temperature_2m_min:[15],temperature_2m_max:[20],wind_speed_10m_max:[12],wind_gusts_10m_max:[24]};
test('Tiempo opens above expanded map and renders without AbortSignal.timeout',async()=>{
 let url,signal;const h=harness(async(u,o)=>{url=u;signal=o.signal;return {ok:true,json:async()=>({daily})}});await h.run();assert.match(url,/latitude=39.98&longitude=4.08/);assert(signal instanceof AbortSignal);assert.equal(h.document.querySelector('#map-wrap').classList.contains('fullscreen-map'),false);assert.match(h.document.querySelector('#weather-result').textContent,/12 km\/h/);assert(h.cleared);
});
test('failed forecast has a working retry',async()=>{
 let count=0;const h=harness(async()=>{if(!count++)throw Error('network');return {ok:true,json:async()=>({daily})}});await h.run();const retry=h.document.querySelector('#weather-result button');assert.equal(retry.textContent,'Reintentar previsión');await retry.onclick();assert.equal(count,2);assert.match(h.document.querySelector('#weather-result').textContent,/24/);
});
test('timeout aborts and leaves retry visible',async()=>{
 const h=harness((u,{signal})=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(Error('aborted')))));const pending=h.run();h.expire();await pending;assert.match(h.document.querySelector('#weather-result').textContent,/tardando demasiado/);assert(h.document.querySelector('#weather-result button'));assert(h.cleared);
});
test('an obsolete response cannot replace the latest forecast',async()=>{
 let finish;const h=harness(()=>new Promise(resolve=>finish=resolve));const pending=h.run();h.ctx.weatherRequest++;h.document.querySelector('#content-body').innerHTML='<div id="weather-result">Otra consulta</div>';finish({ok:true,json:async()=>({daily})});await pending;assert.equal(h.document.querySelector('#weather-result').textContent,'Otra consulta');
});
