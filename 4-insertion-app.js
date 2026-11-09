import {analyze} from './insertions.js';const $=id=>document.getElementById(id),controls=await fetch('./insertion-controls.json').then(r=>r.json());let report=null;
const edge=(e,k)=>`C${k}: t${e[1]} - t${e[0]} ≤ ${e[2]}`,schedule=t=>t.map((x,i)=>`t${i}=${x}`).join(' · '),ids=p=>p.length?p.map(k=>'C'+k).join(' → '):'empty path',option=(v,text)=>Object.assign(document.createElement('option'),{value:v,textContent:text}),cell=t=>Object.assign(document.createElement('td'),{textContent:t}),bound=v=>v===null?'∞':String(v);
function rows(id,data){$(id).replaceChildren(...data.map(row=>{const tr=document.createElement('tr');tr.append(...row.map(cell));return tr}))}
function timeline(t){const lo=Math.min(...t)-1,hi=Math.max(...t)+1,n=t.length,height=42+n*34,width=Math.max(300,Math.min(620,$('timeline').clientWidth));const ns='http://www.w3.org/2000/svg',svg=$('timeline');svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.replaceChildren();const node=(name,attrs,text)=>{const e=document.createElementNS(ns,name);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;svg.append(e)};t.forEach((x,i)=>{const y=26+i*34,cx=55+(x-lo)/(hi-lo)*(width-110);node('line',{x1:55,y1:y,x2:width-35,y2:y,stroke:'#c9d1de'});node('text',{x:12,y:y+5,fill:'#14233c','font-size':15},`t${i}`);node('circle',{cx,cy:y,r:5,fill:'#244ed6'});node('text',{x:cx+10,y:y+5,fill:'#a64013','font-size':14},String(x))});node('text',{x:55,y:height-8,fill:'#46556b','font-size':12},'Relative time; t0 = 0.')}

