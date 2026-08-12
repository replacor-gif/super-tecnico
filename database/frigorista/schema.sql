PRAGMA foreign_keys = ON;

CREATE TABLE catalog_versions (
  id INTEGER PRIMARY KEY,
  dataset_version TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK(status IN ('draft','review','published','retired')),
  content_hash TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  published_at TEXT
);

CREATE TABLE property_sources (
  id INTEGER PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL,
  title TEXT NOT NULL,
  organization TEXT,
  url TEXT,
  version TEXT,
  publication_date TEXT,
  accessed_at TEXT,
  license_notes TEXT,
  trust_level TEXT NOT NULL DEFAULT 'reference'
);

CREATE TABLE thermodynamic_backends (
  id INTEGER PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  revision TEXT,
  source_id INTEGER NOT NULL REFERENCES property_sources(id),
  enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
  UNIQUE(name, version, revision)
);

CREATE TABLE refrigerants (
  id INTEGER PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  designation TEXT NOT NULL UNIQUE,
  canonical_name TEXT,
  family TEXT,
  mixture_type TEXT NOT NULL CHECK(mixture_type IN ('pure','azeotropic','near_azeotropic','zeotropic','other')),
  catalog_status TEXT NOT NULL DEFAULT 'current',
  selectable INTEGER NOT NULL DEFAULT 1 CHECK(selectable IN (0,1)),
  excluded_reason TEXT,
  backend_id INTEGER REFERENCES thermodynamic_backends(id),
  backend_fluid_key TEXT,
  thermodynamic_support_status TEXT NOT NULL DEFAULT 'unverified' CHECK(thermodynamic_support_status IN ('unverified','verified','unsupported','blocked')),
  notes TEXT,
  record_version TEXT NOT NULL,
  catalog_version_id INTEGER NOT NULL REFERENCES catalog_versions(id),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK(selectable = 1 OR excluded_reason IS NOT NULL)
);

CREATE TABLE refrigerant_aliases (
  id INTEGER PRIMARY KEY,
  refrigerant_id INTEGER NOT NULL REFERENCES refrigerants(id) ON DELETE CASCADE,
  alias TEXT NOT NULL,
  alias_type TEXT NOT NULL DEFAULT 'search',
  manufacturer TEXT,
  source_id INTEGER REFERENCES property_sources(id),
  UNIQUE(refrigerant_id, alias)
);

CREATE TABLE refrigerant_components (
  id INTEGER PRIMARY KEY,
  parent_refrigerant_id INTEGER NOT NULL REFERENCES refrigerants(id) ON DELETE CASCADE,
  component_designation TEXT NOT NULL,
  mass_fraction REAL CHECK(mass_fraction IS NULL OR (mass_fraction >= 0 AND mass_fraction <= 1)),
  source_id INTEGER NOT NULL REFERENCES property_sources(id),
  UNIQUE(parent_refrigerant_id, component_designation)
);

CREATE TABLE applications (
  id INTEGER PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT
);

CREATE TABLE refrigerant_applications (
  refrigerant_id INTEGER NOT NULL REFERENCES refrigerants(id) ON DELETE CASCADE,
  application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  suitability TEXT NOT NULL DEFAULT 'identification_only' CHECK(suitability IN ('common','specific','legacy','identification_only','not_recommended')),
  temperature_level TEXT,
  source_id INTEGER NOT NULL REFERENCES property_sources(id),
  notes TEXT,
  PRIMARY KEY (refrigerant_id, application_id)
);

CREATE TABLE safety_metadata (
  id INTEGER PRIMARY KEY,
  refrigerant_id INTEGER NOT NULL REFERENCES refrigerants(id) ON DELETE CASCADE,
  safety_class TEXT NOT NULL,
  lower_flammability_limit_kg_m3 REAL CHECK(lower_flammability_limit_kg_m3 IS NULL OR lower_flammability_limit_kg_m3 >= 0),
  burning_velocity_cm_s REAL CHECK(burning_velocity_cm_s IS NULL OR burning_velocity_cm_s >= 0),
  practical_limit_kg_m3 REAL CHECK(practical_limit_kg_m3 IS NULL OR practical_limit_kg_m3 >= 0),
  source_id INTEGER NOT NULL REFERENCES property_sources(id),
  source_version TEXT NOT NULL,
  valid_from TEXT NOT NULL,
  valid_to TEXT,
  verified_at TEXT NOT NULL,
  UNIQUE(refrigerant_id, source_id, source_version, valid_from)
);

CREATE TABLE refrigerant_regulatory_statuses (
  id INTEGER PRIMARY KEY,
  refrigerant_id INTEGER NOT NULL REFERENCES refrigerants(id) ON DELETE CASCADE,
  jurisdiction_code TEXT NOT NULL,
  application_code TEXT,
  equipment_scope TEXT,
  action_type TEXT NOT NULL CHECK(action_type IN ('placing_on_market','installation','service','recharge','recovery','training','other')),
  status TEXT NOT NULL CHECK(status IN ('allowed','restricted','prohibited','phase_down','unknown')),
  effective_from TEXT NOT NULL,
  effective_to TEXT,
  source_id INTEGER NOT NULL REFERENCES property_sources(id),
  notes TEXT,
  checked_at TEXT NOT NULL,
  UNIQUE(refrigerant_id, jurisdiction_code, application_code, equipment_scope, action_type, effective_from, source_id)
);

