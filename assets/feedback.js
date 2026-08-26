(() => {
  'use strict';
  const TEXT = {
    es: { subtitle:'Ideas pendientes',eyebrow:'UNA LISTA ABIERTA Y SENCILLA',title:'¿Qué mejorarías?',intro:'Escríbelo en unos segundos. La aportación se guarda y aparece directamente en la lista de pendientes.',withoutAccount:'SIN CUENTA NI REVISIÓN PREVIA',formTitle:'Añadir una aportación',pending:'Los dos campos son opcionales. No se abre el correo ni se envía a otro servicio.',nickname:'Apodo (opcional)',comment:'Comentario (opcional)',send:'Guardar en pendientes',boardEyebrow:'LISTA VIVA',community:'Aportaciones pendientes',communityText:'Aquí aparecen todas directamente. Cuando una mejora esté hecha, desaparecerá de esta lista.',loading:'Cargando aportaciones…',empty:'Todavía no hay aportaciones pendientes.',saved:'Guardado. Ya aparece en la lista.',error:'No se ha podido guardar. Inténtalo de nuevo.',anonymous:'Usuario anónimo' },
    en: { subtitle:'Pending ideas',eyebrow:'A SIMPLE OPEN LIST',title:'What would you improve?',intro:'Write it in seconds. Your contribution is saved and appears directly in the pending list.',withoutAccount:'NO ACCOUNT OR PRIOR REVIEW',formTitle:'Add a contribution',pending:'Both fields are optional. No email or third-party service is opened.',nickname:'Nickname (optional)',comment:'Comment (optional)',send:'Save as pending',boardEyebrow:'LIVE LIST',community:'Pending contributions',communityText:'All contributions appear here directly. Completed improvements are removed from this list.',loading:'Loading contributions…',empty:'There are no pending contributions yet.',saved:'Saved. It is already on the list.',error:'Could not save it. Please try again.',anonymous:'Anonymous user' },
    pt: { subtitle:'Ideias pendentes',eyebrow:'UMA LISTA ABERTA E SIMPLES',title:'O que melhoraria?',intro:'Escreva em segundos. A contribuição é guardada e aparece diretamente na lista de pendentes.',withoutAccount:'SEM CONTA NEM REVISÃO PRÉVIA',formTitle:'Adicionar contribuição',pending:'Os dois campos são opcionais. Não abre o e-mail nem envia para outro serviço.',nickname:'Apelido (opcional)',comment:'Comentário (opcional)',send:'Guardar como pendente',boardEyebrow:'LISTA VIVA',community:'Contribuições pendentes',communityText:'Todas aparecem aqui diretamente. Quando uma melhoria estiver concluída, desaparece da lista.',loading:'A carregar contribuições…',empty:'Ainda não existem contribuições pendentes.',saved:'Guardado. Já aparece na lista.',error:'Não foi possível guardar. Tente novamente.',anonymous:'Utilizador anónimo' },
    fr: { subtitle:'Idées en attente',eyebrow:'UNE LISTE OUVERTE ET SIMPLE',title:'Que faudrait-il améliorer ?',intro:'Écrivez-le en quelques secondes. La contribution est enregistrée et apparaît directement dans la liste.',withoutAccount:'SANS COMPTE NI VALIDATION PRÉALABLE',formTitle:'Ajouter une contribution',pending:"Les deux champs sont facultatifs. Aucun e-mail ni service tiers n'est ouvert.",nickname:'Pseudo (facultatif)',comment:'Commentaire (facultatif)',send:'Enregistrer en attente',boardEyebrow:'LISTE ACTIVE',community:'Contributions en attente',communityText:'Toutes apparaissent ici directement. Une amélioration réalisée disparaît de cette liste.',loading:'Chargement des contributions…',empty:"Il n'y a pas encore de contribution en attente.",saved:'Enregistré. La contribution figure déjà dans la liste.',error:"Impossible d'enregistrer. Réessayez.",anonymous:'Utilisateur anonyme' }
  };
  const byId = id => document.getElementById(id);
  const language = () => ['es','en','pt','fr'].includes(document.documentElement.lang) ? document.documentElement.lang : 'es';
  const tr = key => TEXT[language()]?.[key] || TEXT.es[key] || key;
  const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  function formatDate(value) {
    if (!value) return '';
    const date = new Date(String(value).replace(' ', 'T'));
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString(language(), { day:'2-digit',month:'short',year:'numeric' });
  }
  function translate() {
    document.querySelectorAll('[data-idea-i18n]').forEach(node => { const value=tr(node.dataset.ideaI18n); if(value) node.textContent=value; });
  }
  function render(items) {
    byId('proposalCount').textContent = Number(items.length).toLocaleString(language());
    byId('proposalList').innerHTML = items.length ? items.map(item => `
      <article class="proposal-card">
        <div class="proposal-avatar" aria-hidden="true">${escapeHtml((item.nickname || tr('anonymous')).trim().slice(0,1).toUpperCase() || '?')}</div>
        <div><div class="proposal-meta"><strong>${escapeHtml(item.nickname || tr('anonymous'))}</strong><span>${escapeHtml(formatDate(item.created_at))}</span></div><p>${escapeHtml(item.description || '')}</p></div>
      </article>`).join('') : `<div class="feedback-empty">${escapeHtml(tr('empty'))}</div>`;
  }
  async function load() {
    byId('boardMessage').textContent=tr('loading');
    try { const data=await window.ST_COMMUNITY_API.request('proposals'); render(Array.isArray(data.items)?data.items:[]); byId('boardMessage').textContent=''; }
    catch(error){ console.error(error); render([]); byId('boardMessage').textContent=tr('error'); }
  }
  byId('feedbackForm').addEventListener('submit', async event => {
    event.preventDefault();
    const form=event.currentTarget; const button=form.querySelector('button[type="submit"]'); const message=byId('formMessage'); button.disabled=true; message.textContent='…';
    try {
      await window.ST_COMMUNITY_API.request('proposal-submit',{body:{nickname:byId('feedbackNickname').value.trim(),comment:byId('feedbackMessage').value.trim(),source_page:byId('feedbackPage').value,language:language()}});
      form.reset(); byId('feedbackPage').value=location.href; message.textContent=tr('saved'); await load();
    } catch(error){ console.error(error); message.textContent=tr('error'); }
    finally { button.disabled=false; }
  });
  document.addEventListener('st:languagechange',()=>{translate();load();});
  const params=new URLSearchParams(location.search); byId('feedbackPage').value=params.get('page')||document.referrer||location.href;
  translate(); load();
})();
