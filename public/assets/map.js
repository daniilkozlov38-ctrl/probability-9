(() => {
  const stage=document.querySelector('.course-stage');
  if(!stage)return;
  const world=stage.querySelector('.map-world'),svg=world.querySelector('.map-connections'),paths=svg.querySelector('.connection-paths');
  const nodes=[...world.querySelectorAll('.topic-node')],nodeMap=new Map(nodes.map(n=>[n.dataset.topic,n]));
  const edges=JSON.parse(world.dataset.edges),controls=document.querySelector('.map-controls'),switcher=document.querySelector('.view-switch'),output=controls.querySelector('output');
  const mobile=matchMedia('(max-width:760px)'),ports={left:[-1,0],right:[1,0],top:[0,-1],bottom:[0,1]};
  const original=nodes.map(n=>({x:Number(n.dataset.x),y:Number(n.dataset.y)}));
  let camera={x:0,y:0,scale:1},list=false,drawing,dragged=false,gesture;
  const pointers=new Map();
  function paint(){world.style.transform=`translate(${camera.x}px,${camera.y}px) scale(${camera.scale})`;output.value=`${Math.round(camera.scale*100)}%`;}
  function bounds(){
    const boxes=nodes.map(n=>({x:n.offsetLeft,y:n.offsetTop,w:n.offsetWidth,h:n.offsetHeight}));
    const x=Math.min(...boxes.map(b=>b.x)),y=Math.min(...boxes.map(b=>b.y));
    return{x,y,w:Math.max(...boxes.map(b=>b.x+b.w))-x,h:Math.max(...boxes.map(b=>b.y+b.h))-y};
  }
  function fit(){
    const b=bounds(),p=mobile.matches?28:48;
    camera.scale=Math.max(.2,Math.min((stage.clientWidth-p*2)/b.w,(stage.clientHeight-p*2)/b.h,1.15));
    camera.x=(stage.clientWidth-b.w*camera.scale)/2-b.x*camera.scale;
    camera.y=(stage.clientHeight-b.h*camera.scale)/2-b.y*camera.scale;paint();
  }
  function startView(){
    if(!mobile.matches){fit();return;}
    const first=nodes[0];camera.scale=Math.min((stage.clientWidth-64)/first.offsetWidth,1);
    camera.x=(stage.clientWidth-first.offsetWidth*camera.scale)/2-first.offsetLeft*camera.scale;
    camera.y=250-first.offsetTop*camera.scale;paint();
  }
  function zoom(factor,x=stage.clientWidth/2,y=stage.clientHeight/2){
    const next=Math.min(2.2,Math.max(.2,camera.scale*factor)),r=next/camera.scale;
    camera.x=x-(x-camera.x)*r;camera.y=y-(y-camera.y)*r;camera.scale=next;paint();
  }
  function anchor(n,p){const x=n.offsetLeft,y=n.offsetTop,style=getComputedStyle(n),w=Number.parseFloat(style.width),h=Number.parseFloat(style.height);return p==='left'?[x,y+h/2]:p==='right'?[x+w,y+h/2]:p==='top'?[x+w/2,y]:[x+w/2,y+h];}
  function draw(){
    cancelAnimationFrame(drawing);drawing=requestAnimationFrame(()=>{
      if(list)return;paths.replaceChildren();
      for(const e of edges){
        const fp=mobile.matches?'bottom':e.fromPort,tp=mobile.matches?'top':e.toPort;
        const a=anchor(nodeMap.get(e.from),fp),b=anchor(nodeMap.get(e.to),tp),u=ports[fp],v=ports[tp],end=[b[0]+v[0]*4,b[1]+v[1]*4];
        const bend=Math.min(170,Math.max(45,Math.hypot(b[0]-a[0],b[1]-a[1])*.42));
        const line=document.createElementNS('http://www.w3.org/2000/svg','path');line.dataset.from=e.from;line.dataset.to=e.to;
        line.setAttribute('d',`M ${a[0]} ${a[1]} C ${a[0]+u[0]*bend} ${a[1]+u[1]*bend}, ${end[0]+v[0]*bend} ${end[1]+v[1]*bend}, ${end[0]} ${end[1]}`);
        line.setAttribute('marker-end','url(#arrowhead)');paths.append(line);
      }
    });
  }
  function layout(){
    const w=mobile.matches?420:1500,h=mobile.matches?1550:1000;world.style.width=`${w}px`;world.style.height=`${h}px`;svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
    nodes.forEach((n,i)=>{n.style.setProperty('--x',`${mobile.matches?65:original[i].x}px`);n.style.setProperty('--y',`${mobile.matches?250+i*235:original[i].y}px`);});
    draw();if(!list)startView();
  }
  function setView(view){list=view==='list';document.body.classList.toggle('is-list',list);for(const b of switcher.querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.dataset.view===view));stage.scrollTop=0;if(!list)requestAnimationFrame(layout);try{sessionStorage.setItem('course-view',view);}catch{}}
  switcher.hidden=false;controls.hidden=false;
  switcher.addEventListener('click',e=>{const b=e.target.closest('button[data-view]');if(b)setView(b.dataset.view);});
  controls.addEventListener('click',e=>{const a=e.target.closest('button')?.dataset.mapControl;if(a==='fit')fit();else if(a==='zoom-in')zoom(1.2);else if(a==='zoom-out')zoom(1/1.2);});
  stage.addEventListener('wheel',e=>{if(list)return;e.preventDefault();const r=stage.getBoundingClientRect();zoom(Math.exp(-e.deltaY*.0015),e.clientX-r.left,e.clientY-r.top);},{passive:false});
  stage.addEventListener('pointerdown',e=>{
    if(list||e.button!==0)return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(pointers.size===1){gesture={startX:e.clientX,startY:e.clientY,camera:{...camera}};dragged=false;}
    if(pointers.size===2){const[a,b]=[...pointers.values()];gesture={distance:Math.hypot(a.x-b.x,a.y-b.y),midX:(a.x+b.x)/2,midY:(a.y+b.y)/2,camera:{...camera}};dragged=true;}
  });
  window.addEventListener('pointermove',e=>{
    if(!pointers.has(e.pointerId)||!gesture)return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(pointers.size===2){
      const[a,b]=[...pointers.values()],r=stage.getBoundingClientRect(),distance=Math.hypot(a.x-b.x,a.y-b.y),mx=(a.x+b.x)/2-r.left,my=(a.y+b.y)/2-r.top;
      camera.scale=Math.max(.2,Math.min(2.2,gesture.camera.scale*distance/gesture.distance));const ratio=camera.scale/gesture.camera.scale;
      camera.x=mx-(gesture.midX-r.left-gesture.camera.x)*ratio;camera.y=my-(gesture.midY-r.top-gesture.camera.y)*ratio;
    }else if('startX'in gesture){const dx=e.clientX-gesture.startX,dy=e.clientY-gesture.startY;if(Math.hypot(dx,dy)>5)dragged=true;if(!dragged)return;camera.x=gesture.camera.x+dx;camera.y=gesture.camera.y+dy;}else return;
    stage.classList.add('is-dragging');paint();
  });
  const release=e=>{pointers.delete(e.pointerId);if(pointers.size===1){const p=[...pointers.values()][0];gesture={startX:p.x,startY:p.y,camera:{...camera}};}if(!pointers.size){gesture=null;stage.classList.remove('is-dragging');}};
  window.addEventListener('pointerup',release);window.addEventListener('pointercancel',release);
  stage.addEventListener('click',e=>{if(dragged){e.preventDefault();e.stopPropagation();dragged=false;}},true);
  stage.addEventListener('keydown',e=>{
    if(list)return;const d={ArrowLeft:[60,0],ArrowRight:[-60,0],ArrowUp:[0,60],ArrowDown:[0,-60]};
    if(d[e.key]){e.preventDefault();camera.x+=d[e.key][0];camera.y+=d[e.key][1];paint();}
    else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(1.2);}else if(e.key==='-'){e.preventDefault();zoom(1/1.2);}else if(e.key==='0'){e.preventDefault();fit();}
  });
  world.addEventListener('focusin',e=>{if(list||!e.target.matches('.topic-card:focus-visible'))return;const n=e.target.closest('.topic-node');camera.x=stage.clientWidth/2-(n.offsetLeft+n.offsetWidth/2)*camera.scale;camera.y=stage.clientHeight*.6-(n.offsetTop+n.offsetHeight/2)*camera.scale;paint();});
  new ResizeObserver(layout).observe(stage);const observer=new ResizeObserver(draw);nodes.forEach(n=>observer.observe(n));document.fonts.ready.then(layout);
  let saved;try{saved=sessionStorage.getItem('course-view');}catch{}setView(saved==='list'?'list':'graph');
})();
