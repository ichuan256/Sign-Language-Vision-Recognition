// Exercise the actual page script without a browser, camera, or board.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(__dirname+'/demo_control.html','utf8').split('<script>')[1].split('</script>')[0];
const settle=()=>new Promise(resolve=>setImmediate(()=>setImmediate(resolve)));
const response=(status,value)=>({ok:status>=200&&status<300,status,text:async()=>typeof value==='string'?value:JSON.stringify(value)});
const hang=options=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(Object.assign(Error('aborted'),{name:'AbortError'})),{once:true}));
const state=busy=>({mode:'camera',busy,connected:true,title:'USB',message:'运行中',details:{},preview_time:null});
async function page(fetch){
 const elements=new Map();
 const element=()=>({style:{},classList:{toggle(){},remove(){}},disabled:false,value:'0',dataset:{}});
 const buttons=['av','camera','sd_teacher','idle'].map(mode=>Object.assign(element(),{dataset:{mode}}));
 const document={getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id)},querySelectorAll(){return buttons}};
 const context=vm.createContext({document,fetch,AbortController,Date,JSON,Number,Error,
  setTimeout:(fn,ms)=>setTimeout(fn,Math.min(ms,20)),clearTimeout,setInterval:()=>0});
 vm.runInContext(source,context);await settle();return {context,buttons,elements};
}
async function main(){
 {
  let posts=0;
  const p=await page(async(url,options)=>{
   if(url==='/api/switch'){posts++;return hang(options)}
   return response(200,state(false));
  });
  await p.context.switchMode('av');await settle();
  assert.equal(posts,1,'An uncertain timed-out POST must not be resubmitted');
  assert(p.buttons.every(b=>!b.disabled),'Timed-out switch must release buttons');
  assert.match(p.elements.get('error').textContent,/超时/);
 }
 {
  let stalled=false,reads=0;
  const p=await page(async(url,options)=>{reads++;return stalled?hang(options):response(200,state(true))});
  assert(p.buttons.every(b=>b.disabled));stalled=true;const before=reads;
  await Promise.all([p.context.poll(),p.context.poll()]);
  assert.equal(reads,before+1,'Status polls must not overlap');
  assert(p.buttons.every(b=>!b.disabled),'Unavailable status must not leave stale busy buttons');
 }
 for(const forbidden of [false,true]){
  const headers=[],bodies=[];
  const p=await page(async(url,options)=>{
   if(url==='/')return response(200,"const token='replacement-session';");
   if(url==='/api/switch'){
    headers.push(options.headers['X-Session']);bodies.push(options.body);
    return response(forbidden||headers.length===1?403:202,{accepted:true});
   }
   return response(200,state(false));
  });
  await p.context.switchMode('sd_teacher');await settle();
  assert.deepEqual(headers,['__SESSION__','replacement-session']);
  assert.equal(bodies[0],bodies[1],'Session renewal must preserve the selected action');
  assert(p.buttons.every(b=>!b.disabled),'Session rejection must not freeze buttons');
 }
 {
  const digitState=state(false);digitState.details={digit_recognition:{value:3,stable:true,reason:'已识别',speech:{ready:true,error:null}}};
  const p=await page(async()=>response(200,digitState));
  assert.equal(p.elements.get('signLabel').textContent,'3');
  assert.equal(p.elements.get('signPanel').hidden,false);
  assert.equal(p.elements.get('signHelp').hidden,true);
 }
 console.log('5 frontend cases passed');
}
main().catch(error=>{console.error(error);process.exitCode=1});
