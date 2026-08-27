function folded(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function searchFolded(value) {
  return folded(value).replace(/[^a-z0-9]+/g, " ").trim();
}

const IGNORED_TERMS = new Set([
  "a", "al", "de", "del", "la", "las", "el", "los", "y", "o", "con", "para", "por", "en", "un", "una", "tipo", "simbolo", "componente",
]);

const TERM_ALIASES = Object.freeze({
  rele: ["relay"], relay: ["rele"],
  pulsador: ["pushbutton", "boton"], boton: ["pulsador", "pushbutton"],
  abierto: ["no", "normally open"], cerrado: ["nc", "normally closed"],
  automata: ["plc"], plc: ["automata"],
  variador: ["vfd", "variable frequency drive"], vfd: ["variador", "variable frequency drive"],
  tierra: ["pe", "ground"], masa: ["gnd", "ground"],
  alimentacion: ["power", "supply"], sensor: ["transductor"],
});

function terms(value) {
  const normalized = searchFolded(value);
  return [...new Set(normalized.split(/\s+/).filter((term) => term.length >= 2 && !IGNORED_TERMS.has(term)))];
}

function appears(haystack, compactHaystack, term) {
  return [term, ...(TERM_ALIASES[term] || [])].some((variant) => {
    const normalized = searchFolded(variant);
    return haystack.includes(normalized)
      || (normalized.length <= 5 && compactHaystack.includes(normalized.replace(/\s+/g, "")));
  });
}

export function symbolSearchRank(symbol, rawQuery) {
  const query = searchFolded(rawQuery);
  const queryTerms = terms(query);
  const fields = {
    id: searchFolded(symbol.id),
    name: searchFolded(symbol.name),
    aliases: searchFolded(symbol.aliases),
    keywords: searchFolded(symbol.keywords),
    classification: searchFolded(`${symbol.kind} ${symbol.designator} ${symbol.category} ${symbol.subcategory}`),
    detail: searchFolded(`${symbol.description} ${symbol.interpretation} ${symbol.catalog_drawing_type}`),
  };
  const haystack = Object.values(fields).join(" ");
  const compact = haystack.replace(/\s+/g, "");
  const matchedTerms = queryTerms.filter((term) => appears(haystack, compact, term));
  if (!matchedTerms.length
    || (queryTerms.length <= 2 && matchedTerms.length !== queryTerms.length)
    || (queryTerms.length > 2 && matchedTerms.length / queryTerms.length < 0.6)) return null;
  let score = matchedTerms.length * 24 + (matchedTerms.length / Math.max(1, queryTerms.length)) * 80;
  if (fields.id === query) score += 800;
  if (fields.name === query) score += 500;
  if (fields.name.includes(query)) score += 220;
  if (fields.aliases.includes(query)) score += 150;
  matchedTerms.forEach((term) => {
    if (appears(fields.name, fields.name.replace(/\s+/g, ""), term)) score += 45;
    else if (appears(fields.aliases, fields.aliases.replace(/\s+/g, ""), term)) score += 32;
    else if (appears(fields.keywords, fields.keywords.replace(/\s+/g, ""), term)) score += 20;
    else if (appears(fields.classification, fields.classification.replace(/\s+/g, ""), term)) score += 12;
  });
  return { score, matchedTerms, coverage: matchedTerms.length / Math.max(1, queryTerms.length) };
}
