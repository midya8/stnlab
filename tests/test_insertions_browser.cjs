'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{spawn,execFileSync}=require('node:child_process'),{waitForDebugger}=require('./chrome_support.cjs');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function compare(a,b,p='root'){assert.equal(typeof a,typeof b,p);if(typeof a==='number')assert.ok(Number.isFinite(b)&&Math.abs(a-b)<=1e-5*Math.max(1,Math.abs(a),Math.abs(b)),p+' expected '+a+' actual '+b);else if(a===null||typeof a!=='object')assert.equal(a,b,p);else{assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort(),p);for(const k of Object.keys(a))compare(a[k],b[k],p+'.'+k);}}
test('actual Chrome insertion thresholds, every closure cell and alternative weight',{timeout:180000},async()=>{
 const server=require('node:http').createServer((req,res)=>{try{const file=path.join(__dirname,'../docs',req.url==='/'?'index.html':req.url);const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json'};res.setHeader('Content-Type',types[path.extname(file)]||'text/plain');res.end(fs.readFileSync(file));}catch(e){res.statusCode=404;res.end('not found');}});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const profile=fs.mkdtempSync(path.join(os.tmpdir(),'stninsert-')),browser=spawn(process.env.CHROME_BIN||'google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-extensions','--disable-dev-shm-usage','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:['ignore','ignore','pipe']});let ws,startupError,diagnostics='';browser.on('error',e=>startupError=e);browser.stderr.on('data',d=>diagnostics=(diagnostics+d).slice(-4000));
 try{for(let i=0;i<1200&&!startupError&&browser.exitCode===null&&!fs.existsSync(path.join(profile,'DevToolsActivePort'));i++)await delay(25);assert.ok(fs.existsSync(path.join(profile,'DevToolsActivePort')),startupError?.message||diagnostics||'Chrome unavailable');const port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0],tab=await waitForDebugger(`http://127.0.0.1:${port}/json/list`,{alive:()=>browser.exitCode===null&&!startupError});ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej;});let seq=0;const pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){const {res,rej}=pending.get(m.id);pending.delete(m.id);m.error?rej(Error(JSON.stringify(m.error))):res(m.result);}};const call=(method,params={})=>new Promise((res,rej)=>{const id=++seq;pending.set(id,{res,rej});ws.send(JSON.stringify({id,method,params}));});const js=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 await call('Page.enable');await call('Page.navigate',{url:process.env.STN_INSERT_URL||`http://127.0.0.1:${server.address().port}/insertions.html`});for(let i=0;i<500;i++){if(await js('Boolean(window.stnInsertionReport)'))break;await delay(20)}assert.ok(await js('window.stnInsertionReport'));





 const controls=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/insertion-controls.json'),'utf8')),reports=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c','import json,sys;from stnlab.insertions import analyze;print(json.dumps([analyze(c["input"]) for c in json.load(sys.stdin)]))'],{input:JSON.stringify(controls),maxBuffer:48*1024*1024}));
 const set=async(id,value,event='change')=>js(`document.getElementById(${JSON.stringify(id)}).value=${JSON.stringify(String(value))};document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event(${JSON.stringify(event)}))`),text=id=>js(`document.getElementById(${JSON.stringify(id)}).textContent`),rows=id=>js(`Array.from(document.querySelectorAll('#${id} tr'),r=>Array.from(r.children,c=>c.textContent))`),overflow=async()=>assert.equal(await js('document.documentElement.scrollWidth>innerWidth'),false);
 const edge=(e,k)=>`C${k}: t${e[1]} - t${e[0]} ≤ ${e[2]}`,schedule=t=>t.map((x,i)=>`t${i}=${x}`).join(' · '),ids=p=>p.length?p.map(k=>'C'+k).join(' → '):'empty path',bound=x=>x===null?'∞':String(x);
 const counts={controls:controls.length,cells:0,changed:0,finite:0,rays:0,thresholds:0,spectrum:0,cycles:0};
 for(const width of [320,390,1280]){await call('Emulation.setDeviceMetricsOverride',{width,height:1200,deviceScaleFactor:1,mobile:width<700});for(let k=0;k<controls.length;k++){
  await set('control',k);const r=reports[k],es=[...r.input.base.edges,r.input.candidate],m=es.length-1,[a,b,w]=r.input.candidate;assert.deepEqual(await js('window.stnInsertionReport'),r);assert.deepEqual(JSON.parse(await js('document.getElementById("report").value')),r);assert.equal(await js('document.getElementById("failure").hidden'),r.consistent);assert.equal(await js('document.getElementById("success").hidden'),!r.consistent);assert.equal(await js('document.getElementById("threshold-block").hidden'),!r.base_consistent);assert.equal(await js('document.getElementById("spectrum-block").hidden'),!r.base_consistent);
  assert.deepEqual(await rows('input-rows'),es.map((e,i)=>['C'+i+(i===m?' (new)':''),edge(e,i),String(e[2])]));
  if(r.base_consistent){const t=r.threshold;assert.equal(await text('threshold-proof'),t.lower===null?`Old return D[${b},${a}]: ∞
No old return path.
No finite lower threshold: every real candidate weight is feasible.
Redundant at or above: ${bound(t.redundant_at)}`:`Old return D[${b},${a}]: ${-t.lower}
Return path: ${ids(t.return_path)}
Exact feasible weights: w ≥ ${t.lower}
Redundant at or above: ${bound(t.redundant_at)}
Complete schedule at w=${t.lower}
${schedule(t.boundary_schedule)}
At w=${t.below_cycle.candidate_weight}: C${m} then return path sum to -1.`);
   assert.deepEqual(await rows('threshold-rows'),(t.return_path||[]).map(i=>['C'+i,edge(es[i],i),String(es[i][2])]));assert.deepEqual(await rows('spectrum-rows'),r.spectrum.map(q=>[String(q.weight),q.classification,q.changed===null?'undefined':String(q.changed)]));if(width===390)counts.thresholds++;
   for(const q of r.spectrum){await set('weight',q.weight);assert.equal(await text('weight-proof'),`Alternative candidate weight: ${q.weight}
Classification: ${q.classification}
Changed matrix cells: ${q.changed===null?'not defined for inconsistency':q.changed}
The main proof panels still show weight ${w}.`);await overflow();if(width===390)counts.spectrum++}
  }
  if(!r.consistent){const c=r.cycle;assert.equal(await text('cycle-proof'),`${r.base_consistent?'New-edge':'Pre-existing base'} negative cycle
Edges: ${ids(c.edges)}
Sum of left sides: 0
Sum of weights: ${c.weight}
Required: 0 ≤ ${c.weight}
Contradiction.`);assert.deepEqual(await rows('cycle-rows'),c.edges.map(i=>['C'+i,edge(es[i],i),String(es[i][2])]));if(width===390)counts.cycles++;}
  else{
   assert.deepEqual(await js('Array.from(document.querySelectorAll("#matrix tbody tr"),r=>Array.from(r.children,c=>c.textContent))'),r.matrix.map((row,i)=>['t'+i,...row.map(bound)]));assert.equal(await text('changed-title'),r.cells.filter(q=>q.changed).length+' matrix cells change.');
   for(let j=0;j<r.cells.length;j++){await set('pair',j);const q=r.cells[j],via=q.left_path===null||q.right_path===null?null:[...q.left_path,m,...q.right_path];assert.equal(await text('cell-proof'),`t${q.v} - t${q.u}
Before: ${bound(q.before)}
Old left D[${q.u},${a}]: ${bound(r.base_matrix[q.u][a])}
Candidate weight: ${w}
Old right D[${b},${q.v}]: ${bound(r.base_matrix[b][q.v])}
Via candidate: ${bound(q.via)}
After: min(${bound(q.before)}, ${bound(q.via)}) = ${bound(q.after)}
Changed: ${q.changed?'yes':'no'}`);assert.deepEqual(await rows('via-rows'),via===null?[]:via.map(i=>['C'+i,edge(es[i],i),String(es[i][2])]))
    if(q.after!==null){assert.equal(await text('attaining-proof'),`Shortest simple path: ${ids(q.path)}
Path sum: ${q.after}
Complete attaining schedule
${schedule(q.schedule)}
Selected difference: ${q.schedule[q.v]-q.schedule[q.u]}`);assert.deepEqual(await rows('path-rows'),q.path.map(i=>['C'+i,edge(es[i],i),String(es[i][2])]));assert.equal(await text('slacks'),'ALL POST-INSERTION CONSTRAINT SLACKS\n'+es.map(([u,v,w],i)=>`C${i}: ${w-(q.schedule[v]-q.schedule[u])}`).join('\n'));assert.deepEqual(await js('Array.from(document.querySelectorAll("#timeline text")).slice(0,-1).map(t=>t.textContent)'),q.schedule.flatMap((x,i)=>['t'+i,String(x)]));if(width===390)counts.finite++}
    else{assert.equal(await text('ray-proof'),`No finite post-insertion upper bound.
Complete base schedule
${schedule(r.schedule)}
Anchored ray
${schedule(q.ray)}
Selected ray difference: ${q.ray[q.v]-q.ray[q.u]}
ALL POST-INSERTION EDGE RAY DIFFERENCES
`+es.map(([u,v],i)=>`C${i}: ${q.ray[v]-q.ray[u]} ≤ 0`).join('\n'));if(width===390)counts.rays++}
    if(width===390){counts.cells++;counts.changed+=Number(q.changed)}await overflow();
   }
  }await overflow();
 }}
 await set('input','{}','input');assert.equal(await js('window.stnInsertionReport'),null);assert.equal(await js('document.getElementById("output").hidden'),true);assert.equal(await js('document.getElementById("download").disabled'),true);await js('document.getElementById("run").click()');assert.match(await text('error'),/exactly/);await set('control',0);await js('HTMLAnchorElement.prototype.click=function(){window.downloaded={name:this.download,url:this.href}};URL.revokeObjectURL=function(){}');await js('document.getElementById("download").click()');assert.deepEqual(await js('fetch(downloaded.url).then(r=>r.json())'),reports[0]);assert.equal(await js('downloaded.name'),'stnlab-insertion-report.json');
 if(process.env.STN_INSERT_SCREEN_DIR){for(const [name,k,width,pairIndex]of [['320',0,320,2],['390',0,390,2],['1280',0,1280,2],['boundary',1,390,2],['negative',2,390,0],['redundant',3,390,2],['bridge',4,390,2],['ray',4,390,8],['base-conflict',5,390,0],['self',6,390,0],['duplicate',7,390,1],['long-threshold',8,390,30],['maximum',9,390,5]]){await call('Emulation.setDeviceMetricsOverride',{width,height:1200,deviceScaleFactor:1,mobile:width<700});await set('control',k);if(reports[k].consistent)await set('pair',pairIndex);await set('weight',reports[k].input.candidate[2]);await js('document.activeElement.blur();window.scrollTo(0,0);new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');const m=await call('Page.getLayoutMetrics'),image=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:m.cssContentSize.height,scale:1}});fs.writeFileSync(path.join(process.env.STN_INSERT_SCREEN_DIR,name+'.png'),Buffer.from(image.data,'base64'));}}
 console.log(JSON.stringify({...counts,widths:[320,390,1280]}));
 }finally{server.close();if(ws)ws.close();if(browser.pid&&browser.exitCode===null){browser.kill('SIGTERM');await new Promise(r=>browser.once('exit',r));}await fs.promises.rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:200})}
});
