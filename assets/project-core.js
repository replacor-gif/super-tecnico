(() => {
  'use strict';

  const STORAGE_KEY = 'st.technicalProjects.v1';
  const ACTIVE_KEY = 'st.technicalProjects.active.v1';
  const EVENT_NAME = 'st:project-change';

  function now() {
    return new Date().toISOString();
  }

  function uid(prefix = 'project') {
    if (globalThis.crypto?.randomUUID) return `${prefix}-${crypto.randomUUID()}`;
    return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function emptyStore() {
    return { schema_version: '1.0', projects: [] };
  }

  function loadStore() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
      if (!parsed || !Array.isArray(parsed.projects)) return emptyStore();
      return {
        schema_version: '1.0',
        projects: parsed.projects.filter(Boolean).map(project => ({
          id: String(project.id || uid()),
          name: String(project.name || 'Proyecto sin nombre'),
          discipline: String(project.discipline || 'multidisciplinar'),
          client: String(project.client || ''),
          location: String(project.location || ''),
          notes: String(project.notes || ''),
          created_at: project.created_at || now(),
          updated_at: project.updated_at || project.created_at || now(),
          artifacts: Array.isArray(project.artifacts) ? project.artifacts : [],
        })),
      };
    } catch (_) {
      return emptyStore();
    }
  }

  function saveStore(store) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
    window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: summary() }));
    return store;
  }

  function list() {
    return loadStore().projects.sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
  }

  function activeId() {
    try { return localStorage.getItem(ACTIVE_KEY) || ''; } catch (_) { return ''; }
  }

  function get(projectId) {
    const id = projectId || activeId();
    return loadStore().projects.find(project => project.id === id) || null;
  }

  function setActive(projectId) {
    const project = get(projectId);
    if (!project) return null;
    localStorage.setItem(ACTIVE_KEY, project.id);
    window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: summary() }));
    return clone(project);
  }

  function create(input = {}) {
    const store = loadStore();
    const timestamp = now();
    const project = {
      id: uid('stp'),
      name: String(input.name || '').trim() || 'Nuevo proyecto',
      discipline: String(input.discipline || 'multidisciplinar'),
      client: String(input.client || '').trim(),
      location: String(input.location || '').trim(),
      notes: String(input.notes || '').trim(),
      created_at: timestamp,
      updated_at: timestamp,
      artifacts: [],
    };
    store.projects.push(project);
    saveStore(store);
    setActive(project.id);
    return clone(project);
  }

  function update(projectId, input = {}) {
    const store = loadStore();
    const project = store.projects.find(item => item.id === projectId);
    if (!project) throw new Error('No se ha encontrado el proyecto.');
    for (const key of ['name', 'discipline', 'client', 'location', 'notes']) {
      if (Object.hasOwn(input, key)) project[key] = String(input[key] || '').trim();
    }
    if (!project.name) project.name = 'Proyecto sin nombre';
    project.updated_at = now();
    saveStore(store);
    return clone(project);
  }

  function remove(projectId) {
    const store = loadStore();
    const next = store.projects.filter(project => project.id !== projectId);
    if (next.length === store.projects.length) return false;
    store.projects = next;
    saveStore(store);
    if (activeId() === projectId) {
      if (next[0]) setActive(next[0].id);
      else localStorage.removeItem(ACTIVE_KEY);
    }
    return true;
  }

  function normalizeMeasurements(rows) {
    if (!Array.isArray(rows)) return [];
    return rows.map((row, index) => ({
      code: String(row.code || row.id || `ITEM-${index + 1}`),
      description: String(row.description || row.label || 'Partida'),
      unit: String(row.unit || 'ud'),
      quantity: Number(row.quantity) || 0,
      specification: String(row.specification || ''),
    })).filter(row => row.quantity >= 0);
  }

  function attachArtifact(input = {}, projectId = '') {
    const store = loadStore();
    let id = projectId || activeId();
    let project = store.projects.find(item => item.id === id);
    if (!project) {
      project = create({ name: input.suggested_project_name || 'Proyecto de campo', discipline: input.discipline || input.module_id || 'multidisciplinar' });
      return attachArtifact(input, project.id);
    }
    const timestamp = now();
    const moduleId = String(input.module_id || 'general');
    const artifact = {
      id: uid('artifact'),
      module_id: moduleId,
      title: String(input.title || 'Resultado técnico'),
      summary: String(input.summary || ''),
      source_page: String(input.source_page || location.pathname.split('/').pop() || ''),
      status: String(input.status || 'predesign'),
      created_at: timestamp,
      warnings: Array.isArray(input.warnings) ? clone(input.warnings).slice(0, 40) : [],
      measurements: normalizeMeasurements(input.measurements),
      snapshot: clone(input.snapshot || {}),
    };
    const replaceIndex = project.artifacts.findIndex(item => item.module_id === moduleId);
    if (replaceIndex >= 0) project.artifacts[replaceIndex] = artifact;
    else project.artifacts.push(artifact);
    project.updated_at = timestamp;
    saveStore(store);
    return clone({ project, artifact });
  }

  function aggregateMeasurements(project) {
    const grouped = new Map();
    (project?.artifacts || []).flatMap(artifact => artifact.measurements || []).forEach(item => {
      const key = `${item.code}|${item.unit}|${item.description}`;
      const current = grouped.get(key) || { ...item, quantity: 0 };
      current.quantity += Number(item.quantity) || 0;
      grouped.set(key, current);
    });
    return [...grouped.values()].map(item => ({ ...item, quantity: Math.round(item.quantity * 1000) / 1000 }));
  }

  function exportProject(projectId) {
    const project = get(projectId);
    if (!project) throw new Error('No se ha encontrado el proyecto.');
    return {
      schema_version: '1.0',
      exported_at: now(),
      product: 'Super Técnico',
      pricing_status: 'unpriced_measurements_only',
      project: clone(project),
      bill_of_quantities: aggregateMeasurements(project),
    };
  }

  function summary() {
    const projects = list();
    const active = projects.find(project => project.id === activeId()) || null;
    return {
      project_count: projects.length,
      active_project_id: active?.id || '',
      active_project_name: active?.name || '',
      artifact_count: active?.artifacts?.length || 0,
    };
  }

  window.SuperTecnicoProjects = Object.freeze({
    STORAGE_KEY,
    EVENT_NAME,
    list,
    get,
    activeId,
    setActive,
    create,
    update,
    remove,
    attachArtifact,
    aggregateMeasurements,
    exportProject,
    summary,
  });
})();
