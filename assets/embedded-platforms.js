(() => {
  'use strict';
  const CATALOG_URL='data/embedded-platforms/catalog.json';
  const CLASS_LABELS={microcontroller_board:'Placa MCU',development_kit:'Kit de desarrollo',evaluation_board:'Placa de evaluación',industrial_controller:'Control industrial',single_board_computer:'Ordenador SBC',system_on_module:'Módulo SoM',edge_ai_computer:'Ordenador Edge AI',edge_ai_accelerator:'Acelerador Edge AI',integrated_controller:'Control integrado',fpga_board:'Placa FPGA',soc_fpga_board:'SoC + FPGA'};
  const COLORS=['#00eaff','#ff3fa7','#ffe438','#54ff82','#ff7a00','#a66bff'];
  const IGNORED_TERMS=new Set(['a','al','de','del','la','las','el','los','y','o','u','con','para','por','en','un','una','unos','unas','que','como','quiero','necesito','the','and','with','for','from','to','an','of','on','in']);
  let catalog=null; let records=[]; let selectedId=''; let rankedIds=null;
  const byId=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const fold=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const list=value=>Array.isArray(value)?value:[];
  const terms=value=>[...new Set(fold(value).split(/\s+/).filter(term=>term.length>=2&&!IGNORED_TERMS.has(term)))];

  function haystack(record){return fold([record.id,record.name,record.manufacturer,record.platform_class,record.architecture,record.logic_and_power,record.recommended_use,record.primary_risk,...list(record.interfaces),...list(record.tags)].join(' '));}
  function queryMatches(record,query){const queryTerms=terms(query);const text=haystack(record);return !queryTerms.length||queryTerms.every(term=>text.includes(term));}
  function filtered(){
    const q=byId('epQuery').value.trim(); const manufacturer=byId('epManufacturer').value; const platformClass=byId('epClass').value;
    let items=records.filter(record=>queryMatches(record,q)&&(!manufacturer||record.manufacturer===manufacturer)&&(!platformClass||record.platform_class===platformClass));
    if(rankedIds){const order=new Map(rankedIds.map((id,index)=>[id,index]));items=items.filter(record=>order.has(record.id)).sort((a,b)=>order.get(a.id)-order.get(b.id));}
    return items;
  }
  function renderResults({autoSelect=false}={}){
    const items=filtered(); byId('epResultCount').textContent=String(items.length);
    byId('epResultsTitle').textContent=rankedIds?'Preselección documental':(byId('epQuery').value.trim()?'Coincidencias':'Catálogo completo');
    byId('epResultList').innerHTML=items.length?items.map((record,index)=>`<button class="ep-result${record.id===selectedId?' is-active':''}" style="--accent:${COLORS[index%COLORS.length]}" type="button" data-platform-id="${esc(record.id)}"><strong>${esc(record.name)}</strong><small>${esc(record.manufacturer)} · ${esc(CLASS_LABELS[record.platform_class]||record.platform_class)}</small><em>${esc(record.logic_and_power)}</em></button>`).join(''):'<div class="ep-empty"><h2>Sin coincidencias</h2><p>Prueba con una interfaz, una arquitectura o un uso más general.</p></div>';
    byId('epResultList').querySelectorAll('[data-platform-id]').forEach(button=>button.addEventListener('click',()=>selectRecord(button.dataset.platformId)));
    if(autoSelect&&items[0]) selectRecord(items[0].id); else if(selectedId&&!items.some(item=>item.id===selectedId)){selectedId='';byId('epDetail').innerHTML='<div class="ep-empty"><span aria-hidden="true">µ</span><h2>Selecciona una plataforma</h2><p>La ficha básica aparece primero. Las pruebas, integración y procedencia se despliegan solo cuando las necesitas.</p></div>';}
  }
  function selectRecord(id){
    const record=records.find(item=>item.id===id); if(!record)return; selectedId=id; renderResults();
    byId('epDetail').innerHTML=`<article><header class="ep-detail-head"><div><span class="ep-badge">Fuente identificada</span><span class="ep-id">${esc(record.id)}</span></div><h2>${esc(record.name)}</h2><p>${esc(record.manufacturer)} · ${esc(CLASS_LABELS[record.platform_class]||record.platform_class)}</p></header><div class="ep-quick-grid"><div><span>Arquitectura</span><strong>${esc(record.architecture)}</strong></div><div><span>Lógica / alimentación</span><strong>${esc(record.logic_and_power)}</strong></div><div><span>Tipo</span><strong>${esc(CLASS_LABELS[record.platform_class]||record.platform_class)}</strong></div></div><section class="ep-purpose"><strong>Uso recomendado</strong><p>${esc(record.recommended_use)}</p></section><section><p class="ep-kicker">Interfaces declaradas</p><div class="ep-interface-list">${list(record.interfaces).map(item=>`<span>${esc(item)}</span>`).join('')}</div></section><aside class="ep-risk"><strong>Riesgo o limitación principal</strong><p>${esc(record.primary_risk)}</p></aside><details><summary>Pruebas mínimas antes de integrarla</summary><div><ol>${list(catalog.shared_reception_checks).map(item=>`<li>${esc(item)}</li>`).join('')}</ol></div></details><details><summary>Integración profesional y seguridad</summary><div><ul>${list(catalog.shared_integration_requirements).map(item=>`<li>${esc(item)}</li>`).join('')}</ul></div></details><details><summary>Procedencia y estado de revisión</summary><div class="ep-source"><span><strong>Estado:</strong> ${esc(record.review.status)}</span><span><strong>Base:</strong> ${esc(record.review.basis)}</span><span><strong>Fuente:</strong> <code>${esc(record.source_refs.join(', '))}</code></span><span><strong>Localizador:</strong> página PDF ${esc(record.source_locator.pdf_page)}, sección ${esc(record.source_locator.section)}</span><span>Antes de diseñar hardware, contrasta la revisión exacta con la documentación oficial del fabricante.</span></div></details></article>`;
    byId('epResultList').querySelector(`[data-platform-id="${CSS.escape(id)}"]`)?.classList.add('is-active');
  }
  function populateFilters(){
    const manufacturers=[...new Set(records.map(record=>record.manufacturer))].sort((a,b)=>a.localeCompare(b,'es')); const classes=[...new Set(records.map(record=>record.platform_class))].sort();
    manufacturers.forEach(value=>byId('epManufacturer').insertAdjacentHTML('beforeend',`<option value="${esc(value)}">${esc(value)}</option>`));
    classes.forEach(value=>byId('epClass').insertAdjacentHTML('beforeend',`<option value="${esc(value)}">${esc(CLASS_LABELS[value]||value)}</option>`));
  }
  function recommend(){
    const useCase=byId('epUseCase').value.trim(); const interfaces=byId('epInterfaces').value.trim(); if(useCase.length<3){byId('epUseCase').focus();return;}
    const queryTerms=terms(`${useCase} ${interfaces}`); const linuxClasses=new Set(['single_board_computer','system_on_module','edge_ai_computer','soc_fpga_board']); const needsLinux=byId('epLinux').checked||queryTerms.includes('linux');
    rankedIds=records.flatMap(record=>{if(needsLinux&&!linuxClasses.has(record.platform_class))return[];const text=haystack(record);const matched=queryTerms.filter(term=>text.includes(term));const score=matched.length*10+(needsLinux&&linuxClasses.has(record.platform_class)?8:0);return score?[{id:record.id,score}]:[];}).sort((a,b)=>b.score-a.score).slice(0,10).map(item=>item.id);
    byId('epQuery').value=''; byId('epManufacturer').value=''; byId('epClass').value=''; renderResults({autoSelect:true});
  }
  async function load(){
    try{const response=await fetch(new URL(CATALOG_URL,document.baseURI));if(!response.ok)throw new Error(`HTTP ${response.status}`);catalog=await response.json();records=list(catalog.records);populateFilters();renderResults({autoSelect:true});const status=byId('epStatus');status.classList.add('ready');status.querySelector('strong').textContent=`${records.length} fichas normalizadas`;status.querySelector('small').textContent=`Catálogo ${catalog.catalog_version}`;const requested=new URL(location.href).searchParams.get('id');if(requested&&records.some(record=>record.id===requested))selectRecord(requested);}catch(error){console.error(error);const status=byId('epStatus');status.classList.add('error');status.querySelector('strong').textContent='No se pudo cargar';byId('epResultList').innerHTML='<p>La base no está disponible en este momento.</p>';}
  }
  byId('epSearchButton').addEventListener('click',()=>{rankedIds=null;renderResults({autoSelect:true});});
  byId('epQuery').addEventListener('input',()=>{rankedIds=null;renderResults();});
  byId('epQuery').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();rankedIds=null;renderResults({autoSelect:true});}});
  byId('epManufacturer').addEventListener('change',()=>{rankedIds=null;renderResults({autoSelect:true});}); byId('epClass').addEventListener('change',()=>{rankedIds=null;renderResults({autoSelect:true});});
  byId('epModeButton').addEventListener('click',()=>{const open=byId('epRecommend').hidden;byId('epRecommend').hidden=!open;byId('epModeButton').setAttribute('aria-pressed',String(open));if(open)byId('epUseCase').focus();});
  byId('epRecommendButton').addEventListener('click',recommend);
  document.querySelectorAll('[data-ep-query]').forEach(button=>button.addEventListener('click',()=>{rankedIds=null;byId('epQuery').value=button.dataset.epQuery;renderResults({autoSelect:true});}));
  load();
})();
