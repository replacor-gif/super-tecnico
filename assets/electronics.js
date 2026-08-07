'use strict';

(() => {
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const state = {
    collection: null,
    modules: new Map(),
    chapters: new Map(),
    activeModule: null,
    activeChapter: null,
    previousView: 'routes',
    bookmarks: loadSet('st.electronics.bookmarks'),
    completed: loadSet('st.electronics.completed'),
  };

  const ui = {
    es: {
      subtitle:'Electrónica de placas',components:'Componentes',eyebrow:'Biblioteca técnica REPLACOR',title:'Encuentra el bloque, la medida o el procedimiento que necesitas',intro:'Empieza por un síntoma, sigue el recorrido de la placa o busca directamente cualquier concepto. No necesitas conocer el número del artículo.',modules:'temas técnicos',chapters:'apartados',figures:'figuras',tables:'tablas',safetyTitle:'Antes de medir',quickLookup:'Consulta rápida',searchTitle:'¿Qué estás intentando localizar o reparar?',searchLabel:'Buscar en electrónica',searchPlaceholder:'Ejemplos: fuente muerta, bus DC, ULN2003, reset, comunicación, IPM…',searchButton:'Buscar',try:'Prueba:',routesTab:'Por síntoma',groupsTab:'Por bloque de la placa',libraryTab:'Biblioteca completa',savedTab:'Guardados',symptoms:'Diagnóstico orientado',routesTitle:'Empieza por lo que hace la placa',routesIntro:'Cada ruta coloca primero los temas que conviene comprobar, sin afirmar automáticamente cuál es la avería.',boardMap:'Mapa funcional',groupsTitle:'Sigue el recorrido de energía, señal y control',allContent:'Todo el contenido',libraryTitle:'Filtra los temas técnicos',block:'Bloque',allBlocks:'Todos los bloques',level:'Nivel',allLevels:'Todos los niveles',personal:'Tu consulta',savedTitle:'Apartados guardados',results:'Resultados',closeResults:'Cerrar resultados',back:'← Volver',chooseSection:'Elige un apartado',previous:'Anterior',complete:'Marcar consultado',next:'Siguiente',related:'Continúa por aquí',sources:'Fuentes técnicas del tema',connected:'Herramientas conectadas',toolsTitle:'Pasa de la explicación a la comprobación',footer:'Información orientativa: confirma siempre el manual y el datasheet exactos.',openRoute:'Ver ruta',openBlock:'Ver temas',openTopic:'Abrir tema',sections:'apartados',pages:'páginas',basic:'Básico',intermediate:'Intermedio',advanced:'Avanzado',noSaved:'Todavía no has guardado ningún apartado.',noResults:'No se encontraron coincidencias. Prueba con el componente, el síntoma o la medida.',resultsFor:'Resultados para',recommended:'Ruta recomendada',bookmark:'☆ Guardar',bookmarked:'★ Guardado',consulted:'✓ Consultado',markConsulted:'Marcar consultado',progress:'consultados',sourceAdded:'Referencia adicional de revisión',contentSpanish:'Contenido técnico revisado en español',close:'Cerrar',all:'Todos',modulesAvailable:'temas disponibles'
    },
    en: {
      subtitle:'Circuit-board electronics',components:'Components',eyebrow:'REPLACOR technical library',title:'Find the block, measurement or procedure you need',intro:'Start from a symptom, follow the board path or search any concept directly. You do not need to know the article number.',modules:'technical topics',chapters:'sections',figures:'figures',tables:'tables',safetyTitle:'Before measuring',quickLookup:'Quick lookup',searchTitle:'What are you trying to locate or repair?',searchLabel:'Search electronics',searchPlaceholder:'Examples: dead power supply, DC bus, ULN2003, reset, communication, IPM…',searchButton:'Search',try:'Try:',routesTab:'By symptom',groupsTab:'By board block',libraryTab:'Full library',savedTab:'Saved',symptoms:'Guided diagnosis',routesTitle:'Start from what the board is doing',routesIntro:'Each route puts the most useful checks first without automatically declaring a fault.',boardMap:'Functional map',groupsTitle:'Follow energy, signal and control paths',allContent:'All content',libraryTitle:'Filter technical topics',block:'Block',allBlocks:'All blocks',level:'Level',allLevels:'All levels',personal:'Your lookup',savedTitle:'Saved sections',results:'Results',closeResults:'Close results',back:'← Back',chooseSection:'Choose a section',previous:'Previous',complete:'Mark reviewed',next:'Next',related:'Continue here',sources:'Technical sources',connected:'Connected tools',toolsTitle:'Move from explanation to checking',footer:'Guidance only: always confirm the exact manual and datasheet.',openRoute:'View route',openBlock:'View topics',openTopic:'Open topic',sections:'sections',pages:'pages',basic:'Basic',intermediate:'Intermediate',advanced:'Advanced',noSaved:'You have not saved any sections yet.',noResults:'No matches found. Try the component, symptom or measurement.',resultsFor:'Results for',recommended:'Recommended route',bookmark:'☆ Save',bookmarked:'★ Saved',consulted:'✓ Reviewed',markConsulted:'Mark reviewed',progress:'reviewed',sourceAdded:'Additional review reference',contentSpanish:'Reviewed technical content in Spanish',close:'Close',all:'All',modulesAvailable:'topics available'
    },
    pt: {
      subtitle:'Eletrónica de placas',components:'Componentes',eyebrow:'Biblioteca técnica REPLACOR',title:'Encontre o bloco, a medição ou o procedimento de que precisa',intro:'Comece por um sintoma, siga o percurso da placa ou pesquise qualquer conceito diretamente.',modules:'temas técnicos',chapters:'secções',figures:'figuras',tables:'tabelas',safetyTitle:'Antes de medir',quickLookup:'Consulta rápida',searchTitle:'O que está a tentar localizar ou reparar?',searchLabel:'Pesquisar eletrónica',searchPlaceholder:'Exemplos: fonte morta, bus DC, ULN2003, reset, comunicação, IPM…',searchButton:'Pesquisar',try:'Experimente:',routesTab:'Por sintoma',groupsTab:'Por bloco da placa',libraryTab:'Biblioteca completa',savedTab:'Guardados',symptoms:'Diagnóstico orientado',routesTitle:'Comece pelo comportamento da placa',routesIntro:'Cada rota prioriza as verificações úteis sem declarar automaticamente uma avaria.',boardMap:'Mapa funcional',groupsTitle:'Siga os percursos de energia, sinal e controlo',allContent:'Todo o conteúdo',libraryTitle:'Filtrar temas técnicos',block:'Bloco',allBlocks:'Todos os blocos',level:'Nível',allLevels:'Todos os níveis',personal:'A sua consulta',savedTitle:'Secções guardadas',results:'Resultados',closeResults:'Fechar resultados',back:'← Voltar',chooseSection:'Escolha uma secção',previous:'Anterior',complete:'Marcar consultado',next:'Seguinte',related:'Continue por aqui',sources:'Fontes técnicas do tema',connected:'Ferramentas ligadas',toolsTitle:'Passe da explicação à verificação',footer:'Informação orientativa: confirme sempre o manual e o datasheet exatos.',openRoute:'Ver rota',openBlock:'Ver temas',openTopic:'Abrir tema',sections:'secções',pages:'páginas',basic:'Básico',intermediate:'Intermédio',advanced:'Avançado',noSaved:'Ainda não guardou nenhuma secção.',noResults:'Não foram encontradas correspondências.',resultsFor:'Resultados para',recommended:'Rota recomendada',bookmark:'☆ Guardar',bookmarked:'★ Guardado',consulted:'✓ Consultado',markConsulted:'Marcar consultado',progress:'consultados',sourceAdded:'Referência adicional de revisão',contentSpanish:'Conteúdo técnico revisto em espanhol',close:'Fechar',all:'Todos',modulesAvailable:'temas disponíveis'
    },
    fr: {
      subtitle:'Électronique des cartes',components:'Composants',eyebrow:'Bibliothèque technique REPLACOR',title:'Trouvez le bloc, la mesure ou la procédure dont vous avez besoin',intro:'Partez d’un symptôme, suivez le parcours de la carte ou recherchez directement un concept.',modules:'thèmes techniques',chapters:'sections',figures:'figures',tables:'tableaux',safetyTitle:'Avant de mesurer',quickLookup:'Recherche rapide',searchTitle:'Que cherchez-vous à localiser ou réparer ?',searchLabel:'Rechercher en électronique',searchPlaceholder:'Exemples : alimentation morte, bus DC, ULN2003, reset, communication, IPM…',searchButton:'Rechercher',try:'Essayez :',routesTab:'Par symptôme',groupsTab:'Par bloc de carte',libraryTab:'Bibliothèque complète',savedTab:'Enregistrés',symptoms:'Diagnostic guidé',routesTitle:'Commencez par le comportement de la carte',routesIntro:'Chaque parcours place les contrôles utiles en premier sans déclarer automatiquement une panne.',boardMap:'Carte fonctionnelle',groupsTitle:'Suivez les parcours énergie, signal et commande',allContent:'Tout le contenu',libraryTitle:'Filtrer les thèmes techniques',block:'Bloc',allBlocks:'Tous les blocs',level:'Niveau',allLevels:'Tous les niveaux',personal:'Votre consultation',savedTitle:'Sections enregistrées',results:'Résultats',closeResults:'Fermer les résultats',back:'← Retour',chooseSection:'Choisir une section',previous:'Précédent',complete:'Marquer consulté',next:'Suivant',related:'Continuez ici',sources:'Sources techniques du thème',connected:'Outils associés',toolsTitle:'Passez de l’explication au contrôle',footer:'Informations indicatives : confirmez toujours le manuel et la fiche technique exacts.',openRoute:'Voir le parcours',openBlock:'Voir les thèmes',openTopic:'Ouvrir le thème',sections:'sections',pages:'pages',basic:'Débutant',intermediate:'Intermédiaire',advanced:'Avancé',noSaved:'Aucune section enregistrée pour le moment.',noResults:'Aucune correspondance trouvée.',resultsFor:'Résultats pour',recommended:'Parcours recommandé',bookmark:'☆ Enregistrer',bookmarked:'★ Enregistré',consulted:'✓ Consulté',markConsulted:'Marquer consulté',progress:'consultés',sourceAdded:'Référence de révision ajoutée',contentSpanish:'Contenu technique vérifié en espagnol',close:'Fermer',all:'Tous',modulesAvailable:'thèmes disponibles'
    },
  };

  function language() { return window.ST_I18N?.language || 'es'; }
  function t(key) { return ui[language()]?.[key] || ui.es[key] || key; }
  function loadSet(key) { try { return new Set(JSON.parse(localStorage.getItem(key) || '[]')); } catch (_) { return new Set(); } }
  function saveSet(key, value) { localStorage.setItem(key, JSON.stringify([...value])); }
  function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char])); }
  function normalize(value) { return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim(); }
  function levelLabel(level) { return level === 'basico' ? t('basic') : level === 'avanzado' ? t('advanced') : t('intermediate'); }

  function translateUi() {
    $$('[data-el-i18n]').forEach(node => { node.textContent = t(node.dataset.elI18n); });
    $$('[data-el-i18n-placeholder]').forEach(node => node.setAttribute('placeholder', t(node.dataset.elI18nPlaceholder)));
    renderRoutes(); renderGroups(); renderLibrary(); renderSaved(); renderTools();
    if (state.activeModule && state.activeChapter) renderReader(state.activeModule.id, state.activeChapter.id, false);
  }

  function createIndex() {
    state.modules = new Map(state.collection.modules.map(module => [module.id, module]));
    state.chapters.clear();
    state.collection.modules.forEach(module => module.chapters.forEach(chapter => state.chapters.set(chapter.id, {module, chapter})));
  }

  function updateStats() {
    const stats = state.collection.stats;
    $('#elModuleCount').textContent = stats.modules.toLocaleString();
    $('#elChapterCount').textContent = stats.chapters.toLocaleString();
    $('#elFigureCount').textContent = stats.figures.toLocaleString();
    $('#elTableCount').textContent = stats.tables.toLocaleString();
    $('#elSafetyText').textContent = state.collection.safety;
  }

  function moduleCard(module, action = t('openTopic')) {
    return `<article class="el-module-card" data-module="${module.id}">
      <div class="el-module-badge"><span class="el-module-icon">${escapeHtml(module.icon)}</span><span class="el-module-meta">${levelLabel(module.level)} · ${module.pages} ${t('pages')}</span></div>
      <h3>${escapeHtml(module.title)}</h3><p>${escapeHtml(module.summary)}</p>
      <span class="el-module-meta">${module.stats.chapters} ${t('sections')} · ${module.stats.figures} ${t('figures')} · ${module.stats.tables} ${t('tables')}</span>
      <button type="button" data-open-module="${module.id}">${action}</button></article>`;
  }

  function renderRoutes() {
    if (!state.collection) return;
    $('#elRouteGrid').innerHTML = state.collection.routes.map(route => {
      const flow = route.modules.slice(0,5).map(id => `<span>${escapeHtml(state.modules.get(id)?.icon || id)}</span>`).join('');
      return `<article class="el-route-card"><span class="el-module-meta">${t('recommended')}</span><h3>${escapeHtml(route.title)}</h3><p>${escapeHtml(route.summary)}</p><div class="el-route-flow">${flow}</div><button type="button" data-open-route="${route.id}">${t('openRoute')}</button></article>`;
    }).join('');
  }

  function renderGroups() {
    if (!state.collection) return;
    $('#elGroupGrid').innerHTML = state.collection.groups.map(group => {
      const count = state.collection.modules.filter(module => module.group === group.id).length;
      return `<article class="el-group-card"><span class="el-module-meta">${count} ${t('modulesAvailable')}</span><h3>${escapeHtml(group.title)}</h3><p>${escapeHtml(group.summary)}</p><button type="button" data-open-group="${group.id}">${t('openBlock')}</button></article>`;
    }).join('');
  }

  function populateFilters() {
    $('#elGroupFilter').insertAdjacentHTML('beforeend', state.collection.groups.map(group => `<option value="${group.id}">${escapeHtml(group.title)}</option>`).join(''));
  }

  function renderLibrary() {
    if (!state.collection) return;
    const group = $('#elGroupFilter')?.value || '';
    const level = $('#elLevelFilter')?.value || '';
    const modules = state.collection.modules.filter(module => (!group || module.group === group) && (!level || module.level === level));
    $('#elModuleGrid').innerHTML = modules.map(module => moduleCard(module)).join('');
  }

  function renderTools() {
    if (!state.collection) return;
    $('#elToolLinks').innerHTML = state.collection.tools.map(tool => `<article class="el-tool-card"><h3>${escapeHtml(tool.title)}</h3><p>${escapeHtml(tool.summary)}</p><a href="${escapeHtml(tool.href)}">${t('openTopic')}</a></article>`).join('');
  }

  function setView(view) {
    state.previousView = view;
    $('#elReader').hidden = true;
    $('.el-tabs').hidden = false;
    $('.el-search-panel').hidden = false;
    $('.el-tools-section').hidden = false;
    $$('.el-view[data-panel]').forEach(panel => { panel.hidden = panel.dataset.panel !== view; });
    $$('.el-tabs [role="tab"]').forEach(tab => tab.setAttribute('aria-selected', String(tab.dataset.view === view)));
    $('#elSearchResults').hidden = true;
    history.replaceState(null,'',location.pathname + location.search);
    window.scrollTo({top:$('.el-tabs').offsetTop - 12,behavior:'smooth'});
  }

  function showRecommendations(title, ids) {
    state.previousView = $$('.el-tabs [aria-selected="true"]')[0]?.dataset.view || 'routes';
    $$('.el-view[data-panel]').forEach(panel => { panel.hidden = true; });
    $('#elSearchResults').hidden = false;
    $('#elSearchResultsTitle').textContent = title;
    $('#elResultsList').innerHTML = `<div class="el-module-grid">${ids.map(id => state.modules.get(id)).filter(Boolean).map(module => moduleCard(module)).join('')}</div>`;
    $('#elSearchResults').scrollIntoView({behavior:'smooth',block:'start'});
  }

  function runSearch(query) {
    const normalized = normalize(query);
    if (!normalized) return;
    const tokens = normalized.split(' ').filter(Boolean);
    const results = [];
    state.chapters.forEach(({module, chapter}) => {
      const title = normalize(chapter.title);
      const moduleTitle = normalize(module.title);
      let score = title === normalized ? 120 : title.includes(normalized) ? 50 : chapter.search.includes(normalized) ? 25 : 0;
      tokens.forEach(token => { if (title.includes(token)) score += 12; else if (moduleTitle.includes(token)) score += 7; else if (chapter.search.includes(token)) score += 2; });
      if (score) results.push({module,chapter,score});
    });
    results.sort((a,b) => b.score - a.score || a.chapter.title.localeCompare(b.chapter.title));
    state.previousView = $$('.el-tabs [aria-selected="true"]')[0]?.dataset.view || 'routes';
    $$('.el-view[data-panel]').forEach(panel => { panel.hidden = true; });
    $('#elSearchResults').hidden = false;
    $('#elSearchResultsTitle').textContent = `${t('resultsFor')} “${query}” (${results.length})`;
    $('#elResultsList').innerHTML = results.length ? results.slice(0,80).map(({module,chapter}) => `<button class="el-result" type="button" data-open-chapter="${chapter.id}"><strong>${escapeHtml(chapter.title)}</strong><span>${escapeHtml(module.title)} · ${chapter.word_count} palabras</span></button>`).join('') : `<p>${t('noResults')}</p>`;
    $('#elSearchResults').scrollIntoView({behavior:'smooth',block:'start'});
  }

  function renderBlock(block) {
    if (block.type === 'paragraph') return `<p>${escapeHtml(block.text)}</p>`;
    if (block.type === 'subheading') return `<h3>${escapeHtml(block.text)}</h3>`;
    if (block.type === 'caption') return `<p class="el-module-meta">${escapeHtml(block.text)}</p>`;
    if (block.type === 'list') return `<ul>${block.items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
    if (block.type === 'callout') return `<aside class="el-callout ${escapeHtml(block.kind || '')}">${escapeHtml(block.text)}</aside>`;
    if (block.type === 'figure') return `<figure class="el-figure"><img src="${escapeHtml(block.src)}" alt="${escapeHtml(block.alt || '')}" loading="lazy" data-caption="${escapeHtml(block.caption || block.alt || '')}">${block.caption ? `<figcaption>${escapeHtml(block.caption)}</figcaption>` : ''}</figure>`;
    if (block.type === 'table') return `<div class="el-table-wrap"><table><thead><tr>${block.headers.map(cell => `<th>${escapeHtml(cell)}</th>`).join('')}</tr></thead><tbody>${block.rows.map(row => `<tr>${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
    return '';
  }

  function renderReader(moduleId, chapterId, updateHash = true) {
    const module = state.modules.get(moduleId);
    if (!module) return;
    const chapter = module.chapters.find(item => item.id === chapterId) || module.chapters[0];
    if (!chapter) return;
    state.activeModule = module; state.activeChapter = chapter;
    $$('.el-view').forEach(view => { view.hidden = true; });
    $('.el-tabs').hidden = true; $('.el-search-panel').hidden = true; $('.el-tools-section').hidden = true;
    $('#elReader').hidden = false;
    $('#elBreadcrumb').textContent = `${state.collection.groups.find(group => group.id === module.group)?.title || ''} › ${module.title}`;
    $('#elModuleHeader').innerHTML = `<span class="el-module-meta">${levelLabel(module.level)} · ${module.pages} ${t('pages')} · ${module.stats.chapters} ${t('sections')}</span><h1>${escapeHtml(module.title)}</h1><p>${escapeHtml(module.summary)}</p>`;
    $('#elEditorialNotes').innerHTML = module.editorial_notes.map(note => `<p>${escapeHtml(note)}</p>`).join('');
    $('#elChapterSelect').innerHTML = module.chapters.map(item => `<option value="${item.id}" ${item.id === chapter.id ? 'selected' : ''}>${escapeHtml(item.title)}</option>`).join('');
    $('#elChapterList').innerHTML = module.chapters.map(item => `<button type="button" data-reader-chapter="${item.id}" class="${item.id === chapter.id ? 'active' : ''}">${escapeHtml(item.title)}</button>`).join('');
    $('#elChapterTitle').textContent = chapter.title;
    $('#elChapterContent').innerHTML = chapter.blocks.map(renderBlock).join('');
    $('#elBookmark').textContent = state.bookmarks.has(chapter.id) ? t('bookmarked') : t('bookmark');
    $('#elComplete').textContent = state.completed.has(chapter.id) ? t('consulted') : t('markConsulted');
    $('#elProgressText').textContent = `${module.chapters.filter(item => state.completed.has(item.id)).length} / ${module.chapters.length} ${t('progress')}`;
    const index = module.chapters.indexOf(chapter);
    $('#elPrevious').disabled = index <= 0; $('#elNext').disabled = index >= module.chapters.length - 1;
    $('#elRelatedModules').innerHTML = module.related.slice(0,6).map(id => state.modules.get(id)).filter(Boolean).map(item => moduleCard(item)).join('');
    $('#elSources').innerHTML = module.sources.length ? module.sources.map(source => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title)}${source.editorial_addition ? ` · ${t('sourceAdded')}` : ''}</a>`).join('') : `<p>${t('contentSpanish')}</p>`;
    localStorage.setItem('st.electronics.last', chapter.id);
    if (updateHash) history.replaceState(null,'',`#module=${module.id}&chapter=${encodeURIComponent(chapter.id)}`);
    window.scrollTo({top:$('#elReader').offsetTop - 12,behavior:'smooth'});
  }

  function openChapter(chapterId) {
    const entry = state.chapters.get(chapterId);
    if (entry) renderReader(entry.module.id, entry.chapter.id);
  }

  function renderSaved() {
    if (!state.collection) return;
    const entries = [...state.bookmarks].map(id => state.chapters.get(id)).filter(Boolean);
    $('#elSavedList').innerHTML = entries.length ? entries.map(({module,chapter}) => `<button class="el-result" type="button" data-open-chapter="${chapter.id}"><strong>${escapeHtml(chapter.title)}</strong><span>${escapeHtml(module.title)}</span></button>`).join('') : `<p>${t('noSaved')}</p>`;
  }

  function bindEvents() {
    document.addEventListener('click', event => {
      const tab = event.target.closest('[data-view]'); if (tab) return setView(tab.dataset.view);
      const routeButton = event.target.closest('[data-open-route]'); if (routeButton) { const route = state.collection.routes.find(item => item.id === routeButton.dataset.openRoute); return showRecommendations(route.title, route.modules); }
      const groupButton = event.target.closest('[data-open-group]'); if (groupButton) { const group = state.collection.groups.find(item => item.id === groupButton.dataset.openGroup); return showRecommendations(group.title, state.collection.modules.filter(module => module.group === group.id).map(module => module.id)); }
      const moduleButton = event.target.closest('[data-open-module]'); if (moduleButton) return renderReader(moduleButton.dataset.openModule, state.modules.get(moduleButton.dataset.openModule)?.chapters[0]?.id);
      const chapterButton = event.target.closest('[data-open-chapter]'); if (chapterButton) return openChapter(chapterButton.dataset.openChapter);
      const navChapter = event.target.closest('[data-reader-chapter]'); if (navChapter) return renderReader(state.activeModule.id, navChapter.dataset.readerChapter);
      const example = event.target.closest('.el-search-examples button'); if (example) { $('#elSearch').value = example.textContent; return runSearch(example.textContent); }
      const image = event.target.closest('#elChapterContent img'); if (image) { $('#elFigureImage').src = image.src; $('#elFigureImage').alt = image.alt; $('#elFigureCaption').textContent = image.dataset.caption || image.alt; return $('#elFigureDialog').showModal(); }
    });
    $('#elSearchForm').addEventListener('submit', event => { event.preventDefault(); runSearch($('#elSearch').value.trim()); });
    $('#elCloseSearch').addEventListener('click', () => setView(state.previousView));
    $('#elGroupFilter').addEventListener('change', renderLibrary); $('#elLevelFilter').addEventListener('change', renderLibrary);
    $('#elReaderBack').addEventListener('click', () => setView(state.previousView));
    $('#elChapterSelect').addEventListener('change', event => renderReader(state.activeModule.id, event.target.value));
    $('#elPrevious').addEventListener('click', () => { const i = state.activeModule.chapters.indexOf(state.activeChapter); if (i > 0) renderReader(state.activeModule.id, state.activeModule.chapters[i - 1].id); });
    $('#elNext').addEventListener('click', () => { const i = state.activeModule.chapters.indexOf(state.activeChapter); if (i < state.activeModule.chapters.length - 1) renderReader(state.activeModule.id, state.activeModule.chapters[i + 1].id); });
    $('#elBookmark').addEventListener('click', () => { const id = state.activeChapter.id; state.bookmarks.has(id) ? state.bookmarks.delete(id) : state.bookmarks.add(id); saveSet('st.electronics.bookmarks', state.bookmarks); renderReader(state.activeModule.id,id,false); renderSaved(); });
    $('#elComplete').addEventListener('click', () => { const id = state.activeChapter.id; state.completed.has(id) ? state.completed.delete(id) : state.completed.add(id); saveSet('st.electronics.completed', state.completed); renderReader(state.activeModule.id,id,false); });
    $('#elFigureDialog button').addEventListener('click', () => $('#elFigureDialog').close());
    document.addEventListener('st:languagechange', translateUi);
  }

  async function init() {
    bindEvents();
    try {
      const response = await fetch('data/electronics/collection.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.collection = await response.json(); createIndex(); updateStats(); populateFilters(); translateUi();
      const params = new URLSearchParams(location.hash.replace(/^#/,''));
      const moduleId = params.get('module'); const chapterId = params.get('chapter');
      if (moduleId && state.modules.has(moduleId)) renderReader(moduleId, chapterId, false);
    } catch (error) {
      console.error(error); $('#elRouteGrid').innerHTML = '<p>No se pudo cargar la biblioteca de electrónica.</p>';
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
