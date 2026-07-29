(() => {
  'use strict';
  const C = window.STCalc;
  const host = document.getElementById('calculatorHost');
  const homeView = document.getElementById('homeView');
  const toolView = document.getElementById('toolView');
  const toolGrid = document.getElementById('toolGrid');
  const categoryFilters = document.getElementById('categoryFilters');
  const resultCount = document.getElementById('resultCount');
  const emptyState = document.getElementById('emptyState');
  const relatedTools = document.getElementById('relatedTools');
  const template = document.getElementById('calculatorTemplate');
  const printButton = document.getElementById('printButton');
  let activeCategory = 'Todas';

  const localeText = {
    es: {
      calculate: 'Calcular', example: 'Cargar ejemplo', tools: 'herramientas',
      tool: 'herramienta', copied: 'Resultado copiado', copy: 'Copiar resultado',
      copyError: 'No se pudo copiar automáticamente.', breadcrumb: 'Calculadoras',
      groups: ['Todas', 'Fundamentos', 'Identificación', 'Pasivos y circuitos', 'Aire acondicionado'],
    },
    en: {
      calculate: 'Calculate', example: 'Load example', tools: 'tools',
      tool: 'tool', copied: 'Result copied', copy: 'Copy result',
      copyError: 'The result could not be copied automatically.', breadcrumb: 'Calculators',
      groups: ['All', 'Fundamentals', 'Identification', 'Passive components and circuits', 'Air conditioning'],
    },
    pt: {
      calculate: 'Calcular', example: 'Carregar exemplo', tools: 'ferramentas',
      tool: 'ferramenta', copied: 'Resultado copiado', copy: 'Copiar resultado',
      copyError: 'Não foi possível copiar automaticamente.', breadcrumb: 'Calculadoras',
      groups: ['Todas', 'Fundamentos', 'Identificação', 'Passivos e circuitos', 'Climatização'],
    },
    fr: {
      calculate: 'Calculer', example: 'Charger un exemple', tools: 'outils',
      tool: 'outil', copied: 'Résultat copié', copy: 'Copier le résultat',
      copyError: 'Le résultat n’a pas pu être copié automatiquement.', breadcrumb: 'Calculatrices',
      groups: ['Toutes', 'Fondamentaux', 'Identification', 'Composants passifs et circuits', 'Climatisation'],
    },
  };
  const toolTranslations = {
    en: {
      ohm: ['Ohm’s law and power', 'Calculate voltage, current, resistance and power from two known values.'],
      colors: ['Resistor colour bands', 'Interpret four- and five-band resistors, including tolerance and actual range.'],
      smdr: ['SMD resistor codes', 'Decode three-digit, four-digit, decimal-R and EIA-96 resistor markings.'],
      capcode: ['Capacitor codes', 'Decode three-digit capacitor values and their tolerance letter.'],
      equivalent: ['Series and parallel', 'Calculate equivalent resistance or capacitance in series and parallel networks.'],
      divider: ['Resistive divider', 'Calculate loaded and unloaded output, current and resistor dissipation.'],
      rc: ['RC time constant', 'Calculate tau and the time needed to reach common charge percentages.'],
      busdc: ['Rectified DC bus', 'Estimate DC-bus voltage and capacitor ripple after full-wave rectification.'],
      caphealth: ['Capacitor condition', 'Compare measured capacitance with nominal value and tolerance.'],
      ntc: ['NTC Beta calculator', 'Estimate temperature or resistance with the Beta approximation.'],
      windings: ['Winding balance', 'Compare three phase resistances and calculate deviation from the mean.'],
      frequency: ['Frequency, period and RPM', 'Convert frequency to period, pulse-derived speed and synchronous speed.'],
    },
    pt: {
      ohm: ['Lei de Ohm e potência', 'Calcula tensão, corrente, resistência e potência a partir de dois valores conhecidos.'],
      colors: ['Resistências por cores', 'Interpreta resistências de quatro e cinco bandas, tolerância e intervalo real.'],
      smdr: ['Códigos de resistências SMD', 'Descodifica marcações de três e quatro dígitos, R decimal e EIA-96.'],
      capcode: ['Códigos de condensadores', 'Descodifica valores de três dígitos e a letra de tolerância.'],
      equivalent: ['Série e paralelo', 'Calcula resistência ou capacidade equivalente em série e paralelo.'],
      divider: ['Divisor resistivo', 'Calcula saída com e sem carga, corrente e dissipação.'],
      rc: ['Constante de tempo RC', 'Calcula tau e tempos para percentagens de carga habituais.'],
      busdc: ['Bus DC retificado', 'Estima a tensão do bus DC e o ripple do condensador após retificação.'],
      caphealth: ['Estado do condensador', 'Compara a capacidade medida com o valor nominal e a tolerância.'],
      ntc: ['Calculadora NTC por Beta', 'Estima temperatura ou resistência com a aproximação Beta.'],
      windings: ['Equilíbrio de enrolamentos', 'Compara três resistências de fase e calcula o desvio à média.'],
      frequency: ['Frequência, período e RPM', 'Converte frequência em período, velocidade por pulsos e velocidade síncrona.'],
    },
    fr: {
      ohm: ['Loi d’Ohm et puissance', 'Calcule tension, courant, résistance et puissance à partir de deux valeurs connues.'],
      colors: ['Code couleur des résistances', 'Interprète les résistances à quatre et cinq anneaux, tolérance comprise.'],
      smdr: ['Codes des résistances SMD', 'Décode les marquages à trois ou quatre chiffres, R décimal et EIA-96.'],
      capcode: ['Codes des condensateurs', 'Décode les valeurs à trois chiffres et la lettre de tolérance.'],
      equivalent: ['Série et parallèle', 'Calcule la résistance ou capacité équivalente en série et en parallèle.'],
      divider: ['Diviseur résistif', 'Calcule la sortie à vide et en charge, le courant et la dissipation.'],
      rc: ['Constante de temps RC', 'Calcule tau et les durées correspondant aux pourcentages de charge usuels.'],
      busdc: ['Bus DC redressé', 'Estime la tension du bus DC et l’ondulation du condensateur après redressement.'],
      caphealth: ['État d’un condensateur', 'Compare la capacité mesurée à la valeur nominale et à la tolérance.'],
      ntc: ['Calculatrice NTC Beta', 'Estime la température ou la résistance avec l’approximation Beta.'],
      windings: ['Équilibre des bobinages', 'Compare trois résistances de phase et calcule l’écart à la moyenne.'],
      frequency: ['Fréquence, période et tr/min', 'Convertit la fréquence en période et en vitesses par impulsions ou synchrones.'],
    },
  };
  function language() { return window.ST_I18N?.language || 'es'; }
  function ui(key) { return (localeText[language()] || localeText.es)[key]; }
  function translatedTool(tool) {
    const translated = toolTranslations[language()]?.[tool.id];
    return translated ? {...tool, title: translated[0], description: translated[1]} : tool;
  }

  const toolIcons = {
    ohm: 'Ω', colors: '▥', smdr: 'SMD', capcode: 'µF',
    equivalent: 'Σ', divider: '÷', rc: 'τ', busdc: 'DC',
    caphealth: '%', ntc: '°C', windings: '3Φ', frequency: 'Hz'
  };

  const unitFactors = {
    V: 1, mV: 1e-3, kV: 1e3,
    A: 1, mA: 1e-3, uA: 1e-6,
    ohm: 1, kohm: 1e3, Mohm: 1e6,
    F: 1, uF: 1e-6, nF: 1e-9, pF: 1e-12,
    Hz: 1, kHz: 1e3,
    s: 1, ms: 1e-3,
    W: 1, mW: 1e-3
  };

  function n(id) {
    const el = document.getElementById(id);
    return Number(String(el.value).trim().replace(',', '.'));
  }
  function scaled(id, unitId) {
    const raw = n(id);
    const unit = document.getElementById(unitId).value;
    return raw * unitFactors[unit];
  }
  function field(label, id, value = '', type = 'number', attrs = '') {
    return `<div class="field"><label for="${id}">${label}</label><input id="${id}" type="${type}" value="${value}" ${attrs}></div>`;
  }
  function unitField(label, id, value, unitId, units, help = '') {
    return `<div class="field"><label for="${id}">${label}</label><div class="input-group"><input id="${id}" inputmode="decimal" value="${value}"><select id="${unitId}">${units.map(u => `<option value="${u}">${u === 'ohm' ? 'Ω' : u === 'kohm' ? 'kΩ' : u === 'Mohm' ? 'MΩ' : u === 'uA' ? 'µA' : u === 'uF' ? 'µF' : u}</option>`).join('')}</select></div>${help ? `<small>${help}</small>` : ''}</div>`;
  }
  function selectField(label, id, options) {
    return `<div class="field"><label for="${id}">${label}</label><select id="${id}">${options.map(([v,t]) => `<option value="${v}">${t}</option>`).join('')}</select></div>`;
  }
  function actions(example = true) {
    return `<div class="action-row"><button class="primary-button calculate" type="button">${ui('calculate')}</button>${example ? `<button class="example-button load-example" type="button">${ui('example')}</button>` : ''}</div>`;
  }
  function metric(label, value) { return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`; }
  function result(main, metrics, notice = '', severity = '', formula = '') {
    return `<div class="result-main">${main}</div><div class="result-grid">${metrics.join('')}</div>${notice ? `<div class="notice ${severity}">${notice}</div>` : ''}${formula ? `<div class="formula">${formula}</div>` : ''}`;
  }
  function showError(panel, error) {
    panel.innerHTML = `<div class="notice danger"><strong>No se pudo calcular.</strong><br>${error.message || error}</div>`;
  }
  function resistorColor(color) {
    const colors = { negro:'#161616', marron:'#72462d', rojo:'#d53d3d', naranja:'#ef8128', amarillo:'#f2ce3e', verde:'#3a9f61', azul:'#3d67c7', violeta:'#7d4ea3', gris:'#8f959d', blanco:'#f7f5ed', oro:'#c9a227', plata:'#b8bec8', ninguno:'transparent' };
    return colors[color] || 'transparent';
  }

  const tools = [
    {
      id: 'ohm', category: 'Fundamentos', title: 'Ley de Ohm y potencia',
      description: 'Calcula tensión, corriente, resistencia y potencia a partir de dos magnitudes conocidas.',
      body: () => `<div class="form-grid">${selectField('Magnitudes conocidas','ohmMode', [['VI','Tensión + corriente'],['VR','Tensión + resistencia'],['IR','Corriente + resistencia'],['PV','Potencia + tensión'],['PI','Potencia + corriente'],['PR','Potencia + resistencia']])}<div class="field"><label id="ohmLabelA">Tensión</label><div class="input-group"><input id="ohmA" value="230"><select id="ohmUnitA"><option value="V">V</option><option value="mV">mV</option><option value="A">A</option><option value="mA">mA</option><option value="ohm">Ω</option><option value="kohm">kΩ</option><option value="W">W</option></select></div></div><div class="field"><label id="ohmLabelB">Corriente</label><div class="input-group"><input id="ohmB" value="1.2"><select id="ohmUnitB"><option value="A">A</option><option value="mA">mA</option><option value="V">V</option><option value="ohm">Ω</option><option value="kohm">kΩ</option><option value="W">W</option></select></div></div></div>${actions()}`,
      init(panel) {
        const mode = document.getElementById('ohmMode');
        const defs = { VI:[['Tensión','V'],['Corriente','A']], VR:[['Tensión','V'],['Resistencia','ohm']], IR:[['Corriente','A'],['Resistencia','ohm']], PV:[['Potencia','W'],['Tensión','V']], PI:[['Potencia','W'],['Corriente','A']], PR:[['Potencia','W'],['Resistencia','ohm']] };
        const update = () => {
          const d = defs[mode.value];
          document.getElementById('ohmLabelA').textContent = d[0][0]; document.getElementById('ohmUnitA').value = d[0][1];
          document.getElementById('ohmLabelB').textContent = d[1][0]; document.getElementById('ohmUnitB').value = d[1][1];
        };
        mode.addEventListener('change', update); update();
        panel.querySelector('.load-example').onclick = () => { mode.value='VR'; update(); document.getElementById('ohmA').value='325'; document.getElementById('ohmB').value='47'; document.getElementById('ohmUnitB').value='kohm'; };
        panel.querySelector('.calculate').onclick = () => {
          try {
            const r = C.ohmsLaw(mode.value, scaled('ohmA','ohmUnitA'), scaled('ohmB','ohmUnitB'));
            panel.result.innerHTML = result(C.formatEngineering(r.P,'W'), [metric('Tensión',C.formatEngineering(r.V,'V')),metric('Corriente',C.formatEngineering(r.I,'A')),metric('Resistencia',C.formatEngineering(r.R,'Ω')),metric('Potencia',C.formatEngineering(r.P,'W'))], 'Comprueba que la potencia nominal del componente tenga margen suficiente sobre la disipación calculada.', '', 'P = V × I; V = I × R');
          } catch(e) { showError(panel.result,e); }
        };
      }
    },
    {
      id:'colors', category:'Identificación', title:'Resistencias por colores',
      description:'Interpreta resistencias de 4 y 5 bandas, incluyendo tolerancia y rango real.',
      body: () => { const digit = ['negro','marron','rojo','naranja','amarillo','verde','azul','violeta','gris','blanco']; const mult=['plata','oro',...digit]; const tol=['marron','rojo','verde','azul','violeta','gris','oro','plata','ninguno']; const opts = a => a.map(x=>`<option value="${x}">${x[0].toUpperCase()+x.slice(1)}</option>`).join(''); return `<div class="form-grid">${selectField('Número de bandas','bandCount',[['4','4 bandas'],['5','5 bandas']])}<div class="field"><label>Banda 1</label><select id="band1">${opts(digit)}</select></div><div class="field"><label>Banda 2</label><select id="band2">${opts(digit)}</select></div><div class="field" id="band3Wrap"><label>Banda 3</label><select id="band3">${opts(digit)}</select></div><div class="field"><label>Multiplicador</label><select id="bandMult">${opts(mult)}</select></div><div class="field"><label>Tolerancia</label><select id="bandTol">${opts(tol)}</select></div></div><div class="resistor-visual"><div class="resistor-body" id="resistorBody"><i class="band"></i><i class="band"></i><i class="band"></i><i class="band"></i><i class="band"></i></div></div>${actions()}`; },
      init(panel) {
        const controls=['band1','band2','band3','bandMult','bandTol'];
        const updateVisual=()=>{ const count=Number(document.getElementById('bandCount').value); document.getElementById('band3Wrap').style.display=count===5?'grid':'none'; const vals=count===5?[...controls.map(id=>document.getElementById(id).value)]:[document.getElementById('band1').value,document.getElementById('band2').value,document.getElementById('bandMult').value,document.getElementById('bandTol').value]; const bands=[...document.querySelectorAll('#resistorBody .band')]; bands.forEach((b,i)=>{ b.style.display=i<vals.length?'block':'none'; if(vals[i]) b.style.background=resistorColor(vals[i]); }); };
        document.getElementById('bandCount').addEventListener('change',updateVisual); controls.forEach(id=>document.getElementById(id).addEventListener('change',updateVisual));
        panel.querySelector('.load-example').onclick=()=>{ document.getElementById('bandCount').value='4'; document.getElementById('band1').value='marron'; document.getElementById('band2').value='negro'; document.getElementById('bandMult').value='rojo'; document.getElementById('bandTol').value='oro'; updateVisual(); };
        panel.querySelector('.calculate').onclick=()=>{ try{ const count=Number(document.getElementById('bandCount').value); const bands=count===4?[document.getElementById('band1').value,document.getElementById('band2').value,document.getElementById('bandMult').value,document.getElementById('bandTol').value]:[document.getElementById('band1').value,document.getElementById('band2').value,document.getElementById('band3').value,document.getElementById('bandMult').value,document.getElementById('bandTol').value]; const r=C.resistorColors(bands); panel.result.innerHTML=result(`${C.formatEngineering(r.value,'Ω')} ±${r.tolerance}%`,[metric('Valor mínimo',C.formatEngineering(r.min,'Ω')),metric('Valor máximo',C.formatEngineering(r.max,'Ω')),metric('Bandas',bands.join(' · '))],'En resistencias recalentadas o decoloradas, confirma el valor con el esquema o levantando una terminal.'); }catch(e){showError(panel.result,e);} };
        updateVisual();
      }
    },
    {
      id:'smdr', category:'Identificación', title:'Código de resistencias SMD',
      description:'Interpreta códigos de 3 y 4 cifras, notación con R y sistema EIA-96.',
      body:()=>`<div class="form-grid">${field('Código impreso','smdCode','472','text','autocomplete="off"')}<div class="field"><label>Formatos admitidos</label><small>472 · 1001 · 4R7 · R22 · 01C · 000</small></div></div>${actions()}`,
      init(panel){ panel.querySelector('.load-example').onclick=()=>document.getElementById('smdCode').value='01C'; panel.querySelector('.calculate').onclick=()=>{try{const r=C.smdResistorCode(document.getElementById('smdCode').value); panel.result.innerHTML=result(C.formatEngineering(r.value,'Ω'),[metric('Sistema',r.system),metric('Código normalizado',r.normalized)],'El mismo marcado puede tener otra interpretación en componentes que no sean resistencias. Confirma el designador R de la placa.');}catch(e){showError(panel.result,e);}}; }
    },
    {
      id:'capcode', category:'Identificación', title:'Código de condensadores',
      description:'Convierte códigos numéricos de condensadores a pF, nF y µF e interpreta tolerancias comunes.',
      body:()=>`<div class="form-grid">${field('Código impreso','capCode','104K','text')}<div class="field"><label>Ejemplos</label><small>104 = 100 nF · 472J = 4,7 nF ±5 % · 225K = 2,2 µF ±10 %</small></div></div>${actions()}`,
      init(panel){panel.querySelector('.load-example').onclick=()=>document.getElementById('capCode').value='472J'; panel.querySelector('.calculate').onclick=()=>{try{const r=C.capacitorCode(document.getElementById('capCode').value); const tol=r.tolerance===null?'No indicada':typeof r.tolerance==='number'?`±${r.tolerance}%`:r.tolerance; panel.result.innerHTML=result(C.formatEngineering(r.farads,'F'),[metric('Picofaradios',`${r.pf.toLocaleString('es-ES')} pF`),metric('Nanofaradios',`${(r.farads*1e9).toLocaleString('es-ES',{maximumFractionDigits:6})} nF`),metric('Microfaradios',`${(r.farads*1e6).toLocaleString('es-ES',{maximumFractionDigits:6})} µF`),metric('Tolerancia',tol)],'El código no informa necesariamente de la tensión de trabajo ni del dieléctrico.');}catch(e){showError(panel.result,e);}};}
    },
    {
      id:'equivalent', category:'Pasivos', title:'Serie y paralelo',
      description:'Calcula el valor equivalente de resistencias o condensadores introducidos en una lista.',
      body:()=>`<div class="form-grid">${selectField('Componente','eqType',[['R','Resistencias'],['C','Condensadores']])}${selectField('Conexión','eqConn',[['series','Serie'],['parallel','Paralelo']])}<div class="field full"><label for="eqValues">Valores separados por coma o salto de línea</label><textarea id="eqValues" rows="4">1k, 2.2k, 4.7k</textarea><small>Admite sufijos: k, M, m, µ/u, n y p.</small></div></div>${actions()}`,
      init(panel){panel.querySelector('.load-example').onclick=()=>{document.getElementById('eqType').value='C';document.getElementById('eqConn').value='series';document.getElementById('eqValues').value='10u, 22u, 47u';}; panel.querySelector('.calculate').onclick=()=>{try{const type=document.getElementById('eqType').value; const values=document.getElementById('eqValues').value.split(/[\n,;]+/).map(v=>C.parseEngineering(v,type==='R'?'Ω':'F')); if(values.some(v=>!Number.isFinite(v))) throw new Error('Hay uno o más valores no reconocidos.'); const v=C.equivalent(values,type,document.getElementById('eqConn').value); panel.result.innerHTML=result(C.formatEngineering(v,type==='R'?'Ω':'F'),[metric('Cantidad de componentes',String(values.length)),metric('Conexión',document.getElementById('eqConn').selectedOptions[0].text)],type==='C'&&document.getElementById('eqConn').value==='series'?'En condensadores en serie, el reparto de tensión depende también de tolerancias y corrientes de fuga.':'');}catch(e){showError(panel.result,e);}};}
    },
    {
      id:'divider', category:'Circuitos', title:'Divisor resistivo',
      description:'Calcula la salida sin carga y con carga, la corriente del divisor y la disipación de las resistencias.',
      body:()=>`<div class="form-grid three">${unitField('Tensión de entrada','divVin','5','divVinU',['V','mV'])}${unitField('R1 superior','divR1','10','divR1U',['kohm','ohm','Mohm'])}${unitField('R2 inferior','divR2','10','divR2U',['kohm','ohm','Mohm'])}${unitField('Carga opcional','divLoad','','divLoadU',['kohm','ohm','Mohm'],'Déjalo vacío para salida sin carga.')}</div>${actions()}`,
      init(panel){panel.querySelector('.load-example').onclick=()=>{document.getElementById('divVin').value='12';document.getElementById('divR1').value='27';document.getElementById('divR2').value='10';document.getElementById('divLoad').value='100';}; panel.querySelector('.calculate').onclick=()=>{try{const loadText=document.getElementById('divLoad').value.trim(); const load=loadText?scaled('divLoad','divLoadU'):NaN; const r=C.voltageDivider(scaled('divVin','divVinU'),scaled('divR1','divR1U'),scaled('divR2','divR2U'),load); panel.result.innerHTML=result(C.formatEngineering(r.loaded,'V'),[metric('Salida sin carga',C.formatEngineering(r.noLoad,'V')),metric('Salida con carga',C.formatEngineering(r.loaded,'V')),metric('Error por carga',`${r.errorPercent.toLocaleString('es-ES',{maximumFractionDigits:3})} %`),metric('Corriente del divisor',C.formatEngineering(r.dividerCurrent,'A')),metric('Potencia en R1',C.formatEngineering(r.p1,'W')),metric('Potencia en R2',C.formatEngineering(r.p2,'W'))],'Para entradas ADC o redes de feedback, comprueba la impedancia recomendada por el fabricante.','', 'Vout = Vin × R2 / (R1 + R2)');}catch(e){showError(panel.result,e);}};}
    },
    {
      id:'rc', category:'Temporización', title:'Constante de tiempo RC',
      description:'Calcula la constante de tiempo y los tiempos aproximados de carga o descarga.',
      body:()=>`<div class="form-grid">${unitField('Resistencia','rcR','10','rcRU',['kohm','ohm','Mohm'])}${unitField('Capacitancia','rcC','100','rcCU',['uF','nF','pF','F'])}</div>${actions()}`,
      init(panel){panel.querySelector('.load-example').onclick=()=>{document.getElementById('rcR').value='47';document.getElementById('rcC').value='100';};panel.querySelector('.calculate').onclick=()=>{try{const r=C.rcTime(scaled('rcR','rcRU'),scaled('rcC','rcCU'));panel.result.innerHTML=result(C.formatEngineering(r.tau,'s'),[metric('63,2 %',C.formatEngineering(r.t632,'s')),metric('90 %',C.formatEngineering(r.t90,'s')),metric('95 %',C.formatEngineering(r.t95,'s')),metric('99 %',C.formatEngineering(r.t99,'s')),metric('99,9 %',C.formatEngineering(r.t999,'s'))],'Los tiempos son ideales. Las fugas, la carga conectada y la tolerancia del condensador pueden alterar el resultado.','', 'τ = R × C');}catch(e){showError(panel.result,e);}};}
    },
    {
      id:'busdc', category:'Fuentes e inverter', title:'Bus DC tras rectificación',
      description:'Estima el pico rectificado, la tensión de bus, el rizado y la tensión mínima bajo carga.',
      body:()=>`<div class="form-grid three">${unitField('Tensión alterna RMS','busVac','230','busVacU',['V'])}${unitField('Caída por diodo','busDrop','0.9','busDropU',['V'])}${field('Diodos conduciendo','busDiodes','2','number','min="1" step="1"')}${selectField('Frecuencia de red','busHz',[['50','50 Hz'],['60','60 Hz']])}${unitField('Corriente de carga','busI','1','busIU',['A','mA'])}${unitField('Capacitancia total','busC','470','busCU',['uF','nF','F'])}</div>${actions()}`,
      init(panel){panel.querySelector('.load-example').onclick=()=>{document.getElementById('busVac').value='230';document.getElementById('busI').value='1.5';document.getElementById('busC').value='680';};panel.querySelector('.calculate').onclick=()=>{try{const r=C.rectifiedBus(scaled('busVac','busVacU'),scaled('busDrop','busDropU'),n('busDiodes'),n('busHz'),scaled('busI','busIU'),scaled('busC','busCU'));panel.result.innerHTML=result(C.formatEngineering(r.approximateLoaded,'V'),[metric('Pico de la red',C.formatEngineering(r.peak,'V')),metric('Bus sin carga',C.formatEngineering(r.noLoad,'V')),metric('Frecuencia de rizado',C.formatEngineering(r.rippleFrequency,'Hz')),metric('Rizado estimado',C.formatEngineering(r.ripple,'V')),metric('Tensión mínima',C.formatEngineering(r.minimum,'V'))],'Hay tensión letal en el bus DC. Descarga los condensadores y verifica la ausencia de tensión antes de manipular la placa.','danger','Vpk = Vrms × √2; ΔV ≈ I / (2fC)');}catch(e){showError(panel.result,e);}};}
    },
    {
      id:'caphealth', category:'Diagnóstico', title:'Estado de un condensador',
      description:'Compara capacidad nominal y medida, calcula la desviación y evalúa la tolerancia indicada.',
      body:()=>`<div class="form-grid three">${unitField('Capacidad nominal','healthNom','35','healthNomU',['uF','nF','pF'])}${unitField('Capacidad medida','healthMeas','31.8','healthMeasU',['uF','nF','pF'])}${field('Tolerancia permitida (%)','healthTol','5','number','min="0" step="0.1"')}</div>${actions()}`,
      init(panel){panel.querySelector('.load-example').onclick=()=>{document.getElementById('healthNom').value='35';document.getElementById('healthMeas').value='28.5';document.getElementById('healthTol').value='5';};panel.querySelector('.calculate').onclick=()=>{try{const r=C.capacitorHealth(scaled('healthNom','healthNomU'),scaled('healthMeas','healthMeasU'),n('healthTol'));panel.result.innerHTML=result(r.status,[metric('Desviación',`${r.deviation.toLocaleString('es-ES',{maximumFractionDigits:2})} %`),metric('Mínimo admisible',C.formatEngineering(r.min,'F')),metric('Máximo admisible',C.formatEngineering(r.max,'F'))],r.severity==='ok'?'La capacidad está dentro del margen introducido. Aun así, en electrolíticos conviene revisar ESR y corriente de fuga.':'La capacidad está fuera del margen indicado. Confirma la medida fuera de circuito y revisa ESR, fugas y temperatura.',r.severity); }catch(e){showError(panel.result,e);}};}
    },
    {
      id:'ntc', category:'Sensores', title:'Calculadora NTC por Beta',
      description:'Obtiene temperatura desde resistencia o resistencia desde temperatura usando el modelo Beta.',
      body:()=>`<div class="form-grid three">${selectField('Modo','ntcMode',[['temp','Resistencia → temperatura'],['res','Temperatura → resistencia']])}${unitField('R0 a 25 °C','ntcR0','10','ntcR0U',['kohm','ohm'])}${field('Constante Beta (K)','ntcBeta','3950','number','min="1"')}<div class="field" id="ntcRWrap"><label>Resistencia medida</label><div class="input-group"><input id="ntcR" value="6.5"><select id="ntcRU"><option value="kohm">kΩ</option><option value="ohm">Ω</option></select></div></div><div class="field" id="ntcTWrap"><label>Temperatura</label><div class="input-group"><input id="ntcT" value="40"><select><option>°C</option></select></div></div></div>${actions()}`,
      init(panel){const update=()=>{const m=document.getElementById('ntcMode').value;document.getElementById('ntcRWrap').style.display=m==='temp'?'grid':'none';document.getElementById('ntcTWrap').style.display=m==='res'?'grid':'none';};document.getElementById('ntcMode').addEventListener('change',update);panel.querySelector('.load-example').onclick=()=>{document.getElementById('ntcMode').value='temp';document.getElementById('ntcR').value='6.5';document.getElementById('ntcBeta').value='3950';update();};panel.querySelector('.calculate').onclick=()=>{try{const mode=document.getElementById('ntcMode').value;const r0=scaled('ntcR0','ntcR0U');const beta=n('ntcBeta');if(mode==='temp'){const t=C.ntcTemperatureFromResistance(scaled('ntcR','ntcRU'),r0,beta);panel.result.innerHTML=result(`${t.toLocaleString('es-ES',{maximumFractionDigits:2})} °C`,[metric('R medida',C.formatEngineering(scaled('ntcR','ntcRU'),'Ω')),metric('R0',C.formatEngineering(r0,'Ω')),metric('Beta',`${beta} K`)],'El modelo Beta es aproximado. Para diagnóstico por marca y modelo, una tabla oficial del sensor es más precisa.');}else{const rv=C.ntcResistanceFromTemperature(n('ntcT'),r0,beta);panel.result.innerHTML=result(C.formatEngineering(rv,'Ω'),[metric('Temperatura',`${n('ntcT')} °C`),metric('R0',C.formatEngineering(r0,'Ω')),metric('Beta',`${beta} K`)],'Compara el valor con la tabla del fabricante y con una medición de temperatura independiente.');}}catch(e){showError(panel.result,e);}};update();}
    },
    {
      id:'windings', category:'Motores y compresores', title:'Equilibrio de bobinados',
      description:'Compara tres resistencias de fase y calcula la desviación respecto a la media.',
      body:()=>`<div class="form-grid three">${unitField('U-V','w1','1.82','w1U',['ohm'])}${unitField('V-W','w2','1.79','w2U',['ohm'])}${unitField('W-U','w3','1.84','w3U',['ohm'])}</div>${actions()}`,
      init(panel){panel.querySelector('.load-example').onclick=()=>{document.getElementById('w1').value='1.82';document.getElementById('w2').value='1.79';document.getElementById('w3').value='2.08';};panel.querySelector('.calculate').onclick=()=>{try{const vals=[scaled('w1','w1U'),scaled('w2','w2U'),scaled('w3','w3U')];const r=C.windingBalance(vals);panel.result.innerHTML=result(r.status,[metric('Media',C.formatEngineering(r.average,'Ω')),metric('Desviación máxima',`${r.maxDeviation.toLocaleString('es-ES',{maximumFractionDigits:2})} %`),metric('Diferencia máx.-mín.',`${r.spread.toLocaleString('es-ES',{maximumFractionDigits:2})} %`),metric('U-V',`${r.deviations[0].toLocaleString('es-ES',{maximumFractionDigits:2})} %`),metric('V-W',`${r.deviations[1].toLocaleString('es-ES',{maximumFractionDigits:2})} %`),metric('W-U',`${r.deviations[2].toLocaleString('es-ES',{maximumFractionDigits:2})} %`)],'La resistencia de los cables, la temperatura del compresor y la resolución del instrumento pueden alterar mucho medidas tan bajas. Compensa las puntas y confirma aislamiento a masa.',r.severity); }catch(e){showError(panel.result,e);}};}
    },
    {
      id:'frequency', category:'Señales y motores', title:'Frecuencia, periodo y RPM',
      description:'Convierte frecuencia a periodo, velocidad por pulsos y velocidad síncrona por pares de polos.',
      body:()=>`<div class="form-grid three">${unitField('Frecuencia','freq','50','freqU',['Hz','kHz'])}${field('Pulsos por revolución','ppr','2','number','min="0.0001" step="0.1"')}${field('Pares de polos','polePairs','2','number','min="0.5" step="0.5"')}</div>${actions()}`,
      init(panel){panel.querySelector('.load-example').onclick=()=>{document.getElementById('freq').value='60';document.getElementById('ppr').value='6';document.getElementById('polePairs').value='2';};panel.querySelector('.calculate').onclick=()=>{try{const f=scaled('freq','freqU');const r=C.frequencyData(f,n('ppr'),n('polePairs'));panel.result.innerHTML=result(C.formatEngineering(r.period,'s'),[metric('Frecuencia',C.formatEngineering(f,'Hz')),metric('Frecuencia angular',`${r.angular.toLocaleString('es-ES',{maximumFractionDigits:2})} rad/s`),metric('RPM por pulsos',`${r.rpmFromPulses.toLocaleString('es-ES',{maximumFractionDigits:1})} rpm`),metric('RPM síncrona',`${r.synchronousRpm.toLocaleString('es-ES',{maximumFractionDigits:1})} rpm`)],'En motores inverter, la velocidad real puede diferir por deslizamiento, estrategia de control, número de polos y definición de la señal de feedback.','', 'T = 1 / f; rpm = 60f / pulsos por vuelta');}catch(e){showError(panel.result,e);}};}
    }
  ];

  const categoryGroups = [
    ['Todas', () => true],
    ['Fundamentos', t => t.id === 'ohm'],
    ['Identificación', t => ['colors','smdr','capcode'].includes(t.id)],
    ['Pasivos y circuitos', t => ['equivalent','divider','rc','caphealth'].includes(t.id)],
    ['Aire acondicionado', t => ['busdc','ntc','windings','frequency'].includes(t.id)]
  ];

  function groupForTool(tool) {
    const group = categoryGroups.slice(1).find(([, predicate]) => predicate(tool));
    return group ? group[0] : tool.category;
  }

  function groupLabel(groupName) {
    const index = categoryGroups.findIndex(([name]) => name === groupName);
    return index >= 0 ? ui('groups')[index] : groupName;
  }

  function cardMarkup(tool, compact = false) {
    const displayTool = translatedTool(tool);
    const group = groupLabel(groupForTool(tool));
    if (compact) {
      return `<button class="related-card" type="button" data-tool="${tool.id}"><span class="tool-icon">${toolIcons[tool.id] || '∑'}</span><span><strong>${displayTool.title}</strong><small>${group}</small></span></button>`;
    }
    return `<button class="tool-card" type="button" data-tool="${tool.id}" aria-label="${displayTool.title}">
      <span class="tool-card-top"><span class="tool-icon">${toolIcons[tool.id] || '∑'}</span><span class="open-arrow" aria-hidden="true">→</span></span>
      <h3>${displayTool.title}</h3>
      <p>${displayTool.description}</p>
      <span class="tool-category">${group}</span>
    </button>`;
  }

  function renderFilters() {
    categoryFilters.innerHTML = categoryGroups.map(([name]) => `<button class="filter-chip${name === activeCategory ? ' active' : ''}" type="button" data-category="${name}">${groupLabel(name)}</button>`).join('');
    categoryFilters.querySelectorAll('.filter-chip').forEach(button => {
      button.onclick = () => {
        activeCategory = button.dataset.category;
        renderFilters();
        renderCatalog(document.getElementById('toolSearch').value);
      };
    });
  }

  function renderCatalog(filter = '') {
    const text = filter.trim().toLowerCase();
    const category = categoryGroups.find(([name]) => name === activeCategory);
    const predicate = category ? category[1] : () => true;
    const matches = tools.filter(tool => {
      const displayTool = translatedTool(tool);
      return predicate(tool) && `${displayTool.title} ${tool.title} ${tool.category} ${displayTool.description} ${tool.description} ${groupLabel(groupForTool(tool))}`.toLowerCase().includes(text);
    });
    toolGrid.innerHTML = matches.map(tool => cardMarkup(tool)).join('');
    resultCount.textContent = `${matches.length} ${matches.length === 1 ? ui('tool') : ui('tools')}`;
    emptyState.hidden = matches.length !== 0;
    toolGrid.querySelectorAll('[data-tool]').forEach(button => button.onclick = () => navigateToTool(button.dataset.tool));
  }

  function navigateToTool(id) {
    const target = `#/calculadoras/${id}`;
    if (location.hash === target) renderTool(id);
    else location.hash = target;
  }

  function navigateHome() {
    if (location.hash === '#/' || location.hash === '') renderHome();
    else location.hash = '#/';
  }

  function renderHome() {
    homeView.hidden = false;
    toolView.hidden = true;
    printButton.hidden = true;
    document.title = `${ui('breadcrumb')} | Super Técnico`;
    renderFilters();
    renderCatalog(document.getElementById('toolSearch').value);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  function renderRelated(currentTool) {
    const sameGroup = tools.filter(t => t.id !== currentTool.id && groupForTool(t) === groupForTool(currentTool));
    const fallback = tools.filter(t => t.id !== currentTool.id && !sameGroup.includes(t));
    const selected = [...sameGroup, ...fallback].slice(0, 3);
    relatedTools.innerHTML = selected.map(tool => cardMarkup(tool, true)).join('');
    relatedTools.querySelectorAll('[data-tool]').forEach(button => button.onclick = () => navigateToTool(button.dataset.tool));
  }

  function renderTool(id) {
    const tool = tools.find(t => t.id === id);
    if (!tool) {
      navigateHome();
      return;
    }
    homeView.hidden = true;
    toolView.hidden = false;
    printButton.hidden = false;
    host.innerHTML = '';
    const node = template.content.cloneNode(true);
    const displayTool = translatedTool(tool);
    const displayGroup = groupLabel(groupForTool(tool));
    node.querySelector('.category').textContent = displayGroup.toUpperCase();
    node.querySelector('h1').textContent = displayTool.title;
    node.querySelector('.description').textContent = displayTool.description;
    node.querySelector('.calculator-icon').textContent = toolIcons[tool.id] || '∑';
    node.querySelector('.calculator-body').innerHTML = tool.body();
    host.appendChild(node);
    window.ST_I18N?.apply(host);
    document.getElementById('toolBreadcrumb').textContent = `${ui('breadcrumb')} / ${displayGroup} / ${displayTool.title}`;
    const page = host.querySelector('.calculator-page');
    page.result = page.querySelector('.result-panel');
    page.querySelector('.reset-calculator').onclick = () => renderTool(id);
    page.querySelector('.copy-result').onclick = async () => {
      const button = page.querySelector('.copy-result');
      try {
        await navigator.clipboard.writeText(page.result.innerText);
        button.textContent = ui('copied');
        setTimeout(() => button.textContent = ui('copy'), 1200);
      } catch {
        alert(ui('copyError'));
      }
    };
    tool.init(page);
    renderRelated(tool);
    document.title = `${displayTool.title} | Super Técnico`;
    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  function route() {
    const raw = location.hash.replace(/^#/, '');
    const match = raw.match(/^\/calculadoras\/([^/]+)$/);
    const legacyId = raw && !raw.startsWith('/') ? raw : null;
    const id = match ? decodeURIComponent(match[1]) : legacyId;
    if (id && tools.some(tool => tool.id === id)) renderTool(id);
    else renderHome();
  }

  document.getElementById('toolSearch').addEventListener('input', event => renderCatalog(event.target.value));
  document.getElementById('backButton').onclick = navigateHome;
  document.getElementById('brandHome').onclick = navigateHome;
  document.getElementById('themeToggle').onclick = () => {
    document.body.classList.toggle('light');
    try { localStorage.setItem('st-theme', document.body.classList.contains('light') ? 'light' : 'dark'); } catch (_) {}
  };
  printButton.onclick = () => window.print();
  window.addEventListener('hashchange', route);
  document.addEventListener('st:languagechange', route);
  try { if (localStorage.getItem('st-theme') === 'light') document.body.classList.add('light'); } catch (_) {}
  route();
})();
