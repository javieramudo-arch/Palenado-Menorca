// Beaufort lower bounds in m/s: Meteocat, Escala Beaufort.
// https://www.meteo.cat/wpweb/divulgacio/la-prediccio-meteorologica/escales-de-vent-i-mar/escala-beaufort/
// The provider stays in km/h internally; classify the unrounded velocity.
export const beaufortMinMs=Object.freeze([0,.3,1.6,3.4,5.5,8,10.8,13.9,17.2,20.8,24.5,28.5,32.7]);
export const beaufortMinKmh=Object.freeze(beaufortMinMs.map(v=>Number((v*3.6).toFixed(3))));
export function toBeaufort(kmh){if(typeof kmh!=='number'||!Number.isFinite(kmh)||kmh<0)return null;let force=0;while(force<12&&kmh>=beaufortMinKmh[force+1])force++;return force;}
export function beaufortColor(force){return !Number.isInteger(force)||force<0||force>12?'#879a9f':force<=2?'#7cff00':force<=4?'#ff7900':'#ff6347';}
export function beaufortText(kmh,{compact=false}={}){const force=toBeaufort(kmh);return force===null?'No disponible':compact?`${force} Bft`:`Fuerza ${force} · Beaufort`;}
export function beaufortMarkup(kmh,{compact=false,gust=false}={}){const force=toBeaufort(kmh),title=gust?'Racha: equivalencia de velocidad en Beaufort':'Viento previsto en escala Beaufort';return `<span class="bft-value${force===null?' is-missing':''}" data-kind="${gust?'gust':'wind'}"${force===null?'':` data-force="${force}"`} style="--bft-color:${beaufortColor(force)}" title="${title}">${beaufortText(kmh,{compact})}</span>`;}
