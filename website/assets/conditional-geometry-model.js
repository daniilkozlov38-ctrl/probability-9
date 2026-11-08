/* Pure finite probability model, shared by the illustration and its tests. */
(function(root){
  const N=10;
  const counts=Array.from({length:N},(_,r)=>Array.from({length:N},(_,c)=>1+(r+c)%3+((r<5)===(c<5)?5:0)));
  const defaults={aStart:1,aSize:4,bStart:5,bSize:3};
  function normalize(state){
    const clamp=x=>Math.max(0,Math.min(N,Math.round(Number(x)||0)));
    const aSize=clamp(state.aSize),bSize=clamp(state.bSize);
    return {aSize,bSize,aStart:Math.min(clamp(state.aStart),N-aSize),bStart:Math.min(clamp(state.bStart),N-bSize)};
  }
  function measure(input){
    const s=normalize(input);let total=0,a=0,b=0,ab=0;
    for(let r=0;r<N;r++)for(let c=0;c<N;c++){
      const w=counts[r][c],inA=r>=s.aStart&&r<s.aStart+s.aSize,inB=c>=s.bStart&&c<s.bStart+s.bSize;
      total+=w;if(inA)a+=w;if(inB)b+=w;if(inA&&inB)ab+=w;
    }
    return {...s,total,a,b,ab,pa:a/total,pb:b/total,pab:ab/total,conditional:b?ab/b:null};
  }
  const api={N,counts,defaults,normalize,measure};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.ConditionalGeometry=api;
})(typeof window==='undefined'?globalThis:window);
