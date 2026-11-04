import {landMask} from './wave-field.js?v=0.10.1';
export class CoastViews{
 constructor(onChange=()=>{}){this.stack=['routes'];this.onChange=onChange;}
 get current(){return this.stack.at(-1);}
 get previous(){return this.stack.at(-2)||'routes';}
 enter(view){if(!['routes','pending','zones','adventure'].includes(view))throw Error('Vista desconocida');if(view===this.current)return;if(view==='routes')this.stack=['routes'];else{this.stack.push(view);if(this.stack.length>24)this.stack.splice(1,1);}this.onChange();}
 leave(view=this.current){if(view!==this.current)return;if(this.stack.length>1)this.stack.pop();this.onChange();}
 remove(view){this.stack=this.stack.filter(x=>x!==view);if(!this.stack.length)this.stack=['routes'];this.onChange();}
 reset(){this.stack=['routes'];this.onChange();}
}
// Marine ribbon only: leave a clear gap around the coast and erase every land pixel.
export function mountSeaBands(map,{pane='zoneAnalysis'}={}){const canvas=document.createElement('canvas');canvas.className='coast-sea-bands leaflet-zoom-hide';canvas.setAttribute('aria-hidden','true');canvas.hidden=true;map.getPane(pane).append(canvas);const ctx=canvas.getContext('2d'),isLand=landMask();let data=[],visible=false;
 function draw(){if(!ctx)return;const size=map.getSize(),pos=map.containerPointToLayerPoint([0,0]);canvas.style.left=pos.x+'px';canvas.style.top=pos.y+'px';if(canvas.width!==size.x||canvas.height!==size.y){canvas.width=size.x;canvas.height=size.y;}ctx.clearRect(0,0,canvas.width,canvas.height);if(!visible||!data.length)return;ctx.lineCap='round';ctx.lineJoin='round';const paths=[];for(const item of data){const path=new Path2D();for(const[a,b]of item.segments){const A=map.latLngToContainerPoint(a),B=map.latLngToContainerPoint(b);if(Math.max(A.x,B.x)<-20||Math.min(A.x,B.x)>size.x+20||Math.max(A.y,B.y)<-20||Math.min(A.y,B.y)>size.y+20)continue;path.moveTo(A.x,A.y);path.lineTo(B.x,B.y);}paths.push(path);ctx.strokeStyle=item.color;ctx.lineWidth=28;ctx.globalAlpha=.35;ctx.stroke(path);}ctx.globalCompositeOperation='destination-out';ctx.globalAlpha=1;ctx.lineWidth=9;for(const p of paths)ctx.stroke(p);ctx.globalCompositeOperation='source-over';const pixels=ctx.getImageData(0,0,size.x,size.y),bytes=pixels.data;for(let y=0;y<size.y;y++)for(let x=0;x<size.x;x++){const i=(y*size.x+x)*4;if(!bytes[i+3])continue;const p=map.containerPointToLatLng([x+.5,y+.5]);if(isLand([p.lat,p.lng]))bytes[i+3]=0;}ctx.putImageData(pixels,0,0);}
 map.on('moveend zoomend resize',draw);
 return {setData(next){data=next;draw();},setVisible(value){visible=value;canvas.hidden=!value;draw();},destroy(){map.off('moveend zoomend resize',draw);canvas.remove();}};
}
