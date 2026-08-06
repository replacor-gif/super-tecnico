(() => {
  'use strict';

  const UI = {
    es: {
      subtitle:'Formación técnica en climatización', errorLibrary:'Errores por fabricante', eyebrow:'Colección técnica REPLACOR', title:'Aprende o consulta exactamente lo que necesitas', intro:'Recorre la formación completa por módulos o entra directamente en un componente, síntoma, medición o procedimiento de taller.', modules:'módulos', pages:'páginas de origen', chapters:'capítulos', figures:'figuras', courseTab:'Curso por módulos', lookupTab:'Consulta rápida', savedTab:'Guardados y progreso', courseEyebrow:'Ruta formativa flexible', courseTitle:'Elige un módulo para empezar', progress:'Progreso', resume:'Continuar donde lo dejé', backModules:'← Volver a los módulos', save:'Guardar', saved:'Guardado', complete:'Marcar completado', completed:'Completado', chooseChapter:'Ir al capítulo', previous:'Anterior', next:'Siguiente', lookupEyebrow:'Acceso directo', lookupTitle:'Busca por problema, componente o medida', lookupText:'Primero verás todas las coincidencias. Ningún capítulo se abre automáticamente.', query:'¿Qué necesitas consultar?', queryPlaceholder:'Ejemplos: EEV, motor BLDC, retorno de líquido, medir NTC…', module:'Módulo', allModules:'Todos los módulos', area:'Área técnica', allAreas:'Todas las áreas', search:'Buscar', clear:'Limpiar', sort:'Orden', relevance:'Relevancia', byModule:'Por módulo', alphabetical:'Alfabético', showMore:'Mostrar más', savedEyebrow:'Tu espacio', savedTitle:'Capítulos guardados y avance', savedText:'El progreso se guarda únicamente en este dispositivo.', completedChapters:'capítulos completados', savedChapters:'capítulos guardados', important:'Importante', notice:'El contenido explica principios y procedimientos generales. Confirma siempre valores, conexiones y secuencias específicas con el manual OEM del equipo.', footer:'Formación técnica REPLACOR', openModule:'Abrir módulo', moduleProgress:'{done} de {total} completados', pageShort:'{count} págs.', chapterShort:'{count} capítulos', figureShort:'{count} figuras', chapterPosition:'Capítulo {current} de {total}', readTime:'{minutes} min de lectura', openChapter:'Abrir capítulo', results:'{shown} de {total} capítulos', noResults:'No hay coincidencias. Prueba con otro término o elimina algún filtro.', noSaved:'Todavía no has guardado ningún capítulo.', contentSpanish:'El contenido técnico de esta colección está disponible actualmente en español.', table:'Tabla técnica', complementary:'Contenido complementario', facets:'Temas relacionados', continueChapter:'Continuar por {title}', sourceQuality:'Las 158 figuras publicadas son originales. El manifiesto indica 159; falta un archivo gráfico en el módulo de intercambiadores y no se ha sustituido por una imagen inventada.'
    },
    en: {
      subtitle:'HVAC technical training', errorLibrary:'Manufacturer fault codes', eyebrow:'REPLACOR technical collection', title:'Learn or look up exactly what you need', intro:'Follow the full course by module or jump directly to a component, symptom, measurement or workshop procedure.', modules:'modules', pages:'source pages', chapters:'chapters', figures:'figures', courseTab:'Course modules', lookupTab:'Quick lookup', savedTab:'Saved and progress', courseEyebrow:'Flexible learning path', courseTitle:'Choose a module to begin', progress:'Progress', resume:'Continue where I stopped', backModules:'← Back to modules', save:'Save', saved:'Saved', complete:'Mark complete', completed:'Completed', chooseChapter:'Go to chapter', previous:'Previous', next:'Next', lookupEyebrow:'Direct access', lookupTitle:'Search by problem, component or measurement', lookupText:'All matches are shown first. No chapter opens automatically.', query:'What do you need to look up?', queryPlaceholder:'Examples: EEV, BLDC motor, liquid return, measure NTC…', module:'Module', allModules:'All modules', area:'Technical area', allAreas:'All areas', search:'Search', clear:'Clear', sort:'Order', relevance:'Relevance', byModule:'By module', alphabetical:'Alphabetical', showMore:'Show more', savedEyebrow:'Your space', savedTitle:'Saved chapters and progress', savedText:'Progress is stored only on this device.', completedChapters:'completed chapters', savedChapters:'saved chapters', important:'Important', notice:'This material explains general principles and procedures. Always confirm equipment-specific values, wiring and sequences in the OEM manual.', footer:'REPLACOR technical training', openModule:'Open module', moduleProgress:'{done} of {total} completed', pageShort:'{count} pages', chapterShort:'{count} chapters', figureShort:'{count} figures', chapterPosition:'Chapter {current} of {total}', readTime:'{minutes} min read', openChapter:'Open chapter', results:'{shown} of {total} chapters', noResults:'No matches. Try another term or remove a filter.', noSaved:'You have not saved any chapters yet.', contentSpanish:'The technical course content is currently available in Spanish.', table:'Technical table', complementary:'Additional content', facets:'Related topics', continueChapter:'Continue with {title}', sourceQuality:'The 158 published figures are original. The manifest lists 159; one exchanger graphic file is missing and has not been replaced with invented artwork.'
    },
    pt: {
      subtitle:'Formação técnica em climatização', errorLibrary:'Erros por fabricante', eyebrow:'Coleção técnica REPLACOR', title:'Aprenda ou consulte exatamente o que precisa', intro:'Siga a formação por módulos ou aceda diretamente a um componente, sintoma, medição ou procedimento de oficina.', modules:'módulos', pages:'páginas de origem', chapters:'capítulos', figures:'figuras', courseTab:'Curso por módulos', lookupTab:'Consulta rápida', savedTab:'Guardados e progresso', courseEyebrow:'Percurso flexível', courseTitle:'Escolha um módulo para começar', progress:'Progresso', resume:'Continuar onde parei', backModules:'← Voltar aos módulos', save:'Guardar', saved:'Guardado', complete:'Marcar concluído', completed:'Concluído', chooseChapter:'Ir para o capítulo', previous:'Anterior', next:'Seguinte', lookupEyebrow:'Acesso direto', lookupTitle:'Procure por problema, componente ou medida', lookupText:'Primeiro verá todas as correspondências. Nenhum capítulo abre automaticamente.', query:'O que precisa consultar?', queryPlaceholder:'Exemplos: EEV, motor BLDC, retorno de líquido, medir NTC…', module:'Módulo', allModules:'Todos os módulos', area:'Área técnica', allAreas:'Todas as áreas', search:'Procurar', clear:'Limpar', sort:'Ordem', relevance:'Relevância', byModule:'Por módulo', alphabetical:'Alfabética', showMore:'Mostrar mais', savedEyebrow:'O seu espaço', savedTitle:'Capítulos guardados e progresso', savedText:'O progresso é guardado apenas neste dispositivo.', completedChapters:'capítulos concluídos', savedChapters:'capítulos guardados', important:'Importante', notice:'O conteúdo explica princípios e procedimentos gerais. Confirme sempre valores, ligações e sequências específicas no manual OEM.', footer:'Formação técnica REPLACOR', openModule:'Abrir módulo', moduleProgress:'{done} de {total} concluídos', pageShort:'{count} págs.', chapterShort:'{count} capítulos', figureShort:'{count} figuras', chapterPosition:'Capítulo {current} de {total}', readTime:'{minutes} min de leitura', openChapter:'Abrir capítulo', results:'{shown} de {total} capítulos', noResults:'Sem correspondências. Tente outro termo ou retire um filtro.', noSaved:'Ainda não guardou nenhum capítulo.', contentSpanish:'O conteúdo técnico desta coleção está atualmente disponível em espanhol.', table:'Tabela técnica', complementary:'Conteúdo complementar', facets:'Temas relacionados', continueChapter:'Continuar por {title}', sourceQuality:'As 158 figuras publicadas são originais. O manifesto indica 159; falta um ficheiro gráfico no módulo de permutadores e não foi substituído por uma imagem inventada.'
    },
    fr: {
      subtitle:'Formation technique en climatisation', errorLibrary:'Erreurs par fabricant', eyebrow:'Collection technique REPLACOR', title:'Apprenez ou consultez exactement ce dont vous avez besoin', intro:'Suivez la formation par modules ou accédez directement à un composant, symptôme, relevé ou procédé d’atelier.', modules:'modules', pages:'pages sources', chapters:'chapitres', figures:'figures', courseTab:'Cours par modules', lookupTab:'Recherche rapide', savedTab:'Favoris et progression', courseEyebrow:'Parcours flexible', courseTitle:'Choisissez un module pour commencer', progress:'Progression', resume:'Continuer où je me suis arrêté', backModules:'← Retour aux modules', save:'Enregistrer', saved:'Enregistré', complete:'Marquer terminé', completed:'Terminé', chooseChapter:'Aller au chapitre', previous:'Précédent', next:'Suivant', lookupEyebrow:'Accès direct', lookupTitle:'Recherchez par problème, composant ou mesure', lookupText:'Toutes les correspondances sont d’abord affichées. Aucun chapitre ne s’ouvre automatiquement.', query:'Que souhaitez-vous consulter ?', queryPlaceholder:'Exemples : EEV, moteur BLDC, retour liquide, mesurer NTC…', module:'Module', allModules:'Tous les modules', area:'Domaine technique', allAreas:'Tous les domaines', search:'Rechercher', clear:'Effacer', sort:'Ordre', relevance:'Pertinence', byModule:'Par module', alphabetical:'Alphabétique', showMore:'Afficher plus', savedEyebrow:'Votre espace', savedTitle:'Chapitres enregistrés et progression', savedText:'La progression est enregistrée uniquement sur cet appareil.', completedChapters:'chapitres terminés', savedChapters:'chapitres enregistrés', important:'Important', notice:'Le contenu présente des principes et procédures généraux. Vérifiez toujours les valeurs, connexions et séquences propres à l’équipement dans le manuel OEM.', footer:'Formation technique REPLACOR', openModule:'Ouvrir le module', moduleProgress:'{done} sur {total} terminés', pageShort:'{count} pages', chapterShort:'{count} chapitres', figureShort:'{count} figures', chapterPosition:'Chapitre {current} sur {total}', readTime:'{minutes} min de lecture', openChapter:'Ouvrir le chapitre', results:'{shown} sur {total} chapitres', noResults:'Aucune correspondance. Essayez un autre terme ou retirez un filtre.', noSaved:'Vous n’avez encore enregistré aucun chapitre.', contentSpanish:'Le contenu technique de cette collection est actuellement disponible en espagnol.', table:'Tableau technique', complementary:'Contenu complémentaire', facets:'Sujets associés', continueChapter:'Continuer avec {title}', sourceQuality:'Les 158 figures publiées sont originales. Le manifeste en indique 159 ; un fichier graphique du module échangeurs manque et n’a pas été remplacé par une image inventée.'
    }
  };

  const state = {
    collection: null,
    chapters: [],
    chapterMap: new Map(),
    activeView: 'course',
    activeModule: null,
    activeChapter: null,
    completed: new Set(readStoredArray('st.training.completed')),
    bookmarks: new Set(readStoredArray('st.training.bookmarks')),
    lookupMatches: [],
    visibleResults: 20,
  };

  const $ = selector => document.querySelector(selector);
  const $$ = selector => Array.from(document.querySelectorAll(selector));
  const escapeHtml = value => String(value ?? '').replace(/[&<>"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[char]));
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

  function readStoredArray(key) {
    try { return JSON.parse(localStorage.getItem(key) || '[]'); } catch (_) { return []; }
  }

  function storeSet(key, set) { localStorage.setItem(key, JSON.stringify([...set])); }
  function language() { return window.ST_I18N?.language || 'es'; }
  function tr(key, vars = {}) {
    let text = UI[language()]?.[key] || UI.es[key] || key;
    Object.entries(vars).forEach(([name, value]) => { text = text.replaceAll(`{${name}}`, String(value)); });
    return text;
  }

  function translateUi() {
    $$('[data-training-i18n]').forEach(node => { node.textContent = tr(node.dataset.trainingI18n); });
    $$('[data-training-i18n-placeholder]').forEach(node => { node.placeholder = tr(node.dataset.trainingI18nPlaceholder); });
    if (state.collection) {
      renderDashboard();
      renderSaved();
      if (state.activeChapter) renderChapter(state.activeChapter.id, false);
      if (state.activeView === 'lookup') runLookup(false);
    }
  }

  function setView(view) {
    state.activeView = view;
    $$('.training-tabs [role="tab"]').forEach(button => button.setAttribute('aria-selected', button.dataset.view === view ? 'true' : 'false'));
    $$('[data-panel]').forEach(panel => { panel.hidden = panel.dataset.panel !== view; });
    if (view === 'saved') renderSaved();
    if (view === 'lookup' && state.collection) runLookup(false);
  }

  function createIndex() {
    state.chapters = [];
    state.chapterMap.clear();
    state.collection.modules.forEach(module => {
      module.chapters.forEach((chapter, index) => {
        const entry = {...chapter, module, moduleIndex: Number(module.id), chapterIndex: index};
        state.chapters.push(entry);
        state.chapterMap.set(chapter.id, entry);
      });
    });
  }

  function updateStats() {
    const stats = state.collection.stats;
    $('#moduleCount').textContent = stats.modules.toLocaleString();
    $('#pageCount').textContent = stats.pages.toLocaleString();
    $('#chapterCount').textContent = stats.chapters.toLocaleString();
    $('#figureCount').textContent = stats.figures.toLocaleString();
  }

  function renderDashboard() {
    const total = state.chapters.length;
    const done = state.chapters.filter(item => state.completed.has(item.id)).length;
    $('#overallProgressText').textContent = `${done} / ${total}`;
    $('#overallProgressBar').style.width = `${total ? (done / total) * 100 : 0}%`;
    const lastId = localStorage.getItem('st.training.last');
    const last = state.chapterMap.get(lastId);
    $('#resumeTraining').disabled = !last;
    $('#resumeTraining').textContent = last ? tr('continueChapter', {title: last.title}) : tr('resume');

    $('#moduleGrid').innerHTML = state.collection.modules.map(module => {
      const moduleDone = module.chapters.filter(chapter => state.completed.has(chapter.id)).length;
      const percent = module.chapters.length ? moduleDone / module.chapters.length * 100 : 0;
      return `<article class="module-card" style="--module-accent:${escapeHtml(module.accent)}">
        <div class="module-card-head"><span class="module-number">MÓDULO ${escapeHtml(module.id)}</span><span class="module-icon" aria-hidden="true">${escapeHtml(module.icon)}</span></div>
        <div class="module-card-copy"><h3>${escapeHtml(module.title)}</h3><p>${escapeHtml(module.summary)}</p><div class="module-meta"><span>${tr('pageShort',{count:module.pages})}</span><span>${tr('chapterShort',{count:module.chapters.length})}</span><span>${tr('figureShort',{count:module.stats.figures_available})}</span></div></div>
        <div class="module-progress"><div class="module-progress-row"><span>${tr('moduleProgress',{done:moduleDone,total:module.chapters.length})}</span><strong>${Math.round(percent)}%</strong></div><div class="progress-track"><i style="width:${percent}%"></i></div><button class="module-open" type="button" data-module="${escapeHtml(module.id)}">${tr('openModule')}</button></div>
      </article>`;
    }).join('');
  }

  function openModule(moduleId) {
    const module = state.collection.modules.find(item => item.id === moduleId);
    if (!module || !module.chapters.length) return;
    const firstIncomplete = module.chapters.find(chapter => !state.completed.has(chapter.id)) || module.chapters[0];
    openChapter(firstIncomplete.id);
  }

  function openChapter(chapterId, pushHistory = true) {
    const chapter = state.chapterMap.get(chapterId);
    if (!chapter) return;
    state.activeModule = chapter.module;
    state.activeChapter = chapter;
    setView('course');
    $('#courseDashboard').hidden = true;
    $('#chapterWorkspace').hidden = false;
    renderChapter(chapterId, pushHistory);
    $('#chapterWorkspace').scrollIntoView({behavior:'smooth', block:'start'});
  }

  function renderChapter(chapterId, pushHistory = true) {
    const chapter = state.chapterMap.get(chapterId);
    if (!chapter) return;
    state.activeChapter = chapter;
    state.activeModule = chapter.module;
    localStorage.setItem('st.training.last', chapter.id);
    if (pushHistory) history.replaceState(null, '', `#chapter=${encodeURIComponent(chapter.id)}`);

    const chapters = chapter.module.chapters;
    const position = chapter.chapterIndex;
    $('#sidebarModuleLabel').textContent = `Módulo ${chapter.module.id} · ${chapter.module.title}`;
    $('#chapterSelect').innerHTML = chapters.map(item => `<option value="${escapeHtml(item.id)}" ${item.id === chapter.id ? 'selected' : ''}>${escapeHtml(item.title)}</option>`).join('');
    $('#chapterList').innerHTML = chapters.map(item => `<button type="button" data-chapter="${escapeHtml(item.id)}" class="${item.id === chapter.id ? 'active' : ''} ${state.completed.has(item.id) ? 'completed' : ''}">${escapeHtml(item.title)}</button>`).join('');
    $('#chapterBreadcrumb').textContent = `Curso / Módulo ${chapter.module.id} / ${chapter.title}`;
    $('#chapterPosition').textContent = tr('chapterPosition', {current:position + 1, total:chapters.length});
    $('#chapterTitle').textContent = chapter.title;
    $('#chapterWordCount').textContent = tr('readTime', {minutes:Math.max(1, Math.ceil(chapter.word_count / 210))});
    renderFacets(chapter);
    $('#chapterContent').innerHTML = renderBlocks(chapter.blocks);
    $('#previousChapter').disabled = position === 0;
    $('#nextChapter').disabled = position === chapters.length - 1;
    $('#previousChapter').dataset.chapter = chapters[position - 1]?.id || '';
    $('#nextChapter').dataset.chapter = chapters[position + 1]?.id || '';
    updateActionButtons();
  }

  function renderFacets(chapter) {
    const values = Object.entries(chapter.facets || {}).flatMap(([group, terms]) => terms.slice(0, 3).map(term => `${group}: ${term}`));
    $('#chapterFacets').innerHTML = values.slice(0, 12).map(value => `<span>${escapeHtml(value)}</span>`).join('');
  }

  function renderBlocks(blocks) {
    const output = [];
    let section = null;
    const flushSection = () => {
      if (!section) return;
      output.push(`<details class="content-section"><summary>${escapeHtml(section.title)}</summary><div class="content-section-body">${section.parts.join('')}</div></details>`);
      section = null;
    };
    blocks.forEach(block => {
      if (block.type === 'subheading') {
        flushSection();
        section = {title:block.text, parts:[]};
        return;
      }
      const html = renderBlock(block);
      if (section) section.parts.push(html); else output.push(html);
    });
    flushSection();
    return output.join('');
  }

  function renderBlock(block) {
    if (block.type === 'paragraph') return `<p>${escapeHtml(block.text)}</p>`;
    if (block.type === 'list') return `<ul>${block.items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
    if (block.type === 'callout') return `<aside class="technical-callout ${escapeHtml(block.kind || 'note')}">${escapeHtml(block.text)}</aside>`;
    if (block.type === 'caption') return `<p class="standalone-caption">${escapeHtml(block.text)}</p>`;
    if (block.type === 'figure') {
      const caption = block.caption || block.alt;
      return `<figure class="training-figure"><button type="button" data-figure="${escapeHtml(block.src)}" data-caption="${escapeHtml(caption)}"><img src="${escapeHtml(block.src)}" alt="${escapeHtml(block.alt)}" loading="lazy"></button><figcaption>${escapeHtml(caption)}</figcaption></figure>`;
    }
    if (block.type === 'table') {
      return `<div class="table-scroll" role="region" aria-label="${tr('table')}" tabindex="0"><table class="technical-table"><thead><tr>${block.headers.map(cell => `<th scope="col">${escapeHtml(cell)}</th>`).join('')}</tr></thead><tbody>${block.rows.map(row => `<tr>${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
    }
    return '';
  }

  function updateActionButtons() {
    const id = state.activeChapter?.id;
    const bookmarked = state.bookmarks.has(id);
    const completed = state.completed.has(id);
    $('#bookmarkChapter').setAttribute('aria-pressed', bookmarked ? 'true' : 'false');
    $('#bookmarkChapter').innerHTML = `${bookmarked ? '★' : '☆'} <span>${tr(bookmarked ? 'saved' : 'save')}</span>`;
    $('#completeChapter').setAttribute('aria-pressed', completed ? 'true' : 'false');
    $('#completeChapter').innerHTML = `✓ <span>${tr(completed ? 'completed' : 'complete')}</span>`;
  }

  function toggleBookmark() {
    const id = state.activeChapter?.id;
    if (!id) return;
    state.bookmarks.has(id) ? state.bookmarks.delete(id) : state.bookmarks.add(id);
    storeSet('st.training.bookmarks', state.bookmarks);
    updateActionButtons();
    renderSaved();
  }

  function toggleComplete() {
    const id = state.activeChapter?.id;
    if (!id) return;
    state.completed.has(id) ? state.completed.delete(id) : state.completed.add(id);
    storeSet('st.training.completed', state.completed);
    updateActionButtons();
    renderDashboard();
    renderSaved();
    renderChapter(id, false);
  }

  function searchScore(chapter, tokens) {
    if (!tokens.length) return 1;
    const title = normalize(chapter.title);
    const search = chapter.search || '';
    let score = 0;
    for (const token of tokens) {
      if (!search.includes(token) && !title.includes(token)) return 0;
      if (title === token) score += 18;
      else if (title.includes(token)) score += 8;
      else score += 2;
    }
    return score;
  }

  function runLookup(resetVisible = true) {
    if (!state.collection) return;
    if (resetVisible) state.visibleResults = 20;
    const query = normalize($('#trainingQuery').value);
    const tokens = query.split(' ').filter(Boolean);
    const moduleId = $('#moduleFilter').value;
    const facet = $('#facetFilter').value;
    const matches = state.chapters.map(chapter => ({chapter, score:searchScore(chapter, tokens)})).filter(item => {
      if (!item.score) return false;
      if (moduleId && item.chapter.module.id !== moduleId) return false;
      if (facet && !Object.keys(item.chapter.facets || {}).includes(facet)) return false;
      return true;
    });
    const sort = $('#lookupSort').value;
    matches.sort((a,b) => sort === 'title' ? a.chapter.title.localeCompare(b.chapter.title, 'es') : sort === 'module' ? a.chapter.moduleIndex - b.chapter.moduleIndex || a.chapter.chapterIndex - b.chapter.chapterIndex : b.score - a.score || a.chapter.moduleIndex - b.chapter.moduleIndex);
    state.lookupMatches = matches;
    renderLookup(tokens);
  }

  function resultSnippet(chapter, tokens) {
    const source = blockPlainText(chapter.blocks).replace(/\s+/g, ' ').trim();
    if (!source) return chapter.module.summary;
    const normalizedSource = normalize(source);
    const first = tokens.map(token => normalizedSource.indexOf(token)).filter(index => index >= 0).sort((a,b) => a-b)[0] || 0;
    const start = Math.max(0, first - 80);
    const snippet = source.slice(start, start + 240);
    return `${start ? '…' : ''}${snippet}${source.length > start + 240 ? '…' : ''}`;
  }

  function blockPlainText(blocks) {
    return blocks.map(block => block.type === 'table' ? [...block.headers, ...block.rows.flat()].join(' ') : block.type === 'list' ? block.items.join(' ') : block.text || block.caption || block.alt || '').join(' ');
  }

  function renderLookup(tokens) {
    const visible = state.lookupMatches.slice(0, state.visibleResults);
    $('#lookupStatus').textContent = tr('results', {shown:visible.length, total:state.lookupMatches.length});
    $('#lookupResults').innerHTML = visible.length ? visible.map(({chapter}) => resultCard(chapter, resultSnippet(chapter, tokens))).join('') : `<div class="empty-results">${tr('noResults')}</div>`;
    $('#loadMoreTraining').hidden = visible.length >= state.lookupMatches.length;
  }

  function resultCard(chapter, snippet = '') {
    return `<article class="lookup-card" style="--result-accent:${escapeHtml(chapter.module.accent)}"><span class="lookup-module">${escapeHtml(chapter.module.id)}</span><div class="lookup-copy"><h3>${escapeHtml(chapter.title)}</h3><p><strong>${escapeHtml(chapter.module.title)}</strong>${snippet ? ` · ${escapeHtml(snippet)}` : ''}</p></div><button type="button" data-open-chapter="${escapeHtml(chapter.id)}">${tr('openChapter')}</button></article>`;
  }

  function renderSaved() {
    if (!state.collection) return;
    const saved = state.chapters.filter(chapter => state.bookmarks.has(chapter.id));
    $('#completedCount').textContent = state.completed.size;
    $('#savedCount').textContent = saved.length;
    $('#savedResults').innerHTML = saved.length ? saved.map(chapter => resultCard(chapter)).join('') : `<div class="empty-results">${tr('noSaved')}</div>`;
  }

  function populateFilters() {
    $('#moduleFilter').insertAdjacentHTML('beforeend', state.collection.modules.map(module => `<option value="${escapeHtml(module.id)}">${escapeHtml(module.id)} · ${escapeHtml(module.title)}</option>`).join(''));
    $('#facetFilter').insertAdjacentHTML('beforeend', state.collection.facet_groups.map(group => `<option value="${escapeHtml(group)}">${escapeHtml(group)}</option>`).join(''));
  }

  function bindEvents() {
    $$('.training-tabs button').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
    $('#moduleGrid').addEventListener('click', event => { const button = event.target.closest('[data-module]'); if (button) openModule(button.dataset.module); });
    $('#resumeTraining').addEventListener('click', () => { const id = localStorage.getItem('st.training.last'); if (state.chapterMap.has(id)) openChapter(id); });
    $('#backToModules').addEventListener('click', () => { $('#chapterWorkspace').hidden = true; $('#courseDashboard').hidden = false; state.activeChapter = null; history.replaceState(null, '', location.pathname + location.search); renderDashboard(); });
    $('#chapterSelect').addEventListener('change', event => openChapter(event.target.value));
    $('#chapterList').addEventListener('click', event => { const button = event.target.closest('[data-chapter]'); if (button) openChapter(button.dataset.chapter); });
    $('#previousChapter').addEventListener('click', event => { if (event.currentTarget.dataset.chapter) openChapter(event.currentTarget.dataset.chapter); });
    $('#nextChapter').addEventListener('click', event => { if (event.currentTarget.dataset.chapter) openChapter(event.currentTarget.dataset.chapter); });
    $('#bookmarkChapter').addEventListener('click', toggleBookmark);
    $('#completeChapter').addEventListener('click', toggleComplete);
    $('#trainingSearchForm').addEventListener('submit', event => { event.preventDefault(); runLookup(); });
    $('#moduleFilter').addEventListener('change', () => runLookup());
    $('#facetFilter').addEventListener('change', () => runLookup());
    $('#lookupSort').addEventListener('change', () => runLookup(false));
    $('#clearTrainingSearch').addEventListener('click', () => { $('#trainingQuery').value=''; $('#moduleFilter').value=''; $('#facetFilter').value=''; runLookup(); });
    $('#loadMoreTraining').addEventListener('click', () => { state.visibleResults += 20; renderLookup(normalize($('#trainingQuery').value).split(' ').filter(Boolean)); });
    document.addEventListener('click', event => { const button = event.target.closest('[data-open-chapter]'); if (button) openChapter(button.dataset.openChapter); const figure = event.target.closest('[data-figure]'); if (figure) openFigure(figure.dataset.figure, figure.dataset.caption); });
    $('#figureDialog [data-close]').addEventListener('click', () => $('#figureDialog').close());
    $('#figureDialog').addEventListener('click', event => { if (event.target === event.currentTarget) event.currentTarget.close(); });
    document.addEventListener('st:languagechange', translateUi);
  }

  function openFigure(src, caption) {
    $('#figureDialogImage').src = src;
    $('#figureDialogImage').alt = caption || '';
    $('#figureDialogCaption').textContent = caption || '';
    $('#figureDialog').showModal();
  }

  async function init() {
    bindEvents();
    try {
      const response = await fetch('data/training/collection.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.collection = await response.json();
      createIndex();
      updateStats();
      populateFilters();
      renderDashboard();
      renderSaved();
      runLookup();
      translateUi();
      const hash = new URLSearchParams(location.hash.replace(/^#/, '')).get('chapter');
      if (hash && state.chapterMap.has(hash)) openChapter(hash, false);
    } catch (error) {
      console.error(error);
      $('#moduleGrid').innerHTML = `<div class="empty-results">No se pudo cargar el curso técnico.</div>`;
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
