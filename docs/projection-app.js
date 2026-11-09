import {analyze} from './projection.js';const $=id=>document.getElementById(id),controls=await fetch('./projection-controls.json').then(r=>r.json());let report=null;
const edge=(e,k)=>`C${k}: t${e[1]} - t${e[0]} ≤ ${e[2]}`,schedule=t=>t.map((x,i)=>`t${i}=${x}`).join(' · '),ids=p=>p.length?p.map(k=>'C'+k).join(' → '):'empty path',option=(v,text)=>Object.assign(document.createElement('option'),{value:v,textContent:text}),cell=t=>Object.assign(document.createElement('td'),{textContent:t}),bound=v=>v===null?'∞':String(v);
function rows(id,data){$(id).replaceChildren(...data.map(row=>{const tr=document.createElement('tr');tr.append(...row.map(cell));return tr}))}
function matrix(id,m,keep){const head=document.createElement('thead'),tr=document.createElement('tr');for(const x of ['u → v',...keep.map(i=>'t'+i)])tr.append(Object.assign(document.createElement('th'),{textContent:x}));head.append(tr);const body=document.createElement('tbody');m.forEach((r,i)=>{const tr=document.createElement('tr');tr.append(cell('t'+keep[i]),...r.map(bound).map(cell));body.append(tr)});$(id).replaceChildren(head,body)}
function pathRows(id,p){rows(id,(p||[]).map(k=>['C'+k,edge(report.input.base.edges[k],k),report.input.base.edges[k][2]]))}
const slacks=t=>'ALL ORIGINAL CONSTRAINT SLACKS\n'+report.input.base.edges.map(([u,v,w],i)=>`C${i}: ${w-(t[v]-t[u])}`).join('\n');
function timeline(t){const lo=Math.min(...t)-1,hi=Math.max(...t)+1,n=t.length,height=42+n*34,width=Math.max(300,Math.min(620,$('timeline').clientWidth));const ns='http://www.w3.org/2000/svg',svg=$('timeline');svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.replaceChildren();const node=(name,attrs,text)=>{const e=document.createElementNS(ns,name);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;svg.append(e)};t.forEach((x,i)=>{const y=26+i*34,cx=55+(x-lo)/(hi-lo)*(width-110);node('line',{x1:55,y1:y,x2:width-35,y2:y,stroke:'#c9d1de'});node('text',{x:12,y:y+5,fill:'#14233c','font-size':15},`t${i}`);node('circle',{cx,cy:y,r:5,fill:'#244ed6'});node('text',{x:cx+10,y:y+5,fill:'#a64013','font-size':14},String(x))});node('text',{x:55,y:height-8,fill:'#46556b','font-size':12},'Relative time; t0 = 0.')}

