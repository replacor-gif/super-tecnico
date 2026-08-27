import { compileDiagramSpec } from "../electroia-tool-server/src/compiler.mjs";
import { symbolSearchRank } from "../electroia-tool-server/src/symbol-ranking.mjs";

export function compileBrowserDiagramSpec(spec) {
  if (!globalThis.ElectroDiagramCore) throw new Error("El núcleo gráfico de ElectroIA no está disponible.");
  return compileDiagramSpec(spec, {
    registry: globalThis.ElectroDiagramCore.getRegistry(),
    rankSymbol: symbolSearchRank,
    render: globalThis.ElectroDiagramCore.render,
  });
}
