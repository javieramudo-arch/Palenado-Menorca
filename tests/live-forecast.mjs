// Read-only probe of the actual providers. No user account or diary data.
import {fetchForecast} from '../forecast.js';
try{const f=await fetchForecast([39.93168,3.91459],{signal:AbortSignal.timeout(20000)});console.log('REAL_FORECAST',JSON.stringify({status:'response',time:f.time,temperature:f.temperature,windSpeed:f.windSpeed,windDirection:f.windDirection,waveHeight:f.waveHeight,waveDirection:f.waveDirection,marinePoint:f.marinePoint,partial:f.partial}));}catch(error){console.log('REAL_FORECAST',JSON.stringify({status:'unavailable',reason:error.message}));}
