// Presentation-only samples: never upload files or insert records into a user's diary.
export function installDemoImages(){
 const decorate=()=>{for(const input of document.querySelectorAll('input[type="file"][accept*="image"]')){
  if(input.dataset.demoPreview)continue;input.dataset.demoPreview='true';
  const figure=document.createElement('figure');figure.className='demo-upload-preview';figure.innerHTML='<img src="./assets/demo-paddle.webp" alt="Demo: paddle surf en una cala mediterránea" loading="lazy"><figcaption><span class="demo-label">Demo · imagen generada</span><p>Vista de ejemplo. Selecciona una imagen para probar tu fotografía.</p></figcaption>';input.insertAdjacentElement('afterend',figure);
  input.addEventListener('change',()=>{const file=input.files?.[0];if(!file){figure.hidden=false;return;}figure.hidden=true;});
 }};
 decorate();if(typeof MutationObserver==='function')new MutationObserver(decorate).observe(document.body,{childList:true,subtree:true});
}
