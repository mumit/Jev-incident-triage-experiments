'use strict';
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty=value=>JSON.stringify(value,null,2);
const table=(headers,rows)=>`<table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
let catalog,selected,requestNumber=0;
const decisionNames={initial_owner:'Who investigates first?',priority:'Incident priority',next_check:'Next diagnostic check',insufficient_evidence:'Evidence insufficient?'};
function updateGuide(){const context=location.pathname+location.search+location.hash;$('guide').href='/study?'+new URLSearchParams({doc:'task-fit',return:context});$('advisory-guide').href='/study?'+new URLSearchParams({doc:'task-fit-analyst',return:context});}
async function get(url){const response=await fetch(url);const data=await response.json();if(!response.ok)throw new Error(data.error||'Evidence unavailable');return data;}
function summary(){
 const s=catalog.summaries.development;
 $('scores').innerHTML=s?table(['Jev arm','Correct readings','Correct pairs','Packet matches','Hidden reading errors'],Object.entries(s.metrics).map(([a,[m]])=>[catalog.arms[a],`${m.correct_readings}/${m.reports}`,`${m.reading_pairs_correct}/${m.complete_pairs}`,`${m.packet_matches}/${m.reports}`,m.masked_wrong_readings])):'No saved Jev results. Prepared inputs remain inspectable.';
 $('selection').textContent=catalog.candidate?`Frozen candidate: ${catalog.arms[catalog.candidate.arm]}. Selection used development readings, missed faults, repeated-label stability and arm simplicity. ${catalog.analyst_boundary?`The advisory display threshold is ${catalog.analyst_boundary.advisory_threshold.toFixed(2)}; every report requires analyst review.`:'The advisory boundary is unavailable.'}`:'No candidate has been frozen.';
 const local=catalog.summaries.local;
 $('bridges').innerHTML=local?table(['Text-only bridge','Correct readings','Packet matches','Hidden reading errors'],Object.entries(local.metrics).map(([a,[m]])=>[a==='rules'?'Report rules':`Report ML · ${a==='narrow'?'original':'broader'} phrases`,`${m.correct_readings}/${m.reports}`,`${m.packet_matches}/${m.reports}`,m.masked_wrong_readings])):'Local bridge evidence unavailable.';
 const rep=catalog.summaries.repeat;
 $('repetition').textContent=rep?`Repeated diagnostic: ${rep.attempted_requests} calls across six preselected reports and three repetitions. Label flips by arm: ${Object.entries(rep.repeatability).map(([a,m])=>`${a} ${m.reading_flips.length}`).join('; ')}. A stable answer can still be wrong; the primary timing-recovery failure was not among these six reports.`:'No repeated diagnostic is recorded.';
 $('status').textContent=catalog.status.length?catalog.status.join(' · '):'Saved evidence verifies. Inspecting this page makes no model calls.';
}
function evaluation(){
 const b=catalog.analyst_boundary,a=catalog.analyst_assessment;
 $('study-boundary').textContent='Draft references · '+(catalog.cases.evaluation?'held-out evaluation recorded':'evaluation remains sealed or unavailable')+' · analyst review required for every report';
 $('evaluation-result').hidden=!a?.reports;
 if(!a?.reports)return;
 $('inspect-evaluation-error').hidden=!catalog.first_wrong_suggestion;
 if(catalog.first_wrong_suggestion)$('inspect-evaluation-error').href='/task-fit?'+new URLSearchParams({split:'evaluation',case:catalog.first_wrong_suggestion,arm:b.arm})+'#decision';
 $('evaluation-status').textContent=`${a.reports} held-out reports · ${a.qualifying_readings} qualifying readings · ${a.domain_recommendations} domain suggestions · ${a.analyst_review_required} analyst reviews required. ${a.meets_research_criteria?'All provisional research criteria met.':'At least one provisional research criterion failed.'}`;
 const names={wrong_domain_recommendations:'Wrong domain suggestions',qualifying_reading_errors:'Wrong qualifying readings',qualifying_fault_misses:'Qualifying fault misses',reading_coverage:'Qualifying reading coverage',domain_coverage:'Domain suggestion coverage',failed_or_missing:'Failed or missing responses'};
 $('evaluation-scores').innerHTML=table(['Research criterion','Recorded limit','Measured','Result'],Object.entries(b.research_criteria).map(([k,v])=>{const name=k.replace(/^(minimum_|maximum_)/,'');return[names[name],`${k.startsWith('minimum_')?'At least':'At most'} ${name.endsWith('coverage')?Math.round(v*100)+'%':v}`,name.endsWith('coverage')?Math.round(a[name]*100)+'%':a[name],a.research_checks[k]?'Met':'Failed'];}));
}
function options(){
 const split=$('split').value;const cases=catalog.cases[split];const previous=$('case').value;
 $('case').innerHTML=cases.map(r=>`<option value="${esc(r.id)}">${esc(r.domain+' · '+r.family+' · '+r.id.slice(-1).toUpperCase())}</option>`).join('');
 if(cases.some(r=>r.id===previous))$('case').value=previous;
 const arms=split!=='development'&&catalog.candidate?{[catalog.candidate.arm]:catalog.arms[catalog.candidate.arm]}:catalog.arms;
 const arm=$('arm').value;$('arm').innerHTML=Object.entries(arms).map(([a,label])=>`<option value="${esc(a)}">${esc(label)}</option>`).join('');
 if(arm in arms)$('arm').value=arm;else if('structured' in arms)$('arm').value='structured';
}
function readUrl(){const q=new URLSearchParams(location.search);$('split').value=q.get('split') in catalog.cases?q.get('split'):'development';options();if(catalog.cases[$('split').value].some(r=>r.id===q.get('case')))$('case').value=q.get('case');if([...$('arm').options].some(o=>o.value===q.get('arm')))$('arm').value=q.get('arm');}
function coverage(){
 const split=$('split').value,arm=$('arm').value;const curve=catalog.summaries[split]?.review_curves?.[arm];
 $('coverage-source').textContent=`${split==='evaluation'?'Held-out evaluation of the frozen reader':split==='calibration'?'Calibration of the frozen reader':'Development exploration'} · ${catalog.arms[arm]}. This control changes the display only.`;
 if(!curve){$('threshold').disabled=true;$('curve').textContent='No measured review curve for this split and arm.';$('coverage-result').textContent='No coverage values are available.';return;}
 $('threshold').disabled=false;
 const previous=$('threshold').value;$('threshold').innerHTML=curve.points.map(p=>`<option value="${p.threshold}">${p.threshold.toFixed(2)}</option>`).join('');
 $('threshold').value=curve.points.some(p=>String(p.threshold)===previous)?previous:String(catalog.analyst_boundary?.advisory_threshold??0.9);
 const point=curve.points.find(p=>String(p.threshold)===$('threshold').value);
 const routing=catalog.summaries[split]?.routing_review?.arms?.[arm]?.find(p=>p.threshold===point.threshold);
 $('coverage-result').innerHTML=[[`${Math.round(point.coverage*100)}%`,'qualifying report readings'],[point.review_reports,'readings withheld'],[routing?.domain_recommendations??'—','domain recommendations'],[point.reading_errors,'qualifying reading errors']].map(([v,label])=>`<div><strong>${esc(v)}</strong><span>${esc(label)}</span></div>`).join('');
 $('curve').innerHTML=table(['Probability threshold','Qualifying readings','Readings withheld','Reading errors','Domain recommendations','Wrong domains'],curve.points.map(p=>{const route=catalog.summaries[split]?.routing_review?.arms?.[arm]?.find(r=>r.threshold===p.threshold);return[p.threshold.toFixed(2),p.eligible_recommendations,p.review_reports,p.reading_errors,route?.domain_recommendations??'—',route?.wrong_domain_recommendations??'—'];}));
 $('next-boundary').textContent=catalog.analyst_boundary?'Analyst-facing recommendations are selected. The frozen advisory evaluation uses probability '+catalog.analyst_boundary.advisory_threshold.toFixed(2)+'. Other sweep points are descriptive. Specialist-reviewed real reports are the next evidence needed.':'The analyst boundary is unavailable. Evaluation remains inaccessible until recorded evidence verifies.';
}
async function inspect(push=true){
 const number=++requestNumber;const split=$('split').value,id=$('case').value,arm=$('arm').value;
 selected=null;$('partner').disabled=true;$('reveal').disabled=true;
 $('references').hidden=true;$('reveal').textContent='Reveal draft references';$('status').textContent='Loading the selected report…';
 const q=new URLSearchParams({split,id,arm});
 try{
  const data=await get('/api/task-fit/case?'+q);if(number!==requestNumber)return;selected=data;$('partner').disabled=false;$('reveal').disabled=false;$('status').classList.remove('error');
  if(push)history.pushState(null,'','/task-fit?'+new URLSearchParams({split,case:id,arm})+location.hash);
  updateGuide();
  $('case-id').textContent=`${id} · ${split} · report ${id.slice(-1).toUpperCase()}`;
  const obs=data.record.input.observations[0];$('function').textContent='Measured function: '+obs.measurement_scope.function;$('report').textContent=obs.detail;
  $('request-status').textContent=data.saved_request?'This is the exact saved request.':'Prepared request only. No actual response is available for this selection.';
  $('state').textContent=data.request.state;$('question').textContent=pretty(data.request.questions.reading);$('request').textContent=pretty(data.request);
  const r=data.response;const ok=r?.status==='ok';
  $('advisory').hidden=!data.advisory;
  if(data.advisory){const a=data.advisory;const message=a.domain_recommendation?`Suggested initial team: ${a.domain_recommendation}.`:a.disposition==='policy_retains_noc'?'The reading qualifies, but the policy retains NOC.':'Reading suggestion withheld: '+a.disposition.replaceAll('_',' ')+'.';$('advisory').textContent=message+' Analyst review is required; no assignment occurs.';}
  $('response').innerHTML=ok?`<p>Jev returned <strong>${esc(r.reading)}</strong>.</p>`:'<p>No successful saved response for this selection. Missing results remain missing.</p>';
  $('probabilities').innerHTML=ok?Object.entries(r.probabilities).map(([label,p])=>`<div class="probability">${esc(label)}<strong>${(p*100).toFixed(1)}%</strong><meter min="0" max="1" value="${p}" aria-label="${esc(label)} probability">${p}</meter></div>`).join(''):'';
  $('confidence').textContent=ok?`Provider confidence: ${r.provider_confidence??'not supplied'}. This differs from the probability distribution and is not an observed correctness rate.`:'';
  $('policy').innerHTML=data.trace?table(['Software decision','Actual value'],Object.entries(data.trace.predictions).map(([key,value])=>[decisionNames[key]||key,value])):'Software has no valid interpretation to apply.';
  $('raw').textContent=pretty({request_sha256:data.saved_request?.request_sha256,response:data.response,policy_trace:data.trace?.trace,repeated_responses:data.repeats});
  $('local').textContent=Object.keys(data.local_controls).length?pretty(data.local_controls):'No local bridge predictions on this split.';
  $('status').textContent=catalog.status.length?catalog.status.join(' · '):'Exact saved request and response loaded. No model call was made.';
  coverage();
 }catch(error){if(number===requestNumber){$('status').textContent=error.message;$('status').classList.add('error');}}
}
$('split').addEventListener('change',()=>{options();inspect();});
$('case').addEventListener('change',()=>inspect());$('arm').addEventListener('change',()=>inspect());$('threshold').addEventListener('change',coverage);
$('partner').addEventListener('click',()=>{if(selected){$('case').value=selected.partner_id;inspect();}});
$('reveal').addEventListener('click',()=>{if(!selected)return;const show=$('references').hidden;$('references').hidden=!show;$('reveal').textContent=show?'Hide draft references':'Reveal draft references';$('reading-reference').textContent='Draft report reading: '+selected.reference.reading;$('packet-reference').textContent=pretty(selected.packet_reference);const correct=selected.response?.reading===selected.reference.reading;const packetCorrect=selected.trace&&Object.entries(selected.packet_reference).every(([k,v])=>selected.trace.predictions[k]===v);$('masked').textContent=!selected.response?'No saved response to compare.':correct?'The report reading matches this draft reference.':packetCorrect?'The reading is wrong even though every packet decision matches. Packet accuracy hides this error.':'The reading differs from the draft reference; inspect the downstream policy separately.';});
window.addEventListener('popstate',()=>{if(catalog){readUrl();if(selected&&selected.split===$('split').value&&selected.record.id===$('case').value&&selected.arm===$('arm').value){updateGuide();return;}inspect(false);}});
window.addEventListener('hashchange',updateGuide);
get('/api/task-fit/catalog').then(data=>{catalog=data;if(catalog.cases.evaluation)$('split').insertAdjacentHTML('beforeend','<option value="evaluation">Held-out evaluation</option>');summary();evaluation();readUrl();inspect(false);}).catch(error=>{$('status').textContent=error.message;});
