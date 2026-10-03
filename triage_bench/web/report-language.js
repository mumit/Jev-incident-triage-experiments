'use strict';
const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),pretty=v=>JSON.stringify(v,null,2);
const packetFields={initial_owner:'Owner',priority:'Priority',next_check:'Next check',insufficient_evidence:'Evidence insufficient'};
let catalog,detail,serial=0;
const state={split:'development',id:null,arm:'broad',report:0,field:'reading'};
async function api(path){const r=await fetch(path),data=await r.json();if(!r.ok)throw new Error(data.error||'Request failed.');return data;}
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function options(id,rows,value){$(id).replaceChildren(...rows.map(([key,label])=>{const o=document.createElement('option');o.value=key;o.textContent=label;return o;}));if(rows.some(r=>r[0]===value))$(id).value=value;}
function table(head,rows){return `<table><thead><tr>${head.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
function ratio(n,total){return `${n}/${total} (${(100*n/total).toFixed(1)}%)`;}
function metric(m,key){return ratio(Math.round(m[key]*m.records),m.records);}
function renderScores(){
 const local=catalog.local,hosted=catalog.hosted,rows=[];
 $('data-counts').textContent=`186 matched training packets · 210 training reports · 140 development packets · 156 development reports`;
 for(const group of [local,hosted])if(group)for(const [a,result] of Object.entries(group.approaches)){const m=result.metrics;rows.push([esc(catalog.arms[a]),metric(m,'all_fields_accuracy'),metric(m,'semantic_decisions_accuracy'),ratio(Math.round(m.pair_all_fields_accuracy*70),70),metric(m,'with_software_priority_accuracy')]);}
 $('scores').innerHTML=rows.length?table(['Inference path','All four correct','Three semantic decisions','Both packets correct','With software priority'],rows):'<p>No saved predictions. Raw inputs and references remain available.</p>';
 const reportRows=[];
 if(local)for(const [a,m] of Object.entries(local.report_metrics))reportRows.push([esc(catalog.arms[a]),...['domain','reading','both'].map(f=>ratio(m.fields[f].correct,m.fields[f].reports)),String(m.attribution.readings_wrong_triage_correct.length)]);
 if(hosted){const m=hosted.report_metrics;reportRows.push([esc(catalog.arms.jev_reading),...['domain','reading','both'].map(f=>ratio(m.fields[f].correct,m.fields[f].reports)),String(m.attribution.readings_wrong_triage_correct.length)]);}
 $('reading-scores').innerHTML='<h3>Did each interpreter read the report?</h3>'+table(['Interpreter','Domain correct','Reading correct','Both correct','Correct packets with wrong readings'],reportRows)+'<p class="muted">Domain names are explicit; this pack does not test discovering them from unlabeled telemetry. Correct packet decisions can hide incorrect report meanings. Failed or missing report responses count as incorrect.</p>';
 const changes=[];
 if(local){const c=local.changes.broad;changes.push(['Broader versus original report ML',c.packets_fixed.length,c.packets_lost.length,['initial_owner','next_check','insufficient_evidence'].map(f=>c.newly_wrong_fields[f].length).join(' / ')]);}
 if(hosted){const c=hosted.changes.jev_reading;changes.push(['Jev report/policy versus direct triage',c.packets_fixed.length,c.packets_lost.length,['initial_owner','next_check','insufficient_evidence'].map(f=>c.newly_wrong_fields[f].length).join(' / ')]);}
 $('changes').innerHTML='<h3>Fixes and regressions</h3>'+table(['Matched comparison','Packets fixed','Correct packets lost','Newly wrong owner / check / evidence'],changes)+'<p class="muted">The ML comparison changes training wording. Jev changes task boundaries, evidence retention, questions and software policy execution. These scores measure agreement with draft synthetic references.</p>';
 $('controls').innerHTML=local?table(['Control',...Object.keys(local.controls).map(a=>catalog.arms[a])],Object.keys(local.controls.narrow).map(c=>[esc(c),...Object.values(local.controls).map(v=>`${v[c].correct}/${v[c].packets}`)])):'';
 $('provenance').textContent=pretty({manifest:catalog.manifest,local,hosted});
 const examples=[];
 if(local){for(const [label,id] of [['A broader-wording fix',local.changes.broad.packets_fixed[0]],['A broader-wording regression',local.changes.broad.packets_lost[0]]])if(id)examples.push([label,id,'broad']);}
 if(hosted){for(const [label,id] of [['A Jev pipeline fix',hosted.changes.jev_reading.packets_fixed[0]],['A Jev pipeline regression',hosted.changes.jev_reading.packets_lost[0]]])if(id)examples.push([label,id,'jev_reading']);}
 $('examples').innerHTML=examples.map(([label,id,arm])=>`<a href="/report-language?${new URLSearchParams({split:'development',case:id,arm})}#inspect">${esc(label)}</a>`).join('');
}
function families(preferred){const rows=catalog.cases[state.split];options('family',[...new Set(rows.map(r=>r.family))].map(f=>[f,f]),preferred);pairs();}
function pairs(preferred){const rows=catalog.cases[state.split].filter(r=>r.family===$('family').value);options('pair',[...new Set(rows.map(r=>r.pair_id))].map((p,i)=>[p,'Pair '+(i+1)]),preferred);selectPacket('a');}
function selectPacket(letter){const rows=catalog.cases[state.split].filter(r=>r.pair_id===$('pair').value);state.id=rows.find(r=>r.id.endsWith('-'+letter))?.id||rows[0].id;state.report=0;load();}
async function load(){
 const generation=++serial;$('inspect').setAttribute('aria-busy','true');$('copy').disabled=true;$('download').disabled=true;
 try{const d=await api('/api/report-language/case?'+new URLSearchParams({id:state.id,split:state.split,arm:state.arm,report:state.report}));if(generation!==serial)return;detail=d;render();$('inspect').setAttribute('aria-busy','false');$('copy').disabled=false;$('download').disabled=false;}
 catch(e){if(generation===serial){status(e.message,true);$('inspect').setAttribute('aria-busy','false');}}
}
function sync(){history.replaceState(null,'','/report-language?'+new URLSearchParams({split:state.split,case:state.id,arm:state.arm,report:state.report})+(location.hash||'#inspect'));$('guide-link').href='/study?'+new URLSearchParams({doc:'report-language',return:location.pathname+location.search+location.hash});}
function render(){
 const r=detail.record,p=r.input,key=detail.draft_reference,show=$('references').open;
 $('case-id').textContent=`${r.id} · ${key.incident_family_id}`;$('pair-change').textContent=`Only ${detail.changed_paths.join(', ')} changes between this packet and its partner. References are drafts.`;
 for(const l of ['a','b'])$('packet-'+l).setAttribute('aria-pressed',String(r.id.endsWith('-'+l)));
 $('raw-reports').innerHTML=p.observations.map((o,i)=>`<section class="report-card"><strong>Report ${i+1} · ${esc(o.asset_id)}</strong><p>${esc(o.detail)}</p><small>Measured ${esc(o.measured_at??'unknown')} · reported ${esc(o.observed_at)}</small></section>`).join('');
 $('impact').textContent=`Impact: ${p.service_impact.status} · ${p.service_impact.affected_sites} sites · ${p.service_impact.basis}`;
 $('facts').textContent=pretty({dependency_facts:detail.dependency_facts,measurement_facts:detail.measurement_facts});$('packet').textContent=pretty({selected:r,paired:detail.paired});
 $('training-words').hidden=!detail.training_reports;
 if(detail.training_reports)$('training-words').innerHTML='<h4>Actual matched training reports</h4>'+table(['Training wording','Report text'],Object.entries(detail.training_reports).map(([a,reports])=>[esc(catalog.arms[a]),reports.map(o=>esc(o.text)).join('<br><br>')]))+'<p>Both models fit the same annotations and non-text evidence. Training packets have no evaluation predictions.</p>';
 const reportArms=['narrow','broad','report_rules','jev_reading'];
 $('meanings').innerHTML=table(['Report',...reportArms.map(a=>catalog.arms[a]),...(show?['Draft reference']:[])],detail.reports.map(o=>[String(o.observation_index+1),...reportArms.map(a=>{const m=detail.outputs[a]?.readings?.[o.observation_index];const ref=detail.report_references[o.observation_index],wrong=show&&m&&(m.domain!==ref.domain||m.reading!==ref.reading);return m?`<span class="${wrong?'reference-wrong':''}">${esc(m.domain)} / ${esc(m.reading)}</span>`:'No saved prediction';}),...(show?[`${esc(detail.report_references[o.observation_index].domain)} / ${esc(detail.report_references[o.observation_index].reading)}`]:[])]));
 $('decisions-table').innerHTML=table(['Inference path',...Object.values(packetFields)],Object.keys(catalog.arms).map(a=>[esc(catalog.arms[a]),...Object.keys(packetFields).map(f=>{const v=detail.outputs[a]?.predictions?.[f];return v?`<span class="${show&&!key.accepted_answers[f].includes(v)?'reference-wrong':''}">${esc(v)}</span>`:detail.outputs[a]?.status==='error'?'Failed response':'No saved prediction';})]));
 const row=detail.outputs[state.arm];$('policy').hidden=!row?.trace;
 $('policy-reason').textContent=row?.trace?.reason||'';$('policy-joins').innerHTML=row?.trace?table(['Report','Predicted meaning','Freshness','Supported sites','Eligible'],row.trace.observations.map(o=>[o.observation_index+1,`${esc(o.domain)} / ${esc(o.reading)}`,esc(o.freshness),o.supported_sites,o.eligible?'Yes':'No'])):'';$('policy-json').textContent=pretty(row?.trace||null);
 $('reference-content').innerHTML='<p class="muted">Draft · not specialist reviewed. References never enter inference inputs.</p>'+table(['Packet field','Reference'],Object.entries(key.labels).map(([f,v])=>[esc(packetFields[f]),esc(v)]))+'<p>'+esc(key.label_rationale)+'</p>'+table(['Report','Domain','Reading','Meaning rationale'],detail.report_references.map(a=>[a.observation_index+1,esc(a.domain),esc(a.reading),esc(a.rationale)]));
 options('report',detail.reports.map(o=>[String(o.observation_index),'Report '+(o.observation_index+1)]),String(state.report));
 $('input-note').textContent=state.arm==='jev_direct'?'Frozen selected-evidence request and existing triage questions. Raw excluded reports remain visible above.':state.arm==='jev_reading'?'Only the selected normalized report text and domain/reading questions enter Jev. Policy receives its predicted meanings and the separate input facts.':state.arm==='bridge'?'Frozen combined packet features; this classifier predicts the four decisions.':'Report text enters the interpreter. Predicted meanings then join currentness, visible paths, impact and asset grouping in the fixed policy.';
 $('input-json').textContent=pretty(detail.request);$('response-details').hidden=!state.arm.startsWith('jev_');$('response-json').textContent=pretty({request:detail.saved_request,response:detail.saved_response});
 const reportPath=['narrow','broad','jev_reading'].includes(state.arm),packetPath=state.arm==='bridge'||state.arm==='jev_direct';
 $('weights').hidden=!(reportPath||packetPath);
 options('field',reportPath?[['reading','Fault / normal / unknown'],['domain','Domain']]:Object.entries(packetFields),state.field);state.field=$('field').value;renderWeights();sync();
}
function renderWeights(){
 state.field=$('field').value;
 const f=state.field,report=detail.report_inspections?.find(r=>r.observation_index===state.report),e=report?.fields?.[f]||detail.packet_explanation?.[f];
 const row=detail.outputs[state.arm],reading=row?.readings?.[state.report],p=e?.probabilities||(['narrow','broad','jev_reading'].includes(state.arm)?reading?.probabilities?.[f]:row?.probabilities?.[f]),chosen=e?.selected||reading?.[f]||row?.predictions?.[f];
 $('weight-note').textContent=state.arm.startsWith('jev_')?'Jev returns choices and probabilities. Its internal weights and reasoning are unavailable. Policy probabilities are not inferred from report probabilities.':'Positive contributions favor the selected class over its runner-up. These weights explain the fitted score, not physical causation.';
 $('distribution').innerHTML=p?'<div class="probabilities">'+Object.entries(p).sort((a,b)=>b[1]-a[1]).map(([c,v])=>`<span>${esc(c)} ${c===chosen?'✓':''} ${(100*v).toFixed(1)}%</span>`).join('')+'</div><p class="muted">Probabilities are not calibrated for network operations.</p>':'<p>No saved evaluation probabilities. Training inputs are available above.</p>';
 $('margin').hidden=!e;$('margin').textContent=e?`${e.selected} versus ${e.compared_with} · log-odds ${e.log_odds_margin.toFixed(3)} = intercept ${e.intercept_difference.toFixed(3)} + shown contributions + remainder ${e.remaining_contribution.toFixed(3)}`:'';
 $('contributions').innerHTML=e?table(['Feature','Value','Weight difference','Contribution'],e.top_contributions.map(c=>[esc(c.feature),c.value.toFixed(3),c.coefficient_difference.toFixed(3),c.contribution.toFixed(3)])):'';
 $('vector-details').hidden=state.arm.startsWith('jev_');$('vector').textContent=pretty(report||{vector:detail.packet_vector,explanation:e||null});
}
$('split').addEventListener('change',()=>{state.split=$('split').value;state.report=0;$('references').open=false;families();});$('family').addEventListener('change',()=>pairs());$('pair').addEventListener('change',()=>selectPacket('a'));
for(const l of ['a','b'])$('packet-'+l).addEventListener('click',()=>{state.report=0;selectPacket(l);});
$('arm').addEventListener('change',()=>{state.arm=$('arm').value;load();});$('report').addEventListener('change',()=>{state.report=Number($('report').value);load();});$('field').addEventListener('change',renderWeights);$('references').addEventListener('toggle',()=>{if(detail)render();});
$('download').addEventListener('click',()=>{const a=document.createElement('a');a.href='/api/report-language/export?'+new URLSearchParams({id:state.id,split:state.split,arm:state.arm,report:state.report});a.download=state.id+'-'+state.arm+'-input.json';a.click();});
$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(pretty(detail.request));status('Exact input copied. It contains no API key or reference answers.');}catch{$('copy-text').value=pretty(detail.request);$('copy-dialog').showModal();$('copy-text').select();}});$('close-copy').addEventListener('click',()=>$('copy-dialog').close());
(async()=>{try{catalog=await api('/api/report-language/catalog');renderScores();status(catalog.status);const q=new URLSearchParams(location.search);if(q.get('split')==='train')state.split='train';if(q.get('arm') in catalog.arms)state.arm=q.get('arm');$('split').value=state.split;options('arm',Object.entries(catalog.arms),state.arm);const row=catalog.cases[state.split].find(r=>r.id===q.get('case'))||catalog.cases[state.split][0];options('family',[...new Set(catalog.cases[state.split].map(r=>r.family))].map(f=>[f,f]),row.family);options('pair',[...new Set(catalog.cases[state.split].filter(r=>r.family===row.family).map(r=>r.pair_id))].map((p,i)=>[p,'Pair '+(i+1)]),row.pair_id);state.id=row.id;state.report=Number(q.get('report')||0);await load();}catch(e){status(e.message,true);}})();
