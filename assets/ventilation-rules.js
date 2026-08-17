(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.STVentilationRules = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const SOURCES = Object.freeze({
    cteHs3: Object.freeze({
      id: 'CTE_DB_HS3',
      label: 'CTE DB HS 3 · Calidad del aire interior',
      checked: '2026-08-17',
      url: 'https://www.codigotecnico.org/pdf/Documentos/HS/DBHS.pdf',
      notes: 'Documento Básico HS consolidado. Aplicable a viviendas, trasteros, almacenes de residuos, aparcamientos y garajes dentro de su ámbito.',
    }),
    rite: Object.freeze({
      id: 'RITE_IT_1_1_4_2',
      label: 'RITE · IT 1.1.4.2 Calidad del aire interior',
      checked: '2026-08-17',
      url: 'https://www.boe.es/buscar/act.php?id=BOE-A-2007-15820',
      notes: 'Texto consolidado del Real Decreto 1027/2007. El método por persona exige actividad próxima a 1,2 met, baja emisión de otros contaminantes y ausencia de humo.',
    }),
    technical: Object.freeze({
      id: 'TECHNICAL_ACH',
      label: 'Criterio técnico por renovaciones/hora',
      checked: '2026-08-17',
      url: '',
      notes: 'No constituye por sí solo una justificación normativa. El técnico fija las renovaciones requeridas para el caso real.',
    }),
  });

  const PROFILES = Object.freeze({
    cte_dwelling: Object.freeze({
      label: 'Vivienda · ventilación general',
      short: 'Vivienda',
      source: 'cteHs3',
      method: 'cte_dwelling',
      defaultMode: 'balanced',
      basis: 'Caudales mínimos por tipo de estancia y número de dormitorios',
      reference: 'CTE DB HS 3, tabla 2.1',
    }),
    rite_ida2_people: Object.freeze({
      label: 'Oficina, aula, museo o sala de lectura',
      short: 'RITE IDA 2',
      source: 'rite',
      method: 'people',
      lpsPerPerson: 12.5,
      defaultMode: 'balanced',
      basis: '12,5 l/s por persona',
      reference: 'RITE IT 1.1.4.2.2 e IT 1.1.4.2.3 A',
    }),
    rite_ida3_people: Object.freeze({
      label: 'Comercio, cine, teatro u hotel',
      short: 'RITE IDA 3',
      source: 'rite',
      method: 'people',
      lpsPerPerson: 8,
      defaultMode: 'balanced',
      basis: '8 l/s por persona',
      reference: 'RITE IT 1.1.4.2.2 e IT 1.1.4.2.3 A',
    }),
    rite_service_extract: Object.freeze({
      label: 'Local de servicio o aseos · extracción',
      short: 'Servicio',
      source: 'rite',
      method: 'area',
      lpsPerM2: 2,
      defaultMode: 'extract',
      basis: 'Mínimo 2 l/s por m² de superficie en planta',
      reference: 'RITE IT 1.1.4.2.5, apartado 2',
    }),
    cte_storage: Object.freeze({
      label: 'Trasteros y zonas comunes',
      short: 'Trasteros',
      source: 'cteHs3',
      method: 'area',
      lpsPerM2: 0.7,
      defaultMode: 'extract',
      basis: '0,7 l/s por m² útil',
      reference: 'CTE DB HS 3, tabla 2.2',
    }),
    cte_waste: Object.freeze({
      label: 'Almacén de residuos',
      short: 'Residuos',
      source: 'cteHs3',
      method: 'area',
      lpsPerM2: 10,
      defaultMode: 'extract',
      basis: '10 l/s por m² útil',
      reference: 'CTE DB HS 3, tabla 2.2',
    }),
    cte_garage: Object.freeze({
      label: 'Aparcamiento o garaje',
      short: 'Garaje',
      source: 'cteHs3',
      method: 'parking',
      lpsPerSpace: 120,
      defaultMode: 'extract',
      basis: '120 l/s por plaza',
      reference: 'CTE DB HS 3, tabla 2.2',
    }),
    cte_kitchen_hood: Object.freeze({
      label: 'Extracción independiente de cocina',
      short: 'Campana',
      source: 'cteHs3',
      method: 'fixed_per_room',
      lpsPerRoom: 50,
      defaultMode: 'extract',
      basis: 'Mínimo 50 l/s en la zona de cocción',
      reference: 'CTE DB HS 3, apartado 2.4',
    }),
    technical_ach: Object.freeze({
      label: 'Otro recinto · renovaciones por hora',
      short: 'Renovaciones/h',
      source: 'technical',
      method: 'ach',
      defaultMode: 'extract',
      basis: 'Volumen × renovaciones/h indicadas por el técnico',
      reference: 'Criterio de proyecto aportado por el técnico',
    }),
  });

  const ROOM_TYPES = Object.freeze({
    unassigned: Object.freeze({ label: 'Sin identificar', short: 'ESTANCIA', color: '#8a96a8', role: 'neutral' }),
    bedroom_main: Object.freeze({ label: 'Dormitorio principal', short: 'DORM. PRINCIPAL', color: '#00c8ff', role: 'dry' }),
    bedroom: Object.freeze({ label: 'Dormitorio', short: 'DORMITORIO', color: '#29a9ff', role: 'dry' }),
    living: Object.freeze({ label: 'Salón / comedor', short: 'SALÓN', color: '#a66bff', role: 'dry' }),
    office: Object.freeze({ label: 'Oficina / despacho', short: 'OFICINA', color: '#00e6c7', role: 'occupied' }),
    classroom: Object.freeze({ label: 'Aula / sala', short: 'AULA', color: '#39d98a', role: 'occupied' }),
    retail: Object.freeze({ label: 'Comercio / público', short: 'PÚBLICO', color: '#ffe438', role: 'occupied' }),
    kitchen: Object.freeze({ label: 'Cocina', short: 'COCINA', color: '#ff7a00', role: 'wet' }),
    bathroom: Object.freeze({ label: 'Baño', short: 'BAÑO', color: '#ff3fa7', role: 'wet' }),
    toilet: Object.freeze({ label: 'Aseo', short: 'ASEO', color: '#ff5e66', role: 'wet' }),
    utility: Object.freeze({ label: 'Lavadero / servicio', short: 'SERVICIO', color: '#ef8bff', role: 'wet' }),
    hallway: Object.freeze({ label: 'Pasillo / distribuidor', short: 'PASILLO', color: '#51ff7d', role: 'neutral' }),
    storage: Object.freeze({ label: 'Trastero / almacén', short: 'ALMACÉN', color: '#d6a96b', role: 'service' }),
    garage: Object.freeze({ label: 'Garaje / aparcamiento', short: 'GARAJE', color: '#8c9aaf', role: 'service' }),
    other: Object.freeze({ label: 'Otro recinto', short: 'RECINTO', color: '#f0f3f8', role: 'occupied' }),
  });

  return { schemaVersion: '1.0', checked: '2026-08-17', SOURCES, PROFILES, ROOM_TYPES };
});
