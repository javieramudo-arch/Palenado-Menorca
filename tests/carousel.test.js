import test from 'node:test';
import assert from 'node:assert/strict';
import {wrapIndex} from '../carousel.js';
test('circular indexes work forward, backward and through many complete cycles',()=>{
 assert.equal(wrapIndex(4,4),0);assert.equal(wrapIndex(-1,4),3);
 assert.equal(wrapIndex(100,4),0);assert.equal(wrapIndex(-101,4),3);
 for(let i=-40;i<=40;i++){assert(wrapIndex(i,4)>=0&&wrapIndex(i,4)<4);assert.equal(wrapIndex(i+4,4),wrapIndex(i,4));}
 assert.equal(wrapIndex(0,0),0);
});