CREATE TABLE pt_points (
  id INTEGER PRIMARY KEY,
  refrigerant_id INTEGER NOT NULL REFERENCES refrigerants(id) ON DELETE CASCADE,
  pressure_pa_abs REAL NOT NULL CHECK(pressure_pa_abs > 0),
  bubble_temperature_k REAL,
  dew_temperature_k REAL,
  backend_id INTEGER REFERENCES thermodynamic_backends(id),
  source_id INTEGER NOT NULL REFERENCES property_sources(id),
  source_version TEXT NOT NULL,
  uncertainty_k REAL CHECK(uncertainty_k IS NULL OR uncertainty_k >= 0),
  CHECK(bubble_temperature_k IS NOT NULL OR dew_temperature_k IS NOT NULL),
  UNIQUE(refrigerant_id, pressure_pa_abs, source_id, source_version)
);

CREATE TABLE system_sessions (
  id TEXT PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  refrigerant_id INTEGER NOT NULL REFERENCES refrigerants(id),
  goal TEXT NOT NULL DEFAULT 'pt_only' CHECK(goal IN ('pt_only','superheat','subcooling','basic_system_study','deep_analysis')),
  system_type TEXT,
  operating_mode TEXT,
  expansion_device TEXT,
  compressor_control TEXT,
  brand TEXT,
  model TEXT,
  atmospheric_pressure_pa REAL NOT NULL DEFAULT 101325 CHECK(atmospheric_pressure_pa > 0),
  steady_state TEXT NOT NULL DEFAULT 'unknown' CHECK(steady_state IN ('yes','no','unknown')),
  engine_version TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE measurements (
  id INTEGER PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES system_sessions(id) ON DELETE CASCADE,
  measurement_type TEXT NOT NULL,
  location_code TEXT,
  value_si REAL,
  si_unit TEXT,
  display_value REAL,
  display_unit TEXT,
  pressure_reference TEXT CHECK(pressure_reference IS NULL OR pressure_reference IN ('gauge','absolute')),
  quality TEXT NOT NULL CHECK(quality IN ('measured','machine_read','observed_estimate','unknown')),
  uncertainty_si REAL CHECK(uncertainty_si IS NULL OR uncertainty_si >= 0),
  instrument TEXT,
  last_calibration_at TEXT,
  measured_at TEXT,
  notes TEXT,
  CHECK((quality = 'unknown' AND value_si IS NULL) OR (quality <> 'unknown' AND value_si IS NOT NULL))
);

CREATE TABLE derived_values (
  id INTEGER PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES system_sessions(id) ON DELETE CASCADE,
  value_type TEXT NOT NULL,
  value_si REAL,
  si_unit TEXT,
  method TEXT NOT NULL,
  engine_version TEXT NOT NULL,
  input_measurement_ids_json TEXT NOT NULL CHECK(json_valid(input_measurement_ids_json)),
  details_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(details_json)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE diagnostic_rule_sets (
  id INTEGER PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  version TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('draft','review','active','retired')),
  source_id INTEGER REFERENCES property_sources(id),
  changelog TEXT,
  activated_at TEXT
);

CREATE TABLE diagnostic_rules (
  id INTEGER PRIMARY KEY,
  rule_set_id INTEGER NOT NULL REFERENCES diagnostic_rule_sets(id) ON DELETE CASCADE,
  rule_code TEXT NOT NULL,
  hypothesis_code TEXT NOT NULL,
  required_inputs_json TEXT NOT NULL CHECK(json_valid(required_inputs_json)),
  condition_json TEXT NOT NULL CHECK(json_valid(condition_json)),
  contraindication_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(contraindication_json)),
  explanation_template TEXT NOT NULL,
  weight REAL NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
  UNIQUE(rule_set_id, rule_code)
);

CREATE TABLE diagnostic_results (
  id INTEGER PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES system_sessions(id) ON DELETE CASCADE,
  rule_set_id INTEGER REFERENCES diagnostic_rule_sets(id),
  status TEXT NOT NULL CHECK(status IN ('inconclusive','partial','complete','rejected')),
  confidence_level TEXT NOT NULL CHECK(confidence_level IN ('none','low','medium','high')),
  evidence_json TEXT NOT NULL CHECK(json_valid(evidence_json)),
  contradictions_json TEXT NOT NULL CHECK(json_valid(contradictions_json)),
  unknowns_json TEXT NOT NULL CHECK(json_valid(unknowns_json)),
  next_measurement_json TEXT NOT NULL CHECK(json_valid(next_measurement_json)),
  warnings_json TEXT NOT NULL CHECK(json_valid(warnings_json)),
  engine_version TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE confirmed_outcomes (
  id INTEGER PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES system_sessions(id) ON DELETE CASCADE,
  confirmed_cause TEXT,
  repair_performed TEXT,
  verification_result TEXT,
  moderation_status TEXT NOT NULL DEFAULT 'pending' CHECK(moderation_status IN ('pending','reviewed','rejected')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refrigerants_designation ON refrigerants(designation);
CREATE INDEX idx_aliases_alias ON refrigerant_aliases(alias);
CREATE INDEX idx_pt_refrigerant_pressure ON pt_points(refrigerant_id, pressure_pa_abs);
CREATE INDEX idx_regulatory_lookup ON refrigerant_regulatory_statuses(refrigerant_id, jurisdiction_code, action_type, effective_from);
CREATE INDEX idx_measurements_session_type ON measurements(session_id, measurement_type);
CREATE INDEX idx_derived_session_type ON derived_values(session_id, value_type);
