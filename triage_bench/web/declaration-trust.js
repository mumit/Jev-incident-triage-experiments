'use strict';
const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),pretty=v=>JSON.stringify(v,null,2);
const packetFields={initial_owner:'Owner',priority:'Priority',next_check:'Next check',insufficient_evidence:'Evidence insufficient'};
let catalog,detail,serial=0;
const state={split:'development',id:null,arm:'jev_declared__guarded',report:0,field:'reading'};
async function api(path){const r=await fetch(path),data=await r.json();if(!r.ok)throw new Error(data.error||'Request failed.');return data;}
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function options(id,rows,value){$(id).replaceChildren(...rows.map(([key,label])=>{const o=document.createElement('option');o.value=key;o.textContent=label;return o;}));if(rows.some(r=>r[0]===value))$(id).value=value;}
function table(head,rows){return `<table><thead><tr>${head.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
function armName(a){const [r,p]=a.split('__');return ({jev_declared:'Jev',narrow:'ML · original',broad:'ML · broader',report_rules:'Rules'}[r]||r)+' · '+(p==='guarded'?'guard':'base');}
function ratio(n,total){return `${n}/${total} (${(100*n/total).toFixed(1)}%)`;}
function metric(m,key){return ratio(Math.round(m[key]*m.records),m.records);}
function renderScores(){
 const rows=[],reportRows=[],changeRows=[],masked=[];
 $('data-counts').textContent=`${catalog.manifest.records} packets · ${catalog.manifest.reports} occurrences · ${catalog.manifest.distinct_report_texts} distinct texts · ${catalog.manifest.pairs} pairs`;
 for(const group of [catalog.hosted,catalog.local])if(group){
  for(const [reader,label] of Object.entries(group.readers)){
   const m=group.approaches[reader+'__unguarded'].metrics,s=group.approaches[reader+'__guarded'].metrics;
   rows.push([esc(label),metric(m,'all_fields_accuracy'),metric(s,'all_fields_accuracy'),ratio(Math.round(m.pair_all_fields_accuracy*catalog.manifest.pairs),catalog.manifest.pairs),ratio(Math.round(s.pair_all_fields_accuracy*catalog.manifest.pairs),catalog.manifest.pairs)]);
   const rm=group.report_metrics[reader];reportRows.push([esc(label),ratio(rm.fields.domain.correct_distinct_texts,rm.fields.domain.distinct_texts),ratio(rm.fields.reading.correct_distinct_texts,rm.fields.reading.distinct_texts)]);
   masked.push([esc(label),...['unguarded','guarded'].map(p=>group.attribution[reader+'__'+p].operation_reading.readings_wrong_triage_correct.length)]);
   const c=group.changes[reader][reader+'__guarded'];changeRows.push([esc(label),c.packets_fixed.length,c.packets_lost.length,Object.keys(packetFields).map(f=>c.newly_wrong_fields[f].length).join(' / ')]);
  }
 }
 $('scores').innerHTML=rows.length?table(['Frozen reader','Base: packet matches','Guard: packet matches','Base: pair matches','Guard: pair matches'],rows):'<p>No saved predictions. Inputs and references remain available.</p>';
 $('reading-scores').innerHTML='<h3>Actual shared report predictions</h3>'+table(['Reader','Raw domain head: prose annotation','Operation reading: same across policies'],reportRows)+'<p class="muted">Forty distinct texts supply 160 correlated occurrences. Both policies ignore the raw domain head and use occurrence-specific structured declarations. No probabilities are invented for copied domains. A matching NOC disposition can conceal a wrong operation reading.</p>';
 $('changes').innerHTML='<h3>Guard compared with the same reader’s base policy</h3>'+table(['Reader','Packets fixed','Packets lost','Newly wrong owner / priority / check / evidence'],changeRows)+'<p class="muted">Only the policy changes. No new model calls, training changes or reading corrections occur when switching policies. Full verified results include report errors hidden by matching packet decisions.</p>';
 $('changes').innerHTML+='<h3>Matching packets that conceal wrong operation readings</h3>'+table(['Reader','Base','Guard'],masked);
 $('provenance').textContent=pretty({manifest:catalog.manifest,local:catalog.local,hosted:catalog.hosted});
 const examples=['fault_conflict','normal_conflict','missing','ambiguous','stale','unlinked','clean_comparability'].map(kind=>catalog.cases.development.find(c=>c.control===kind)).filter(Boolean);
 $('examples').innerHTML=examples.map(c=>`<a href="/declaration-trust?${new URLSearchParams({case:c.id,arm:'jev_declared__guarded'})}#inspect">Inspect ${esc(c.control.replaceAll('_',' '))}</a>`).join('');
}

function families(preferred){const rows=catalog.cases[state.split];options('family',[...new Set(rows.map(r=>r.family))].map(f=>[f,f]),preferred);pairs();}
function pairs(preferred){const rows=catalog.cases[state.split].filter(r=>r.family===$('family').value);options('pair',[...new Set(rows.map(r=>r.pair_id))].map((p,i)=>[p,'Pair '+(i+1)]),preferred);selectPacket('a');}
function selectPacket(letter){const rows=catalog.cases[state.split].filter(r=>r.pair_id===$('pair').value);state.id=rows.find(r=>r.id.endsWith('-'+letter))?.id||rows[0].id;state.report=0;load();}
async function load(){
 const generation=++serial;$('inspect').setAttribute('aria-busy','true');$('copy').disabled=true;$('download').disabled=true;
 try{const d=await api('/api/declaration-trust/case?'+new URLSearchParams({id:state.id,split:state.split,arm:state.arm,report:state.report}));if(generation!==serial)return;detail=d;render();$('inspect').setAttribute('aria-busy','false');$('copy').disabled=false;$('download').disabled=false;}
 catch(e){if(generation===serial){status(e.message,true);$('inspect').setAttribute('aria-busy','false');}}
}
function sync(){history.replaceState(null,'','/declaration-trust?'+new URLSearchParams({split:state.split,case:state.id,arm:state.arm,report:state.report})+(location.hash||'#inspect'));$('guide-link').href='/study?'+new URLSearchParams({doc:'declaration-trust',return:location.pathname+location.search+location.hash});$('decision-link').href='/task-fit';}
function render(){
 const r=detail.record,p=r.input,key=detail.draft_reference,show=$('references').open;
 $('case-id').textContent=`${r.id} · ${key.incident_family_id}`;$('pair-change').textContent=`Only ${detail.changed_paths.join(', ')} changes between this packet and its partner. References are drafts.`;
 for(const l of ['a','b'])$('packet-'+l).setAttribute('aria-pressed',String(r.id.endsWith('-'+l)));
 $('raw-reports').innerHTML=p.observations.map((o,i)=>`<section class="report-card"><strong>Report ${i+1} · ${esc(o.asset_id)}</strong><p>${esc(o.detail)}</p><small>Measured ${esc(o.measured_at??'unknown')} · reported ${esc(o.observed_at)}</small><p class="muted">Declared domain: ${esc(o.instrument_domain?.status||'missing')} · ${esc(o.instrument_domain?.domain||o.instrument_domain?.candidates?.join(' / ')||'none')}<br>Supplied scope: ${esc(o.measurement_scope?.status||'missing')} · ${esc(o.measurement_scope?.function||'unknown function')} · ${esc(o.measurement_scope?.comparison_context||'unknown conditions')}</p></section>`).join('');
 $('impact').textContent=`Impact: ${p.service_impact.status} · ${p.service_impact.affected_sites} ${p.service_impact.affected_sites===1?'site':'sites'} · ${p.service_impact.basis}`;
 $('facts').textContent=pretty({dependency_facts:detail.dependency_facts,measurement_facts:detail.measurement_facts});$('packet').textContent=pretty({selected:r,paired:detail.paired});
 $('training-words').hidden=!detail.training_reports;
 if(detail.training_reports)$('training-words').innerHTML='<h4>Actual matched training reports</h4>'+table(['Training wording','Report text'],Object.entries(detail.training_reports).map(([a,reports])=>[esc(catalog.arms[a]),reports.map(o=>esc(o.text)).join('<br><br>')]))+'<p>Both models fit the same annotations and non-text evidence. Training packets have no evaluation predictions.</p>';
 const reportArms=Object.keys(catalog.readers).map(r=>r+'__guarded');
 $('meanings').innerHTML=table(['Report','Interpreter','Predicted meaning',...(show?['Draft meaning']:[])],detail.reports.flatMap(o=>reportArms.map(a=>{const m=detail.reading_outputs[a]?.raw_readings?.[o.observation_index],ref=detail.report_references[o.observation_index],wrong=show&&m&&(m.domain!==ref.domain||m.reading!==ref.reading);return [String(o.observation_index+1),esc(catalog.readers[a.split('__')[0]]),m?`<span class="${wrong?'reference-wrong':''}">${esc(m.domain)} / ${esc(m.reading)}</span>`:'No saved prediction',...(show?[`${esc(ref.domain)} / ${esc(ref.reading)}`]:[])];})));
 $('decisions-table').innerHTML=table(['Inference path',...Object.values(packetFields)],Object.keys(catalog.arms).map(a=>[esc(armName(a)),...Object.keys(packetFields).map(f=>{const v=detail.outputs[a]?.predictions?.[f];return v?`<span class="${show&&!key.accepted_answers[f].includes(v)?'reference-wrong':''}">${esc(v)}</span>`:detail.outputs[a]?.status==='error'?'Failed response':'No saved prediction';})]));
 const row=detail.outputs[state.arm];$('policy').hidden=!row?.trace;
 $('policy-reason').textContent=row?.trace?.reason||'';$('grouping-note').textContent='Both policies use the same supplied structured domains and actual operation readings. Raw domain heads do not enter ownership policy.';
 const guard=row?.trace?.declaration_guard;
 $('policy-joins').innerHTML=guard?table(['Report','Structured domain','Prose header','Conflict','Eligible','Fault-bearing asset','Blocks ownership'],guard.facts.map(o=>[o.observation_index+1,esc(o.structured.domain),esc(o.prose_header.domain),o.conflict?'Yes':'No',o.eligible?'Yes':'No',o.fault_bearing_asset?'Yes':'No',o.blocks_ownership?'Yes':'No'])):'';
 $('policy-json').textContent=pretty(row?.trace||null);$('scope-warning').hidden=false;$('scope-warning').textContent='Switch policy to compare ownership with the same actual reading. Switch A/B to inspect the one changed metadata or eligibility field. Stale and disconnected declaration conflicts cannot block a linked fault.';
 $('reference-content').innerHTML='<p class="muted">Draft · not specialist reviewed. References never enter inference inputs.</p>'+table(['Packet field','Reference'],Object.entries(key.labels).map(([f,v])=>[esc(packetFields[f]),esc(v)]))+'<p>'+esc(key.label_rationale)+'</p>'+table(['Report','Domain','Reading','Meaning rationale'],detail.report_references.map(a=>[a.observation_index+1,esc(a.domain),esc(a.reading),esc(a.rationale)]));
 $('reference-content').innerHTML+='<h4>Reference meanings fed to the selected policy</h4><p>Evaluation diagnostic, not model performance or an accuracy ceiling.</p>'+table(['Packet field','Reference-reading diagnostic','Draft reference'],Object.entries(key.labels).map(([f,v])=>[esc(packetFields[f]),esc(detail.reference_policy_diagnostic.predictions[f]),esc(v)]));
 options('report',detail.reports.map(o=>[String(o.observation_index),'Report '+(o.observation_index+1)]),String(state.report));
 $('input-note').textContent='Only normalized report text enters the frozen interpreter. Both policies copy domain from each occurrence’s structured metadata; the candidate also checks its explicit prose header. Switching policy leaves this exact interpreter input unchanged. This text supplies '+detail.shared_report.occurrences.length+' correlated occurrences.';
 $('policy-input-json').textContent=pretty(detail.policy_facts);
 $('instruction-text').innerHTML=Object.entries(detail.reading_instructions).map(([a,q])=>`<section class="report-card"><strong>${esc(catalog.readers[a])}</strong><p>${esc(q.instructions)}</p><pre>${esc(pretty(q.criteria))}</pre></section>`).join('')+'<p>The complete declared-domain Jev request is frozen, including its domain head. Both policies ignore that predicted domain; the operation reading is shared.</p>';
 $('input-json').textContent=pretty(detail.request);$('response-details').hidden=!state.arm.startsWith('jev_');$('response-json').textContent=pretty({request:detail.saved_request,response:detail.saved_response});
 const reportPath=detail.selected_reader!=='report_rules',packetPath=false;
 $('weights').hidden=!(reportPath||packetPath);
 options('field',[['reading','Fault / normal / unknown']],state.field);state.field=$('field').value;renderWeights();sync();
}
function renderWeights(){
 state.field=$('field').value;
 const f=state.field,report=detail.report_inspections?.find(r=>r.observation_index===state.report),e=report?.fields?.[f]||detail.packet_explanation?.[f];
 const row=detail.outputs[state.arm],reading=row?.raw_readings?.[state.report],p=e?.probabilities||(detail.selected_reader!=='report_rules'?reading?.probabilities?.[f]:row?.probabilities?.[f]),chosen=e?.selected||reading?.[f]||row?.predictions?.[f];
 $('weight-note').textContent=state.arm.startsWith('jev_')?'Jev returns choices and probabilities. Its internal weights and reasoning are unavailable. Policy probabilities are not inferred from report probabilities.':'Positive contributions favor the selected class over its runner-up. These weights explain the fitted score, not physical causation.';
 $('distribution').innerHTML=p?'<div class="probabilities">'+Object.entries(p).sort((a,b)=>b[1]-a[1]).map(([c,v])=>`<span>${esc(c)} ${c===chosen?'✓':''} ${(100*v).toFixed(1)}%</span>`).join('')+'</div><p class="muted">Probabilities are not calibrated for network operations.</p>':'<p>No saved evaluation probabilities. Training inputs are available above.</p>';
 $('margin').hidden=!e;$('margin').textContent=e?`${e.selected} versus ${e.compared_with} · log-odds ${e.log_odds_margin.toFixed(3)} = intercept ${e.intercept_difference.toFixed(3)} + shown contributions + remainder ${e.remaining_contribution.toFixed(3)}`:'';
 $('contributions').innerHTML=e?table(['Feature','Value','Weight difference','Contribution'],e.top_contributions.map(c=>[esc(c.feature),c.value.toFixed(3),c.coefficient_difference.toFixed(3),c.contribution.toFixed(3)])):'';
 $('vector-details').hidden=state.arm.startsWith('jev_');$('vector').textContent=pretty(report||{vector:detail.packet_vector,explanation:e||null});
}
$('split').addEventListener('change',()=>{state.split=$('split').value;state.report=0;$('references').open=false;families();});$('family').addEventListener('change',()=>pairs());$('pair').addEventListener('change',()=>selectPacket('a'));
for(const l of ['a','b'])$('packet-'+l).addEventListener('click',()=>{state.report=0;selectPacket(l);});
$('arm').addEventListener('change',()=>{state.arm=$('arm').value+'__'+$('grouping').value;load();});$('grouping').addEventListener('change',()=>{state.arm=$('arm').value+'__'+$('grouping').value;load();});$('report').addEventListener('change',()=>{state.report=Number($('report').value);load();});$('field').addEventListener('change',renderWeights);$('references').addEventListener('toggle',()=>{if(detail)render();});
$('download').addEventListener('click',()=>{const a=document.createElement('a');a.href='/api/declaration-trust/export?'+new URLSearchParams({id:state.id,split:state.split,arm:state.arm,report:state.report});a.download=state.id+'-'+state.arm+'-input.json';a.click();});
$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(pretty(detail.request));status('Exact input copied. It contains no API key or reference answers.');}catch{$('copy-text').value=pretty(detail.request);$('copy-dialog').showModal();$('copy-text').select();}});$('close-copy').addEventListener('click',()=>$('copy-dialog').close());
(async()=>{try{catalog=await api('/api/declaration-trust/catalog');renderScores();status(catalog.status);const q=new URLSearchParams(location.search);if(q.get('arm') in catalog.arms)state.arm=q.get('arm');$('split').value=state.split;options('arm',Object.entries(catalog.readers),state.arm.split('__')[0]);options('grouping',Object.entries(catalog.policies),state.arm.split('__')[1]);const row=catalog.cases[state.split].find(r=>r.id===q.get('case'))||catalog.cases[state.split][0];options('family',[...new Set(catalog.cases[state.split].map(r=>r.family))].map(f=>[f,f]),row.family);options('pair',[...new Set(catalog.cases[state.split].filter(r=>r.family===row.family).map(r=>r.pair_id))].map((p,i)=>[p,'Pair '+(i+1)]),row.pair_id);state.id=row.id;state.report=Number(q.get('report')||0);await load();}catch(e){status(e.message,true);}})();
