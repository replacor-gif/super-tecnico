const ElectroDiagram = (function () {
  "use strict";

  const DiagramCore = typeof globalThis !== "undefined" && globalThis.ElectroDiagramCore
    ? globalThis.ElectroDiagramCore
    : (typeof require === "function" ? require("./diagram-core.js") : null);

  function esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function part(model, ref) {
    return (model.parts || []).find((item) => item.ref === ref) || {};
  }

  function resistorHorizontal(x, y, width, ref, value) {
    const lead = 28;
    const bodyWidth = width - lead * 2;
    return `
      <g data-symbol-id="SYM-0023" aria-label="${esc(ref)} ${esc(value)}">
        <path class="wire signal" d="M${x} ${y}h${lead}"/>
        <rect class="symbol" x="${x + lead}" y="${y - 14}" width="${bodyWidth}" height="28" rx="2"/>
        <path class="wire signal" d="M${x + width - lead} ${y}h${lead}"/>
        <text class="ref" x="${x + width / 2}" y="${y - 26}">${esc(ref)}</text>
        <text class="value" x="${x + width / 2}" y="${y + 38}">${esc(value)}</text>
      </g>`;
  }

  function resistorVertical(x, y, height, ref, value) {
    const lead = 28;
    const bodyHeight = height - lead * 2;
    return `
      <g data-symbol-id="SYM-0023" aria-label="${esc(ref)} ${esc(value)}">
        <path class="wire" d="M${x} ${y}v${lead}"/>
        <rect class="symbol" x="${x - 14}" y="${y + lead}" width="28" height="${bodyHeight}" rx="2"/>
        <path class="wire" d="M${x} ${y + height - lead}v${lead}"/>
        <text class="ref left" x="${x - 24}" y="${y + height / 2 - 5}">${esc(ref)}</text>
        <text class="value left" x="${x - 24}" y="${y + height / 2 + 16}">${esc(value)}</text>
      </g>`;
  }

  function relayCoil(x, y, ref, value, showRef = true) {
    return `
      <g data-symbol-id="SYM-0119" aria-label="${esc(ref)} ${esc(value)}">
        <path class="wire power" d="M${x} ${y + 40}h34M${x + 156} ${y + 40}h34"/>
        <rect class="symbol" x="${x + 34}" y="${y + 10}" width="122" height="60" rx="29"/>
        <text class="coil-letter" x="${x + 95}" y="${y + 48}">K</text>
        ${showRef ? `<text class="ref" x="${x + 95}" y="${y - 8}">${esc(ref)} · BOBINA</text>` : ""}
      </g>`;
  }

  function diodeHorizontal(x, y, ref, value) {
    return `
      <g data-symbol-id="SYM-0057" aria-label="${esc(ref)} ${esc(value)}">
        <path class="wire power" d="M${x} ${y}h55M${x + 135} ${y}h55"/>
        <path class="symbol" d="M${x + 132} ${y - 28}L${x + 72} ${y}l60 28z"/>
        <path class="symbol" d="M${x + 66} ${y - 30}v60"/>
        <text class="ref" x="${x + 95}" y="${y - 43}">${esc(ref)} · PROTECCIÓN</text>
        <text class="value" x="${x + 95}" y="${y + 49}">${esc(value)}</text>
        <text class="pin" x="${x + 49}" y="${y + 23}">K</text>
        <text class="pin" x="${x + 141}" y="${y + 23}">A</text>
      </g>`;
  }

  function mosfetN(x, y, ref, value) {
    return `
      <g data-symbol-id="SYM-0080" aria-label="${esc(ref)} ${esc(value)}">
        <path class="wire signal" d="M${x} ${y + 60}h42"/>
        <path class="symbol" d="M${x + 47} ${y + 20}v80M${x + 72} ${y + 25}v70"/>
        <path class="wire" d="M${x + 72} ${y + 30}l88 -20h18M${x + 72} ${y + 90}l88 20h18"/>
        <path class="accent" d="M${x + 65} ${y + 60}H${x + 45}m8 -7l-8 7l8 7"/>
        <text class="pin" x="${x - 2}" y="${y + 51}">G</text>
        <text class="pin" x="${x + 151}" y="${y + 4}">D</text>
        <text class="pin" x="${x + 151}" y="${y + 129}">S</text>
        <text class="ref left" x="${x + 190}" y="${y + 49}">${esc(ref)}</text>
        <text class="value left" x="${x + 190}" y="${y + 72}">${esc(value)}</text>
      </g>`;
  }

  function contactNo(x, y, ref) {
    return `
      <g data-symbol-id="SYM-0120" aria-label="${esc(ref)} contacto normalmente abierto">
        <path class="wire load" d="M${x} ${y}h42M${x + 148} ${y}h42"/>
        <circle class="symbol" cx="${x + 48}" cy="${y}" r="6"/>
        <circle class="symbol" cx="${x + 142}" cy="${y}" r="6"/>
        <path class="symbol" d="M${x + 54} ${y - 5}l80 -42"/>
        <text class="ref" x="${x + 95}" y="${y - 61}">${esc(ref)} · CONTACTO NO</text>
        <text class="pin" x="${x + 35}" y="${y + 29}">COM</text>
        <text class="pin" x="${x + 132}" y="${y + 29}">NO</text>
      </g>`;
  }

  function renderRelayDriver(design) {
    const model = design.circuit_model || {};
    const values = design.values || {};
    const relay = part(model, "K1");
    const diode = part(model, "D1");
    const mosfet = part(model, "Q1");
    const resistorGate = part(model, "R1");
    const resistorPull = part(model, "R2");
    const load = part(model, "LOAD1");
    const relayVoltage = `${values.relay_voltage} V`;
    const signalVoltage = `${values.signal_voltage} V`;

    return `
      <svg class="electrical-diagram" viewBox="0 0 620 710" role="img"
        data-model-version="${esc(model.schema_version || "")}" data-topology="${esc(model.topology || "")}"
        aria-label="Esquema eléctrico de un relé de ${esc(relayVoltage)} controlado con ${esc(signalVoltage)}">
        <style>
          .wire{fill:none;stroke:#26302c;stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round}.wire.signal{stroke:#648d1c}.wire.power{stroke:#d96735}.wire.load{stroke:#59635f}.symbol{fill:#fffefa;stroke:#26302c;stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round}.accent{fill:none;stroke:#648d1c;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}.node{fill:#26302c}.terminal{fill:#fffefa;stroke:#26302c;stroke-width:2.8}.section{font:800 12px Inter,Arial,sans-serif;letter-spacing:1.7px;fill:#6b756f}.ref{font:800 15px Inter,Arial,sans-serif;text-anchor:middle;fill:#28312d}.ref.left{text-anchor:start}.value{font:600 14px Inter,Arial,sans-serif;text-anchor:middle;fill:#5d6863}.value.left{text-anchor:start}.pin{font:700 11px ui-monospace,monospace;fill:#7a847f}.label{font:750 16px Inter,Arial,sans-serif;fill:#28312d}.note{font:500 13px Inter,Arial,sans-serif;fill:#68726d}.coil-letter{font:800 22px Inter,Arial,sans-serif;text-anchor:middle;fill:#28312d}.block{fill:#f9f7ef;stroke:#aab2ad;stroke-width:2}.pending{fill:#fff6e8;stroke:#c77a35;stroke-width:2;stroke-dasharray:6 5}.divider{stroke:#ccd1cd;stroke-width:1.5;stroke-dasharray:5 7}
        </style>
        <text class="section" x="24" y="30">CONTROL Y BOBINA</text>
        <line class="divider" x1="24" y1="505" x2="596" y2="505"/>

        <circle class="terminal" cx="70" cy="120" r="7"/>
        <text class="label" x="38" y="94">+${esc(relayVoltage)}</text>
        <text class="note" x="38" y="143">Fuente del relé</text>
        <path class="wire power" d="M77 120H320"/>
        ${relayCoil(320, 80, "K1", relay.value || `Bobina ${relayVoltage}`)}
        <path class="wire power" d="M510 120v90M320 120v90"/>
        ${diodeHorizontal(320, 210, "D1", diode.value || "Diodo de rueda libre")}
        <path class="wire power" d="M510 210v70"/>
        <circle class="node" cx="510" cy="210" r="5"/>
        <circle class="node" cx="320" cy="210" r="5"/>

        <rect class="block" x="20" y="280" width="120" height="70" rx="10"/>
        <text class="label" x="80" y="310" text-anchor="middle">CONTROL</text>
        <text class="note" x="80" y="333" text-anchor="middle">Salida ${esc(signalVoltage)}</text>
        <circle class="node" cx="140" cy="315" r="5"/>
        ${resistorHorizontal(140, 315, 200, "R1", resistorGate.value || "100 Ω")}
        <path class="wire signal" d="M340 315h10v15"/>
        <circle class="node" cx="350" cy="330" r="5"/>
        ${resistorVertical(335, 330, 130, "R2", resistorPull.value || "100 kΩ")}
        <path class="wire" d="M335 330h15M335 460h175"/>
        ${mosfetN(350, 270, "Q1", mosfet.value || "MOSFET N lógico")}
        <path class="wire power" d="M510 280v-70M510 380v80"/>
        <circle class="node" cx="510" cy="460" r="5"/>

        <circle class="terminal" cx="70" cy="460" r="7"/>
        <path class="wire" d="M77 460H335"/>
        <text class="label" x="38" y="438">0 V</text>
        <text class="note" x="38" y="484">Masa común</text>
        <path class="wire" d="M470 460v20m-24 0h48m-38 10h28m-19 10h10"/>

        <text class="section" x="24" y="535">CONTACTOS PARA LA CARGA · CIRCUITO SEPARADO</text>
        <rect class="block" x="20" y="553" width="576" height="132" rx="12"/>
        <circle class="terminal" cx="58" cy="625" r="7"/>
        <text class="note" x="40" y="662">Entrada</text>
        <path class="wire load" d="M65 625h55"/>
        ${contactNo(120, 625, "K1.1")}
        <path class="wire load" d="M310 625h42"/>
        <rect class="symbol" x="352" y="585" width="174" height="80" rx="9"/>
        <text class="label" x="439" y="615" text-anchor="middle">CARGA</text>
        <text class="note" x="439" y="640" text-anchor="middle">${esc(String(load.value || "Equipo a controlar").slice(0, 28))}</text>
        <path class="wire load" d="M526 625h30"/>
        <circle class="terminal" cx="563" cy="625" r="7"/>
        <text class="note" x="538" y="662">Retorno</text>
      </svg>`;
  }

  function renderIsolatedRelayDriver(design) {
    const model = design.circuit_model || {};
    const values = design.values || {};
    const relay = part(model, "K1");
    const diode = part(model, "D1");
    const mosfet = part(model, "Q1");
    const resistorGate = part(model, "R1");
    const resistorPull = part(model, "R2");
    const resistorInput = part(model, "R3");
    const optocoupler = part(model, "U1");
    const load = part(model, "LOAD1");
    const relayVoltage = `${values.relay_voltage} V`;
    const signalVoltage = `${values.signal_voltage} V`;

    return `
      <svg class="electrical-diagram" viewBox="0 0 620 930" role="img"
        data-model-version="${esc(model.schema_version || "")}" data-topology="${esc(model.topology || "")}"
        aria-label="Esquema eléctrico aislado de un relé de ${esc(relayVoltage)} controlado con ${esc(signalVoltage)}">
        <style>
          .wire{fill:none;stroke:#26302c;stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round}.wire.signal{stroke:#648d1c}.wire.power{stroke:#d96735}.wire.load{stroke:#59635f}.symbol{fill:#fffefa;stroke:#26302c;stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round}.accent{fill:none;stroke:#648d1c;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}.node{fill:#26302c}.terminal{fill:#fffefa;stroke:#26302c;stroke-width:2.8}.section{font:800 12px Inter,Arial,sans-serif;letter-spacing:1.7px;fill:#6b756f}.ref{font:800 15px Inter,Arial,sans-serif;text-anchor:middle;fill:#28312d}.ref.left{text-anchor:start}.value{font:600 14px Inter,Arial,sans-serif;text-anchor:middle;fill:#5d6863}.value.left{text-anchor:start}.pin{font:700 11px ui-monospace,monospace;fill:#7a847f}.label{font:750 16px Inter,Arial,sans-serif;fill:#28312d}.note{font:500 13px Inter,Arial,sans-serif;fill:#68726d}.coil-letter{font:800 22px Inter,Arial,sans-serif;text-anchor:middle;fill:#28312d}.block{fill:#fffefa;stroke:#aab2ad;stroke-width:2}.control-zone{fill:#f4f8eb;stroke:#b8ca91;stroke-width:2}.relay-zone{fill:#fff7ef;stroke:#e3b89d;stroke-width:2}.barrier{fill:#edf0ee;stroke:#a7afab;stroke-width:1.5;stroke-dasharray:7 6}.divider{stroke:#ccd1cd;stroke-width:1.5;stroke-dasharray:5 7}
        </style>

        <rect class="control-zone" x="20" y="18" width="580" height="212" rx="14"/>
        <text class="section" x="38" y="47">LADO DE CONTROL · ${esc(signalVoltage)}</text>
        <rect class="block" x="35" y="92" width="105" height="68" rx="10"/>
        <text class="label" x="87" y="120" text-anchor="middle">CONTROL</text>
        <text class="note" x="87" y="144" text-anchor="middle">Salida ${esc(signalVoltage)}</text>
        <circle class="node" cx="140" cy="128" r="5"/>
        ${resistorHorizontal(140, 128, 150, "R3", resistorInput.value || values.isolation_input_resistor || "820 Ω")}

        <rect class="block" x="308" y="67" width="237" height="124" rx="12" data-symbol-id="SYM-0097"/>
        <text class="ref" x="426" y="58">U1 · ${esc(optocoupler.value || "PC817")}</text>
        <path class="wire signal" d="M290 128h38M446 128h57v46"/>
        <path class="symbol" d="M402 104L348 128l54 24zM414 102v52"/>
        <path class="accent" d="M380 92l18 -18m-4 1l4 -1l-1 5M397 101l18 -18m-4 1l4 -1l-1 5"/>
        <text class="pin" x="326" y="118">A</text><text class="pin" x="423" y="118">K</text>
        <text class="note" x="426" y="178" text-anchor="middle">LED de entrada</text>
        <path class="wire" d="M503 174v12"/>
        <path class="wire" d="M503 186v10m-24 0h48m-38 10h28m-19 10h10"/>
        <text class="note" x="438" y="215">0 V CONTROL</text>

        <rect class="barrier" x="20" y="245" width="580" height="54" rx="9"/>
        <text class="section" x="310" y="266" text-anchor="middle">BARRERA DE AISLAMIENTO</text>
        <text class="note" x="310" y="287" text-anchor="middle">NO UNIR LAS DOS MASAS</text>

        <rect class="relay-zone" x="20" y="315" width="580" height="382" rx="14"/>
        <text class="section" x="38" y="343">LADO DEL RELÉ · ${esc(relayVoltage)}</text>

        <rect class="block" x="35" y="370" width="155" height="132" rx="11" data-symbol-id="SYM-0097"/>
        <text class="ref" x="112" y="362">U1 · SALIDA</text>
        <path class="symbol" d="M94 405v62M103 421l47 -31M103 447l47 30"/>
        <path class="accent" d="M58 417l25 12m-9 -12l9 12l-13 2M58 444l25 12m-9 -12l9 12l-13 2"/>
        <path class="wire power" d="M150 390v-20"/>
        <path class="wire signal" d="M150 477v-32h40"/>
        <text class="pin" x="157" y="398">C</text><text class="pin" x="157" y="470">E</text>
        <text class="note" x="112" y="493" text-anchor="middle">Fototransistor</text>

        <circle class="terminal" cx="230" cy="370" r="7"/>
        <text class="label" x="206" y="393">+${esc(relayVoltage)}</text>
        <path class="wire power" d="M150 370h180"/>
        <text class="ref" x="425" y="343">K1 · BOBINA</text>
        ${relayCoil(330, 330, "K1", relay.value || `Bobina ${relayVoltage}`, false)}
        <path class="wire power" d="M330 370v100M520 370v140"/>
        ${diodeHorizontal(330, 470, "D1", diode.value || "Diodo de rueda libre")}
        <circle class="node" cx="330" cy="470" r="5"/>
        <circle class="node" cx="520" cy="470" r="5"/>

        ${resistorHorizontal(190, 445, 160, "R1", resistorGate.value || "100 Ω")}
        <path class="wire signal" d="M350 445v115h10"/>
        <circle class="node" cx="360" cy="560" r="5"/>
        ${resistorVertical(345, 560, 90, "R2", resistorPull.value || "100 kΩ")}
        <path class="wire" d="M345 560h15M345 650h193"/>
        ${mosfetN(360, 500, "Q1", mosfet.value || "MOSFET N lógico")}
        <path class="wire power" d="M520 510h18"/>
        <path class="wire" d="M538 610v40"/>
        <circle class="node" cx="538" cy="650" r="5"/>
        <path class="wire" d="M500 650v13m-24 0h48m-38 10h28m-19 10h10"/>
        <text class="note" x="420" y="684">0 V RELÉ</text>

        <line class="divider" x1="24" y1="720" x2="596" y2="720"/>
        <text class="section" x="24" y="750">CONTACTOS PARA LA CARGA · CIRCUITO SEPARADO</text>
        <rect class="block" x="20" y="768" width="576" height="140" rx="12"/>
        <circle class="terminal" cx="58" cy="840" r="7"/>
        <text class="note" x="40" y="879">Entrada</text>
        <path class="wire load" d="M65 840h55"/>
        ${contactNo(120, 840, "K1.1")}
        <path class="wire load" d="M310 840h42"/>
        <rect class="symbol" x="352" y="800" width="174" height="80" rx="9"/>
        <text class="label" x="439" y="830" text-anchor="middle">CARGA</text>
        <text class="note" x="439" y="855" text-anchor="middle">${esc(String(load.value || "Equipo a controlar").slice(0, 28))}</text>
        <path class="wire load" d="M526 840h30"/>
        <circle class="terminal" cx="563" cy="840" r="7"/>
        <text class="note" x="538" y="879">Retorno</text>
      </svg>`;
  }

  function renderTemperatureFanController(design) {
    const model = design.circuit_model || {};
    const values = design.values || {};
    const thermistor = part(model, "TH1");
    const comparator = part(model, "U1");
    const mosfet = part(model, "Q1");
    const fan = part(model, "FAN1");
    const diode = part(model, "D1");
    const feedback = part(model, "R5");
    const fanVoltage = `${values.fan_voltage} V`;
    const turnOn = `${values.turn_on_temperature_c} °C`;
    const turnOff = `${values.turn_off_temperature_c} °C`;

    return `
      <svg class="electrical-diagram fan-temperature-diagram" viewBox="0 0 900 560" role="img"
        data-model-version="${esc(model.schema_version || "")}" data-topology="${esc(model.topology || "")}"
        aria-label="Esquema de un ventilador de ${esc(fanVoltage)} controlado por temperatura">
        <style>
          .wire{fill:none;stroke:#26302c;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}.wire.signal{stroke:#648d1c}.wire.power{stroke:#d96735}.symbol{fill:#fffefa;stroke:#26302c;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}.node{fill:#26302c}.section{font:800 12px Inter,Arial,sans-serif;letter-spacing:1.6px;fill:#6b756f}.ref{font:800 14px Inter,Arial,sans-serif;text-anchor:middle;fill:#28312d}.value{font:600 13px Inter,Arial,sans-serif;text-anchor:middle;fill:#5d6863}.label{font:800 16px Inter,Arial,sans-serif;fill:#28312d}.note{font:600 12px Inter,Arial,sans-serif;fill:#68726d}.pin{font:800 11px ui-monospace,monospace;fill:#7a847f}.zone{fill:#fffefa;stroke:#d1d6d2;stroke-width:2}.sensor-zone{fill:#f4f8eb;stroke:#b8ca91}.decision-zone{fill:#f7f7f3}.power-zone{fill:#fff7ef;stroke:#e3b89d}.rail-label{font:800 14px Inter,Arial,sans-serif;fill:#d05f31}.status-box{fill:#edf3df;stroke:#9fb96a;stroke-width:2}.fan-blade{fill:#dbe7c1;stroke:#26302c;stroke-width:2}
        </style>

        <text class="label" x="42" y="35">+${esc(fanVoltage)} DC</text>
        <path class="wire power" d="M42 58H858"/>
        <path class="wire" d="M42 510H858"/>
        <text class="label" x="42" y="540">0 V</text>

        <rect class="zone sensor-zone" x="25" y="82" width="280" height="390" rx="16"/>
        <text class="section" x="45" y="112">1 · MEDIR TEMPERATURA</text>
        <g data-symbol-id="SYM-0023" aria-label="R1 10 kΩ">
          <path class="wire power" d="M125 58v65"/>
          <rect class="symbol" x="105" y="123" width="40" height="92" rx="4"/>
          <path class="wire signal" d="M125 215v45"/>
          <text class="ref" x="125" y="238">R1</text>
          <text class="value" x="82" y="282">10 kΩ</text>
        </g>
        <circle class="node" cx="125" cy="260" r="5"/>
        <g data-symbol-id="SYM-0031" aria-label="TH1 ${esc(thermistor.value || "NTC 10 kΩ")}">
          <path class="wire signal" d="M125 260v64"/>
          <rect class="symbol" x="107" y="324" width="36" height="72" rx="3"/>
          <path class="wire signal" d="M94 334l62 58m-4 -16l4 16l-16 -3"/>
          <path class="wire" d="M125 396v114"/>
          <text class="ref" x="125" y="418">TH1</text>
          <text class="value" x="125" y="438">${esc(thermistor.value || "NTC 10 kΩ")}</text>
        </g>
        <path class="wire signal" d="M125 260h55V130h150v112h52"/>
        <path d="M235 130h20" style="fill:none;stroke:#f4f8eb;stroke-width:10"/>
        <path class="wire signal" d="M235 130q10 -15 20 0"/>
        <text class="note" x="46" y="466">TH1 baja su resistencia al calentarse</text>

        <g data-symbol-id="SYM-0023" aria-label="RV1 ajuste de temperatura">
          <path class="wire power" d="M245 58v92"/>
          <rect class="symbol" x="226" y="150" width="38" height="170" rx="4"/>
          <path class="wire" d="M245 320v190"/>
          <path class="wire signal" d="M264 275h118"/>
          <path class="wire signal" d="M280 254l-16 21l20 7"/>
          <text class="ref" x="245" y="345">RV1</text>
          <text class="value" x="245" y="365">AJUSTE ${esc(turnOn)}</text>
        </g>

        <rect class="zone decision-zone" x="325" y="82" width="260" height="390" rx="16"/>
        <text class="section" x="345" y="112">2 · DECIDIR SIN OSCILAR</text>
        <g data-symbol-id="SYM-0184" aria-label="U1 ${esc(comparator.value || "LM393")}">
          <path class="symbol" d="M382 182v156l160 -78z"/>
          <text class="pin" x="388" y="232">−</text>
          <text class="pin" x="388" y="294">+</text>
          <text class="ref" x="462" y="220">U1 · ${esc(comparator.value || "LM393")}</text>
          <text class="value" x="462" y="245">COMPARADOR</text>
        </g>
        <path class="wire signal" d="M542 260h48"/>
        <circle class="node" cx="570" cy="260" r="5"/>
        <g data-symbol-id="SYM-0023" aria-label="R2 pull-up 10 kΩ">
          <path class="wire power" d="M570 58v32"/>
          <rect class="symbol" x="554" y="90" width="32" height="70" rx="3"/>
          <path class="wire signal" d="M570 160v100"/>
          <text class="ref" x="526" y="181">R2</text>
          <text class="value" x="522" y="202">10 kΩ</text>
        </g>
        <g data-symbol-id="SYM-0023" aria-label="R5 ${esc(feedback.value || values.feedback_resistance || "470 kΩ")}">
          <path class="wire signal" d="M570 260v90h-60"/>
          <rect class="symbol" x="430" y="336" width="80" height="28" rx="3"/>
          <path class="wire signal" d="M430 350h-48v-75"/>
          <text class="ref" x="470" y="329">R5</text>
        </g>
        <rect class="status-box" x="360" y="365" width="190" height="72" rx="10"/>
        <text class="label" x="455" y="394" text-anchor="middle">ENCIENDE ${esc(turnOn)}</text>
        <text class="note" x="455" y="418" text-anchor="middle">APAGA CERCA DE ${esc(turnOff)}</text>
        <text class="note" x="455" y="458" text-anchor="middle">R5 ${esc(feedback.value || values.feedback_resistance || "470 kΩ")} evita arranques repetidos</text>

        <rect class="zone power-zone" x="605" y="82" width="270" height="390" rx="16"/>
        <text class="section" x="625" y="112">3 · MOVER EL VENTILADOR</text>
        <g data-symbol-id="SYM-0035" aria-label="C1 100 nF">
          <path class="wire power" d="M635 58v82"/>
          <path class="symbol" d="M615 140h40M615 154h40"/>
          <path class="wire" d="M635 154v34m-22 0h44m-34 10h24m-17 10h10"/>
          <text class="note" x="610" y="225">C1 · 100 nF</text>
        </g>
        <g data-symbol-id="SYM-0156" aria-label="FAN1 ${esc(fan.value || fanVoltage)}">
          <path class="wire power" d="M745 58v72"/>
          <circle class="symbol" cx="745" cy="190" r="58"/>
          <circle class="node" cx="745" cy="190" r="7"/>
          <path class="fan-blade" d="M745 183c8 -42 50 -32 42 -3c-5 18 -25 20 -42 10z"/>
          <path class="fan-blade" d="M752 190c42 8 32 50 3 42c-18 -5 -20 -25 -10 -42z"/>
          <path class="fan-blade" d="M745 197c-8 42 -50 32 -42 3c5 -18 25 -20 42 -10z"/>
          <text class="ref" x="745" y="272">FAN1 · ${esc(fan.value || fanVoltage)}</text>
        </g>
        <path class="wire power" d="M745 248v72"/>
        <g data-symbol-id="SYM-0080" aria-label="Q1 ${esc(mosfet.value || "MOSFET N")}">
          <rect class="symbol" x="710" y="320" width="70" height="96" rx="8"/>
          <text class="ref" x="745" y="354">Q1</text>
          <text class="value" x="745" y="378">MOSFET N</text>
          <text class="pin" x="690" y="375">G</text><text class="pin" x="748" y="315">D</text><text class="pin" x="748" y="436">S</text>
          <path class="wire" d="M745 416v94"/>
        </g>
        <g data-symbol-id="SYM-0023" aria-label="R3 100 Ω">
          <path class="wire signal" d="M570 260v108h40"/>
          <rect class="symbol" x="610" y="354" width="64" height="28" rx="3"/>
          <path class="wire signal" d="M674 368h36"/>
          <text class="ref" x="642" y="342">R3</text>
          <text class="value" x="642" y="404">100 Ω</text>
        </g>
        <g data-symbol-id="SYM-0023" aria-label="R4 100 kΩ">
          <path class="wire" d="M690 368v24"/>
          <rect class="symbol" x="675" y="392" width="30" height="58" rx="3"/>
          <path class="wire" d="M690 450v60"/>
          <text class="note" x="620" y="470">R4 · 100 kΩ</text>
        </g>
        <g data-symbol-id="SYM-0057" aria-label="D1 ${esc(diode.value || "Diodo de protección")}">
          <path class="wire power" d="M835 58v92M835 230v90H745"/>
          <path class="symbol" d="M813 155h44l-22 42zM811 205h48"/>
          <text class="ref" x="835" y="248">D1</text>
          <text class="note" x="817" y="137">BANDA +</text>
        </g>
      </svg>`;
  }

  function renderTemperatureFanControllerOnGrid(design) {
    if (!DiagramCore) throw new Error("El núcleo gráfico normalizado no está disponible");
    const model = design.circuit_model || {};
    const values = design.values || {};
    const parts = new Map((model.parts || []).map((item) => [item.ref, item]));
    const positions = {
      PS1: { x: 2, y: 10, symbol_id: "SYM-0018", rotation: 0, label_position: "left" },
      R1: { x: 8, y: 5, symbol_id: "SYM-0023", rotation: 90, label_position: "left" },
      TH1: { x: 8, y: 11, symbol_id: "SYM-0031", rotation: 90, label_position: "right" },
      RV1: { x: 16, y: 8, symbol_id: "SYM-0026", rotation: 0, label_position: "left" },
      U1: { x: 26, y: 8, symbol_id: "SYM-0184", rotation: 0, label_position: "inside" },
      R2: { x: 32, y: 5, symbol_id: "SYM-0023", rotation: 90, label_position: "right" },
      R5: { x: 27, y: 15, symbol_id: "SYM-0023", rotation: 0, label_position: "below" },
      R3: { x: 37, y: 13, symbol_id: "SYM-0023", rotation: 0, label_position: "above" },
      R4: { x: 40, y: 16, symbol_id: "SYM-0023", rotation: 90, label_position: "right" },
      Q1: { x: 44, y: 13, symbol_id: "SYM-0080", rotation: 0, label_position: "right" },
      FAN1: { x: 44, y: 5, symbol_id: "SYM-0156", rotation: 0, label_position: "left" },
      D1: { x: 51, y: 5, symbol_id: "SYM-0057", rotation: 270, label_position: "right" },
      C1: { x: 58, y: 5, symbol_id: "SYM-0035", rotation: 90, label_position: "right" },
    };
    const components = Object.entries(positions).map(([ref, layout]) => {
      const item = parts.get(ref) || {};
      return {
        ref,
        symbol_id: layout.symbol_id,
        value: item.value || "",
        position: { x: layout.x, y: layout.y },
        rotation: layout.rotation,
        label_position: layout.label_position,
      };
    });
    const allowedRefs = new Set(components.map((item) => item.ref));
    const nets = (model.nets || []).map((net) => ({
      id: net.id,
      label: net.id === "VIN" ? `+${values.fan_voltage} V DC` : net.id === "GND" ? "0 V" : net.id,
      role: net.id === "VIN" ? "power" : net.id === "GND" ? "ground" : "signal",
      show_label: ["VIN", "GND", "TEMP_SENSE", "TEMP_REF"].includes(net.id),
      label_position: net.id === "TEMP_SENSE" ? { x: 9, y: 8 } : net.id === "TEMP_REF" ? { x: 18, y: 8 } : undefined,
      connections: (net.connections || []).filter((connection) => {
        const separator = connection.lastIndexOf(".");
        return separator > 0 && allowedRefs.has(connection.slice(0, separator));
      }),
    })).filter((net) => net.connections.length > 0);
    const document = {
      schema_version: "1.0",
      document_kind: "circuit_diagram",
      standard_profile: "IEC_EXPERIMENTAL",
      title: `Control de ventilador ${values.fan_voltage} V por temperatura`,
      document_id: "ELECTROIA-CASE-002",
      revision: "A",
      grid: { pitch_mil: 50, show: true },
      layout: { direction: "left_to_right", single_canvas: true },
      components,
      nets,
    };
    const result = DiagramCore.render(document);
    return result.svg.replace(
      '<svg class="electrical-diagram',
      `<svg data-model-version="${esc(model.schema_version || "")}" data-topology="${esc(model.topology || "")}" class="electrical-diagram`
    );
  }

  function renderRelayDriverOnGrid(design) {
    if (!DiagramCore) throw new Error("El núcleo gráfico normalizado no está disponible");
    const model = design.circuit_model || {};
    const values = design.values || {};
    const isolated = model.topology === "isolated_low_side_relay_driver";
    const parts = new Map((model.parts || []).map((item) => [item.ref, item]));
    const common = isolated ? {
      PORT1: { x: 2, y: 12, symbol_id: "ST-CONTROL-PORT", rotation: 0, label_position: "below", value: `Control ${values.signal_voltage} V` },
      R3: { x: 9, y: 10, symbol_id: "SYM-0023", rotation: 0, label_position: "above" },
      U1: { x: 16, y: 12, symbol_id: "SYM-0097", rotation: 0, label_position: "inside" },
      R1: { x: 25, y: 14, symbol_id: "SYM-0023", rotation: 0, label_position: "above" },
      R2: { x: 30, y: 19, symbol_id: "SYM-0023", rotation: 90, label_position: "right" },
      Q1: { x: 34, y: 15, symbol_id: "SYM-0080", rotation: 0, label_position: "right" },
      K1: { x: 34, y: 5, symbol_id: "SYM-0119", rotation: 90, label_position: "left" },
      D1: { x: 40, y: 5, symbol_id: "SYM-0057", rotation: 270, label_position: "right" },
      PS1: { x: 52, y: 15, symbol_id: "SYM-0018", rotation: 0, label_position: "right" },
      PORT2: { x: 26, y: 29, symbol_id: "ST-LOAD-PORT", rotation: 0, label_position: "below", value: "Circuito de carga" },
      "K1.1": { x: 34, y: 28, symbol_id: "SYM-0120", rotation: 0, label_position: "above" },
      LOAD1: { x: 43, y: 28, symbol_id: "ST-GENERIC-2P", rotation: 90, label_position: "right" },
    } : {
      PORT1: { x: 2, y: 10, symbol_id: "ST-CONTROL-PORT", rotation: 0, label_position: "below", value: `Control ${values.signal_voltage} V` },
      R1: { x: 10, y: 10, symbol_id: "SYM-0023", rotation: 0, label_position: "above" },
      R2: { x: 15, y: 16, symbol_id: "SYM-0023", rotation: 90, label_position: "right" },
      Q1: { x: 20, y: 12, symbol_id: "SYM-0080", rotation: 0, label_position: "right" },
      K1: { x: 20, y: 4, symbol_id: "SYM-0119", rotation: 90, label_position: "left" },
      D1: { x: 26, y: 4, symbol_id: "SYM-0057", rotation: 270, label_position: "right" },
      PS1: { x: 40, y: 12, symbol_id: "SYM-0018", rotation: 0, label_position: "right" },
      PORT2: { x: 12, y: 25, symbol_id: "ST-LOAD-PORT", rotation: 0, label_position: "below", value: "Circuito de carga" },
      "K1.1": { x: 20, y: 24, symbol_id: "SYM-0120", rotation: 0, label_position: "above" },
      LOAD1: { x: 29, y: 24, symbol_id: "ST-GENERIC-2P", rotation: 90, label_position: "right" },
    };
    const components = Object.entries(common).map(([ref, layout]) => ({
      ref,
      symbol_id: layout.symbol_id,
      value: layout.value || parts.get(ref)?.value || "",
      position: { x: layout.x, y: layout.y },
      rotation: layout.rotation,
      label_position: layout.label_position,
    }));
    const allowedRefs = new Set(components.map((item) => item.ref));
    const nets = (model.nets || []).map((net) => {
      const connections = (net.connections || []).filter((connection) => {
        const separator = connection.lastIndexOf(".");
        return separator > 0 && allowedRefs.has(connection.slice(0, separator));
      });
      if (!isolated && net.id === "GND_RELAY" && !connections.includes("PORT1.GND")) connections.push("PORT1.GND");
      return {
        id: net.id,
        label: net.label || net.id,
        role: net.id === "VRELAY_PLUS" ? "power" : net.id.startsWith("GND_") ? "ground" : "signal",
        show_label: ["CTRL_OUT", "VRELAY_PLUS", "GND_RELAY", "GND_CONTROL", "LOAD_COM"].includes(net.id),
        connections,
      };
    }).filter((net) => net.connections.length > 0);
    const document = {
      schema_version: "1.0",
      document_kind: "circuit_diagram",
      standard_profile: "IEC_EXPERIMENTAL",
      title: `Control de relé ${values.relay_voltage} V${isolated ? " con aislamiento" : ""}`,
      document_id: isolated ? "ELECTROIA-CASE-001-ISO" : "ELECTROIA-CASE-001",
      revision: "A",
      notes: isolated ? ["DOMINIOS AISLADOS: NO UNIR GND_CONTROL Y GND_RELAY"] : [],
      grid: { pitch_mil: 50, show: true },
      layout: { direction: "left_to_right", single_canvas: true },
      components,
      nets,
      relationships: [{
        from: "K1",
        to: "K1.1",
        kind: "mechanical",
        via: isolated ? [{ x: 37, y: 5 }, { x: 37, y: 28 }] : [{ x: 23, y: 4 }, { x: 23, y: 24 }],
      }],
    };
    const result = DiagramCore.render(document);
    return result.svg.replace(
      '<svg class="electrical-diagram',
      `<svg data-model-version="${esc(model.schema_version || "")}" data-topology="${esc(model.topology || "")}" class="electrical-diagram`
    );
  }

  function render(design) {
    const topology = design?.circuit_model?.topology || "";
    if (topology === "low_side_relay_driver") return renderRelayDriverOnGrid(design);
    if (topology === "isolated_low_side_relay_driver") return renderRelayDriverOnGrid(design);
    if (topology === "thermostatic_dc_fan_controller") return renderTemperatureFanControllerOnGrid(design);
    throw new Error("El modelo eléctrico todavía no tiene un formato de diagrama compatible");
  }

  return { render };
})();

if (typeof globalThis !== "undefined") globalThis.ElectroDiagram = ElectroDiagram;
if (typeof module !== "undefined" && module.exports) module.exports = ElectroDiagram;
