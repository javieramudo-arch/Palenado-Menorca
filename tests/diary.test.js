import test from 'node:test';
import assert from 'node:assert/strict';
import {diaryTrips,diarySummary,diaryPeriods,diaryPhotos,recordedMinutes,savedDate,routePreview} from '../diary.js';
import {measuredTripKm} from '../core.js';
const points=[[39.93805,3.93665],[39.93168,3.91459]],now=new Date('2026-11-06T12:00:00Z');
const trip=(id,data={})=>({id,kind:'trip',title:'Mismo nombre',data:{date:'2026-11-06',points,source:'coastal',photos:[],markers:[],...data}});
test('diary search finds saved place/endpoints/notes with accents, filters combine and IDs break chronological ties',()=>{
 const rows=[trip('b',{departure:'Cala Galdana',zone:'Sur',favorite:true,duration:60,photos:[{path:'private/one'}]}),trip('a',{arrival:'Ciutadella',notes:'Última palada',zone:'Norte'}),trip('old',{date:'2025-10-01'}),{...trip('pending'),kind:'plan'},{...trip('gone'),deleted_at:'2026-11-06'}],copy=structuredClone(rows);
 assert.deepEqual(diaryTrips(rows,{},now).map(e=>e.id),['a','b','old']);assert.deepEqual(diaryTrips(rows,{query:'ultima'},now).map(e=>e.id),['a']);assert.equal(diaryTrips(rows,{query:'Ciutadella'},now)[0].id,'a');assert.equal(diaryTrips(rows,{query:'galdana',favorite:true,photos:true,year:'2026',month:'2026-11',zone:'Sur'},now)[0].id,'b');assert.equal(diaryTrips(rows,{photos:true,zone:'Norte'},now).length,0);assert.deepEqual(diaryTrips(rows,{thisMonth:true},now).map(e=>e.id),['a','b']);assert.deepEqual(rows,copy);
});
test('the diary counts real duration only, preserves a real zero and does not double full GPX returns',()=>{
 const base=trip('one',{duration:60}),rows=[base,trip('return',{roundtrip:true,duration:''}),trip('gpx',{source:'gpx',roundtrip:true,estimatedMinutes:999}),trip('zero',{duration:0}),trip('bad',{points:[],duration:-5})],s=diarySummary(rows),km=measuredTripKm(base.data);
 assert.equal(s.count,5);assert(Math.abs(s.km-km*5)<1e-9);assert.equal(s.minutes,60);assert.equal(s.knownDuration,2);assert.equal(s.missingDuration,3);assert.equal(s.missingKm,1);assert.equal(recordedMinutes(trip('space',{duration:' '})),null);assert.equal(recordedMinutes(trip('false',{duration:'invalid'})),null);assert.equal(diarySummary([trip('unknown')]).knownDuration,0);
});
test('invalid/missing dates stay last and are excluded from period selectors; local month follows Menorca',()=>{
 const rows=[trip('invalid',{date:'2026-02-31'}),trip('missing',{date:''}),trip('good'),trip('old',{date:'2025-10-01'}),{...trip('plan',{date:'2030-01-01'}),kind:'plan'}];assert.equal(savedDate('2026-02-31'),'');assert.equal(savedDate('2026-02-28'),'2026-02-28');assert.deepEqual(diaryPeriods(rows),['2026-11','2025-10']);assert.deepEqual(diaryTrips(rows,{year:'2026'},now).map(e=>e.id),['good']);assert.equal(diaryTrips([trip('boundary',{date:'2026-11-01'})],{thisMonth:true},new Date('2026-10-31T23:30:00Z')).length,1);
});
test('real galleries omit sample/name-only records and thumbnails use saved valid geometry and established route colors',()=>{
 const e=trip('photo',{photos:[{name:'No path'},{path:'example'},{path:'private/safe',name:'<safe>'}]});assert.equal(diaryPhotos(e).length,1);assert.equal(diaryPhotos(e,true).length,2);assert.match(routePreview(e),/#11796f/);assert.match(routePreview(trip('back',{roundtrip:true})),/#ad5c28/);assert.match(routePreview({...e,kind:'plan'}),/#2678c8/);assert.match(routePreview(trip('bad',{points:[]})),/Recorrido no disponible/);assert(!routePreview({...e,title:'<img onerror="bad">'}).includes('<img'));
});
