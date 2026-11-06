import {measuredTripKm,number,escapeHtml as esc} from './core.js?v=0.12.0';
import {dayKey} from './forecast.js?v=0.12.0';
import {durationText,estimatePlan} from './route-features.js?v=0.12.0';
import {beaufortMarkup} from './beaufort.js?v=0.13.0';

export const icons={
 info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
 coast:'<path d="M3 17c4-7 7 3 11-5s5-3 7-7M3 21h18"/>',
 diary:'<path d="M5 3h14v18H5zM8 7h8M8 11h8M8 15h5M3 6h4M3 12h4M3 18h4"/>',
 route:'<circle cx="5" cy="18" r="2"/><circle cx="19" cy="6" r="2"/><path d="M5 16v-5a4 4 0 0 1 4-4h4a3 3 0 0 1 0 6h-2a3 3 0 0 0 0 6h5l3-3"/>',
 weather:'<path d="M3 8h12a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h6"/>',
 map:'<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3ZM9 3v15M15 6v15"/>',
 progress:'<path d="M4 3v17h17M8 15l4-5 4 2 5-7"/>',
 island:'<path d="m10 3 4 2 1 4 5 2 1 4-6 5-7-2-5-5 2-6Z"/>',
 location:'<circle cx="12" cy="12" r="5"/><path d="M12 2v5M12 17v5M2 12h5M17 12h5"/>',
 layers:'<path d="m12 3 10 6-10 6L2 9ZM2 13l10 6 10-6M2 17l10 6 10-6"/>',
 fullscreen:'<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',
 refresh:'<path d="M20 7a9 9 0 1 0 1 8M20 2v6h-6"/>',
 menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
 plus:'<path d="M12 4v16M4 12h16"/>',
 search:'<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
 sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1 1M18 18l1 1M19 5l-1 1M6 18l-1 1"/>',
 star:'<path d="m12 3 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z"/>',
};
export const icon=name=>`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${icons[name]||icons.route}</svg>`;

// Display models only: never fetch, save, alter estimates or select a map layer.
export function nextAdventure(entries,now=Date.now()){
 const today=dayKey(now/1000);
 return entries.filter(e=>e.kind==='plan'&&!e.deleted_at).map(e=>{
  const d=e.data||{},t=Date.parse(d.plannedStart);
  if(d.plannedStart)return Number.isFinite(t)&&t>=now?{entry:e,at:t,timed:true}:null;
  const date=d.date,parsed=Date.parse(date+'T12:00:00Z');
  return /^\d{4}-\d{2}-\d{2}$/.test(date||'')&&date>=today&&Number.isFinite(parsed)&&new Date(parsed).toISOString().slice(0,10)===date?{entry:e,at:Date.parse(date+'T12:00:00Z'),timed:false}:null;
 }).filter(Boolean).sort((a,b)=>a.at-b.at||String(a.entry.id).localeCompare(String(b.entry.id)))[0]||null;
}
export function monthActivity(entries,now=Date.now()){
 const month=dayKey(now/1000).slice(0,7),trips=entries.filter(e=>e.kind==='trip'&&!e.deleted_at&&String(e.data?.date||'').startsWith(month));
 let km=0,invalid=0;for(const e of trips){const n=measuredTripKm(e.data);if(n===null)invalid++;else km+=n;}
 return {count:trips.length,km,invalid,month};
}
export function routeEstimate(entry,preferences={}){
 const d=entry?.data||{},km=measuredTripKm(d);if(km===null)return {km:null,minutes:null};
 let minutes=d.estimatedMinutes??(d.duration!==''?d.duration:null);
 if(minutes==null)try{minutes=estimatePlan(d,preferences).estimatedMinutes;}catch{return {km,minutes:null};}
 return {km,minutes:Number.isFinite(Number(minutes))&&Number(minutes)>=0?Number(minutes):null};
}
const stamp=t=>new Date(t).toLocaleString('es-ES',{timeZone:'Europe/Madrid',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});

