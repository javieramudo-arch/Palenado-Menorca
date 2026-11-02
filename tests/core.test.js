import test from 'node:test';
import assert from 'node:assert/strict';
import {distance,tripKm,aggregate,exportGPX,escapeHtml,validPoint} from '../core.js';
const points=[[39.95,4.0],[39.96,4.01],[39.97,4.02]];
test('distancia geodésica y recorrido repetido',()=>{assert.equal(distance([]),0);assert.equal(distance([[0,0],[0,0]]),0);assert.ok(Math.abs(distance([[0,0],[0,1]])-111.195)<.01);assert.equal(tripKm({points,roundtrip:true}),distance(points)*2);});
test('un GPX de ida y vuelta no se duplica',()=>{const complete=[...points,...points.slice(0,-1).reverse()];assert.equal(tripKm({points:complete,roundtrip:true,source:'gpx'}),distance(complete));});
test('pendientes y eliminadas no suman; restaurar recalcula',()=>{const entries=[{kind:'trip',data:{points,date:'2026-05-01',duration:90}},{kind:'plan',data:{points,date:'2026-05-02'}},{kind:'trip',deleted_at:'2026-11-02',data:{points,date:'2026-05-02'}}];assert.equal(aggregate(entries).count,1);assert.equal(aggregate(entries).minutes,90);assert.equal(aggregate(entries).km,distance(points));entries[2].deleted_at=null;assert.equal(aggregate(entries).count,2);assert.equal(aggregate(entries,2025).km,0);assert.equal(aggregate(entries,2026).months[4],distance(points)*2);});
test('exportar devuelve el tramo de vuelta solo para dibujo manual',()=>{const e={title:'Mar & <calma>',data:{points,roundtrip:true}};const xml=exportGPX(e);assert.equal((xml.match(/<trkpt /g)||[]).length,5);assert.ok(xml.includes('Mar &amp; &lt;calma&gt;'));e.data.source='gpx';assert.equal((exportGPX(e).match(/<trkpt /g)||[]).length,3);});
test('coordenadas y textos no confiables',()=>{assert.equal(validPoint([39,4]),true);assert.equal(validPoint([Infinity,4]),false);assert.equal(validPoint([91,4]),false);assert.equal(validPoint(['39',4]),false);assert.throws(()=>distance([[0,0],[NaN,1]]));assert.equal(escapeHtml('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;');});

import {validateEntry} from '../core.js';
test('rechaza rutas degeneradas, fechas inexistentes, duración y marcadores inválidos',()=>{
 const base={kind:'trip',title:'Salida',data:{date:'2026-01-31',points,duration:60,markers:[]}};
 assert.equal(validateEntry(base),base);
 for(const patch of [{points:[[39,4],[39,4]]},{date:'2026-02-31'},{duration:-2},{rating:1000},{markers:[{title:'Acceso',category:'invalid',point:[39,4]}]}])assert.throws(()=>validateEntry({...base,data:{...base.data,...patch}}));
 assert.throws(()=>validateEntry({kind:'goal',title:'Reto',data:{target:0}}));
 assert.throws(()=>validateEntry({kind:'place',title:'Lugar',data:{point:[999,4],category:'access'}}));
});
