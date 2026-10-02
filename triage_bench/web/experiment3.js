'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty = value => JSON.stringify(value, null, 2);
const fields = {initial_owner:'Investigating team', priority:'Priority', next_check:'Next check', insufficient_evidence:'Evidence insufficient'};
const stages = ['evidence','facts','input','decisions'];
const guides = ['Start with the observation and the field that changes between A and B.', 'Follow the supporting paths and compare measurement age with report age.', 'Compare the added facts with the baseline. Policy and questions are identical.', 'Inspect each error against the draft rationale, then switch to the paired packet.'];
const pageQuery=new URLSearchParams(location.search);
const trial=['questions','conflicts','selection','robustness','structured','wording'].includes(pageQuery.get('trial'))?pageQuery.get('trial'):'facts';
const repetition=['1','2','3'].includes(pageQuery.get('repetition'))?pageQuery.get('repetition'):'1';
const repeatTrial=trial==='conflicts'||trial==='robustness';
const selectionTrial=trial==='selection'||trial==='robustness';
const wordingTrial=trial==='wording';
const mlTrial=trial==='structured'||wordingTrial;
const questionTrial=trial==='questions'||trial==='conflicts';
let catalog, detail, selected = {}, stage = 'evidence', generation = 0;
async function api(path, options) {
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
  return result;
}
function notice(message, error=false) { $('notice').textContent=message; $('notice').classList.toggle('error',error); }
function options(id, rows, value) {
  $(id).replaceChildren(...rows.map(([key,label]) => { const o=document.createElement('option');o.value=key;o.textContent=label;return o; }));
  if (rows.some(r=>r[0]===value)) $(id).value=value;
}
function metric(value) { return Number.isFinite(value) ? (100*value).toFixed(1)+'%' : 'Unavailable'; }
function minutes(value) {
  if(value===null||value===undefined)return 'Unknown';
  const seconds=Math.round(value*60),whole=Math.floor(seconds/60),part=seconds%60;
  return part?`${whole} min ${part} s`:`${whole} min`;
}
function scores() {
  const pilot=catalog.pilot,hosted=catalog.hosted_pilot;
  $('comparison').value=trial;
  if(trial!=='facts'&&!mlTrial) {
    $('data-summary').textContent=`${catalog.manifest.records} development packets · ${catalog.manifest.pairs} pairs · no training split`;
    $('hero-title').innerHTML='Follow the evidence.<br>Test how the questions change decisions.';
    $('hero-intro').textContent='Hold the evidence fixed, compare exact question wording, then inspect the saved Jev decisions.';
    $('results-heading').textContent='Same evidence, two question arms';
    $('variant-label').textContent='Question wording';
    $('provenance-label').textContent='Inspect saved run provenance';
    for(const link of document.querySelectorAll('[data-main-guide]'))link.href='/study?doc=experiment-3-questions';
    $('comparison-description').textContent='Identical combined evidence in both arms. Only owner, diagnostic and evidence-sufficiency instructions change. Checkpoint, policy, choices and priority question stay fixed. References remain provisional.';
    $('run-local').hidden=true; $('split').disabled=true;
  }
  if(selectionTrial) {
    $('hero-title').innerHTML='Select usable evidence.<br>Keep the questions fixed.';
    $('hero-intro').textContent='Inspect what software retains or removes, then compare three Jev inputs on the same new packets.';
    $('results-heading').textContent='Same packets, three evidence inputs';
    $('variant-label').textContent='Evidence input';
    $('comparison-description').textContent='The combined baseline, explicit eligibility facts and eligible observations only use identical explicit questions. Current contradictions remain in the input. References are provisional.';
  }
  if(trial==='conflicts') {
    $('repetition-label').hidden=false;$('repetition').value=repetition;
    $('hero-title').innerHTML='Repeat fixed questions.<br>Inspect where decisions hold or vary.';
    $('hero-intro').textContent='Four new conflict pairs, two frozen question sets and three planned repetitions. Repeated responses are not independent incidents.';
    $('results-heading').textContent='Repetition '+repetition+' · same evidence, two question arms';
    $('comparison-description').textContent='The questions and combined evidence remain fixed across repetitions. Only the paired nominal-reading timestamp changes from current to stale. Eight distinct packets are repeated three times; references remain drafts.';
    for(const link of document.querySelectorAll('[data-main-guide]'))link.href='/study?doc=experiment-3-conflicts';
  }
  if(trial==='robustness') {
    $('repetition-label').hidden=false;$('repetition').value=repetition;
    $('hero-title').innerHTML='Test where the filter holds.<br>Repeat fixed requests.';
    $('hero-intro').textContent='Inspect validity limits, inventory gaps and multiple current faults. The filter and explicit questions remain unchanged.';
    $('results-heading').textContent='Repetition '+repetition+' · combined versus selected evidence';
    $('comparison-description').textContent='Eight new packets in four correlated pairs compare combined facts and selected observations. Three repeats check decision agreement. The multiple-domain reference remains a draft interpretation.';
  }
  if(mlTrial) {
    const splits=catalog.manifest.splits;
    $('data-summary').textContent=`${splits.train.records} training packets · ${splits.development.records} development packets`;
    $('hero-title').innerHTML='Give facts a place in the model.<br>Inspect what the weights learn.';
    $('hero-intro').textContent='Compare structured dependency and freshness features with the same compact text baseline. Every observation stays available.';
    $('results-heading').textContent='Same training recipe, four feature sets';
    $('comparison-description').textContent='One matched fit per arm on 96 training packets, scored on 64 development packets. Only the added feature blocks vary. Jev stays frozen; references remain provisional.';
    $('variant-label').textContent='ML features';
    $('input-heading').textContent='Exact features supplied to ML';
    $('copy-request').textContent='Copy ML input';
    $('request-summary').textContent='Inspect full ML input and fitted nonzero vector';
    $('fingerprints-summary').textContent='Inspect input fingerprints';
    $('hosted-details').hidden=true;
  }
  if(wordingTrial) {
    $('hero-title').innerHTML='Change the training words.<br>Inspect what transfers.';
    $('hero-intro').textContent='Can tests and diagnostics describe both healthy and faulty readings without confusing the classifier?';
    $('results-heading').textContent='Same features, three training wordings';
    $('comparison-description').textContent='Each arm fits 96 matched training packets and scores the same 80 new development packets. The primary comparison swaps only tests/diagnostics nouns between coupled and counterbalanced training. Original wording provides a bridge control.';
    $('variant-label').textContent='Training wording';
    $('run-local').textContent='Replay wording comparison';
    $('wording-summary').hidden=false;
    $('wording-summary').innerHTML=`<h3>What changes in training?</h3><p>The feature recipe stays fixed. Each arm learns its vocabulary and weights from its own training wording. Counts below cover the twelve domain families; the four extra teaching families stay unchanged. Counts balance across domains; per-domain counts differ by one pair.</p><table><thead><tr><th>Training wording</th><th>Fault reports: tests / diagnostics</th><th>Normal reports: tests / diagnostics</th></tr></thead><tbody>${Object.entries(catalog.manifest.training_word_counts).map(([a,c])=>`<tr><td>${esc(catalog.variants[a])}</td><td>${c.fault.tests} / ${c.fault.diagnostics}</td><td>${c.normal.tests} / ${c.normal.diagnostics}</td></tr>`).join('')}</tbody></table><p>Choose <strong>Training</strong> under Data split to compare the actual report words. Development inputs are identical across arms; fitted feature vectors can differ because training-only vocabularies change.</p>`;
  }
  $('jev-summary').textContent=mlTrial?'This is a local ML comparison. No Jev calls are planned.':hosted?`${hosted.attempted_requests} Jev requests attempted; ${hosted.failed_requests} failed.`:'Jev has not run on this pack.';
  if(catalog.repeat_summary)$('jev-summary').textContent=`${catalog.repeat_summary.attempted_requests} Jev requests attempted across three repetitions; ${catalog.repeat_summary.failed_requests} failed.`;
  const rows=[];
  if(pilot)for(const v of [...Object.keys(catalog.variants),'rules'])rows.push({name:v==='rules'?'Rules':'ML · '+catalog.variants[v],metrics:pilot.approaches[v].metrics});
  if(hosted)for(const v of Object.keys(catalog.variants))rows.push({name:'Jev · '+catalog.variants[v],metrics:hosted.approaches[v].metrics,hosted:true});
  $('scores').innerHTML=rows.length?`<table><caption class="muted">Development packets · controlled pairs · provisional references</caption><thead><tr><th>Approach / input</th><th>All four correct</th><th>Three semantic decisions</th><th>Both packets correct</th><th>Owner / next check / evidence</th></tr></thead><tbody>${rows.map(r=>{const m=r.metrics;return `<tr class="${r.hosted?'hosted-row':''}"><td>${esc(r.name)}<small>${m.records} packets · ${m.attempted_records} attempted · ${m.failed_records} failed · ${m.missing_records} missing</small></td><td>${metric(m.all_fields_accuracy)}</td><td>${metric(m.semantic_decisions_accuracy)}</td><td>${metric(m.pair_all_fields_accuracy)}</td><td>${['initial_owner','next_check','insufficient_evidence'].map(f=>metric(m.fields[f].accuracy)).join(' / ')}</td></tr>`;}).join('')}</tbody></table><p class="muted">The scores use this draft pack, with failures and missing responses in the denominator. All four decisions remain visible. These results do not establish operational performance or an improvement over experiments 1 and 2.</p>`:`<p>${esc(catalog.status)}</p><p>Raw evidence, calculated facts and prepared Jev requests are available without saved runs.</p>`;
  if(pilot&&hosted&&(pilot.input_sha256!==hosted.input_sha256||pilot.label_sha256!==hosted.label_sha256))$('scores').insertAdjacentHTML('beforeend','<p class="change">The local and hosted runs cover different packets or references. Compare their per-packet decisions; aggregate scores are not matched.</p>');
  $('repeat-summary').innerHTML=catalog.repeat_summary?`<h3>Across all three repetitions</h3><p class="muted">Eight distinct packets, four correlated pairs. Agreement does not establish correctness.</p><table><thead><tr><th>${trial==='robustness'?'Input':'Questions'}</th><th>Correct responses</th><th>Both packets correct</th><th>Identical decisions on all repeats</th><th>Correct on all repeats</th></tr></thead><tbody>${Object.entries(catalog.repeat_summary.approaches).map(([a,m])=>`<tr><td>${esc(catalog.variants[a])}</td><td>${m.fully_correct_responses}/${m.planned_packet_responses}</td><td>${m.pair_successes}/${m.planned_pairs}</td><td>${m.cases_with_identical_decisions}/${m.distinct_packets}</td><td>${m.cases_correct_in_every_repetition}/${m.distinct_packets}</td></tr>`).join('')}</tbody></table>`:'';
  $('ml-changes').hidden=!mlTrial;
  if(mlTrial)$('ml-changes').innerHTML=catalog.changes?`<h3>Fixes and regressions against ${wordingTrial?'matched coupled wording':'the text baseline'}</h3><p>Newly wrong fields count even when the control already failed the packet. A gain in complete packets can conceal these regressions.</p><table><thead><tr><th>${wordingTrial?'Training wording':'Feature set'}</th><th>Packets fixed</th><th>Correct packets lost</th><th>Newly wrong owner / check / evidence</th></tr></thead><tbody>${Object.entries(catalog.changes).map(([a,c])=>`<tr><td>${esc(catalog.variants[a])}</td><td>${c.packets_fixed.length}</td><td>${c.packets_lost.length}</td><td>${['initial_owner','next_check','insufficient_evidence'].map(f=>c.newly_wrong_fields[f].length).join(' / ')}</td></tr>`).join('')}</tbody></table>`:'<p>No saved matched predictions.</p>';
  if(wordingTrial&&pilot) {
    const d=catalog.diagnostics,arms=Object.keys(catalog.variants);
    $('wording-summary').insertAdjacentHTML('beforeend',`<h3>What transfers, and what regresses?</h3><table><thead><tr><th>Control</th>${arms.map(a=>`<th>${esc(catalog.variants[a])}</th>`).join('')}</tr></thead><tbody>${Object.keys(d.baseline.controls).map(g=>`<tr><td>${esc(g)}</td>${arms.map(a=>`<td>${d[a].controls[g].correct}/${d[a].controls[g].packets}</td>`).join('')}</tr>`).join('')}<tr><td>Synonym pairs: identical four decisions</td>${arms.map(a=>`<td>${d[a].synonym_agreement}/${d[a].synonym_pairs}</td>`).join('')}</tr><tr><td>Synonym pairs: both packets correct</td>${arms.map(a=>`<td>${d[a].synonym_pairs_correct}/${d[a].synonym_pairs}</td>`).join('')}</tr></tbody></table><p>Counterbalancing makes ${d.balanced.synonym_agreement} synonym pairs stable, but only ${d.balanced.synonym_pairs_correct} correct. Stability can preserve a wrong decision.</p><h3>The method-word shortcut weakens</h3><p>Coefficients below compare NOC with power in the supported/current observation channel. Positive favors NOC; negative favors power. They are fitted coefficients, not packet contributions or calibrated confidence.</p><table><thead><tr><th>Training wording</th><th>tests</th><th>diagnostics</th></tr></thead><tbody>${arms.map(a=>`<tr><td>${esc(catalog.variants[a])}</td>${['tests','diagnostics'].map(w=>`<td>${pilot.approaches[a].method_weights[w].in_vocabulary?pilot.approaches[a].method_weights[w].noc_minus_domain.power.toFixed(3):'Outside vocabulary'}</td>`).join('')}</tr>`).join('')}</tbody></table><p>Matched complete-packet scores: ${Math.round(pilot.approaches.coupled.metrics.all_fields_accuracy*pilot.development_records)}/${pilot.development_records} coupled, ${Math.round(pilot.approaches.balanced.metrics.all_fields_accuracy*pilot.development_records)}/${pilot.development_records} counterbalanced. <a href="/experiment-3?trial=wording&case=NSW-834dfcc6be01-b&variant=balanced#decisions">Inspect the stale-conflict fix</a> or <a href="/experiment-3?trial=wording&case=NSW-ebc3b6e65b9a-a&variant=balanced#decisions">inspect a new power-owner regression</a>.</p>`);
  }
  $('provenance').textContent=pretty({data:catalog.manifest,local:pilot?{id:pilot.run_id,source_sha256:pilot.source_sha256,training:pilot.approaches.baseline.training}:null,hosted:hosted?{id:hosted.run_id,status:hosted.status,model:hosted.requested_model,endpoint:hosted.endpoint,execution:hosted.execution,requests_sha256:hosted.requests_sha256,source_sha256:hosted.source_sha256,stopped_reason:hosted.stopped_reason}:null});
}
function chooseFamilies(preferred) {
  const families=[...new Set(catalog.cases[$('split').value].map(r=>r.family))];
  options('family',families.map(f=>[f,f]),preferred);choosePairs();
}
function choosePairs(preferred) {
  const rows=catalog.cases[$('split').value].filter(r=>r.family===$('family').value);
  const pairs=[...new Set(rows.map(r=>r.pair_id))];
  options('pair',pairs.map((p,i)=>[p,`Pair ${i+1}`]),preferred);selected.packet='a';loadCase();
}
async function loadCase() {
  const token=++generation;
  detail=null; $('copy-request').disabled=true; $('download-request').disabled=true;
  document.querySelector('.workbench').setAttribute('aria-busy','true');
  const rows=catalog.cases[$('split').value].filter(r=>r.pair_id===$('pair').value);
  const row=rows.find(r=>r.id.endsWith('-'+(selected.packet||'a'))) || rows[0];
  selected={split:$('split').value,id:row.id,variant:$('variant').value,packet:row.id.slice(-1)};
  $('case-count').textContent=`${rows.length} packets · one controlled change`;
  for (const letter of ['a','b']) $('packet-'+letter).setAttribute('aria-pressed',String(selected.packet===letter));
  try {
    const result=await api('/api/experiment3/case?'+new URLSearchParams({trial,repetition,id:selected.id,split:selected.split,variant:selected.variant}));
    if(token!==generation)return;
    detail=result;renderCase();
    $('copy-request').disabled=false; $('download-request').disabled=false;
    document.querySelector('.workbench').setAttribute('aria-busy','false');
    showStage(stage);
  } catch(error) { if(token===generation){notice(error.message,true);document.querySelector('.workbench').setAttribute('aria-busy','false');} }
}
function valueAt(packet,path) { return path.replace(/^input\./,'').replace(/\[(\d+)\]/g,'.$1').split('.').reduce((o,k)=>o?.[k],packet); }
function rawGraph(packet) {
  const t=packet.topology||{}, nodes=t.nodes||[], edges=t.edges||[];
  if(!nodes.length)return '<p class="status tone-unknown">Topology is missing. Dependency coverage stays unknown.</p>';
  const levels=new Map(), queue=(packet.service_impact.affected_site_ids||[]).filter(n=>nodes.includes(n)).map(n=>[n,0]);
  while(queue.length){const [node,level]=queue.shift();if(levels.has(node))continue;levels.set(node,level);for(const [a,b] of edges)if(a===node)queue.push([b,level+1]);}
  const last=Math.max(0,...levels.values())+1;
  for(const node of nodes)if(!levels.has(node))levels.set(node,last);
  const columns=Array.from({length:last+1},(_,i)=>nodes.filter(n=>levels.get(n)===i));
  const width=Math.max(540,columns.length*145),height=Math.max(160,...columns.map(c=>c.length*44+30));
  const positions=new Map();columns.forEach((col,i)=>col.forEach((n,j)=>positions.set(n,[60+i*(width-120)/Math.max(1,last),30+j*44])));
  return `<p class="muted">Coverage: ${esc(t.coverage||'unknown')} · scope: ${esc(t.scope||'unknown')}</p><div class="graph"><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Directed dependency graph, arrows from sites toward required components"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#6a927b"/></marker></defs>${edges.map(([a,b])=>{const start=positions.get(a),end=positions.get(b);return start&&end?`<line x1="${start[0]}" y1="${start[1]}" x2="${end[0]}" y2="${end[1]}" stroke="#90b29b" stroke-width="1.5" marker-end="url(#arrow)"/>`:'';}).join('')}${nodes.map(n=>{const [x,y]=positions.get(n),site=(packet.service_impact.affected_site_ids||[]).includes(n);return `<g><rect x="${x-51}" y="${y-12}" width="102" height="25" rx="6" fill="${site?'#d7ed93':'#edf3e9'}" stroke="#98b6a0"/><text x="${x}" y="${y+4}" text-anchor="middle">${esc(n)}</text></g>`;}).join('')}</svg></div><details><summary>Inspect every directed edge</summary><pre>${esc(pretty(edges))}</pre></details>`;
}
function renderCase() {
  const p=detail.record.input,key=detail.draft_reference;
  $('packet-id').textContent=`${detail.record.id} · ${key.incident_family_id} · ${key.pair_kind==='decision_change'?'draft decision should change':'draft decision should stay the same'}`;
  $('pair-change').innerHTML=`<strong>Only ${esc(key.changed_path)} changes between A and B.</strong><div class="pair-values"><div><small>This packet · ${esc(selected.packet.toUpperCase())}</small><pre>${esc(pretty(valueAt(p,key.changed_path)))}</pre></div><div><small>Paired packet · ${esc(detail.paired.id.slice(-1).toUpperCase())}</small><pre>${esc(pretty(valueAt(detail.paired.input,key.changed_path)))}</pre></div></div>`;
  $('decision-time').textContent=p.decision_timestamp;
  $('impact').innerHTML=`<div class="impact"><span>${esc(p.service_impact.status)}</span><span>${esc(p.service_impact.affected_sites)} affected ${p.service_impact.affected_sites===1?'site':'sites'}</span><span>${esc(p.service_impact.basis)}</span></div>`;
  $('observations').innerHTML=p.observations.map((o,i)=>`<div class="observation"><span class="number">${i+1}</span><div><p>${esc(o.detail)}</p><small>Asset ${esc(o.asset_id)} · measured ${esc(o.measured_at||'unknown')} · arrived ${esc(o.observed_at)}</small><small>Declared validity ${esc(o.valid_for_minutes)} minutes · ${esc(o.source)}</small></div></div>`).join('');
  $('topology').innerHTML=rawGraph(p);$('change-record').textContent=`${p.change_record.status}: ${p.change_record.detail}`;$('raw').textContent=pretty(detail.record);
  $('dependency-included').textContent=wordingTrial||(!mlTrial&&trial!=='facts')||['dependency','combined'].includes(selected.variant)?'Included in this variant':'Not included in this variant';
  $('measurement-included').textContent=wordingTrial||(!mlTrial&&trial!=='facts')||['measurement','combined'].includes(selected.variant)?'Included in this variant':'Not included in this variant';
  $('dependency').innerHTML=detail.dependency_facts.map(f=>`<div class="dependency-card"><strong>Observation ${f.observation_index+1} · ${esc(f.asset_id||'unknown asset')}</strong> <span class="status ${f.relation==='unknown'?'tone-unknown':'tone-current'}">${esc(f.relation.replaceAll('_',' '))}</span><p class="muted">${f.supported_site_count} supported · ${f.excluded_site_count} excluded · ${f.unknown_site_count===null?'unknown scope':f.unknown_site_count+' unknown'}</p><div class="paths">${f.supporting_paths.map(p=>`<span class="path">${p.path.map(esc).join(' → ')}</span>`).join('')}</div>${f.excluded_sites.length?`<p class="muted">Excluded by the complete map: ${f.excluded_sites.map(esc).join(', ')}</p>`:''}${f.unknown_sites.length?`<p class="muted">Relationship unknown for: ${f.unknown_sites.map(esc).join(', ')}</p>`:''}</div>`).join('');
  $('measurement').innerHTML=`<table><thead><tr><th>Observation</th><th>Report age</th><th>Measurement age</th><th>Declared window</th><th>Status</th></tr></thead><tbody>${detail.measurement_facts.map(f=>`<tr><td>${f.observation_index+1}</td><td>${minutes(f.report_age_minutes)}</td><td>${minutes(f.measurement_age_minutes)}</td><td>${f.declared_valid_for_minutes??'Unknown'} min</td><td><span class="status tone-${f.freshness_status}">${f.freshness_status}</span></td></tr>`).join('')}</tbody></table>`;
  $('baseline-heading').textContent=wordingTrial?'Original training input':questionTrial?'Original questions':selectionTrial?'Combined facts':'Compact baseline';
  $('baseline-packet').textContent=pretty(questionTrial?detail.question_sets.original:detail.packets.baseline);$('selected-packet').textContent=pretty(questionTrial?detail.question_sets[selected.variant]:detail.packets[selected.variant]);$('selected-heading').textContent=catalog.variants[selected.variant];
  if(mlTrial)$('input-meta').textContent=`${catalog.variants[selected.variant]} · ${wordingTrial?'arm-specific training-only vocabulary':'common training-only text vocabulary'} · ${detail.request.fitted_vector?detail.request.fitted_vector.semantic.dimensions.toLocaleString()+' semantic features':'fitted vector unavailable'}`;
  else $('input-meta').textContent=`${catalog.variants[selected.variant]} · ${detail.request.model} · ${detail.request_bytes.toLocaleString()} request bytes · ${questionTrial?'identical state across question arms':'identical policy and questions across variants'}`;
  $('request-note').textContent=selected.split==='train'?'This is a prepared training-packet request. Training packets do not enter hosted evaluation.':detail.hosted_outputs?.[selected.variant]?'The saved Jev run used this state, the fixed policy and identical questions. The corresponding local ML variant receives the same state string. Inspect the saved request and response in Decisions.':'The selected ML variant receives the same state string. Policy, checkpoint and questions stay fixed across variants. No saved hosted response exists for this packet and variant.';
  if(questionTrial)$('request-note').textContent='Both arms receive the same combined state string. Compare the full questions below, then inspect the saved request and response in Decisions. Priority and valid choices are unchanged.';
  if(selectionTrial)$('request-note').textContent='Compare the combined baseline with the selected input. Every input uses the frozen explicit questions. Removed reports stay in Raw evidence, outside the selected request. No reference decisions enter Jev.';
  if(selectionTrial)$('facts-note').textContent='Dependency and age facts below describe every raw report. The eligibility table shows which observations and fact rows enter the selected request. The calculators do not read reference answers.';
  $('eligibility-review').hidden=!selectionTrial;
  if(selectionTrial) {
    $('eligibility-note').textContent=selected.variant==='selected'?'Only eligible observations and their reindexed facts enter this request. Source numbers refer to Raw evidence.':selected.variant==='eligibility'?'All reports remain. An added block marks eligibility without selecting a fault domain.':'All reports and the existing dependency and age facts remain. The eligibility calculation below is for inspection only.';
    const kept=detail.eligibility.filter(r=>r.eligible);
    $('eligibility-rows').innerHTML=`<table><thead><tr><th>Raw observation</th><th>Freshness</th><th>Supported sites</th><th>Eligible</th><th>Reason</th><th>Request observation</th></tr></thead><tbody>${detail.eligibility.map(r=>`<tr><td>${r.observation_index+1}</td><td>${esc(r.freshness_status)}</td><td>${r.supported_site_count}</td><td>${r.eligible?'Yes':'No'}</td><td>${esc(r.reasons.join(', ')||'Current and related')}</td><td>${selected.variant==='selected'?(r.eligible?kept.indexOf(r)+1:'Removed'):r.observation_index+1}</td></tr>`).join('')}</tbody></table>`;
    if(selected.variant==='selected')for(const id of ['dependency-included','measurement-included'])$(id).textContent='Only retained observations enter Jev';
  }
  if(mlTrial) {
    $('request-note').textContent='All arms share the same compact text and impact features. This arm adds the counts and observation channels shown below. The fitted vector is saved evidence, not a hosted request. No reference decisions enter the feature calculator.';
    $('ml-input-channels').hidden=false;
    $('ml-counts').textContent=Object.entries(detail.request.structured_counts).map(([k,v])=>`${k.replace('observation_count/','')}: ${v}`).join(' · ')||'The text baseline uses common compact text and impact features.';
    $('ml-channel-table').innerHTML=detail.request.observation_channels.length?`<table><thead><tr><th>Observation</th><th>Feature channel</th><th>Words supplied to the channel</th></tr></thead><tbody>${detail.request.observation_channels.map(o=>`<tr><td>${o.observation_index+1}</td><td>${esc(o.channel)}</td><td>${esc(o.text)}</td></tr>`).join('')}</tbody></table>`:'';
    $('facts-note').textContent='The same calculators supply dependency and freshness categories. The selected ML arm binds each observation text to its category without removing observations or assigning a fault domain.';
  }
  if(wordingTrial)$('request-note').textContent=selected.split==='train'?'Each arm fits this packet with the report wording shown below. Its target decisions and non-text evidence stay fixed. Training packets have no saved evaluation predictions.':'All arms receive this same development evidence and use both structured feature blocks. Their training-only vocabularies and fitted weights can differ. The saved nonzero vector belongs to the selected training arm.';
  $('training-wordings').hidden=!wordingTrial;
  if(wordingTrial)$('training-wordings').innerHTML=detail.training_wordings?`<h4>Actual training reports, same packet</h4><table><thead><tr><th>Training arm</th><th>Report wording</th></tr></thead><tbody>${Object.entries(detail.training_wordings).map(([a,rows])=>`<tr><td>${esc(catalog.variants[a])}</td><td>${rows.map(esc).join('<br><br>')}</td></tr>`).join('')}</tbody></table><p>Coupled and counterbalanced reports differ only in method nouns. The references, dependency graph, timestamps and impact stay the same.</p>`:'<p>Every arm receives the same development evidence. Switch Data split to Training to inspect the intervention.</p>';
  $('request').textContent=pretty(detail.request);$('request-hashes').textContent=pretty(mlTrial?{text_state_sha256:detail.state_sha256,input_sha256:detail.input_sha256}:{state_sha256:detail.state_sha256,questions_sha256:detail.questions_sha256});
  $('reference').open=false;$('reference-content').innerHTML=`<p class="status tone-unknown">Draft · not reviewed by a network specialist</p><table><tbody>${Object.entries(fields).map(([f,label])=>`<tr><th>${label}</th><td>${esc(key.labels[f])}</td></tr>`).join('')}</tbody></table><h4>Pair rationale (A → B)</h4><p>The rationale describes the paired intervention. The table above applies to the selected packet.</p><p>${esc(key.label_rationale)}</p>`;
  decisions();probabilities();
}
function decisions() {
  const output=detail.outputs,hosted=detail.hosted_outputs||{},hasLocal=!!catalog.pilot,hasHosted=!!catalog.hosted_pilot;
  $('decision-note').textContent=selected.split==='train'?'This packet was used for training. Evaluation predictions are unavailable; inspect the draft reference separately.':'Actual saved decisions. References remain drafts. Reveal them to mark disagreements. Missing and failed responses remain explicit.';
  const rows=[];
  if(hasLocal)for(const v of [...Object.keys(catalog.variants),'rules'])rows.push({name:v==='rules'?'Rules':'ML · '+catalog.variants[v],row:output[v],selected:v===selected.variant});
  if(hasHosted)for(const v of Object.keys(catalog.variants))rows.push({name:'Jev · '+catalog.variants[v],row:hosted[v],selected:v===selected.variant,hosted:true});
  $('decisions').innerHTML=selected.split==='train'||!rows.length?'<p>No saved evaluation predictions for this packet.</p>':`<table><thead><tr><th>Approach</th>${Object.values(fields).map(f=>`<th>${f}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr class="${r.selected?'selected-row':''}"><td>${esc(r.name)}</td>${Object.keys(fields).map(f=>{const prediction=r.row?.status==='ok'?r.row.predictions?.[f]:null;return `<td>${prediction?`<span class="${$('reference').open?(detail.draft_reference.accepted_answers[f].includes(prediction)?'status tone-correct':'status tone-error'):''}">${esc(prediction)}</span>`:r.row?.status==='error'?'Failed response':'Not attempted'}</td>`;}).join('')}</tr>`).join('')}${mlTrial||hasHosted?'':'<tr><td>Jev · input variants</td><td colspan="4">No saved hosted run</td></tr>'}</tbody></table>`;
  $('repeated-decisions').innerHTML=repeatTrial?`<h4>This packet across three planned repetitions</h4><table><thead><tr><th>${trial==='robustness'?'Input arm':'Question arm'}</th><th>Repeat</th>${Object.values(fields).map(f=>`<th>${f}</th>`).join('')}</tr></thead><tbody>${Object.keys(catalog.variants).flatMap(a=>[1,2,3].map(n=>{const row=detail.repeated_outputs?.[String(n)]?.[a];return `<tr class="${String(n)===repetition&&a===selected.variant?'selected-row':''}"><td>${esc(catalog.variants[a])}</td><td>${n}</td>${Object.keys(fields).map(f=>{const v=row?.status==='ok'?row.predictions[f]:null;return `<td>${v?`<span class="${$('reference').open?(detail.draft_reference.accepted_answers[f].includes(v)?'status tone-correct':'status tone-error'):''}">${esc(v)}</span>`:row?'Failed response':'Not attempted'}</td>`;}).join('')}</tr>`;})).join('')}</tbody></table>`:'';
  const row=hosted[selected.variant],request=detail.hosted_saved_requests?.[selected.variant];
  $('hosted-evidence').textContent=pretty({variant:selected.variant,attempted:!!row,request:request||null,response:row||null});
}
function probabilities() {
  if(!detail)return;
  const field=$('probability-field').value;
  const cards=(group,rows)=>Object.keys(catalog.variants).map(v=>{const row=rows[v],dist=row?.status==='ok'?row.probabilities?.[field]:null;return `<div class="prob-card"><strong>${esc(group+' · '+catalog.variants[v])}</strong>${dist?Object.entries(dist).sort((a,b)=>b[1]-a[1]).map(([c,p])=>`<div class="prob-bar"><span>${esc(c)}${row.predictions[field]===c?' ✓':''}</span><meter min="0" max="1" value="${p}" aria-label="${esc(c)} probability"></meter><span>${(p*100).toFixed(1)}%</span></div>`).join(''):'<p class="muted">No saved evaluation probabilities.</p>'}</div>`;}).join('');
  $('probabilities').innerHTML=`${trial!=='facts'&&!mlTrial?'':`<h4>Local ML probabilities</h4><div class="prob-grid">${cards('ML',detail.outputs)}</div>`}${mlTrial?'':`<h4>Hosted Jev probabilities</h4><div class="prob-grid">${cards('Jev',detail.hosted_outputs||{})}</div>`}`;
  const explanation=detail.explanation?.[field];$('ml-microscope').hidden=!mlTrial;
  if(mlTrial){$('ml-margin').textContent=explanation?`${explanation.selected} versus ${explanation.compared_with} · log-odds margin ${explanation.log_odds_margin.toFixed(3)} · intercept ${explanation.intercept_difference.toFixed(3)} · remaining features ${explanation.remaining_contribution.toFixed(3)}`:'No saved fitted explanation for this packet.';
    $('ml-contributions').innerHTML=explanation?`<table><thead><tr><th>Feature</th><th>Input value</th><th>Weight difference</th><th>Contribution</th></tr></thead><tbody>${explanation.top_contributions.map(c=>`<tr><td>${esc(c.feature)}</td><td>${c.value.toFixed(3)}</td><td>${c.coefficient_difference.toFixed(3)}</td><td>${c.contribution.toFixed(3)}</td></tr>`).join('')}</tbody></table>`:'';}
}
function showStage(value,focus=false) {
  stage=stages.includes(value)?value:'evidence';
  for(const name of stages){const active=name===stage;$('stage-'+name).hidden=!active;$('tab-'+name).setAttribute('aria-selected',String(active));$('tab-'+name).tabIndex=active?0:-1;}
  const index=stages.indexOf(stage);$('previous-stage').disabled=index===0;$('next-stage').disabled=index===3;$('next-stage').textContent=['Calculate facts →','Compare input →','Inspect decisions →','Last step'][index];$('step-guide').textContent=wordingTrial&&stage==='input'?(selected.split==='train'?'Compare the actual training reports. Only method nouns change between the matched arms.':'Development inputs match; training words change the learned vocabulary and weights.'):mlTrial&&stage==='input'?'Compare added observation channels against the common text baseline.':questionTrial&&stage==='input'?'Compare the original and explicit instructions. Both receive identical evidence.':guides[index];
  if(detail)history.replaceState(null,'','/experiment-3?'+new URLSearchParams({trial,repetition,split:selected.split,case:selected.id,variant:selected.variant})+'#'+stage);
  for(const link of document.querySelectorAll('[data-main-guide]')) {
    const doc=wordingTrial?'experiment-3-wording':mlTrial?'experiment-3-structured':trial==='robustness'?'experiment-3-robustness':trial==='selection'?'experiment-3-selection':trial==='conflicts'?'experiment-3-conflicts':trial==='questions'?'experiment-3-questions':'experiment-3';
    link.href='/study?'+new URLSearchParams({doc,return:location.pathname+location.search+location.hash});
  }
  if(focus)$('tab-'+stage).focus();
}
$('repetition').addEventListener('change',()=>{location.href='/experiment-3?'+new URLSearchParams({trial,repetition:$('repetition').value,split:selected.split,case:selected.id,variant:selected.variant})+'#'+stage;});
$('comparison').addEventListener('change',()=>{location.href='/experiment-3?'+new URLSearchParams({trial:$('comparison').value});});
for(const button of document.querySelectorAll('[data-stage]')) {
  button.addEventListener('click',()=>showStage(button.dataset.stage));
  button.addEventListener('keydown',event=>{const i=stages.indexOf(stage);const n=event.key==='ArrowRight'?(i+1)%4:event.key==='ArrowLeft'?(i+3)%4:event.key==='Home'?0:event.key==='End'?3:null;if(n!==null){event.preventDefault();showStage(stages[n],true);}});
}
$('previous-stage').addEventListener('click',()=>showStage(stages[stages.indexOf(stage)-1],true));$('next-stage').addEventListener('click',()=>showStage(stages[stages.indexOf(stage)+1],true));
$('split').addEventListener('change',()=>chooseFamilies());$('family').addEventListener('change',()=>choosePairs());$('pair').addEventListener('change',()=>{selected.packet='a';loadCase();});$('variant').addEventListener('change',loadCase);
for(const letter of ['a','b'])$('packet-'+letter).addEventListener('click',()=>{selected.packet=letter;loadCase();});
$('probability-field').addEventListener('change',probabilities);
$('reference').addEventListener('toggle',()=>{if(detail)decisions();});
$('run-local').addEventListener('click',async()=>{
  $('run-local').disabled=true;notice('Fitting four local classifiers on training data and scoring development packets…');
  try { catalog=await api('/api/experiment3/run?'+new URLSearchParams({trial}),{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});scores();await loadCase();notice(catalog.status+' '+catalog.hosted_status); }catch(error){notice(error.message,true);}finally{$('run-local').disabled=false;}
});
$('download-request').addEventListener('click',()=>{if(!detail)return;const link=document.createElement('a');link.href='/api/experiment3/export?'+new URLSearchParams({trial,repetition,id:selected.id,split:selected.split,variant:selected.variant});link.download=`${selected.id}-${selected.variant}-request.json`;link.click();});
$('copy-request').addEventListener('click',async()=>{if(!detail)return;try{await navigator.clipboard.writeText(pretty(detail.request));notice(mlTrial?'Exact ML input copied. It contains no API key or draft reference.':'Exact request copied. It contains no API key or draft reference.');}catch{ $('copy-text').value=pretty(detail.request);$('copy-dialog').showModal();$('copy-text').select(); }});$('close-copy').addEventListener('click',()=>$('copy-dialog').close());
(async()=>{
  try {
    catalog=await api('/api/experiment3/catalog?'+new URLSearchParams({trial,repetition}));scores();options('variant',Object.entries(catalog.variants));
    const query=new URLSearchParams(location.search),split=query.get('split');if(split==='train'&&(trial==='facts'||mlTrial))$('split').value=split;
    const row=catalog.cases[$('split').value].find(r=>r.id===query.get('case'));
    options('family',[...new Set(catalog.cases[$('split').value].map(r=>r.family))].map(f=>[f,f]),row?.family);
    const rows=catalog.cases[$('split').value].filter(r=>r.family===$('family').value);
    options('pair',[...new Set(rows.map(r=>r.pair_id))].map((p,i)=>[p,`Pair ${i+1}`]),row?.pair_id);
    if(query.get('variant') in catalog.variants)$('variant').value=query.get('variant');
    selected.packet=row?.id.slice(-1)||'a';showStage(location.hash.slice(1));await loadCase();notice(catalog.status+' '+catalog.hosted_status);
  }catch(error){notice(error.message,true);$('run-local').disabled=true;}
})();
