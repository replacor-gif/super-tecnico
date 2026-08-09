const ElectroDiagram = (function () {
  "use strict";

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

  function relayCoil(x, y, ref, value) {
    return `
      <g data-symbol-id="SYM-0119" aria-label="${esc(ref)} ${esc(value)}">
        <path class="wire power" d="M${x} ${y + 40}h34M${x + 156} ${y + 40}h34"/>
        <rect class="symbol" x="${x + 34}" y="${y + 10}" width="122" height="60" rx="29"/>
        <text class="coil-letter" x="${x + 95}" y="${y + 48}">K</text>
        <text class="ref" x="${x + 95}" y="${y - 8}">${esc(ref)} · BOBINA</text>
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
    const isolated = Boolean(values.isolated);
    const relayVoltage = `${values.relay_voltage} V`;
    const signalVoltage = `${values.signal_voltage} V`;
    const sourceEnd = isolated ? 240 : 140;
    const resistorStart = isolated ? 240 : 140;
    const resistorWidth = isolated ? 100 : 200;

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
        <path class="wire signal" d="M140 315H${sourceEnd}"/>
        ${isolated ? `
          <rect class="pending" x="150" y="275" width="90" height="80" rx="9" data-symbol-id="SYM-0097"/>
          <text class="ref" x="195" y="307">U1</text>
          <text class="note" x="195" y="330" text-anchor="middle">Aislamiento</text>
          <text class="pin" x="158" y="371">POR ELEGIR</text>
        ` : ""}
        ${resistorHorizontal(resistorStart, 315, resistorWidth, "R1", resistorGate.value || "100 Ω")}
        <path class="wire signal" d="M${resistorStart + resistorWidth} 315h10v15"/>
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

  function render(design) {
    const topology = design?.circuit_model?.topology || "";
    if (topology === "low_side_relay_driver" || topology === "isolated_low_side_relay_driver") {
      return renderRelayDriver(design);
    }
    throw new Error("El modelo eléctrico todavía no tiene un formato de diagrama compatible");
  }

  return { render };
})();
