import {escapeHtml as esc} from './core.js?v=0.12.0';
import {PlaceSearch} from './sea-tools.js?v=0.15.0';
const fold=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
// Representative coastal positions; the existing coastal router validates and snaps the route.
export const coastalPlaces=[
 {title:'Cala Galdana',point:[39.93805,3.93665]},
 {title:'Cala Pregonda',point:[40.0564,4.0414]},
 {title:'Cala Morell',point:[40.0507,3.8825]},
 {title:'Punta Nati',point:[40.0498,3.8238]}
];
export function parseRouteQuery(text){
 const clean=text.trim().replace(/\s+/g,' '),match=clean.match(/^(?:ruta\s+)?(?:desde|de)\s+(.+?)\s+(?:hasta|a)\s+(.+)$/i);
 if(match)return [match[1].trim(),match[2].trim()];
 if(clean.length<3)throw Error('Escribe al menos tres caracteres.');
 return [clean];
}
export async function findRoutePlaces(query,{signal,fetcher=fetch}={}){
 const exact=coastalPlaces.filter(p=>fold(p.title)===fold(query));
 if(exact.length)return exact.map(p=>({...p,source:'Referencia costera · revisa el punto en el mapa'}));
 const local=coastalPlaces.filter(p=>fold(p.title).includes(fold(query)));
 try{const remote=await new PlaceSearch(fetcher).find(query,{signal});return [...local,...remote].filter((p,i,all)=>all.findIndex(x=>fold(x.title)===fold(p.title)&&Math.hypot(x.point[0]-p.point[0],x.point[1]-p.point[1])<.003)===i);}
 catch(error){if(signal?.aborted||!local.length)throw error;return local;}
}
export function mountRouteSearch(api){
 const button=document.querySelector('#route-search-button');if(!button)return;
 let controller=null,generation=0;
 button.onclick=()=>{
  controller?.abort();generation++;
  api.open('¿Desde dónde salimos?',`<p>Busca una cala como salida o escribe el origen y el destino para preparar una ruta.</p><form id="route-search-form"><label>Salida o ruta<input name="query" type="search" required minlength="3" maxlength="180" autocomplete="off" placeholder="Ruta desde Cala Morell a Punta Nati"></label><button class="button primary" type="submit">Buscar ruta</button></form><p class="field-note">Ejemplos: Cala Galdana · Cala Pregonda · Ruta desde Cala Morell a Punta Nati. Solo se prepara un borrador; revisa los puntos y el trazado antes de guardar.</p><p id="route-search-state" role="status" aria-live="polite"></p><div id="route-search-results"></div><small>Otros lugares: Photon · © OpenStreetMap. La consulta se envía al pulsar Buscar.</small>`);
  const body=api.body(),form=body.querySelector('form'),state=body.querySelector('#route-search-state'),out=body.querySelector('#route-search-results'),input=form.elements.query;
  const cancel=()=>{generation++;controller?.abort();form.querySelector('button').disabled=false;out.replaceChildren();state.textContent='';};
  input.addEventListener('input',cancel);body.closest('dialog')?.addEventListener('close',cancel,{once:true});
  form.onsubmit=async ev=>{
   ev.preventDefault();if(!form.reportValidity())return;controller?.abort();controller=new AbortController();const seq=++generation,signal=controller.signal,timer=setTimeout(()=>controller.abort(),12000);
   const valid=()=>seq===generation&&form.isConnected;state.textContent='Localizando puntos en Menorca…';out.replaceChildren();form.querySelector('button').disabled=true;
   try{
    const queries=parseRouteQuery(input.value),groups=await Promise.all(queries.map(q=>findRoutePlaces(q,{signal})));
    if(!valid())return;
    const missing=groups.findIndex(g=>!g.length);if(missing>=0){state.textContent='No encontramos «'+queries[missing]+'». Revisa el nombre o prueba con una cala cercana.';return;}
    const chosen=groups.map(g=>g.length===1?g[0]:null);
    const use=()=>{if(valid()&&chosen.every(Boolean))api.start(chosen);};
    if(chosen.every(Boolean)){use();return;}
    state.textContent='Hay varias coincidencias. Elige la ubicación correcta.';
    out.innerHTML=groups.map((g,i)=>`<label>${i===0?'Salida':'Llegada'}: ${esc(queries[i])}<select data-route-choice="${i}">${g.length>1?'<option value="">Selecciona un lugar</option>':''}${g.map((p,j)=>`<option value="${j}">${esc(p.title)} · ${esc(p.subtitle||p.source||'Menorca')}</option>`).join('')}</select></label>`).join('')+'<button id="use-searched-route" class="button primary" disabled>Preparar ruta</button>';
    out.onchange=ev=>{if(!ev.target.matches('[data-route-choice]'))return;const i=Number(ev.target.dataset.routeChoice);chosen[i]=ev.target.value===''?null:groups[i][Number(ev.target.value)];out.querySelector('button').disabled=!chosen.every(Boolean);};out.querySelector('button').onclick=use;
   }catch(error){if(valid())state.textContent=error.name==='AbortError'?'La búsqueda ha tardado demasiado. Vuelve a intentarlo.':error.message;}
   finally{clearTimeout(timer);if(valid())form.querySelector('button').disabled=false;}
  };input.focus();
 };
}
