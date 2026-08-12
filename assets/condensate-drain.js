(() => {
  'use strict';
  const engine = window.CondensateDrainEngine;
  const unitList = document.getElementById('unitList');
  const resultPanel = document.getElementById('resultPanel');
  let nextId = 1;

  function unitTemplate(values = {}) {
    const id = nextId++;
    const card = document.createElement('article');
    card.className = 'cd-unit-card';
    card.dataset.unitId = String(id);
    card.innerHTML = `
      <div class="cd-unit-head"><span class="cd-unit-number"></span><input class="cd-name" aria-label="Nombre del equipo" value="${escapeHtml(values.name || `Máquina ${id}`)}"><button class="cd-remove" type="button" aria-label="Eliminar equipo">×</button></div>
      <div class="cd-unit-grid">
        <label class="cd-field cd-field-mode"><span>Dato disponible</span><select class="cd-mode"><option value="capacity">Potencia de la máquina</option><option value="known_flow">Caudal conocido</option></select></label>
        <label class="cd-field cd-capacity-field"><span>Potencia frigorífica</span><span class="cd-value-wrap"><input class="cd-capacity" type="text" inputmode="decimal" value="${values.capacity || '3,5'}"><select class="cd-capacity-unit"><option value="kw">kW</option><option value="frig_h">frig/h</option><option value="btu_h">BTU/h</option></select></span></label>
        <label class="cd-field cd-climate-field"><span>Condición</span><select class="cd-climate"><option value="normal">Normal</option><option value="humid" selected>Húmeda</option><option value="very_humid">Muy húmeda</option></select></label>
        <label class="cd-field cd-flow-field" hidden><span>Caudal real</span><span class="cd-value-wrap"><input class="cd-flow" type="text" inputmode="decimal" value="${values.flow || '2'}"><select disabled><option>L/h</option></select></span></label>
        <label class="cd-field"><span>Conexión interior</span><span class="cd-value-wrap"><input class="cd-connection" type="text" inputmode="decimal" value="${values.connection || '16'}"><select disabled><option>mm</option></select></span></label>
        <label class="cd-field"><span>Tramo hasta la unión</span><span class="cd-value-wrap"><input class="cd-length" type="text" inputmode="decimal" value="${values.length || '4'}"><select disabled><option>m</option></select></span></label>
      </div>`;
    card.querySelector('.cd-mode').value = values.mode || 'capacity';
    card.querySelector('.cd-capacity-unit').value = values.capacityUnit || 'kw';
    card.querySelector('.cd-climate').value = values.climate || 'humid';
    updateMode(card);
    card.querySelector('.cd-mode').addEventListener('change', () => updateMode(card));
    card.querySelector('.cd-remove').addEventListener('click', () => { card.remove(); renumber(); });
    unitList.append(card);
    renumber();
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[char]));
  }

  function updateMode(card) {
    const known = card.querySelector('.cd-mode').value === 'known_flow';
    const capacityField = card.querySelector('.cd-capacity-field');
    const climateField = card.querySelector('.cd-climate-field');
    const flowField = card.querySelector('.cd-flow-field');
    capacityField.hidden = known;
    climateField.hidden = known;
    flowField.hidden = !known;
    capacityField.style.display = known ? 'none' : 'grid';
    climateField.style.display = known ? 'none' : 'grid';
    flowField.style.display = known ? 'grid' : 'none';
  }

  function renumber() {
    [...unitList.children].forEach((card, index) => {
      card.querySelector('.cd-unit-number').textContent = String(index + 1);
      card.querySelector('.cd-remove').hidden = unitList.children.length === 1;
    });
  }

  function value(card, selector) { return card.querySelector(selector).value.trim(); }

  function collect() {
    return {
      slope_percent: document.getElementById('slopeInput').value,
      units: [...unitList.children].map(card => ({
        id: card.dataset.unitId,
        name: value(card, '.cd-name'),
        mode: value(card, '.cd-mode'),
        capacity: value(card, '.cd-capacity'),
        capacity_unit: value(card, '.cd-capacity-unit'),
        climate: value(card, '.cd-climate'),
        flow_l_h: value(card, '.cd-flow'),
        connection_mm: value(card, '.cd-connection'),
        segment_length_m: value(card, '.cd-length'),
      })),
    };
  }

  function fmt(value, digits = 1) { return Number(value).toLocaleString('es-ES', { maximumFractionDigits: digits, minimumFractionDigits: digits }); }

  function render(result) {
    document.getElementById('totalFlow').textContent = `${fmt(result.total_design_flow_l_h)} L/h`;
    document.getElementById('collectorSize').textContent = result.collector_internal_diameter_mm ? `Ø ${result.collector_internal_diameter_mm} mm` : 'Revisión específica';
    document.getElementById('totalFall').textContent = `${fmt(result.total_fall_cm)} cm`;
    document.getElementById('totalLength').textContent = `en ${fmt(result.total_length_m)} m al ${fmt(result.slope_percent)} %`;
    document.getElementById('segmentRows').innerHTML = result.segments.map(segment => `<tr><td><b>${escapeHtml(segment.from)}</b><br><small>hasta ${escapeHtml(segment.to)}</small></td><td>${fmt(segment.cumulative_design_flow_l_h)} L/h</td><td><strong>${segment.recommended_internal_diameter_mm ? `Ø ${segment.recommended_internal_diameter_mm} mm` : 'Especial'}</strong></td><td>${fmt(segment.segment_length_m)} m</td><td>${fmt(segment.fall_cm)} cm</td></tr>`).join('');
    document.getElementById('networkDiagram').innerHTML = result.segments.map((segment, index) => `<div class="cd-network-node"><div class="cd-machine"><b>${escapeHtml(segment.from)}</b><small>Σ ${fmt(segment.cumulative_design_flow_l_h)} L/h</small></div><div class="cd-pipe" style="height:${Math.max(6, Math.min(16, (segment.recommended_internal_diameter_mm || 16) / 3))}px"><span>Ø ${segment.recommended_internal_diameter_mm || '?'} · ${fmt(segment.fall_cm)} cm↓</span></div></div>${index === result.segments.length - 1 ? '<div class="cd-outlet">DESAGÜE</div>' : ''}`).join('');
    const standard = [
      'El diámetro mostrado es interior y nunca baja de la mayor conexión de fabricante indicada aguas arriba.',
      'Verifica sifón, entrada de aire, registros de limpieza y conexión final al saneamiento según el equipo y la obra.',
      ...result.warnings,
    ];
    document.getElementById('warningList').innerHTML = standard.map(text => `<p class="cd-warning">${escapeHtml(text)}</p>`).join('');
    resultPanel.hidden = false;
    resultPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function calculate() {
    const error = document.getElementById('formError');
    try {
      render(engine.designNetwork(collect()));
      error.hidden = true;
    } catch (exception) {
      error.textContent = exception.message || 'Revisa los datos introducidos.';
      error.hidden = false;
    }
  }

  document.getElementById('addUnitButton').addEventListener('click', () => unitTemplate({ length: '3' }));
  document.getElementById('calculateButton').addEventListener('click', calculate);
  document.getElementById('exampleButton').addEventListener('click', () => {
    unitList.replaceChildren(); nextId = 1;
    unitTemplate({ name: 'Dormitorio 1', capacity: '2,6', length: '5', climate: 'humid' });
    unitTemplate({ name: 'Dormitorio 2', capacity: '2,6', length: '4', climate: 'humid' });
    unitTemplate({ name: 'Salón', capacity: '5,2', length: '7', climate: 'very_humid', connection: '20' });
    document.getElementById('slopeInput').value = '1';
    calculate();
  });

  unitTemplate({ name: 'Máquina 1', capacity: '3,5', length: '4' });
  unitTemplate({ name: 'Máquina 2', capacity: '3,5', length: '5' });
})();
