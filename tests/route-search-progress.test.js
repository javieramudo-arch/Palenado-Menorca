import test from 'node:test';
import assert from 'node:assert/strict';
import {parseRouteQuery,findRoutePlaces,coastalPlaces} from '../route-search.js';
import {appendCoastalPoint} from '../coastal.js';
import {routePreview} from '../diary.js';
import {progressMarkup} from '../progress.js';
import {coastProgress} from '../coast-progress.js';
const now=new Date('2026-11-06T12:00:00Z');
test('search parses a departure and origin/destination phrases',()=>{
 assert.deepEqual(parseRouteQuery('Cala Galdana'),['Cala Galdana']);
 assert.deepEqual(parseRouteQuery('Ruta desde Cala Morell a Punta Nati'),['Cala Morell','Punta Nati']);
 assert.deepEqual(parseRouteQuery('desde Cala Galdana hasta Cala Pregonda'),['Cala Galdana','Cala Pregonda']);
 assert.throws(()=>parseRouteQuery('a'));
});
test('demo places work without a network and each can start a coastal plan',async()=>{
 for(const place of coastalPlaces){const [found]=await findRoutePlaces(place.title,{fetcher:()=>{throw Error('Network should not be used');}});assert.deepEqual(found.point,place.point);assert.equal(appendCoastalPoint({points:[],source:'manual'},found.point).points.length,1);}
 const from=coastalPlaces[2],to=coastalPlaces[3];const route=appendCoastalPoint(appendCoastalPoint({points:[],source:'manual'},from.point),to.point);assert(route.points.length>2);assert.equal(route.anchors.length,2);
});
test('ambiguous results remain distinct, no matches and network errors are handled',async()=>{
 const fetcher=async()=>({ok:true,json:async()=>({features:[{geometry:{coordinates:[4,40]},properties:{name:'Cala Test',osm_type:'N',osm_id:1}},{geometry:{coordinates:[4.1,40.1]},properties:{name:'Cala Test',osm_type:'N',osm_id:2}}]})});
 assert.equal((await findRoutePlaces('Test',{fetcher})).length,2);
 assert.deepEqual(await findRoutePlaces('Unknown',{fetcher:async()=>({ok:true,json:async()=>({features:[]})})}),[]);
 await assert.rejects(findRoutePlaces('Unknown',{fetcher:async()=>{throw Error('offline');}}),/offline/);
});
test('map preview projects actual tiles under the route and includes attribution',()=>{
 const e={title:'<unsafe>',kind:'trip',data:{points:[[39.93805,3.93665],[39.93168,3.91459]],source:'coastal'}};
 const html=routePreview(e);assert.match(html,/tile.openstreetmap.org\/\d+\/\d+\/\d+.png/);assert(html.indexOf('<image')<html.indexOf('<polyline'));assert.match(html,/© OpenStreetMap/);assert(!html.includes('<unsafe>'));assert(!html.includes('NaN'));assert.equal((html.match(/<image/g)||[]).length<=6,true);
});
test('progress excludes plans and deleted trips, shows goals and escapes feed content without mutating data',()=>{
 const trip={id:'safe',kind:'trip',title:'<script>bad</script>',data:{date:'2026-11-01',duration:60,points:[[39.93805,3.93665],[39.93168,3.91459]],source:'coastal'}};
 const entries=[trip,{...trip,id:'pending',kind:'plan',title:'DO_NOT_SHOW_PLAN'},{...trip,id:'gone',deleted_at:'2026-11-02',title:'DO_NOT_SHOW_DELETED'},{id:'g',kind:'goal',data:{year:2026,target:100}}],before=structuredClone(entries),html=progressMarkup(entries,coastProgress(entries),now);
 assert.match(html,/Editar mi objetivo/);assert.match(html,/Actividad reciente/);assert.match(html,/&lt;script&gt;/);assert(!html.includes('DO_NOT_SHOW'));assert.deepEqual(entries,before);
 assert.match(progressMarkup([],coastProgress([]),now),/Tu historia empieza con una salida/);
});