function pair(){const q=report.pairs[+$('pair').value];pathRows('path-rows',q.path);if(q.bound!==null){$('pair-proof').textContent=`t${q.v} - t${q.u} ≤ ${q.bound}
Original path: ${ids(q.path)}
Full attaining schedule
${schedule(q.schedule)}
Attained difference: ${q.schedule[q.v]-q.schedule[q.u]}`;$('pair-slacks').textContent=slacks(q.schedule)}else{$('pair-proof').textContent=`t${q.v} - t${q.u} is unbounded above.
Full base schedule
${schedule(report.schedule)}
Full anchored ray
${schedule(q.ray)}
Ray difference: ${q.ray[q.v]-q.ray[q.u]}`;$('pair-slacks').textContent='ALL ORIGINAL EDGE RAY DIFFERENCES\n'+report.input.base.edges.map(([u,v],i)=>`C${i}: ${q.ray[v]-q.ray[u]} ≤ 0`).join('\n')}}
function loss(){const q=report.lost[+$('loss').value];$('loss-proof').textContent=`t${q.v} - t${q.u}
Exact projected bound: ${q.bound}
Naive induced bound: ${bound(q.naive_bound)}
Original path: ${ids(q.path)}
Naive-valid retained counterexample
${report.input.keep.map((u,i)=>`t${u}=${q.values[i]}`).join(' · ')}
Actual difference: ${q.actual} > ${q.bound}`;pathRows('loss-rows',q.path)}
function run(){try{report=analyze(JSON.parse($('input').value));window.stnProjectionReport=report;$('error').textContent='';$('output').hidden=false;$('download').disabled=false;$('report').value=JSON.stringify(report,null,2);const {base,keep,values}=report.input;$('status').textContent=report.consistent?'The original plan has a solution.':'The original plan is impossible.';$('summary').textContent=`Retained: ${keep.map(i=>'t'+i).join(', ')}
Hidden: ${Array.from({length:base.nodes},(_,i)=>i).filter(i=>!keep.includes(i)).map(i=>'t'+i).join(', ')||'none'}
Original consistent: ${report.consistent?'yes':'no'}`;rows('input-rows',base.edges.map((e,i)=>['C'+i,edge(e,i),e[2]]));$('failure').hidden=report.consistent;$('success').hidden=!report.consistent;if(!report.consistent){const c=report.negative_cycle;$('cycle-proof').textContent=`Original negative cycle: ${ids(c.edges)}
Sum of left sides: 0
Sum of weights: ${c.weight}
Required: 0 ≤ ${c.weight}
Contradiction.`;pathRows('cycle-rows',c.edges);return}
$('projection-rule').textContent=`Exact projection: original closure restricted to keep × keep.
Original IDs retained; no renumbering.
${report.projected_edges.length} finite off-diagonal projected constraints.
Full original feasible schedule
${schedule(report.schedule)}`;matrix('matrix',report.matrix,keep);matrix('naive-matrix',report.naive_matrix,keep);rows('projected-rows',report.projected_edges.map(([u,v,w])=>['t'+u,'t'+v,w]));const q=report.query;$('query-title').textContent=q.accepted?'These retained values extend together.':'These retained values cannot extend.';const fixed=keep.map((u,i)=>`t${u}=${values[i]}`).join(' · ');$('query-lift').hidden=!q.accepted;if(q.accepted){$('query-proof').textContent=`Retained assignment
${fixed}
Complete original-network extension
${schedule(q.extension)}`;pathRows('query-rows',[]);timeline(q.extension);$('query-slacks').textContent=slacks(q.extension)}else{const v=q.violation,lookup=Object.fromEntries(keep.map((u,i)=>[u,values[i]]));$('query-proof').textContent=`Retained assignment
${fixed}
Required t${v.v} - t${v.u} ≤ ${v.bound}
Actual difference: ${v.actual}
Original path: ${ids(v.path)}
Pinned cycle: path + t${v.v} → t0 + t0 → t${v.u}
Weights: ${v.bound} + ${-lookup[v.v]} + ${lookup[v.u]} = ${v.cycle_weight}
Required: 0 ≤ ${v.cycle_weight}
No extension.`;pathRows('query-rows',v.path)}
$('naive-title').textContent=report.naive_equivalent?'Here, naive deletion happens to agree.':`${report.lost.length} ${report.lost.length===1?'bound is':'bounds are'} lost by naive deletion.`;$('loss-block').hidden=report.naive_equivalent;$('no-loss').textContent=report.naive_equivalent?'The two closed matrices agree for this consistent base and retained set. Their full retained solution sets agree, not just this queried assignment.':'';if(report.lost.length){$('loss').replaceChildren(...report.lost.map((q,i)=>option(i,`t${q.v} - t${q.u}: ${q.bound} versus ${bound(q.naive_bound)}`)));loss()}
$('pair').replaceChildren(...report.pairs.map((q,i)=>option(i,`t${q.v} - t${q.u}: ${bound(q.bound)}`)));const first=report.pairs.findIndex(q=>q.u!==q.v&&q.bound!==null);$('pair').value=String(first<0?0:first);pair();}catch(e){report=null;window.stnProjectionReport=null;$('output').hidden=true;$('download').disabled=true;$('error').textContent=e.message}}
controls.forEach((c,i)=>$('control').append(option(i,c.name)));function select(){$('input').value=JSON.stringify(controls[+$('control').value].input,null,2);$('note').textContent=controls[+$('control').value].description;run()}$('control').addEventListener('change',select);$('pair').addEventListener('change',pair);$('loss').addEventListener('change',loss);$('run').addEventListener('click',run);$('input').addEventListener('input',()=>{report=null;window.stnProjectionReport=null;$('output').hidden=true;$('download').disabled=true});$('download').addEventListener('click',()=>{if(!report)return;const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json'}));a.href=url;a.download='stnlab-projection-report.json';a.click();URL.revokeObjectURL(url)});select();
