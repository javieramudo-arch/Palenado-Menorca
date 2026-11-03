import data from './coast-data.js?v=0.3.0';
import {CoastalRouter} from './coastal.js?v=0.3.0';
import {distance,validPoint} from './core.js?v=0.3.0';

// Store intervals on reference edges, not kilometres summed per outing.
// Repeated outings and return journeys therefore cover the same intervals once.
export class CoastProgress {
 constructor(geometry){
  this.nodes=geometry.nodes;const main=new CoastalRouter(geometry);this.nodeIds=new Map(this.nodes.map((p,i)=>[p.join(','),i]));this.edges=[];this.byPair=new Map();this.adj=new Map();this.grid=new Map();this.cell=.002;this.scale=Math.cos(40*Math.PI/180);this.cache=new WeakMap();
  for(const[a,b]of main.edges){const key=this.key(a,b);if(this.byPair.has(key))continue;const edge={id:this.edges.length,a,b,A:this.nodes[a],B:this.nodes[b],km:distance([this.nodes[a],this.nodes[b]])};if(!edge.km)continue;this.edges.push(edge);this.byPair.set(key,edge);for(const n of[a,b]){if(!this.adj.has(n))this.adj.set(n,[]);this.adj.get(n).push(edge);}for(const k of this.cells(edge.A,edge.B,0)){if(!this.grid.has(k))this.grid.set(k,[]);this.grid.get(k).push(edge);}}
  this.totalKm=this.edges.reduce((s,e)=>s+e.km,0);
 }
 key(a,b){return a<b?`${a}:${b}`:`${b}:${a}`;}
 *cells(a,b,padding){const minLat=Math.max(39.7,Math.min(a[0],b[0])-padding),maxLat=Math.min(40.2,Math.max(a[0],b[0])+padding),minLng=Math.max(3.6,Math.min(a[1],b[1])-padding),maxLng=Math.min(4.5,Math.max(a[1],b[1])+padding);for(let x=Math.floor(minLat/this.cell);x<=Math.floor(maxLat/this.cell);x++)for(let y=Math.floor(minLng/this.cell);y<=Math.floor(maxLng/this.cell);y++)yield `${x}:${y}`;}
 project(p,edge){const dx=(edge.B[1]-edge.A[1])*this.scale,dy=edge.B[0]-edge.A[0],px=(p[1]-edge.A[1])*this.scale,py=p[0]-edge.A[0],den=dx*dx+dy*dy;const t=den?(px*dx+py*dy)/den:0;const clamp=Math.max(0,Math.min(1,t));return {t,error:Math.hypot(px-clamp*dx,py-clamp*dy)*111195};}
 candidates(a,b,padding=0){const result=new Set();for(const cell of this.cells(a,b,padding))for(const e of this.grid.get(cell)||[])result.add(e);return result;}
 exactSegment(a,b){const ia=this.nodeIds.get(a.join(',')),ib=this.nodeIds.get(b.join(','));if(ia!==undefined&&ib!==undefined){const edge=this.byPair.get(this.key(ia,ib));return edge?[[edge.id,0,1]]:[];}const options=ia!==undefined?this.adj.get(ia):ib!==undefined?this.adj.get(ib):this.candidates(a,b,.000002);const matches=[];for(const e of options||[]){const p=this.project(a,e),q=this.project(b,e);if(p.error<.05&&q.error<.05){const lo=Math.max(0,Math.min(p.t,q.t)),hi=Math.min(1,Math.max(p.t,q.t));if(hi-lo>1e-9)matches.push([e.id,lo,hi]);}}return matches;}
 gpsSegment(a,b){
  // Only the portions of coastline actually alongside a track are credited.
  // A straight GPS chord never fills an unseen bay via endpoint routing.
  const ax=a[1]*this.scale*111195,ay=a[0]*111195,bx=b[1]*this.scale*111195,by=b[0]*111195,dx=bx-ax,dy=by-ay,len=Math.hypot(dx,dy);if(len<.2)return [];
  const result=[];for(const e of this.candidates(a,b,.001)){const ex=e.A[1]*this.scale*111195,ey=e.A[0]*111195,vx=(e.B[1]-e.A[1])*this.scale*111195,vy=(e.B[0]-e.A[0])*111195,vlen=Math.hypot(vx,vy);if(Math.abs((dx*vx+dy*vy)/(len*vlen))<.7)continue;
   let lo=0,hi=1;const constrain=(start,delta,min,max)=>{if(Math.abs(delta)<1e-12)return start>=min&&start<=max;let a=(min-start)/delta,b=(max-start)/delta;if(a>b)[a,b]=[b,a];lo=Math.max(lo,a);hi=Math.min(hi,b);return hi>lo;};
   if(!constrain(((ex-ax)*dx+(ey-ay)*dy)/(len*len),(vx*dx+vy*dy)/(len*len),0,1))continue;
   if(!constrain((dx*(ey-ay)-dy*(ex-ax))/len,(dx*vy-dy*vx)/len,-75,75))continue;
   if(hi-lo>1e-9)result.push([e.id,lo,hi]);
  }return result;
 }
 coverage(d){const points=d?.points;if(!Array.isArray(points)||!points.every(validPoint))return [];const cached=this.cache.get(points);if(cached&&cached.source===d.source&&cached.length===points.length)return cached.intervals;const intervals=[];for(let i=1;i<points.length;i++){const a=points[i-1],b=points[i];if(!validPoint(a)||!validPoint(b))continue;intervals.push(...(d.source==='gpx'?this.gpsSegment(a,b):this.exactSegment(a,b)));}this.cache.set(points,{source:d.source,length:points.length,intervals});return intervals;}
 measure(entries){const byEdge=new Map();let unmatched=0,gps=0;for(const e of entries){if(e.kind!=='trip'||e.deleted_at)continue;const intervals=this.coverage(e.data);if(!intervals.length&&e.data.points?.length>1)unmatched++;if(e.data.source==='gpx'&&intervals.length)gps++;for(const[id,lo,hi]of intervals){if(!byEdge.has(id))byEdge.set(id,[]);byEdge.get(id).push([lo,hi]);}}
  let coveredKm=0;for(const[id,segments]of byEdge){segments.sort((a,b)=>a[0]-b[0]);let start=segments[0][0],end=segments[0][1],length=0;for(const[a,b]of segments.slice(1)){if(a<=end+1e-9)end=Math.max(end,b);else{length+=end-start;start=a;end=b;}}length+=end-start;coveredKm+=Math.min(1,length)*this.edges[id].km;}
  coveredKm=Math.min(this.totalKm,coveredKm);return {totalKm:this.totalKm,coveredKm,pendingKm:Math.max(0,this.totalKm-coveredKm),percent:this.totalKm?coveredKm/this.totalKm*100:0,unmatched,gps};
 }
}
let reference;
export function coastProgress(entries){reference??=new CoastProgress(data);return reference.measure(entries);}

export function pendingCoast(entries){reference??=new CoastProgress(data);const byEdge=new Map();for(const e of entries.filter(e=>e.kind==='trip'&&!e.deleted_at))for(const[id,a,b]of reference.coverage(e.data)){if(!byEdge.has(id))byEdge.set(id,[]);byEdge.get(id).push([a,b]);}const result=[];for(const edge of reference.edges){let end=0;const lerp=t=>[edge.A[0]+(edge.B[0]-edge.A[0])*t,edge.A[1]+(edge.B[1]-edge.A[1])*t];for(const[a,b]of (byEdge.get(edge.id)||[]).sort((a,b)=>a[0]-b[0])){if(a>end)result.push([lerp(end),lerp(a)]);end=Math.max(end,b);}if(end<1)result.push([lerp(end),lerp(1)]);}return result;}
