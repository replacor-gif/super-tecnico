<?php
declare(strict_types=1);

function st_electroia_validation_domains(): array
{
    return [
        'electrical_panels' => 'Cuadros eléctricos',
        'automation' => 'Automatización',
        'hvac_electronics' => 'Electrónica HVAC',
        'embedded_systems' => 'Sistemas embebidos',
    ];
}

function st_electroia_validation_ensure_schema(): void
{
    st_db()->exec(
        "CREATE TABLE IF NOT EXISTS st_electroia_field_validations (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          case_key CHAR(64) NOT NULL,
          document_id VARCHAR(80) NULL,
          title VARCHAR(160) NOT NULL,
          domain VARCHAR(32) NOT NULL,
          outcome ENUM('approved','needs_changes') NOT NULL,
          device ENUM('mobile','tablet','desktop','unknown') NOT NULL DEFAULT 'unknown',
          tester_alias VARCHAR(40) NOT NULL DEFAULT 'Administrador',
          notes TEXT NULL,
          engine_version VARCHAR(40) NULL,
          validation_errors SMALLINT UNSIGNED NOT NULL DEFAULT 0,
          relevant_warnings SMALLINT UNSIGNED NOT NULL DEFAULT 0,
          client_hash CHAR(64) NOT NULL,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uq_electroia_validation_case (case_key),
          KEY idx_electroia_validation_outcome (outcome, updated_at),
          KEY idx_electroia_validation_domain (domain, outcome, updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
    );
}

function st_electroia_validation_summary(): array
{
    st_electroia_validation_ensure_schema();
    $domains = st_electroia_validation_domains();
    $counts = [];
    foreach ($domains as $id => $label) {
        $counts[$id] = ['id' => $id, 'label' => $label, 'approved' => 0, 'needs_changes' => 0];
    }

    foreach (st_db()->query('SELECT domain, outcome, COUNT(*) AS total FROM st_electroia_field_validations GROUP BY domain, outcome')->fetchAll() as $row) {
        $domain = (string) $row['domain'];
        $outcome = (string) $row['outcome'];
        if (isset($counts[$domain]) && in_array($outcome, ['approved', 'needs_changes'], true)) {
            $counts[$domain][$outcome] = (int) $row['total'];
        }
    }

    $totals = st_db()->query(
        "SELECT COUNT(*) AS total,
                SUM(outcome = 'approved') AS approved,
                SUM(outcome = 'needs_changes') AS needs_changes
         FROM st_electroia_field_validations"
    )->fetch() ?: [];
    $latest = st_db()->query(
        "SELECT case_key, document_id, title, domain, outcome, device, tester_alias,
                validation_errors, relevant_warnings, updated_at
         FROM st_electroia_field_validations
         ORDER BY updated_at DESC
         LIMIT 12"
    )->fetchAll();
    $approved = (int) ($totals['approved'] ?? 0);
    $target = 20;

    return [
        'ok' => true,
        'target' => [
            'total' => $target,
            'per_domain' => 5,
            'domains' => array_keys($domains),
            'criterion' => 'Veinte esquemas distintos aprobados, repartidos entre cuatro ámbitos y comprobados en dispositivos reales.',
        ],
        'progress' => [
            'total_records' => (int) ($totals['total'] ?? 0),
            'approved' => $approved,
            'needs_changes' => (int) ($totals['needs_changes'] ?? 0),
            'remaining' => max(0, $target - $approved),
            'percent' => min(100, round(($approved / $target) * 100, 1)),
        ],
        'domains' => array_values($counts),
        'latest' => $latest,
    ];
}

function st_electroia_validation_create(array $body, string $clientHash): array
{
    st_electroia_validation_ensure_schema();
    $caseKey = strtolower(st_text($body, 'case_key', 64, 64));
    if (preg_match('/^[a-f0-9]{64}$/', $caseKey) !== 1) st_json(['ok' => false, 'error' => 'invalid_case_key'], 422);

    $domains = st_electroia_validation_domains();
    $domain = st_text($body, 'domain', 3, 32);
    if (!isset($domains[$domain])) st_json(['ok' => false, 'error' => 'invalid_domain'], 422);
    $outcome = st_text($body, 'outcome', 8, 13);
    if (!in_array($outcome, ['approved', 'needs_changes'], true)) st_json(['ok' => false, 'error' => 'invalid_outcome'], 422);
    $device = st_text($body, 'device', 6, 7);
    if (!in_array($device, ['mobile', 'tablet', 'desktop', 'unknown'], true)) st_json(['ok' => false, 'error' => 'invalid_device'], 422);

    $title = st_text($body, 'title', 1, 160);
    $documentId = st_text($body, 'document_id', 0, 80, false);
    $testerAlias = st_text($body, 'tester_alias', 0, 40, false) ?: 'Administrador';
    $notes = st_text($body, 'notes', 0, 1200, false);
    if ($outcome === 'needs_changes' && mb_strlen($notes) < 6) {
        st_json(['ok' => false, 'error' => 'notes_required_for_changes'], 422);
    }
    $engineVersion = st_text($body, 'engine_version', 0, 40, false);
    $validationErrors = min(999, max(0, (int) ($body['validation_errors'] ?? 0)));
    $relevantWarnings = min(999, max(0, (int) ($body['relevant_warnings'] ?? 0)));
    if ($outcome === 'approved' && $validationErrors > 0) {
        st_json(['ok' => false, 'error' => 'validation_errors_prevent_approval'], 422);
    }

    $statement = st_db()->prepare(
        "INSERT INTO st_electroia_field_validations
          (case_key, document_id, title, domain, outcome, device, tester_alias, notes, engine_version, validation_errors, relevant_warnings, client_hash)
         VALUES (?, NULLIF(?, ''), ?, ?, ?, ?, ?, NULLIF(?, ''), NULLIF(?, ''), ?, ?, ?)
         ON DUPLICATE KEY UPDATE
          document_id = VALUES(document_id), title = VALUES(title), domain = VALUES(domain),
          outcome = VALUES(outcome), device = VALUES(device), tester_alias = VALUES(tester_alias),
          notes = VALUES(notes), engine_version = VALUES(engine_version),
          validation_errors = VALUES(validation_errors), relevant_warnings = VALUES(relevant_warnings),
          client_hash = VALUES(client_hash), updated_at = CURRENT_TIMESTAMP"
    );
    $statement->execute([
        $caseKey, $documentId, $title, $domain, $outcome, $device, $testerAlias, $notes,
        $engineVersion, $validationErrors, $relevantWarnings, $clientHash,
    ]);

    return ['ok' => true, 'saved' => true, 'case_key' => $caseKey, 'summary' => st_electroia_validation_summary()];
}
