const copy=document.querySelector('#copy'),channel=document.querySelector('#channel'),report=document.querySelector('#report');
const escapeHTML=value=>String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
Promise.all([fetch('/demo/campaign.json').then(r=>r.json()),fetch('/demo/policy.json').then(r=>r.json())]).then(([campaign,policy])=>{window.policy=policy;copy.value=campaign.text;channel.value=campaign.channel;window.demo=campaign}).catch(()=>{report.innerHTML='<h2>Demo could not load</h2><p>Start this project with <code>python app.py</code> from its root folder.</p>'});
document.querySelector('#review').onclick=async()=>{
  report.innerHTML='<h2>Reviewing…</h2>';
  try{
    const campaign={...window.demo,text:copy.value,channel:channel.value};
    const r=await fetch('/api/review',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({campaign,policy:window.policy})});
    const x=await r.json(); if(!r.ok) throw new Error(x.error||'Review failed');
    const findings=x.findings.map(f=>`<div class="finding"><strong class="${escapeHTML(f.severity)}">${escapeHTML(f.rule)}</strong><p>Found: ${escapeHTML(f.evidence)}</p><small>Recommendation: ${escapeHTML(f.recommendation)}</small></div>`).join('')||'<p class="pass">✓ No policy issues detected. Ready for human review.</p>';
    const changes=x.rewrite_changes.map(item=>`<li>${escapeHTML(item)}</li>`).join('')||'<li>No rewrite was needed.</li>';
    report.innerHTML=`<p class="eyebrow">QA REPORT</p><div class="summary"><div class="score">${x.score}</div><div><span class="status">${escapeHTML(x.status.replaceAll('_',' '))}</span><p>${x.finding_count} issue${x.finding_count===1?'':'s'} found</p></div></div><div class="findings">${findings}</div><section class="rewrite"><div class="rewrite-head"><div><p class="eyebrow">SUGGESTED REWRITE</p><h2>Stronger first draft</h2></div><button id="copy-rewrite" class="secondary">Copy rewrite</button></div><textarea id="rewrite-text" rows="7">${escapeHTML(x.rewritten_text)}</textarea><h3>What changed</h3><ul>${changes}</ul><p class="disclaimer">Suggestion only—confirm claims, legal requirements, and brand voice before publishing.</p></section>`;
    document.querySelector('#copy-rewrite').onclick=async event=>{await navigator.clipboard.writeText(document.querySelector('#rewrite-text').value);event.currentTarget.textContent='Copied ✓'};
  }catch(error){report.innerHTML=`<h2>We couldn't complete the review</h2><p>${escapeHTML(error.message)}</p><p>Make sure the app is running at <code>http://localhost:8001</code>.</p>`}
};