export function mountDashboard(api){
 const root=document.querySelector('#summary-carousel'),track=root.querySelector('#summary-track'),cards=[...track.querySelectorAll('.summary-card')],dots=[...root.querySelectorAll('[data-summary-index]')];
 let index=0,width=0,frame=0,resizeFrame=0,weatherKey='';const reduce=matchMedia('(prefers-reduced-motion: reduce)');
 const overflow=()=>track.scrollWidth>track.clientWidth+2;
 const offset=i=>cards[i].offsetLeft-cards[0].offsetLeft;
 function position(){root.querySelector('#summary-position').textContent=overflow()?`${index+1} de ${cards.length}`:`${cards.length} resúmenes`;dots.forEach((d,i)=>d.classList.toggle('selected',i===index));root.querySelector('#summary-prev').disabled=!overflow()||index===0;root.querySelector('#summary-next').disabled=!overflow()||index===cards.length-1;}
 function select(i){index=Math.max(0,Math.min(cards.length-1,i));track.scrollTo({left:overflow()?offset(index):0,behavior:reduce.matches?'instant':'smooth'});position();}
 root.querySelector('#summary-prev').onclick=()=>select(index-1);root.querySelector('#summary-next').onclick=()=>select(index+1);
 track.addEventListener('keydown',e=>{if(e.target!==track)return;const keys={ArrowLeft:index-1,ArrowRight:index+1,Home:0,End:cards.length-1};if(e.key in keys){e.preventDefault();select(keys[e.key]);}});
 track.addEventListener('scroll',()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{if(!overflow())return;index=cards.reduce((best,_,i)=>Math.abs(offset(i)-track.scrollLeft)<Math.abs(offset(best)-track.scrollLeft)?i:best,0);position();});},{passive:true});
 const observer=new ResizeObserver(()=>{if(!track.clientWidth||track.clientWidth===width)return;width=track.clientWidth;cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{track.scrollTo({left:overflow()?offset(index):0,behavior:'instant'});position();});});observer.observe(track);
 root.addEventListener('click',e=>{const b=e.target.closest('[data-summary-action]');if(!b)return;api.action(b.dataset.summaryAction,b.dataset.id);});
 for(const el of document.querySelectorAll('[data-ui-icon]'))el.innerHTML=icon(el.dataset.uiIcon);
 for(const b of document.querySelectorAll('[data-tab]')){const name=b.dataset.tab;b.setAttribute('aria-current',b.classList.contains('active')?'page':'false');b.innerHTML=icon({mapa:'map',diario:'diary',progreso:'progress'}[name])+`<span>${{mapa:'Mapa',diario:'Diario',progreso:'Progreso'}[name]}</span>`;}
 for(const b of document.querySelectorAll('[data-map]'))b.innerHTML=icon({island:'island',location:'location',layers:'layers',fullscreen:'fullscreen'}[b.dataset.map]);
 function render({entries,preferences={},practice=false}){
  const month=monthActivity(entries);root.querySelector('#summary-month').textContent=`Este mes: ${month.count} ${month.count===1?'salida':'salidas'} · ${number(month.km)} km${month.invalid?' · revisa '+month.invalid+' trazado':''}`;
  const next=nextAdventure(entries),title=root.querySelector('#summary-next-title'),meta=root.querySelector('#summary-next-meta'),metrics=root.querySelector('#summary-next-metrics'),view=root.querySelector('#summary-next-view'),edit=root.querySelector('#summary-next-edit');
  if(next){title.textContent=next.entry.title;title.title=next.entry.title;meta.textContent=next.timed?stamp(next.at):new Date(next.at).toLocaleDateString('es-ES',{timeZone:'Europe/Madrid',day:'numeric',month:'short'})+' · sin hora';const estimate=routeEstimate(next.entry,preferences);metrics.textContent=`${estimate.km===null?'Distancia no disponible':number(estimate.km)+' km'} · ${durationText(estimate.minutes)}`;view.textContent='Ver aventura';view.dataset.summaryAction='adventure';view.dataset.id=next.entry.id;edit.dataset.id=next.entry.id;edit.hidden=false;}
  else{title.textContent='Tu próxima ruta';title.removeAttribute('title');meta.textContent='Sin aventura próxima con fecha';metrics.textContent='Elige una ruta pendiente o prepara otra.';view.textContent='Ver rutas pendientes';view.dataset.summaryAction='plans';delete view.dataset.id;edit.hidden=true;}
  const favorites=preferences.weatherFavorites||[];root.querySelector('#summary-favorites-count').textContent=`${favorites.length} ${favorites.length===1?'cala favorita':'calas favoritas'}`;root.querySelector('#summary-favorites-names').textContent=favorites.length?favorites.map(p=>p.title).join(' · '):'Guarda tus calas para compararlas';root.querySelector('#summary-favorites-names').title=favorites.map(p=>p.title).join(', ');
  root.querySelector('#summary-favorites').disabled=practice;root.querySelector('#summary-coast').disabled=practice;root.querySelector('#summary-next-view').disabled=practice;edit.disabled=practice;root.querySelector('#summary-practice').hidden=!practice;
  renderWeather();
 }
 function renderWeather(){const data=api.weather(),out=root.querySelector('#summary-weather'),key=JSON.stringify(data);if(key===weatherKey)return;weatherKey=key;
  if(!data){out.innerHTML='<span>Consulta el viento, las rachas y las olas.</span>';return;}
  out.innerHTML=`<span class="summary-weather-values">Viento ${beaufortMarkup(data.sample.windSpeed,{compact:true})} · Rachas ${beaufortMarkup(data.sample.windGust,{compact:true,gust:true})} · Olas ${Number.isFinite(data.sample.waveHeight)?number(data.sample.waveHeight)+' m':'No disponible'}</span><small>${esc(data.title)} · ${stamp(data.sample.time*1000)} · Open-Meteo</small><small>Consulta ${stamp(data.fetchedAt)}${data.stale?' · actualiza para consultar de nuevo':''}</small>`;
 }
 position();return {render,renderWeather,reset(){select(0);weatherKey='';renderWeather();},getIndex:()=>index,destroy(){observer.disconnect();cancelAnimationFrame(frame);cancelAnimationFrame(resizeFrame);}};
}
