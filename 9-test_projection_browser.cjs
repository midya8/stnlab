'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{spawn,execFileSync}=require('node:child_process'),{waitForDebugger}=require('./chrome_support.cjs');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function compare(a,b,p='root'){assert.equal(typeof a,typeof b,p);if(typeof a==='number')assert.ok(Number.isFinite(b)&&Math.abs(a-b)<=1e-5*Math.max(1,Math.abs(a),Math.abs(b)),p+' expected '+a+' actual '+b);else if(a===null||typeof a!=='object')assert.equal(a,b,p);else{assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort(),p);for(const k of Object.keys(a))compare(a[k],b[k],p+'.'+k);}}
test('actual Chrome projected bounds, every original lift and naive-deletion counterexample',{timeout:180000},async()=>{
 const server=require('node:http').createServer((req,res)=>{try{const file=path.join(__dirname,'../docs',req.url==='/'?'index.html':req.url);const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json'};res.setHeader('Content-Type',types[path.extname(file)]||'text/plain');res.end(fs.readFileSync(file));}catch(e){res.statusCode=404;res.end('not found');}});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const profile=fs.mkdtempSync(path.join(os.tmpdir(),'stninsert-')),browser=spawn(process.env.CHROME_BIN||'google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-extensions','--disable-dev-shm-usage','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:['ignore','ignore','pipe']});let ws,startupError,diagnostics='';browser.on('error',e=>startupError=e);browser.stderr.on('data',d=>diagnostics=(diagnostics+d).slice(-4000));
 try{for(let i=0;i<1200&&!startupError&&browser.exitCode===null&&!fs.existsSync(path.join(profile,'DevToolsActivePort'));i++)await delay(25);assert.ok(fs.existsSync(path.join(profile,'DevToolsActivePort')),startupError?.message||diagnostics||'Chrome unavailable');const port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0],tab=await waitForDebugger(`http://127.0.0.1:${port}/json/list`,{alive:()=>browser.exitCode===null&&!startupError});ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej;});let seq=0;const pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){const {res,rej}=pending.get(m.id);pending.delete(m.id);m.error?rej(Error(JSON.stringify(m.error))):res(m.result);}};const call=(method,params={})=>new Promise((res,rej)=>{const id=++seq;pending.set(id,{res,rej});ws.send(JSON.stringify({id,method,params}));});const js=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 await call('Page.enable');await call('Page.navigate',{url:process.env.STN_PROJECTION_URL||`http://127.0.0.1:${server.address().port}/projection.html`});for(let i=0;i<500;i++){if(await js('Boolean(window.stnProjectionReport)'))break;await delay(20)}assert.ok(await js('window.stnProjectionReport'));






 const controls=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/projection-controls.json'),'utf8')),reports=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c','import json,sys;from stnlab.projection import analyze;print(json.dumps([analyze(c["input"])for c in json.load(sys.stdin)]))'],{input:JSON.stringify(controls),maxBuffer:48*1024*1024}));
 const set=async(id,value,event='change')=>js(`document.getElementById(${JSON.stringify(id)}).value=${JSON.stringify(String(value))};document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event(${JSON.stringify(event)}))`),text=id=>js(`document.getElementById(${JSON.stringify(id)}).textContent`),rows=id=>js(`Array.from(document.querySelectorAll('#${id} tr'),r=>Array.from(r.children,c=>c.textContent))`),overflow=async()=>assert.equal(await js('document.documentElement.scrollWidth>innerWidth'),false);
 const edge=(e,k)=>`C${k}: t${e[1]} - t${e[0]} ≤ ${e[2]}`,schedule=t=>t.map((x,i)=>`t${i}=${x}`).join(' · '),ids=p=>p.length?p.map(k=>'C'+k).join(' → '):'empty path',bound=x=>x===null?'∞':String(x);let pairs=0,lost=0,accepted=0,rejected=0,cycles=0;
 for(const width of [320,390,1280]){await call('Emulation.setDeviceMetricsOverride',{width,height:1200,deviceScaleFactor:1,mobile:width<700});for(let k=0;k<controls.length;k++){
  await set('control',k);const r=reports[k],{base,keep,values}=r.input,es=base.edges;assert.deepEqual(await js('window.stnProjectionReport'),r);assert.deepEqual(JSON.parse(await js('document.getElementById("report").value')),r);assert.equal(await text('note'),controls[k].description);assert.equal(await js('document.getElementById("failure").hidden'),r.consistent);assert.equal(await js('document.getElementById("success").hidden'),!r.consistent);assert.deepEqual(await rows('input-rows'),es.map((e,i)=>['C'+i,edge(e,i),String(e[2])]));const pathRows=async(id,p)=>assert.deepEqual(await rows(id),(p||[]).map(i=>['C'+i,edge(es[i],i),String(es[i][2])]));
  if(!r.consistent){const c=r.negative_cycle;assert.equal(await text('cycle-proof'),`Original negative cycle: ${ids(c.edges)}
Sum of left sides: 0
Sum of weights: ${c.weight}
Required: 0 ≤ ${c.weight}
Contradiction.`);await pathRows('cycle-rows',c.edges);if(width===390)cycles++;}
  else{for(const [id,m]of [['matrix',r.matrix],['naive-matrix',r.naive_matrix]])assert.deepEqual(await js(`Array.from(document.querySelectorAll('#${id} tbody tr'),r=>Array.from(r.children,c=>c.textContent))`),m.map((row,i)=>['t'+keep[i],...row.map(bound)]));assert.deepEqual(await rows('projected-rows'),r.projected_edges.map(([u,v,w])=>['t'+u,'t'+v,String(w)]));assert.equal(await text('projection-rule'),`Exact projection: original closure restricted to keep × keep.
Original IDs retained; no renumbering.
${r.projected_edges.length} finite off-diagonal projected constraints.
Full original feasible schedule
${schedule(r.schedule)}`);const fixed=keep.map((u,i)=>`t${u}=${values[i]}`).join(' · '),q=r.query;assert.equal(await js('document.getElementById("query-lift").hidden'),!q.accepted);
   if(q.accepted){assert.equal(await text('query-proof'),`Retained assignment
${fixed}
Complete original-network extension
${schedule(q.extension)}`);assert.equal(await text('query-slacks'),'ALL ORIGINAL CONSTRAINT SLACKS\n'+es.map(([u,v,w],i)=>`C${i}: ${w-(q.extension[v]-q.extension[u])}`).join('\n'));assert.deepEqual(await js('Array.from(document.querySelectorAll("#timeline text")).slice(0,-1).map(t=>t.textContent)'),q.extension.flatMap((x,i)=>['t'+i,String(x)]));if(width===390)accepted++;}
   else{const v=q.violation,f=Object.fromEntries(keep.map((u,i)=>[u,values[i]]));assert.equal(await text('query-proof'),`Retained assignment
${fixed}
Required t${v.v} - t${v.u} ≤ ${v.bound}
Actual difference: ${v.actual}
Original path: ${ids(v.path)}
Pinned cycle: path + t${v.v} → t0 + t0 → t${v.u}
Weights: ${v.bound} + ${-f[v.v]} + ${f[v.u]} = ${v.cycle_weight}
Required: 0 ≤ ${v.cycle_weight}
No extension.`);await pathRows('query-rows',v.path);if(width===390)rejected++;}
   assert.equal(await js('document.getElementById("loss-block").hidden'),r.naive_equivalent);for(let i=0;i<r.lost.length;i++){await set('loss',i);const q=r.lost[i];assert.equal(await text('loss-proof'),`t${q.v} - t${q.u}
Exact projected bound: ${q.bound}
Naive induced bound: ${bound(q.naive_bound)}
Original path: ${ids(q.path)}
Naive-valid retained counterexample
${keep.map((u,i)=>`t${u}=${q.values[i]}`).join(' · ')}
Actual difference: ${q.actual} > ${q.bound}`);await pathRows('loss-rows',q.path);await overflow();if(width===390)lost++;}
   for(let i=0;i<r.pairs.length;i++){await set('pair',i);const q=r.pairs[i];if(q.bound!==null){assert.equal(await text('pair-proof'),`t${q.v} - t${q.u} ≤ ${q.bound}
Original path: ${ids(q.path)}
Full attaining schedule
${schedule(q.schedule)}
Attained difference: ${q.schedule[q.v]-q.schedule[q.u]}`);assert.equal(await text('pair-slacks'),'ALL ORIGINAL CONSTRAINT SLACKS\n'+es.map(([u,v,w],i)=>`C${i}: ${w-(q.schedule[v]-q.schedule[u])}`).join('\n'))}else{assert.equal(await text('pair-proof'),`t${q.v} - t${q.u} is unbounded above.
Full base schedule
${schedule(r.schedule)}
Full anchored ray
${schedule(q.ray)}
Ray difference: ${q.ray[q.v]-q.ray[q.u]}`);assert.equal(await text('pair-slacks'),'ALL ORIGINAL EDGE RAY DIFFERENCES\n'+es.map(([u,v],i)=>`C${i}: ${q.ray[v]-q.ray[u]} ≤ 0`).join('\n'))}await pathRows('path-rows',q.path);await overflow();if(width===390)pairs++;}
  }await overflow();
 }}
 await set('input','{}','input');assert.equal(await js('window.stnProjectionReport'),null);assert.equal(await js('document.getElementById("output").hidden'),true);assert.equal(await js('document.getElementById("download").disabled'),true);await js('document.getElementById("run").click()');assert.match(await text('error'),/exactly/);await set('control',0);await js('HTMLAnchorElement.prototype.click=function(){window.downloaded={name:this.download,url:this.href}};URL.revokeObjectURL=function(){}');await js('document.getElementById("download").click()');assert.deepEqual(await js('fetch(downloaded.url).then(r=>r.json())'),reports[0]);assert.equal(await js('downloaded.name'),'stnlab-projection-report.json');
 if(process.env.STN_PROJECTION_SCREEN_DIR){for(const [name,k,width,pairIndex]of [['320',0,320,1],['390',0,390,1],['1280',0,1280,1],['rejected',1,390,1],['joint-conflict',2,390,5],['hidden-conflict',3,390,0],['anchor-only',4,390,0],['all-kept',5,390,2],['unbounded',6,390,1],['duplicates',7,390,1],['long-chain',8,390,1],['maximum',9,390,2],['single',10,390,0],['self-cycle',11,390,0]]){await call('Emulation.setDeviceMetricsOverride',{width,height:1200,deviceScaleFactor:1,mobile:width<700});await set('control',k);if(reports[k].consistent)await set('pair',pairIndex);await js('document.activeElement.blur();window.scrollTo(0,0);new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');const m=await call('Page.getLayoutMetrics'),image=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:m.cssContentSize.height,scale:1}});fs.writeFileSync(path.join(process.env.STN_PROJECTION_SCREEN_DIR,name+'.png'),Buffer.from(image.data,'base64'));}}
 console.log(JSON.stringify({controls:controls.length,pairs,lost,accepted,rejected,cycles,widths:[320,390,1280]}));
 }finally{server.close();if(ws)ws.close();if(browser.pid&&browser.exitCode===null){browser.kill('SIGTERM');await new Promise(r=>browser.once('exit',r));}await fs.promises.rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:200})}
});
