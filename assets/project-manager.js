(() => {
  'use strict';
  const API = window.SuperTecnicoProjects;
  if (!API) return;
  const $ = id => document.getElementById(id);
  const elements = {
    form: $('projectCreateForm'), name: $('projectName'), discipline: $('projectDiscipline'), client: $('projectClient'), location: $('projectLocation'), notes: $('projectNotes'),
    list: $('projectList'), empty: $('projectEmpty'), workspace: $('projectWorkspace'), activeName: $('activeProjectName'), activeMeta: $('activeProjectMeta'), artifactList: $('artifactList'), measurementRows: $('projectMeasurementRows'), measurementEmpty: $('measurementEmpty'), projectCount: $('projectCount'), artifactCount: $('artifactCount'), exportButton: $('projectExport'), printButton: $('projectPrint'), deleteButton: $('projectDelete'),
  };

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function formatDate(value) {
    try { return new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)); }
    catch (_) { return String(value || ''); }
  }

  function moduleLabel(id) {
    return ({ ducts: 'Conductos', ventilation: 'Ventilación', refrigerant_piping: 'Tuberías frigoríficas', condensate: 'Desagües', electrical_panels: 'Cuadros eléctricos' })[id] || id;
  }

  function renderProjects(projects, activeId) {
    elements.projectCount.textContent = String(projects.length);
    elements.list.innerHTML = projects.map(project => `<button class="project-row${project.id === activeId ? ' is-active' : ''}" type="button" data-project-id="${escapeHtml(project.id)}"><span><strong>${escapeHtml(project.name)}</strong><small>${escapeHtml(project.discipline)} · ${formatDate(project.updated_at)}</small></span><b>${project.artifacts.length}</b></button>`).join('');
    elements.empty.hidden = projects.length > 0;
  }

  function renderWorkspace(project) {
    elements.workspace.hidden = !project;
    if (!project) return;
    elements.activeName.textContent = project.name;
    elements.activeMeta.textContent = [project.discipline, project.client, project.location].filter(Boolean).join(' · ') || 'Proyecto técnico local';
    elements.artifactCount.textContent = String(project.artifacts.length);
    elements.artifactList.innerHTML = project.artifacts.length ? project.artifacts.map(artifact => `<article class="artifact-card"><div class="artifact-icon">${escapeHtml(moduleLabel(artifact.module_id).slice(0, 2).toUpperCase())}</div><div><span>${escapeHtml(moduleLabel(artifact.module_id))}</span><h3>${escapeHtml(artifact.title)}</h3><p>${escapeHtml(artifact.summary || 'Resultado guardado en el proyecto.')}</p><small>${formatDate(artifact.created_at)} · ${artifact.measurements.length} partidas sin precio</small></div></article>`).join('') : '<div class="workspace-empty"><strong>Aún no hay resultados guardados</strong><p>Abre una herramienta, realiza el cálculo y pulsa «Guardar en Proyecto».</p></div>';
    const measurements = API.aggregateMeasurements(project);
    elements.measurementEmpty.hidden = measurements.length > 0;
    elements.measurementRows.innerHTML = measurements.map(item => `<tr><td><strong>${escapeHtml(item.description)}</strong><small>${escapeHtml(item.code)}</small></td><td>${escapeHtml(item.unit)}</td><td>${String(item.quantity).replace('.', ',')}</td></tr>`).join('');
  }

  function render() {
    const projects = API.list();
    let active = API.get();
    if (!active && projects[0]) active = API.setActive(projects[0].id);
    renderProjects(projects, active?.id || '');
    renderWorkspace(active);
  }

  elements.form.addEventListener('submit', event => {
    event.preventDefault();
    API.create({ name: elements.name.value, discipline: elements.discipline.value, client: elements.client.value, location: elements.location.value, notes: elements.notes.value });
    elements.form.reset();
    render();
  });
  elements.list.addEventListener('click', event => {
    const button = event.target.closest('[data-project-id]');
    if (!button) return;
    API.setActive(button.dataset.projectId);
    render();
  });
  elements.exportButton.addEventListener('click', () => {
    const project = API.get();
    if (!project) return;
    const blob = new Blob([JSON.stringify(API.exportProject(project.id), null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${project.name.toLocaleLowerCase('es').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'proyecto-super-tecnico'}.json`;
    link.click();
    URL.revokeObjectURL(url);
  });
  elements.printButton.addEventListener('click', () => window.print());
  elements.deleteButton.addEventListener('click', () => {
    const project = API.get();
    if (!project || !confirm(`¿Eliminar «${project.name}» de este dispositivo?`)) return;
    API.remove(project.id);
    render();
  });
  window.addEventListener(API.EVENT_NAME, render);
  render();
})();
