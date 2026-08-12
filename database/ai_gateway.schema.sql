-- Diseño de persistencia para el futuro gateway de IA.
-- No se ejecuta durante la compilación estática ni activa acceso remoto.
-- Los secretos se generan fuera de la base y solo se guarda su hash con pepper de aplicación.

CREATE TABLE IF NOT EXISTS st_ai_clients (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  public_id CHAR(26) NOT NULL,
  display_name VARCHAR(160) NOT NULL,
  customer_kind ENUM('developer','company','ai_platform','internal') NOT NULL,
  plan_code VARCHAR(40) NOT NULL DEFAULT 'private_preview',
  status ENUM('pending','active','suspended','closed') NOT NULL DEFAULT 'pending',
  monthly_unit_limit BIGINT UNSIGNED NULL,
  allowed_tools_json JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ai_client_public_id (public_id),
  KEY idx_ai_client_status (status, plan_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_ai_credentials (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  client_id BIGINT UNSIGNED NOT NULL,
  key_prefix VARCHAR(16) NOT NULL,
  secret_hash CHAR(64) NOT NULL,
  status ENUM('active','revoked','expired') NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NULL,
  last_used_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ai_credential_prefix (key_prefix),
  KEY idx_ai_credential_client_status (client_id, status),
  CONSTRAINT fk_ai_credential_client FOREIGN KEY (client_id) REFERENCES st_ai_clients(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_ai_usage_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  request_id CHAR(36) NOT NULL,
  client_id BIGINT UNSIGNED NOT NULL,
  credential_id BIGINT UNSIGNED NULL,
  tool_name VARCHAR(80) NOT NULL,
  tool_version VARCHAR(40) NOT NULL,
  result_level ENUM('coverage','basic','diagnostic','field','diagram') NOT NULL,
  billable_units INT UNSIGNED NOT NULL DEFAULT 0,
  response_status ENUM('success','not_found','insufficient_context','rejected','error') NOT NULL,
  coverage_found TINYINT(1) NULL,
  cache_status ENUM('hit','miss','not_applicable') NOT NULL DEFAULT 'not_applicable',
  request_bytes INT UNSIGNED NOT NULL DEFAULT 0,
  response_bytes INT UNSIGNED NOT NULL DEFAULT 0,
  input_tokens INT UNSIGNED NULL,
  output_tokens INT UNSIGNED NULL,
  source_documents_used SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  estimated_documents_avoided SMALLINT UNSIGNED NULL,
  estimated_searches_avoided SMALLINT UNSIGNED NULL,
  estimated_turns_avoided SMALLINT UNSIGNED NULL,
  internal_compute_cost_microunits BIGINT UNSIGNED NULL,
  charged_cost_microunits BIGINT UNSIGNED NULL,
  estimated_without_tool_cost_microunits BIGINT UNSIGNED NULL,
  latency_ms INT UNSIGNED NOT NULL DEFAULT 0,
  knowledge_version VARCHAR(40) NULL,
  source_version_set_hash CHAR(64) NULL,
  normalized_input_hash CHAR(64) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ai_usage_request (request_id),
  KEY idx_ai_usage_client_date (client_id, created_at),
  KEY idx_ai_usage_tool_date (tool_name, created_at),
  CONSTRAINT fk_ai_usage_client FOREIGN KEY (client_id) REFERENCES st_ai_clients(id) ON DELETE RESTRICT,
  CONSTRAINT fk_ai_usage_credential FOREIGN KEY (credential_id) REFERENCES st_ai_credentials(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_ai_usage_daily (
  client_id BIGINT UNSIGNED NOT NULL,
  usage_date DATE NOT NULL,
  tool_name VARCHAR(80) NOT NULL,
  result_level ENUM('coverage','basic','diagnostic','field','diagram') NOT NULL,
  requests BIGINT UNSIGNED NOT NULL DEFAULT 0,
  successful_requests BIGINT UNSIGNED NOT NULL DEFAULT 0,
  cache_hits BIGINT UNSIGNED NOT NULL DEFAULT 0,
  billable_units BIGINT UNSIGNED NOT NULL DEFAULT 0,
  response_bytes BIGINT UNSIGNED NOT NULL DEFAULT 0,
  input_tokens BIGINT UNSIGNED NOT NULL DEFAULT 0,
  output_tokens BIGINT UNSIGNED NOT NULL DEFAULT 0,
  estimated_documents_avoided BIGINT UNSIGNED NOT NULL DEFAULT 0,
  estimated_searches_avoided BIGINT UNSIGNED NOT NULL DEFAULT 0,
  estimated_turns_avoided BIGINT UNSIGNED NOT NULL DEFAULT 0,
  internal_compute_cost_microunits BIGINT UNSIGNED NOT NULL DEFAULT 0,
  charged_cost_microunits BIGINT UNSIGNED NOT NULL DEFAULT 0,
  estimated_without_tool_cost_microunits BIGINT UNSIGNED NOT NULL DEFAULT 0,
  latency_ms_total BIGINT UNSIGNED NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (client_id, usage_date, tool_name, result_level),
  KEY idx_ai_usage_daily_date (usage_date),
  CONSTRAINT fk_ai_usage_daily_client FOREIGN KEY (client_id) REFERENCES st_ai_clients(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_ai_security_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  client_id BIGINT UNSIGNED NULL,
  event_type ENUM('auth_failure','rate_limited','enumeration_suspected','policy_violation','credential_revoked') NOT NULL,
  action_taken VARCHAR(120) NOT NULL,
  details_json JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_ai_security_client_date (client_id, created_at),
  KEY idx_ai_security_type_date (event_type, created_at),
  CONSTRAINT fk_ai_security_client FOREIGN KEY (client_id) REFERENCES st_ai_clients(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_ai_benchmark_runs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  run_id CHAR(26) NOT NULL,
  benchmark_version VARCHAR(40) NOT NULL,
  comparison_mode ENUM('independent_search','super_tecnico') NOT NULL,
  cases_total INT UNSIGNED NOT NULL,
  cases_resolved INT UNSIGNED NOT NULL DEFAULT 0,
  unsupported_claims INT UNSIGNED NOT NULL DEFAULT 0,
  documents_opened INT UNSIGNED NULL,
  searches_performed INT UNSIGNED NULL,
  interaction_turns INT UNSIGNED NULL,
  retries INT UNSIGNED NULL,
  input_tokens BIGINT UNSIGNED NULL,
  output_tokens BIGINT UNSIGNED NULL,
  wall_time_ms BIGINT UNSIGNED NULL,
  estimated_cost_microunits BIGINT UNSIGNED NULL,
  result_json JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ai_benchmark_run (run_id),
  KEY idx_ai_benchmark_version (benchmark_version, comparison_mode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
