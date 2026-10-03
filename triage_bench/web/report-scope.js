'use strict';
const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),pretty=v=>JSON.stringify(v,null,2);
const packetFields={initial_owner:'Owner',priority:'Priority',next_check:'Next check',insufficient_evidence:'Evidence insufficient'};
let catalog,detail,serial=0;
const state={split:'development',id:null,arm:'jev_focal',report:0,field:'reading'};
async function api(path){const r=await fetch(path),data=await r.json();if(!r.ok)throw new Error(data.error||'Request failed.');return data;}
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function options(id,rows,value){$(id).replaceChildren(...rows.map(([key,label])=>{const o=document.createElement('option');o.value=key;o.textContent=label;return o;}));if(rows.some(r=>r[0]===value))$(id).value=value;}
function table(head,rows){return `<table><thead><tr>${head.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
function ratio(n,total){return `${n}/${total} (${(100*n/total).toFixed(1)}%)`;}
function metric(m,key){return ratio(Math.round(m[key]*m.records),m.records);}
function renderScores(){
 const local=catalog.local,hosted=catalog.hosted,rows=[],reportRows=[];
 $('data-counts').textContent=`${catalog.manifest.records} development packets · ${catalog.manifest.reports} reports · ${catalog.manifest.pairs} pairs · ${catalog.manifest.families} families`;
 for(const group of [hosted,local])if(group)for(const [a,result] of Object.entries(group.approaches)){
  const m=result.metrics;rows.push([esc(catalog.arms[a]),metric(m,'all_fields_accuracy'),ratio(Math.round(m.pair_all_fields_accuracy*catalog.manifest.pairs),catalog.manifest.pairs)]);
  const rm=group.report_metrics[a];reportRows.push([esc(catalog.arms[a]),...['domain','reading','both'].map(f=>ratio(rm.fields[f].correct,rm.fields[f].reports)),String(rm.attribution.readings_wrong_triage_correct.length),String(rm.attribution.readings_correct_triage_wrong.length)]);
 }
 $('scores').innerHTML=rows.length?table(['Inference path','All four match draft reference','Both packets match'],rows)+'<p class="change">A correct packet can hide a wrong reading or policy error. Inspect the report scores and predeclared policy gaps below before interpreting the packet score.</p>':'<p>No saved predictions. Inputs and references remain available.</p>';
 $('reading-scores').innerHTML='<h3>Report meaning and policy errors</h3>'+table(['Interpreter','Domain correct','Reading correct','Both correct','Correct triage / wrong readings','Wrong triage / correct readings'],reportRows)+'<p class="muted">Explicit domain prefixes make domain classification easier. Failed or missing replies count as incorrect. Agreement with draft references is not operational validation.</p>';
 const changes=[];
 if(hosted){const c=hosted.changes.jev_focal;changes.push(['Measured-function versus original Jev question',c.packets_fixed.length,c.packets_lost.length,['initial_owner','next_check','insufficient_evidence'].map(f=>c.newly_wrong_fields[f].length).join(' / ')]);}
 $('changes').innerHTML=hosted?'<h3>Matched Jev fixes and losses</h3>'+table(['Comparison','Packets fixed','Correct packets lost','Newly wrong owner / check / evidence'],changes)+`<p>Reports fixed: ${hosted.report_changes.reports_fixed.length}. Correct reports lost: ${hosted.report_changes.reports_lost.length}. Newly wrong domain: ${hosted.report_changes.newly_wrong_domain.length}; reading: ${hosted.report_changes.newly_wrong_reading.length}.</p>`:'<p>Jev comparison has not run.</p>';
 $('provenance').textContent=pretty({manifest:catalog.manifest,local,hosted});
 const examples=[];
 if(hosted){const c=hosted.changes.jev_focal;for(const [label,id] of [['Inspect a question fix',c.packets_fixed[0]],['Inspect a question regression',c.packets_lost[0]],['Inspect a report fix',hosted.report_changes.reports_fixed[0]?.id],['Inspect a report regression',hosted.report_changes.reports_lost[0]?.id]])if(id)examples.push([label,id]);}
 $('examples').innerHTML=examples.map(([label,id])=>`<a href="/report-scope?${new URLSearchParams({case:id,arm:'jev_focal'})}#inspect">${esc(label)}</a>`).join('');
 $('policy-gap').innerHTML=catalog.manifest.known_policy_gaps.map(id=>`<p><a href="/report-scope?${new URLSearchParams({case:id,arm:'jev_focal'})}#inspect">Inspect ${esc(id)}</a></p>`).join('');
}
function families(preferred){const rows=catalog.cases[state.split];options('family',[...new Set(rows.map(r=>r.family))].map(f=>[f,f]),preferred);pairs();}
function pairs(preferred){const rows=catalog.cases[state.split].filter(r=>r.family===$('family').value);options('pair',[...new Set(rows.map(r=>r.pair_id))].map((p,i)=>[p,'Pair '+(i+1)]),preferred);selectPacket('a');}
function selectPacket(letter){const rows=catalog.cases[state.split].filter(r=>r.pair_id===$('pair').value);state.id=rows.find(r=>r.id.endsWith('-'+letter))?.id||rows[0].id;state.report=0;load();}
async function load(){
 const generation=++serial;$('inspect').setAttribute('aria-busy','true');$('copy').disabled=true;$('download').disabled=true;
 try{const d=await api('/api/report-scope/case?'+new URLSearchParams({id:state.id,split:state.split,arm:state.arm,report:state.report}));if(generation!==serial)return;detail=d;render();$('inspect').setAttribute('aria-busy','false');$('copy').disabled=false;$('download').disabled=false;}
 catch(e){if(generation===serial){status(e.message,true);$('inspect').setAttribute('aria-busy','false');}}
}
function sync(){history.replaceState(null,'','/report-scope?'+new URLSearchParams({split:state.split,case:state.id,arm:state.arm,report:state.report})+(location.hash||'#inspect'));$('guide-link').href='/study?'+new URLSearchParams({doc:'report-scope',return:location.pathname+location.search+location.hash});}
function render(){
 const r=detail.record,p=r.input,key=detail.draft_reference,show=$('references').open;
 $('case-id').textContent=`${r.id} · ${key.incident_family_id}`;$('pair-change').textContent=`Only ${detail.changed_paths.join(', ')} changes between this packet and its partner. References are drafts.`;
 for(const l of ['a','b'])$('packet-'+l).setAttribute('aria-pressed',String(r.id.endsWith('-'+l)));
 $('raw-reports').innerHTML=p.observations.map((o,i)=>`<section class="report-card"><strong>Report ${i+1} · ${esc(o.asset_id)}</strong><p>${esc(o.detail)}</p><small>Measured ${esc(o.measured_at??'unknown')} · reported ${esc(o.observed_at)}</small></section>`).join('');
 $('impact').textContent=`Impact: ${p.service_impact.status} · ${p.service_impact.affected_sites} sites · ${p.service_impact.basis}`;
 $('facts').textContent=pretty({dependency_facts:detail.dependency_facts,measurement_facts:detail.measurement_facts});$('packet').textContent=pretty({selected:r,paired:detail.paired});
 $('training-words').hidden=!detail.training_reports;
 if(detail.training_reports)$('training-words').innerHTML='<h4>Actual matched training reports</h4>'+table(['Training wording','Report text'],Object.entries(detail.training_reports).map(([a,reports])=>[esc(catalog.arms[a]),reports.map(o=>esc(o.text)).join('<br><br>')]))+'<p>Both models fit the same annotations and non-text evidence. Training packets have no evaluation predictions.</p>';
 const reportArms=Object.keys(catalog.arms);
 $('meanings').innerHTML=table(['Report','Interpreter','Predicted meaning',...(show?['Draft meaning']:[])],detail.reports.flatMap(o=>reportArms.map(a=>{const m=detail.outputs[a]?.readings?.[o.observation_index],ref=detail.report_references[o.observation_index],wrong=show&&m&&(m.domain!==ref.domain||m.reading!==ref.reading);return [String(o.observation_index+1),esc(catalog.arms[a]),m?`<span class="${wrong?'reference-wrong':''}">${esc(m.domain)} / ${esc(m.reading)}</span>`:'No saved prediction',...(show?[`${esc(ref.domain)} / ${esc(ref.reading)}`]:[])];})));
 $('decisions-table').innerHTML=table(['Inference path',...Object.values(packetFields)],Object.keys(catalog.arms).map(a=>[esc(catalog.arms[a]),...Object.keys(packetFields).map(f=>{const v=detail.outputs[a]?.predictions?.[f];return v?`<span class="${show&&!key.accepted_answers[f].includes(v)?'reference-wrong':''}">${esc(v)}</span>`:detail.outputs[a]?.status==='error'?'Failed response':'No saved prediction';})]));
 const row=detail.outputs[state.arm];$('policy').hidden=!row?.trace;
 $('policy-reason').textContent=row?.trace?.reason||'';$('policy-joins').innerHTML=row?.trace?table(['Report','Predicted meaning','Freshness','Supported sites','Eligible'],row.trace.observations.map(o=>[o.observation_index+1,`${esc(o.domain)} / ${esc(o.reading)}`,esc(o.freshness),o.supported_sites,o.eligible?'Yes':'No'])):'';$('policy-json').textContent=pretty(row?.trace||null);$('scope-warning').hidden=!key.known_policy_gap;$('scope-warning').textContent='Known policy gap: successful intake and failed completion can coexist. Grouping by domain and asset cannot represent their different functions. A predicted unknown intake reading can hide that gap and accidentally match the draft triage reference.';
 $('reference-content').innerHTML='<p class="muted">Draft · not specialist reviewed. References never enter inference inputs.</p>'+table(['Packet field','Reference'],Object.entries(key.labels).map(([f,v])=>[esc(packetFields[f]),esc(v)]))+'<p>'+esc(key.label_rationale)+'</p>'+table(['Report','Domain','Reading','Meaning rationale'],detail.report_references.map(a=>[a.observation_index+1,esc(a.domain),esc(a.reading),esc(a.rationale)]));
 $('reference-content').innerHTML+='<h4>Reference readings fed to frozen policy</h4><p>Evaluation diagnostic, not a model prediction or accuracy ceiling. Incorrect readings can hide a policy error.</p>'+table(['Packet field','Policy output','Draft reference'],Object.entries(detail.reference_policy_diagnostic.predictions).map(([f,v])=>[esc(packetFields[f]),`<span class="${!key.accepted_answers[f].includes(v)?'reference-wrong':''}">${esc(v)}</span>`,esc(key.labels[f])]))+'<p>'+esc(detail.reference_policy_diagnostic.trace.reason)+'</p>';
 options('report',detail.reports.map(o=>[String(o.observation_index),'Report '+(o.observation_index+1)]),String(state.report));
 $('input-note').textContent=state.arm.startsWith('jev_')?'Only this normalized report text and domain/reading questions enter Jev. Returned meanings then feed frozen policy with separate input facts.':'The frozen interpreter reads each normalized report. Policy receives predicted meanings, currentness, paths, impact and asset grouping.';
 $('instruction-text').innerHTML=Object.entries(detail.reading_instructions).map(([a,text])=>`<section class="report-card"><strong>${esc(catalog.arms[a])}</strong><p>${esc(text)}</p></section>`).join('')+'<p>The added paragraph is the only request difference. State, domain question, choice criteria and model remain identical.</p>';
 $('input-json').textContent=pretty(detail.request);$('response-details').hidden=!state.arm.startsWith('jev_');$('response-json').textContent=pretty({request:detail.saved_request,response:detail.saved_response});
 const reportPath=state.arm!=='report_rules',packetPath=false;
 $('weights').hidden=!(reportPath||packetPath);
 options('field',reportPath?[['reading','Fault / normal / unknown'],['domain','Domain']]:Object.entries(packetFields),state.field);state.field=$('field').value;renderWeights();sync();
}
function renderWeights(){
 state.field=$('field').value;
 const f=state.field,report=detail.report_inspections?.find(r=>r.observation_index===state.report),e=report?.fields?.[f]||detail.packet_explanation?.[f];
 const row=detail.outputs[state.arm],reading=row?.readings?.[state.report],p=e?.probabilities||(state.arm!=='report_rules'?reading?.probabilities?.[f]:row?.probabilities?.[f]),chosen=e?.selected||reading?.[f]||row?.predictions?.[f];
 $('weight-note').textContent=state.arm.startsWith('jev_')?'Jev returns choices and probabilities. Its internal weights and reasoning are unavailable. Policy probabilities are not inferred from report probabilities.':'Positive contributions favor the selected class over its runner-up. These weights explain the fitted score, not physical causation.';
 $('distribution').innerHTML=p?'<div class="probabilities">'+Object.entries(p).sort((a,b)=>b[1]-a[1]).map(([c,v])=>`<span>${esc(c)} ${c===chosen?'✓':''} ${(100*v).toFixed(1)}%</span>`).join('')+'</div><p class="muted">Probabilities are not calibrated for network operations.</p>':'<p>No saved evaluation probabilities. Training inputs are available above.</p>';
 $('margin').hidden=!e;$('margin').textContent=e?`${e.selected} versus ${e.compared_with} · log-odds ${e.log_odds_margin.toFixed(3)} = intercept ${e.intercept_difference.toFixed(3)} + shown contributions + remainder ${e.remaining_contribution.toFixed(3)}`:'';
 $('contributions').innerHTML=e?table(['Feature','Value','Weight difference','Contribution'],e.top_contributions.map(c=>[esc(c.feature),c.value.toFixed(3),c.coefficient_difference.toFixed(3),c.contribution.toFixed(3)])):'';
 $('vector-details').hidden=state.arm.startsWith('jev_');$('vector').textContent=pretty(report||{vector:detail.packet_vector,explanation:e||null});
}
$('split').addEventListener('change',()=>{state.split=$('split').value;state.report=0;$('references').open=false;families();});$('family').addEventListener('change',()=>pairs());$('pair').addEventListener('change',()=>selectPacket('a'));
for(const l of ['a','b'])$('packet-'+l).addEventListener('click',()=>{state.report=0;selectPacket(l);});
$('arm').addEventListener('change',()=>{state.arm=$('arm').value;load();});$('report').addEventListener('change',()=>{state.report=Number($('report').value);load();});$('field').addEventListener('change',renderWeights);$('references').addEventListener('toggle',()=>{if(detail)render();});
$('download').addEventListener('click',()=>{const a=document.createElement('a');a.href='/api/report-scope/export?'+new URLSearchParams({id:state.id,split:state.split,arm:state.arm,report:state.report});a.download=state.id+'-'+state.arm+'-input.json';a.click();});
$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(pretty(detail.request));status('Exact input copied. It contains no API key or reference answers.');}catch{$('copy-text').value=pretty(detail.request);$('copy-dialog').showModal();$('copy-text').select();}});$('close-copy').addEventListener('click',()=>$('copy-dialog').close());
(async()=>{try{catalog=await api('/api/report-scope/catalog');renderScores();status(catalog.status);const q=new URLSearchParams(location.search);if(q.get('arm') in catalog.arms)state.arm=q.get('arm');$('split').value=state.split;options('arm',Object.entries(catalog.arms),state.arm);const row=catalog.cases[state.split].find(r=>r.id===q.get('case'))||catalog.cases[state.split][0];options('family',[...new Set(catalog.cases[state.split].map(r=>r.family))].map(f=>[f,f]),row.family);options('pair',[...new Set(catalog.cases[state.split].filter(r=>r.family===row.family).map(r=>r.pair_id))].map((p,i)=>[p,'Pair '+(i+1)]),row.pair_id);state.id=row.id;state.report=Number(q.get('report')||0);await load();}catch(e){status(e.message,true);}})();
