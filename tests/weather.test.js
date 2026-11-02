import test from 'node:test';
import assert from 'node:assert/strict';
import {fetchForecast} from '../forecast.js';
test('forecast cancellation reaches both network requests',async()=>{const controller=new AbortController();let aborted=0;const pending=fetchForecast([40,4],{signal:controller.signal,fetcher:(url,{signal})=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>{aborted++;reject(Error('aborted'));}))});controller.abort();await assert.rejects(pending,/cancelada/);assert.equal(aborted,2);});
