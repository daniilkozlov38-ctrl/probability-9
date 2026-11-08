(() => {
  const model=window.ConditionalGeometry,NS='http://www.w3.org/2000/svg';
  if(!model)return;
  for(const lab of document.querySelectorAll('[data-geometry-lab]')){
    const svg=lab.querySelector('[data-geometry-board]');let state={...model.defaults},gesture=null;
    const el=(tag,attrs,parent=svg,text)=>{const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;parent.append(n);return n;};
    el('title',{},svg,'Вероятности по числу равновероятных исходов');
    const cells=el('g',{'class':'geometry-cells'});
    for(let r=0;r<10;r++)for(let c=0;c<10;c++){
      const w=model.counts[r][c],n=el('rect',{x:c*50,y:r*50,width:50,height:50,fill:`rgba(187,121,72,${.03+w*.027})`,stroke:'#e2d5c7','stroke-width':1},cells);
      el('title',{},n,`Строка ${r+1}, столбец ${c+1}: ${w} элементарных исходов`);
    }
    const a=el('rect',{'class':'geometry-band geometry-band-a','data-drag':'a-move'});
    const b=el('rect',{'class':'geometry-band geometry-band-b','data-drag':'b-move'});
    const intersection=el('rect',{'class':'geometry-intersection','pointer-events':'none'});
    const numbers=el('g',{'class':'geometry-numbers','pointer-events':'none'});
    for(let r=0;r<10;r++)for(let c=0;c<10;c++)el('text',{x:c*50+25,y:r*50+26},numbers,model.counts[r][c]);
    const frame=el('rect',{x:0,y:0,width:500,height:500,rx:2,fill:'none',stroke:'#a58b74','stroke-width':2,'pointer-events':'none'});
    const handles={};
    for(const kind of ['a-start','a-end','b-start','b-end']){
      const g=el('g',{'class':'geometry-handle','data-drag':kind,'aria-hidden':'true'});
      const line=el('line',{},g),circle=el('circle',{r:10},g);handles[kind]={line,circle};
    }
    const aTag=el('text',{'class':'geometry-band-label','data-drag':'a-move','text-anchor':'middle'},svg,'A');
    const bTag=el('text',{'class':'geometry-band-label','data-drag':'b-move','text-anchor':'middle'},svg,'B');
    const aCount=el('tspan',{'class':'geometry-event-count'},aTag);
    const bCount=el('tspan',{'class':'geometry-event-count'},bTag);
    const set=(n,attrs)=>{for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);};
    const fmt=x=>x.toLocaleString('ru-RU',{maximumFractionDigits:4});
    function render(){
      state=model.normalize(state);const m=model.measure(state),ay=state.aStart*50,ah=state.aSize*50,bx=state.bStart*50,bw=state.bSize*50;
      set(a,{x:0,y:ay,width:500,height:ah});set(b,{x:bx,y:0,width:bw,height:500});set(intersection,{x:bx,y:ay,width:bw,height:ah});
      set(aTag,{x:-23,y:ay+ah/2-7,'aria-label':`A: ${m.a} элементарных исходов`});
      set(aCount,{x:-23,dy:22});aCount.textContent=m.a;
      set(bTag,{x:bx+bw/2,y:-25,'aria-label':`B: ${m.b} элементарных исходов`});
      set(bCount,{x:bx+bw/2,dy:19});bCount.textContent=m.b;
      for(const [kind,h]of Object.entries(handles)){
        const isA=kind[0]==='a',p=isA?(kind.endsWith('start')?ay:ay+ah):(kind.endsWith('start')?bx:bx+bw);
        set(h.line,isA?{x1:0,x2:500,y1:p,y2:p}:{x1:p,x2:p,y1:0,y2:500});set(h.circle,isA?{cx:-16,cy:p}:{cx:p,cy:516});
      }
      for(const input of lab.querySelectorAll('[data-geometry-input]')){
        const key=input.dataset.geometryInput;input.max=key==='aStart'?10-state.aSize:key==='bStart'?10-state.bSize:10;input.value=state[key];input.disabled=Number(input.max)===0;
        lab.querySelector(`[data-geometry-value="${key}"]`).value=state[key];
      }
      lab.querySelector('[data-geometry-total]').textContent=m.total;
      for(const [name,count,prob]of [['pa',m.a,m.pa],['pb',m.b,m.pb],['pab',m.ab,m.pab]])lab.querySelector(`[data-geometry-${name}]`).value=`${count} / ${m.total} = ${fmt(prob)}`;
      lab.querySelector('[data-geometry-conditional]').value=m.conditional===null?'не определена':`${m.ab} / ${m.b} = ${fmt(m.conditional)}`;
      lab.querySelector('[data-geometry-ratio]').style.width=`${(m.conditional??0)*100}%`;
      lab.querySelector('[data-geometry-explanation]').textContent=m.conditional===null?'В условии B нет исходов. Их число равно нулю — делить на него нельзя.':`Внутри B всего ${m.b} элементарных исходов. Из них ${m.ab} находятся также в A: это ${fmt(m.conditional*100)}% исходов условия.`;
      lab.dataset.aCount=m.a;lab.dataset.bCount=m.b;lab.dataset.intersectionCount=m.ab;lab.dataset.conditional=m.conditional===null?'undefined':String(m.conditional);
    }
    for(const input of lab.querySelectorAll('[data-geometry-input]'))input.addEventListener('input',()=>{state[input.dataset.geometryInput]=Number(input.value);render();});
    lab.querySelector('[data-geometry-reset]').addEventListener('click',()=>{state={...model.defaults};render();});
    const point=e=>{const p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;return p.matrixTransform(svg.getScreenCTM().inverse());};
    svg.addEventListener('pointerdown',e=>{
      if(e.button!==0)return;const hit=e.target.closest('[data-drag]');if(!hit)return;e.preventDefault();
      gesture={kind:hit.dataset.drag,p:point(e),state:{...state},pointerId:e.pointerId};svg.setPointerCapture(e.pointerId);
    });
    svg.addEventListener('pointermove',e=>{
      if(!gesture||e.pointerId!==gesture.pointerId)return;const p=point(e),g=gesture,s=g.state;
      const d=Math.round((g.kind[0]==='a'?p.y-g.p.y:p.x-g.p.x)/50),isA=g.kind[0]==='a',start=isA?'aStart':'bStart',size=isA?'aSize':'bSize';state={...s};
      if(g.kind.endsWith('move'))state[start]=Math.max(0,Math.min(10-s[size],s[start]+d));
      else if(g.kind.endsWith('start')){const boundary=Math.max(0,Math.min(s[start]+s[size],s[start]+d));state[start]=boundary;state[size]=s[start]+s[size]-boundary;}
      else state[size]=Math.max(0,Math.min(10-s[start],s[size]+d));
      render();
    });
    const release=e=>{if(gesture?.pointerId===e.pointerId)gesture=null;};
    svg.addEventListener('pointerup',release);svg.addEventListener('pointercancel',release);svg.addEventListener('lostpointercapture',release);
    render();
  }
})();