function pair(){const q=report.cells[+$('pair').value],es=[...report.input.base.edges,report.input.candidate],k=es.length-1,[a,b,w]=report.input.candidate;const via=q.left_path===null||q.right_path===null?null:[...q.left_path,k,...q.right_path];
 $('cell-proof').textContent=`t${q.v} - t${q.u}
Before: ${bound(q.before)}
Old left D[${q.u},${a}]: ${bound(report.base_matrix[q.u][a])}
Candidate weight: ${w}
Old right D[${b},${q.v}]: ${bound(report.base_matrix[b][q.v])}
Via candidate: ${bound(q.via)}
After: min(${bound(q.before)}, ${bound(q.via)}) = ${bound(q.after)}
Changed: ${q.changed?'yes':'no'}`;rows('via-rows',via===null?[]:via.map(i=>['C'+i,edge(es[i],i),es[i][2]]));$('finite').hidden=q.after===null;$('unbounded').hidden=q.after!==null;
 if(q.after!==null){$('attaining-proof').textContent=`Shortest simple path: ${ids(q.path)}
Path sum: ${q.after}
Complete attaining schedule
${schedule(q.schedule)}
Selected difference: ${q.schedule[q.v]-q.schedule[q.u]}`;rows('path-rows',q.path.map(i=>['C'+i,edge(es[i],i),es[i][2]]));timeline(q.schedule);$('slacks').textContent='ALL POST-INSERTION CONSTRAINT SLACKS\n'+es.map(([u,v,w],i)=>`C${i}: ${w-(q.schedule[v]-q.schedule[u])}`).join('\n')}
 else $('ray-proof').textContent=`No finite post-insertion upper bound.
Complete base schedule
${schedule(report.schedule)}
Anchored ray
${schedule(q.ray)}
Selected ray difference: ${q.ray[q.v]-q.ray[q.u]}
ALL POST-INSERTION EDGE RAY DIFFERENCES
`+es.map(([u,v],i)=>`C${i}: ${q.ray[v]-q.ray[u]} ≤ 0`).join('\n');}
function weight(){const q=report.spectrum[+$('weight').value+20];$('weight-proof').textContent=`Alternative candidate weight: ${q.weight}
Classification: ${q.classification}
Changed matrix cells: ${q.changed===null?'not defined for inconsistency':q.changed}
The main proof panels still show weight ${report.input.candidate[2]}.`}
function run(){try{report=analyze(JSON.parse($('input').value));window.stnInsertionReport=report;$('error').textContent='';$('output').hidden=false;$('download').disabled=false;$('report').value=JSON.stringify(report,null,2);const es=[...report.input.base.edges,report.input.candidate],k=es.length-1,[a,b,w]=report.input.candidate;
 $('status').textContent={'base-inconsistent':'The base is already impossible.',inconsistent:'This proposal breaks consistency.',redundant:'The proposal repeats a consequence.',tightening:'The proposal tightens the network.'}[report.classification];$('summary').textContent=`Candidate C${k}: t${b} - t${a} ≤ ${w}
Base consistent: ${report.base_consistent?'yes':'no'}
After insertion consistent: ${report.consistent?'yes':'no'}
`+(report.consistent?'COMPLETE POST-INSERTION SCHEDULE\n'+schedule(report.schedule):'No post-insertion schedule or matrix.');rows('input-rows',es.map((e,i)=>['C'+i+(i===k?' (new)':''),edge(e,i),e[2]]));$('threshold-block').hidden=!report.base_consistent;$('spectrum-block').hidden=!report.base_consistent;$('failure').hidden=report.consistent;$('success').hidden=!report.consistent;
 if(report.base_consistent){const t=report.threshold;$('threshold-proof').textContent=t.lower===null?`Old return D[${b},${a}]: ∞
No old return path.
No finite lower threshold: every real candidate weight is feasible.
Redundant at or above: ${bound(t.redundant_at)}`:`Old return D[${b},${a}]: ${-t.lower}
Return path: ${ids(t.return_path)}
Exact feasible weights: w ≥ ${t.lower}
Redundant at or above: ${bound(t.redundant_at)}
Complete schedule at w=${t.lower}
${schedule(t.boundary_schedule)}
At w=${t.below_cycle.candidate_weight}: C${k} then return path sum to -1.`;rows('threshold-rows',(t.return_path||[]).map(i=>['C'+i,edge(es[i],i),es[i][2]]));$('threshold-note').textContent=t.lower===null?'An insertion without a return path cannot close any new cycle. This does not imply the resulting bounds are all finite.':'The boundary schedule satisfies all original edges and the candidate at the threshold. The candidate used in this boundary witness can lie outside the public input window.';$('weight').replaceChildren(...report.spectrum.map(q=>option(q.weight,`${q.weight}: ${q.classification}`)));$('weight').value=String(w);weight();rows('spectrum-rows',report.spectrum.map(q=>[q.weight,q.classification,q.changed===null?'undefined':q.changed]));}
 if(!report.consistent){const c=report.cycle;$('cycle-proof').textContent=`${report.base_consistent?'New-edge':'Pre-existing base'} negative cycle
Edges: ${ids(c.edges)}
Sum of left sides: 0
Sum of weights: ${c.weight}
Required: 0 ≤ ${c.weight}
Contradiction.`;rows('cycle-rows',c.edges.map(i=>['C'+i,edge(es[i],i),es[i][2]]));return}
 $('update-rule').textContent=`D'[i,j] = min(D[i,j], D[i,${a}] + ${w} + D[${b},j])
All D terms are from the old matrix.
A finite minimum includes a complete attaining witness.`;$('pair').replaceChildren(...report.cells.map((q,i)=>option(i,`t${q.v} - t${q.u}: ${bound(q.before)} → ${bound(q.after)}${q.changed?' (changed)':''}`)));const first=report.cells.findIndex(q=>q.changed&&q.u===0&&q.v!==0);$('pair').value=String(first<0?0:first);const head=document.createElement('thead'),hr=document.createElement('tr');for(const x of ['u → v',...report.matrix.map((_,i)=>'t'+i)])hr.append(Object.assign(document.createElement('th'),{textContent:x}));head.append(hr);const body=document.createElement('tbody');report.matrix.forEach((row,i)=>{const tr=document.createElement('tr');tr.append(cell('t'+i),...row.map(bound).map(cell));body.append(tr)});$('matrix').replaceChildren(head,body);$('changed-title').textContent=report.cells.filter(q=>q.changed).length+' matrix cells change.';pair();
 }catch(e){report=null;window.stnInsertionReport=null;$('output').hidden=true;$('download').disabled=true;$('error').textContent=e.message}}
controls.forEach((c,i)=>$('control').append(option(i,c.name)));function select(){$('input').value=JSON.stringify(controls[+$('control').value].input,null,2);$('note').textContent=controls[+$('control').value].note;run()}
$('control').addEventListener('change',select);$('pair').addEventListener('change',pair);$('weight').addEventListener('change',weight);$('run').addEventListener('click',run);$('input').addEventListener('input',()=>{report=null;window.stnInsertionReport=null;$('output').hidden=true;$('download').disabled=true});$('download').addEventListener('click',()=>{if(!report)return;const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json'}));a.href=url;a.download='stnlab-insertion-report.json';a.click();URL.revokeObjectURL(url)});select();
