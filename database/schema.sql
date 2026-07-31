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
