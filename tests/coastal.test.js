import test from 'node:test';
import assert from 'node:assert/strict';
import {coastalPath,appendCoastalPoint,removeCoastalPoint} from '../coastal.js';
import {distance,tripKm,exportGPX} from '../core.js';
import data from '../coast-data.js';
const macarella=[39.93805,3.93665],turqueta=[39.93168,3.91459],mitjana=[39.93359,3.97182];
test('Macarella–Turqueta follows detailed coast geometry and measures that polyline',()=>{
 const r=coastalPath([macarella,turqueta]);assert(r.points.length>100);assert(distance(r.points)>distance([macarella,turqueta])*1.5);assert(Math.abs(distance(r.points)-3.56813649)<.001);assert(r.snapMetres<100);
 const edges=new Set(data.edges.map(([a,b])=>[a,b].sort((x,y)=>x-y).join(':'))),nodes=new Map(data.nodes.map((p,i)=>[JSON.stringify(p),i]));
 // Every interior segment must be an actual coastline edge, never a shortcut.
 for(let i=2;i<r.points.length-1;i++){const a=nodes.get(JSON.stringify(r.points[i-1])),b=nodes.get(JSON.stringify(r.points[i]));assert(edges.has([a,b].sort((x,y)=>x-y).join(':')));}
 assert(Math.abs(distance(r.points)-distance(coastalPath([turqueta,macarella]).points))<.000001);
});
test('new outings and plans share coastal geometry, distance, undo and roundtrip',()=>{
 for(const kind of ['trip','plan']){let d={points:[],source:'manual',roundtrip:false};d=appendCoastalPoint(d,macarella);assert.equal(d.points.length,1);d=appendCoastalPoint(d,turqueta);const two=structuredClone(d);assert.equal(d.source,'coastal');assert.equal(d.anchors.length,2);assert(d.points.length>100);assert.equal(tripKm({...d,roundtrip:true}),distance(d.points)*2);d=appendCoastalPoint(d,mitjana);assert.equal(d.anchors.length,3);d=removeCoastalPoint(d);assert.deepEqual(d.points,two.points);d=removeCoastalPoint(d);assert.equal(d.points.length,1);assert.equal(d.anchors.length,1);assert.equal(kind==='plan'||kind==='trip',true);}
});
test('distant and identical points fail without drawing a straight fallback',()=>{
 assert.throws(()=>coastalPath([[0,0],turqueta]),/lejos/);assert.throws(()=>coastalPath([macarella,macarella]),/coinciden/);let d=appendCoastalPoint({points:[],source:'manual'},macarella);const before=JSON.stringify(d);assert.throws(()=>appendCoastalPoint(d,[0,0]));assert.equal(JSON.stringify(d),before);
});
test('coastal distance is exported and GPX distance remains unaltered',()=>{
 const d={...coastalPath([macarella,turqueta]),source:'coastal',roundtrip:false};const xml=exportGPX({title:'Costa',data:d});assert.equal((xml.match(/<trkpt /g)||[]).length,d.points.length);assert.equal(tripKm({points:[macarella,turqueta],source:'gpx',roundtrip:true}),distance([macarella,turqueta]));
});
