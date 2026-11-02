import data from './coast-data.js?v=0.3.0';
 const norm=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[·'’\-]/g,' ').replace(/\s+/g,' ').trim();
 const dist=(a,b)=>{const rad=Math.PI/180;const x=Math.sin((b[0]-a[0])*rad/2)**2+Math.cos(a[0]*rad)*Math.cos(b[0]*rad)*Math.sin((b[1]-a[1])*rad/2)**2;return 6371000*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));};
 class Heap{constructor(){this.a=[]}push(v){let i=this.a.length;this.a.push(v);while(i){let p=(i-1)>>1;if(this.a[p][0]<=v[0])break;this.a[i]=this.a[p];i=p}this.a[i]=v}pop(){const first=this.a[0],last=this.a.pop();if(this.a.length){let i=0;while(i*2+1<this.a.length){let c=i*2+1;if(c+1<this.a.length&&this.a[c+1][0]<this.a[c][0])c++;if(this.a[c][0]>=last[0])break;this.a[i]=this.a[c];i=c}this.a[i]=last}return first}}
export class CoastalRouter{
 constructor(data){this.data=data;this.nodes=data.nodes;this.adj=this.nodes.map(()=>[]);for(const [a,b]of data.edges){const d=dist(this.nodes[a],this.nodes[b]);this.adj[a].push([b,d]);this.adj[b].push([a,d])}const seen=new Set();let largest=[];for(let i=0;i<this.nodes.length;i++){if(seen.has(i))continue;const c=[],stack=[i];seen.add(i);while(stack.length){const n=stack.pop();c.push(n);for(const [j] of this.adj[n])if(!seen.has(j)){seen.add(j);stack.push(j)}}if(c.length>largest.length)largest=c}this.main=new Set(largest);this.edges=data.edges.filter(([a])=>this.main.has(a));}
 snap(point){let best=null;const scale=Math.cos(point[0]*Math.PI/180);for(const [a,b]of this.edges){const A=this.nodes[a],B=this.nodes[b],dx=(B[1]-A[1])*scale,dy=B[0]-A[0],den=dx*dx+dy*dy;const t=den?Math.max(0,Math.min(1,((point[1]-A[1])*scale*dx+(point[0]-A[0])*dy)/den)):0;const p=[A[0]+t*(B[0]-A[0]),A[1]+t*(B[1]-A[1])],d=dist(point,p);if(!best||d<best.d)best={a,b,p,d};}if(!best||best.d>1500)throw Error('El lugar está demasiado lejos de la costa principal de Menorca. Elige una cala, playa o punta.');return best;}
 route(from,to,alternative=false){const s=this.snap(from),t=this.snap(to);if(dist(s.p,t.p)<2)throw Error('Salida y llegada coinciden en la costa. Elige dos lugares diferentes.');const solve=blocked=>{const n=this.nodes.length,S=n,T=n+1,adj=this.adj.slice();adj.push([[s.a,dist(s.p,this.nodes[s.a])],[s.b,dist(s.p,this.nodes[s.b])]],[]);const extra=new Map();for(const k of [t.a,t.b])extra.set(k,dist(this.nodes[k],t.p));if((s.a===t.a&&s.b===t.b)||(s.a===t.b&&s.b===t.a))adj[S].push([T,dist(s.p,t.p)]);const d=new Float64Array(n+2).fill(Infinity),prev=new Int32Array(n+2).fill(-1),heap=new Heap();d[S]=0;heap.push([0,S]);while(heap.a.length){const [cost,a]=heap.pop();if(cost!==d[a])continue;if(a===T)break;const neighbors=extra.has(a)?[...adj[a],[T,extra.get(a)]]:adj[a];for(const [b,w] of neighbors){if(blocked&&((a===blocked[0]&&b===blocked[1])||(a===blocked[1]&&b===blocked[0])))continue;const nd=cost+w;if(nd<d[b]){d[b]=nd;prev[b]=a;heap.push([nd,b])}}}if(!Number.isFinite(d[T]))return null;let ids=[];for(let i=T;i!==-1;i=prev[i])ids.push(i);ids.reverse();return {ids,points:ids.map(i=>i===S?s.p:i===T?t.p:this.nodes[i]),metres:d[T]};};let path=solve(null);if(!path)throw Error('No hay un tramo continuo de costa entre estos lugares en la cartografía.');if(alternative){const internal=path.ids.filter(i=>i<this.nodes.length);if(internal.length<3)throw Error('No hay otro sentido disponible para este tramo.');const i=Math.floor(internal.length/2);path=solve([internal[i-1],internal[i]]);if(!path)throw Error('La cartografía no permite calcular el otro sentido. Usa el tramo más corto.');}return {...path,startSnap:s.d,endSnap:t.d};}
 }

let router;
export const coastalSource={name:data.source,url:data.sourceUrl};
export function coastalPath(waypoints){
 if(!Array.isArray(waypoints)||waypoints.length<2||waypoints.length>100||!waypoints.every(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=90&&Math.abs(p[1])<=180))throw Error('Elige puntos válidos para el recorrido costero.');
 router??=new CoastalRouter(data);
 const points=[],snaps=[];
 for(let i=1;i<waypoints.length;i++){
  const leg=router.route(waypoints[i-1],waypoints[i]);
  points.push(...(i===1?leg.points:leg.points.slice(1)));
  snaps.push(leg.startSnap,leg.endSnap);
  if(points.length>50000)throw Error('El recorrido tiene demasiados puntos. Divide la ruta en varias salidas.');
 }
 return {points,snapMetres:Math.max(...snaps)};
}
export function appendCoastalPoint(d,point){
 const anchors=d.source==='coastal'?(d.anchors||[]):d.source==='gpx'?[]:(d.points||[]);
 const next=[...anchors,point];
 if(next.length===1){router??=new CoastalRouter(data);router.snap(point);return {...d,anchors:next,points:[point],source:'coastal',snapMetres:0};}
 const path=coastalPath(next);return {...d,anchors:next,...path,source:'coastal'};
}
export function removeCoastalPoint(d){
 const anchors=(d.anchors||[]).slice(0,-1);
 if(anchors.length<2)return {...d,anchors,points:anchors.map(p=>[...p]),source:'coastal',snapMetres:0};
 return {...d,anchors,...coastalPath(anchors),source:'coastal'};
}
