const assert=require('node:assert/strict');
const model=require('../assets/conditional-geometry-model.js');
let cases=0;
for(let ah=0;ah<=10;ah++)for(let ay=0;ay<=10-ah;ay++)for(let bw=0;bw<=10;bw++)for(let bx=0;bx<=10-bw;bx++){
 const state={aStart:ay,aSize:ah,bStart:bx,bSize:bw},m=model.measure(state);
 let total=0,a=0,b=0,ab=0;
 model.weights.forEach((row,r)=>row.forEach((w,c)=>{
  total+=w;const ia=r>=ay&&r<ay+ah,ib=c>=bx&&c<bx+bw;
  if(ia)a+=w;if(ib)b+=w;if(ia&&ib)ab+=w;
 }));
 assert.equal(m.total,total);assert.equal(m.a,a);assert.equal(m.b,b);assert.equal(m.ab,ab);
 assert(m.pa>=0&&m.pa<=1&&m.pb>=0&&m.pb<=1&&m.pab<=Math.min(m.pa,m.pb));
 if(!b)assert.equal(m.conditional,null);else assert.equal(m.conditional,ab/b);
 cases++;
}
const left=model.measure({...model.defaults,bStart:0}),right=model.measure({...model.defaults,bStart:7});
assert.equal(left.pa,right.pa);assert.notEqual(left.conditional,right.conditional);
const whole=model.measure({aStart:0,aSize:10,bStart:0,bSize:10});assert.equal(whole.conditional,1);
assert.equal(model.measure({aStart:0,aSize:0,bStart:0,bSize:10}).conditional,0);
assert.deepEqual(model.normalize({aStart:100,aSize:100,bStart:-3,bSize:-1}),{aStart:0,aSize:10,bStart:0,bSize:0});
console.log(`Passed ${cases} finite stripe configurations, nonuniform conditional probabilities and zero-weight conditions.`);
