import test from 'node:test';
import assert from 'node:assert/strict';
import {nextAdventure,monthActivity,routeEstimate} from '../dashboard.js';
const now=Date.UTC(2026,10,6,12),points=[[39.94,3.93],[39.95,3.94]],plan=(id,start,extra={})=>({id,title:'Mismo nombre',kind:'plan',data:{plannedStart:start,date:'2026-11-06',points,source:'coastal',...extra}});
test('next adventure uses future dates and IDs, excludes deleted/past/invalid dates, and does not mutate data',()=>{
 const list=[plan('later','2026-11-07T12:00:00Z'),plan('old','2026-11-06T11:00:00Z'),plan('next','2026-11-06T14:00:00Z'),{...plan('deleted','2026-11-06T13:00:00Z'),deleted_at:'2026-11-06'},plan('invalid','wrong'),plan('invalid-date','',{date:'2026-99-99'})],copy=structuredClone(list);
 assert.equal(nextAdventure(list,now).entry.id,'next');assert.deepEqual(list,copy);assert.equal(nextAdventure([list[1]],now),null);
 const noHour=nextAdventure([plan('dated','',{date:'2026-11-07'})],now);assert.equal(noHour.entry.id,'dated');assert.equal(noHour.timed,false);
});
test('month activity includes repeats and both coastal legs while keeping GPX geometry intact',()=>{
 const trip=(id,data,kind='trip')=>({id,kind,data:{date:'2026-11-06',points,source:'coastal',...data}}),a=trip('a',{}),km=monthActivity([a],now).km;
 const result=monthActivity([a,trip('b',{roundtrip:true}),trip('gpx',{roundtrip:true,source:'gpx'}),trip('pending',{},'plan'),trip('prior',{date:'2026-10-01'}),{...a,id:'deleted',deleted_at:'2026-11-06'}],now);
 assert.equal(result.count,3);assert(Math.abs(result.km-km*4)<1e-9);assert.equal(result.invalid,0);
});
test('summary estimates reuse saved manual duration and full route distance, without writing computed defaults',()=>{
 const entry=plan('a','2026-11-07T12:00:00Z',{roundtrip:true,stopMinutes:10,paceMinutesPerKm:15}),copy=structuredClone(entry),computed=routeEstimate(entry),one=routeEstimate({...entry,data:{...entry.data,roundtrip:false}});
 assert.equal(computed.km,one.km*2);assert(computed.minutes>one.minutes);assert.equal(routeEstimate({...entry,data:{...entry.data,estimatedMinutes:125,estimateMode:'manual'}}).minutes,125);assert.equal(routeEstimate({...entry,data:{...entry.data,points:[]}}).km,null);assert.deepEqual(entry,copy);
});
