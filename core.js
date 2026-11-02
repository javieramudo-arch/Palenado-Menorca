export const categories={parking:'Aparcamientos',access:'Accesos al mar',photo:'Fotografías',warning:'Precauciones',interest:'Puntos de interés'};
export const symbols={parking:'P',access:'↘',photo:'▧',warning:'!',interest:'★'};
export function escapeHtml(value=''){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
export function validPoint(p){return Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=90&&Math.abs(p[1])<=180;}
export function distance(points){let km=0;for(let i=1;i<points.length;i++){if(!validPoint(points[i-1])||!validPoint(points[i]))throw Error('Coordenadas no válidas');const [a,b]=[points[i-1],points[i]],r=Math.PI/180;const dlat=(b[0]-a[0])*r,dlon=(b[1]-a[1])*r;const h=Math.sin(dlat/2)**2+Math.cos(a[0]*r)*Math.cos(b[0]*r)*Math.sin(dlon/2)**2;km+=6371*2*Math.atan2(Math.sqrt(h),Math.sqrt(Math.max(0,1-h)));}return km;}
export function tripKm(data){return distance(data.points||[])*(data.roundtrip&&data.source!=='gpx'?2:1);}
export function measuredTripKm(data){if(!data||!Array.isArray(data.points)||data.points.length<2||!data.points.every(validPoint)||!data.points.some(p=>p[0]!==data.points[0][0]||p[1]!==data.points[0][1]))return null;try{const km=tripKm(data);return Number.isFinite(km)?km:null;}catch{return null;}}
export function aggregate(entries,year){const trips=entries.filter(e=>e.kind==='trip'&&!e.deleted_at&&(!year||String(e.data?.date||'').startsWith(String(year))));const valid=trips.map(e=>({entry:e,km:measuredTripKm(e.data)})),minutes=trips.reduce((n,e)=>{const m=Number(e.data?.duration||0);return n+(Number.isFinite(m)&&m>=0?m:0);},0);return {count:trips.length,invalidCount:valid.filter(e=>e.km===null).length,km:valid.reduce((n,e)=>n+(e.km??0),0),minutes,months:Array.from({length:12},(_,i)=>valid.filter(e=>Number(e.entry.data?.date?.slice(5,7))===i+1).reduce((n,e)=>n+(e.km??0),0))};}

export function parseGPX(text,Parser=globalThis.DOMParser){const doc=new Parser().parseFromString(text,'application/xml');if(doc.querySelector('parsererror'))throw Error('El GPX no es un XML válido.');const segments=[...doc.getElementsByTagNameNS('*','trkseg')];const routes=[...doc.getElementsByTagNameNS('*','rte')];const containers=segments.length?segments:routes;if(containers.length>1)throw Error('Este GPX tiene varios tramos. Impórtalos por separado para no sumar los saltos entre ellos.');const nodes=containers.length?[...containers[0].getElementsByTagNameNS('*',segments.length?'trkpt':'rtept')]:[];if(nodes.length<2)throw Error('El GPX debe contener al menos dos puntos de recorrido.');if(nodes.length>50000)throw Error('El GPX supera 50.000 puntos. Simplifícalo antes de importarlo.');if(nodes.some(p=>!p.hasAttribute('lat')||!p.hasAttribute('lon')||!p.getAttribute('lat').trim()||!p.getAttribute('lon').trim()))throw Error('Faltan coordenadas en el GPX.');const points=nodes.map(p=>[Number(p.getAttribute('lat')),Number(p.getAttribute('lon'))]);if(!points.every(validPoint))throw Error('El GPX contiene coordenadas no válidas.');const title=doc.getElementsByTagNameNS('*','name')[0]?.textContent?.trim()||'Recorrido importado';return {points,title,source:'gpx',roundtrip:false};}
export function exportGPX(entry){const esc=s=>String(s).replace(/[<>&"']/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]));let points=entry.data.points;if(entry.data.roundtrip&&entry.data.source!=='gpx')points=[...points,...points.slice(0,-1).reverse()];return `<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Paleando Menorca" xmlns="http://www.topografix.com/GPX/1/1"><trk><name>${esc(entry.title)}</name><trkseg>${points.map(p=>`<trkpt lat="${p[0]}" lon="${p[1]}"></trkpt>`).join('')}</trkseg></trk></gpx>`;}
export const number=n=>new Intl.NumberFormat('es-ES',{maximumFractionDigits:2}).format(n);
export const today=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};

// Validate persisted and locally recovered records before they can affect the UI.
export function validateEntry(e){
 if(!e||!['trip','plan','place','goal','preferences'].includes(e.kind)||typeof e.title!=='string'||!e.title.trim()||e.title.length>180||!e.data||typeof e.data!=='object')throw Error('La ficha no es válida. Revisa su nombre y sus datos.');
 const d=e.data;
 if(['trip','plan'].includes(e.kind)){
  if(!Array.isArray(d.points)||d.points.length<2||d.points.length>50000||!d.points.every(validPoint)||distance(d.points)<=.01)throw Error('El recorrido necesita al menos dos puntos distintos y válidos.');
  if(!/^\d{4}-\d{2}-\d{2}$/.test(d.date||'')||new Date(d.date+'T12:00:00Z').toISOString().slice(0,10)!==d.date)throw Error('Revisa la fecha de la salida.');
  if(d.duration!==''&&d.duration!=null&&(!Number.isFinite(Number(d.duration))||Number(d.duration)<0||Number(d.duration)>10000))throw Error('La duración debe estar entre 0 y 10.000 minutos.');
  if(d.rating!==''&&d.rating!=null&&(!Number.isInteger(Number(d.rating))||Number(d.rating)<1||Number(d.rating)>5))throw Error('La valoración debe estar entre 1 y 5.');
  for(const m of d.markers||[])if(!validPoint(m.point)||!categories[m.category]||typeof m.title!=='string')throw Error('Hay un marcador que necesita revisión.');
 }
 if(e.kind==='place'&&(!validPoint(d.point)||!categories[d.category]))throw Error('Revisa la ubicación y la categoría del lugar.');
 if(e.kind==='goal'&&(!Number.isFinite(Number(d.target))||Number(d.target)<1||Number(d.target)>100000))throw Error('El objetivo debe estar entre 1 y 100.000 km.');
 return e;
}
