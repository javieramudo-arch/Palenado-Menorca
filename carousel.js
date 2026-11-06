export function wrapIndex(index,length){return length>0?((index%length)+length)%length:0;}

// Native scrolling keeps touch inertia and scroll snapping. Inert presentation
// copies provide a complete cycle on either side; actions live on four originals.
export function mountLoopCarousel({track,cards,status}){
 const media=matchMedia('(max-width:1099px)'),before=[],after=[],signatures=[];
 let index=0,width=0,hidden=false,frame=0,restoreFrame=0,timer=0,dragging=false,touching=false,destroyed=false;
 const loop=()=>media.matches&&track.clientWidth>0;
 function copy(card,side,i){
  const node=card.cloneNode(true),ids=new Map();node.classList.remove('summary-card');node.classList.add('summary-copy');node.dataset.carouselCopy=side;node.dataset.carouselIndex=i;node.setAttribute('aria-hidden','true');node.inert=true;node.setAttribute('inert','');
  for(const el of [node,...node.querySelectorAll('[id]')])if(el.id){const id=el.id,unique=`carousel-${side}-${i}-${id}`;ids.set(id,unique);el.dataset.summaryOrigin=id;el.id=unique;}
  for(const el of [node,...node.querySelectorAll('*')]){for(const name of ['aria-labelledby','aria-describedby','aria-controls','for'])if(el.hasAttribute(name))el.setAttribute(name,el.getAttribute(name).split(/\s+/).map(id=>ids.get(id)||id).join(' '));if(el.matches('button,a,input,select,textarea,[tabindex]'))el.tabIndex=-1;}
  return node;
 }
 cards.forEach((card,i)=>{card.dataset.carouselIndex=i;before.push(copy(card,'before',i));after.push(copy(card,'after',i));signatures[i]=card.outerHTML;});
 track.prepend(...before);track.append(...after);
 const nodes=()=>[...before,...cards,...after];
 const offset=node=>node.offsetLeft-before[0].offsetLeft;
 function nearest(){return nodes().reduce((best,node)=>Math.abs(offset(node)-track.scrollLeft)<Math.abs(offset(best)-track.scrollLeft)?node:best,cards[0]);}
 function announce(){status.textContent=loop()?`${index+1} de ${cards.length}`:`${cards.length} resúmenes`;}
 function jump(left){cancelAnimationFrame(restoreFrame);track.classList.add('carousel-rebase');track.scrollTo({left,behavior:'instant'});restoreFrame=requestAnimationFrame(()=>track.classList.remove('carousel-rebase'));}
 function settle(){clearTimeout(timer);if(destroyed||!loop()||dragging)return;const node=nearest();index=Number(node.dataset.carouselIndex);if(node.dataset.carouselCopy){const remainder=track.scrollLeft-offset(node);jump(offset(cards[index])+remainder);}announce();}
 function select(value){clearTimeout(timer);index=wrapIndex(value,cards.length);jump(loop()?offset(cards[index]):0);announce();}
 function layout(){if(!track.clientWidth){hidden=true;return;}if(width===track.clientWidth&&!hidden)return;width=track.clientWidth;hidden=false;select(index);}
 function scheduleLayout(){cancelAnimationFrame(frame);frame=requestAnimationFrame(layout);}
 function scroll(){if(!loop())return;index=Number(nearest().dataset.carouselIndex);announce();clearTimeout(timer);timer=setTimeout(settle,140);}
 function key(event){if(event.target!==track)return;const values={ArrowLeft:index-1,ArrowRight:index+1,Home:0,End:cards.length-1};if(event.key in values){event.preventDefault();select(values[event.key]);}}
 function down(){settle();dragging=true;clearTimeout(timer);}
 function up(){if(touching||!dragging)return;dragging=false;clearTimeout(timer);timer=setTimeout(settle,140);}
 function touchStart(){down();touching=true;}
 function touchEnd(){touching=false;up();}
 function sync(){cards.forEach((card,i)=>{const signature=card.outerHTML;if(signature===signatures[i])return;signatures[i]=signature;for(const[side,list]of [['before',before],['after',after]]){const node=copy(card,side,i);list[i].replaceWith(node);list[i]=node;}});}
 const mutation=new MutationObserver(sync);cards.forEach(card=>mutation.observe(card,{subtree:true,childList:true,attributes:true,characterData:true}));
 const observer=new ResizeObserver(scheduleLayout);observer.observe(track);media.addEventListener('change',scheduleLayout);
 track.addEventListener('scroll',scroll,{passive:true});track.addEventListener('scrollend',settle);track.addEventListener('keydown',key);track.addEventListener('pointerdown',down,{passive:true});track.addEventListener('touchstart',touchStart,{passive:true});window.addEventListener('touchend',touchEnd,{passive:true});window.addEventListener('touchcancel',touchEnd,{passive:true});window.addEventListener('pointerup',up,{passive:true});window.addEventListener('pointercancel',up,{passive:true});
 scheduleLayout();announce();
 return {getIndex:()=>index,reset(){select(0);},destroy(){destroyed=true;clearTimeout(timer);cancelAnimationFrame(frame);cancelAnimationFrame(restoreFrame);observer.disconnect();mutation.disconnect();media.removeEventListener('change',scheduleLayout);track.removeEventListener('scroll',scroll);track.removeEventListener('scrollend',settle);track.removeEventListener('keydown',key);track.removeEventListener('pointerdown',down);track.removeEventListener('touchstart',touchStart);window.removeEventListener('touchend',touchEnd);window.removeEventListener('touchcancel',touchEnd);window.removeEventListener('pointerup',up);window.removeEventListener('pointercancel',up);before.forEach(n=>n.remove());after.forEach(n=>n.remove());track.classList.remove('carousel-rebase');}};
}
