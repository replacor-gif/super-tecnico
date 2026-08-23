CREATE TABLE IF NOT EXISTS st_fault_cases (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  board_reference VARCHAR(120) NOT NULL,
  board_reference_normalized VARCHAR(120) NOT NULL,
  brand VARCHAR(80) NULL,
  equipment_type VARCHAR(80) NULL,
  symptom TEXT NOT NULL,
  notes TEXT NULL,
  nickname VARCHAR(40) NOT NULL,
  content_hash CHAR(64) NOT NULL,
  status ENUM('pending','published','rejected') NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TIMESTAMP NULL,
  published_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_fault_content (content_hash),
  KEY idx_fault_reference (board_reference_normalized),
  KEY idx_fault_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_fault_solutions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  fault_case_id BIGINT UNSIGNED NOT NULL,
  solution TEXT NOT NULL,
  nickname VARCHAR(40) NOT NULL,
  status ENUM('pending','published','rejected') NOT NULL DEFAULT 'pending',
  confirmations_count INT UNSIGNED NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TIMESTAMP NULL,
  published_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  KEY idx_solution_case_status (fault_case_id, status),
  CONSTRAINT fk_solution_case FOREIGN KEY (fault_case_id) REFERENCES st_fault_cases(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_fault_confirmations (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  solution_id BIGINT UNSIGNED NOT NULL,
  client_hash CHAR(64) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_solution_client (solution_id, client_hash),
  CONSTRAINT fk_confirmation_solution FOREIGN KEY (solution_id) REFERENCES st_fault_solutions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_proposals (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nickname VARCHAR(40) NOT NULL,
  type ENUM('idea','change','bug','technical') NOT NULL,
  area VARCHAR(100) NOT NULL,
  context VARCHAR(160) NULL,
  title VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  proposed_change TEXT NULL,
  language CHAR(2) NOT NULL DEFAULT 'es',
  source_page VARCHAR(500) NULL,
  content_hash CHAR(64) NOT NULL,
  status ENUM('pending','study','accepted','planned','development','applied','duplicate','discarded') NOT NULL DEFAULT 'pending',
  supports_count INT UNSIGNED NOT NULL DEFAULT 0,
  official_note TEXT NULL,
  is_public TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TIMESTAMP NULL,
  published_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_proposal_content (content_hash),
  KEY idx_proposal_public_status (is_public, status, created_at),
  KEY idx_proposal_area (area)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_proposal_supports (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  proposal_id BIGINT UNSIGNED NOT NULL,
  client_hash CHAR(64) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_proposal_client (proposal_id, client_hash),
  CONSTRAINT fk_support_proposal FOREIGN KEY (proposal_id) REFERENCES st_proposals(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_rate_limits (
  action_key VARCHAR(40) NOT NULL,
  client_hash CHAR(64) NOT NULL,
  window_start DATETIME NOT NULL,
  hits SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  PRIMARY KEY (action_key, client_hash),
  KEY idx_rate_window (window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_moderation_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  entity_type ENUM('fault','solution','proposal') NOT NULL,
  entity_id BIGINT UNSIGNED NOT NULL,
  action_name VARCHAR(40) NOT NULL,
  details_json JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_moderation_entity (entity_type, entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_page_counters (
  page_key VARCHAR(64) NOT NULL,
  views BIGINT UNSIGNED NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (page_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_page_daily (
  page_key VARCHAR(64) NOT NULL,
  view_date DATE NOT NULL,
  views BIGINT UNSIGNED NOT NULL DEFAULT 0,
  unique_visitors BIGINT UNSIGNED NOT NULL DEFAULT 0,
  mobile_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
  tablet_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
  desktop_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
  internal_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
  external_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
  direct_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (page_key, view_date),
  KEY idx_page_daily_date (view_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_page_daily_visitors (
  page_key VARCHAR(64) NOT NULL,
  view_date DATE NOT NULL,
  client_hash CHAR(64) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (page_key, view_date, client_hash),
  KEY idx_daily_visitors_date (view_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_page_ratings (
  page_key VARCHAR(64) NOT NULL,
  likes BIGINT UNSIGNED NOT NULL DEFAULT 0,
  dislikes BIGINT UNSIGNED NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (page_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_page_rating_votes (
  page_key VARCHAR(64) NOT NULL,
  client_hash CHAR(64) NOT NULL,
  vote ENUM('like','dislike') NOT NULL,
  feedback VARCHAR(600) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (page_key, client_hash),
  KEY idx_rating_feedback (vote, updated_at),
  CONSTRAINT fk_rating_page FOREIGN KEY (page_key) REFERENCES st_page_ratings(page_key) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_regulation_search_events (
  request_id CHAR(32) NOT NULL,
  client_hash CHAR(64) NOT NULL,
  client_type ENUM('human','ai','software','unknown') NOT NULL DEFAULT 'unknown',
  query_hash CHAR(64) NOT NULL,
  query_sample VARCHAR(180) NULL,
  document_filter VARCHAR(64) NULL,
  domain_filter VARCHAR(80) NULL,
  result_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  top_document_id VARCHAR(64) NULL,
  match_mode ENUM('exact','all_terms','related','none') NOT NULL DEFAULT 'none',
  latency_ms INT UNSIGNED NOT NULL DEFAULT 0,
  opened_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (request_id),
  KEY idx_regulation_search_date (created_at),
  KEY idx_regulation_search_query (query_hash, created_at),
  KEY idx_regulation_search_client (client_type, created_at),
  KEY idx_regulation_search_document (top_document_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_connector_reviews (
  connector_id VARCHAR(80) NOT NULL,
  review_status ENUM('pending_review','source_identified','reviewed','rejected') NOT NULL DEFAULT 'pending_review',
  confidence DECIMAL(4,3) NOT NULL DEFAULT 0.000,
  reviewer_alias VARCHAR(40) NOT NULL DEFAULT 'Administrador',
  evidence_source_id VARCHAR(80) NULL,
  evidence_locator VARCHAR(180) NULL,
  notes TEXT NULL,
  contacts_checked TINYINT(1) NOT NULL DEFAULT 0,
  orientation_checked TINYINT(1) NOT NULL DEFAULT 0,
  variants_checked TINYINT(1) NOT NULL DEFAULT 0,
  catalog_version VARCHAR(40) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  reviewed_at TIMESTAMP NULL,
  PRIMARY KEY (connector_id),
  KEY idx_connector_review_status (review_status, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_connector_review_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  connector_id VARCHAR(80) NOT NULL,
  review_status VARCHAR(32) NOT NULL,
  reviewer_alias VARCHAR(40) NOT NULL,
  evidence_source_id VARCHAR(80) NULL,
  evidence_locator VARCHAR(180) NULL,
  details_json JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_connector_review_event (connector_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_connector_import_batches (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  original_filename VARCHAR(255) NOT NULL,
  stored_filename VARCHAR(100) NOT NULL,
  sha256 CHAR(64) NOT NULL,
  media_type VARCHAR(100) NOT NULL,
  file_size BIGINT UNSIGNED NOT NULL,
  import_status ENUM('uploaded','needs_extractor','extracted','ready_for_review','merged','rejected') NOT NULL DEFAULT 'uploaded',
  summary VARCHAR(500) NULL,
  extracted_json JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_connector_import_sha (sha256),
  KEY idx_connector_import_status (import_status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_connector_usage_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  action_name ENUM('search','get','resolve') NOT NULL,
  client_hash CHAR(64) NOT NULL,
  client_type ENUM('human','ai','software','unknown') NOT NULL DEFAULT 'unknown',
  query_hash CHAR(64) NULL,
  query_sample VARCHAR(120) NULL,
  connector_id VARCHAR(80) NULL,
  result_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  latency_ms INT UNSIGNED NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_connector_usage_date (created_at),
  KEY idx_connector_usage_connector (connector_id, created_at),
  KEY idx_connector_usage_client (client_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS st_private_backlog (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  item_type ENUM('idea','improvement','bug','content') NOT NULL DEFAULT 'idea',
  area VARCHAR(100) NOT NULL,
  title VARCHAR(140) NOT NULL,
  details TEXT NULL,
  priority ENUM('normal','high','urgent') NOT NULL DEFAULT 'normal',
  status ENUM('pending','in_progress','done','archived') NOT NULL DEFAULT 'pending',
  author_alias VARCHAR(40) NOT NULL DEFAULT 'Administrador',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  KEY idx_private_backlog_status_priority (status, priority, updated_at),
  KEY idx_private_backlog_area (area, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
