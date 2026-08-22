<?php
declare(strict_types=1);

const ST_CONNECTOR_SERVICE_VERSION = '1.0.0-beta.1';

function st_connectors_catalog(): array
{
    static $catalog = null;
    if (is_array($catalog)) return $catalog;
    $path = dirname(__DIR__) . '/data/connectors/catalog.json';
    $raw = @file_get_contents($path);
    $catalog = json_decode($raw ?: '{}', true);
    if (!is_array($catalog) || !isset($catalog['records']) || !is_array($catalog['records'])) {
        throw new RuntimeException('connector_catalog_unavailable');
    }
    return $catalog;
}

function st_connectors_fold(string $value): string
{
    $value = mb_strtolower(trim($value), 'UTF-8');
    $ascii = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value);
    return preg_replace('/[^a-z0-9]+/', ' ', $ascii === false ? $value : strtolower($ascii)) ?? '';
}

function st_connectors_find(string $id): ?array
{
    foreach (st_connectors_catalog()['records'] as $record) {
        if (hash_equals((string) $record['id'], $id)) return $record;
    }
    return null;
}

function st_connectors_client_type(): string
{
    $type = strtolower((string) ($_SERVER['HTTP_X_ST_CLIENT_TYPE'] ?? 'unknown'));
    return in_array($type, ['human', 'ai', 'software'], true) ? $type : 'unknown';
}

function st_connectors_ensure_schema(): void
{
    static $ready = false;
    if ($ready) return;
    $pdo = st_db();
    $statements = [
        "CREATE TABLE IF NOT EXISTS st_connector_reviews (connector_id VARCHAR(80) NOT NULL, review_status ENUM('pending_review','source_identified','reviewed','rejected') NOT NULL DEFAULT 'pending_review', confidence DECIMAL(4,3) NOT NULL DEFAULT 0.000, reviewer_alias VARCHAR(40) NOT NULL DEFAULT 'Administrador', evidence_source_id VARCHAR(80) NULL, evidence_locator VARCHAR(180) NULL, notes TEXT NULL, contacts_checked TINYINT(1) NOT NULL DEFAULT 0, orientation_checked TINYINT(1) NOT NULL DEFAULT 0, variants_checked TINYINT(1) NOT NULL DEFAULT 0, catalog_version VARCHAR(40) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, reviewed_at TIMESTAMP NULL, PRIMARY KEY (connector_id), KEY idx_connector_review_status (review_status, updated_at)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        "CREATE TABLE IF NOT EXISTS st_connector_review_events (id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, connector_id VARCHAR(80) NOT NULL, review_status VARCHAR(32) NOT NULL, reviewer_alias VARCHAR(40) NOT NULL, evidence_source_id VARCHAR(80) NULL, evidence_locator VARCHAR(180) NULL, details_json JSON NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (id), KEY idx_connector_review_event (connector_id, created_at)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        "CREATE TABLE IF NOT EXISTS st_connector_import_batches (id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, original_filename VARCHAR(255) NOT NULL, stored_filename VARCHAR(100) NOT NULL, sha256 CHAR(64) NOT NULL, media_type VARCHAR(100) NOT NULL, file_size BIGINT UNSIGNED NOT NULL, import_status ENUM('uploaded','needs_extractor','extracted','ready_for_review','merged','rejected') NOT NULL DEFAULT 'uploaded', summary VARCHAR(500) NULL, extracted_json JSON NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (id), UNIQUE KEY uq_connector_import_sha (sha256), KEY idx_connector_import_status (import_status, created_at)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        "CREATE TABLE IF NOT EXISTS st_connector_usage_events (id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, action_name ENUM('search','get','resolve') NOT NULL, client_hash CHAR(64) NOT NULL, client_type ENUM('human','ai','software','unknown') NOT NULL DEFAULT 'unknown', query_hash CHAR(64) NULL, query_sample VARCHAR(120) NULL, connector_id VARCHAR(80) NULL, result_count SMALLINT UNSIGNED NOT NULL DEFAULT 0, latency_ms INT UNSIGNED NOT NULL DEFAULT 0, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (id), KEY idx_connector_usage_date (created_at), KEY idx_connector_usage_connector (connector_id, created_at), KEY idx_connector_usage_client (client_type, created_at)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
    ];
    foreach ($statements as $sql) $pdo->exec($sql);
    $ready = true;
}

function st_connectors_log_usage(string $action, string $clientHash, string $query, ?string $connectorId, int $count, int $startedAt): void
{
    try {
        st_connectors_ensure_schema();
        $stmt = st_db()->prepare('INSERT INTO st_connector_usage_events (action_name, client_hash, client_type, query_hash, query_sample, connector_id, result_count, latency_ms) VALUES (?, ?, ?, NULLIF(?, \'\'), NULLIF(?, \'\'), NULLIF(?, \'\'), ?, ?)');
        $sample = mb_substr(trim($query), 0, 120);
        $stmt->execute([$action, $clientHash, st_connectors_client_type(), $query === '' ? '' : hash('sha256', st_connectors_fold($query)), $sample, $connectorId ?? '', $count, max(0, (int) round((microtime(true) * 1000) - $startedAt))]);
    } catch (Throwable $error) {
        error_log('Connector usage log: ' . $error->getMessage());
    }
}

function st_connectors_search(array $input, string $clientHash): array
{
    $startedAt = (int) round(microtime(true) * 1000);
    $query = trim((string) ($input['q'] ?? $input['query'] ?? ''));
    if (mb_strlen($query) < 1 || mb_strlen($query) > 120) st_json(['ok' => false, 'error' => 'invalid_query'], 422);
    $needle = st_connectors_fold($query);
    $category = st_connectors_fold((string) ($input['category'] ?? ''));
    $reviewStatus = trim((string) ($input['review_status'] ?? ''));
    $limit = min(20, max(1, (int) ($input['limit'] ?? 8)));
    $matches = [];
    foreach (st_connectors_catalog()['records'] as $record) {
        $haystack = st_connectors_fold(implode(' ', array_merge(
            [$record['id'], $record['canonical_name'], $record['category'], $record['interface'], $record['form_factor']],
            $record['aliases'] ?? [], $record['search_terms'] ?? [],
            array_map(fn(array $contact): string => ($contact['id'] ?? '') . ' ' . ($contact['signal'] ?? ''), $record['contacts'] ?? [])
        )));
        if (!str_contains($haystack, $needle)) continue;
        if ($category !== '' && !str_contains(st_connectors_fold((string) $record['category']), $category)) continue;
        if ($reviewStatus !== '' && ($record['review']['status'] ?? '') !== $reviewStatus) continue;
        $matches[] = [
            'id' => $record['id'], 'canonical_name' => $record['canonical_name'], 'aliases' => $record['aliases'],
            'category' => $record['category'], 'interface' => $record['interface'], 'form_factor' => $record['form_factor'],
            'gender' => $record['gender'], 'contact_count' => count($record['contacts']), 'view' => $record['view'],
            'review' => $record['review'], 'source_ids' => $record['source_ids'],
        ];
        if (count($matches) >= $limit) break;
    }
    st_connectors_log_usage('search', $clientHash, $query, null, count($matches), $startedAt);
    return ['ok' => true, 'tool' => 'supertecnico_search_connectors', 'service_version' => ST_CONNECTOR_SERVICE_VERSION, 'query' => $query, 'total' => count($matches), 'items' => $matches];
}

function st_connectors_get(array $input, string $clientHash): array
{
    $startedAt = (int) round(microtime(true) * 1000);
    $id = trim((string) ($input['connector_id'] ?? $input['id'] ?? ''));
    $record = st_connectors_find($id);
    if (!$record) st_json(['ok' => false, 'error' => 'connector_not_found'], 404);
    st_connectors_log_usage('get', $clientHash, '', $id, 1, $startedAt);
    return ['ok' => true, 'tool' => 'supertecnico_get_connector', 'service_version' => ST_CONNECTOR_SERVICE_VERSION, 'record' => $record];
}

function st_connectors_resolve(array $input, string $clientHash): array
{
    $startedAt = (int) round(microtime(true) * 1000);
    $id = trim((string) ($input['connector_id'] ?? ''));
    $query = trim((string) ($input['contact_or_signal'] ?? $input['q'] ?? ''));
    if ($query === '') st_json(['ok' => false, 'error' => 'invalid_contact_query'], 422);
    $record = st_connectors_find($id);
    if (!$record) st_json(['ok' => false, 'error' => 'connector_not_found'], 404);
    $needle = st_connectors_fold($query);
    $contacts = array_values(array_filter($record['contacts'], fn(array $contact): bool => str_contains(st_connectors_fold(($contact['id'] ?? '') . ' ' . ($contact['signal'] ?? '') . ' ' . ($contact['description'] ?? '')), $needle)));
    st_connectors_log_usage('resolve', $clientHash, $query, $id, count($contacts), $startedAt);
    return ['ok' => true, 'tool' => 'supertecnico_resolve_connector_contact', 'service_version' => ST_CONNECTOR_SERVICE_VERSION, 'connector_id' => $id, 'view' => $record['view'], 'review' => $record['review'], 'contacts' => $contacts];
}

function st_connectors_admin_catalog(array $input): array
{
    st_connectors_ensure_schema();
    $rows = st_db()->query('SELECT * FROM st_connector_reviews ORDER BY updated_at DESC')->fetchAll();
    $reviews = [];
    foreach ($rows as $row) $reviews[$row['connector_id']] = $row;
    $records = [];
    foreach (st_connectors_catalog()['records'] as $record) {
        $record['admin_review'] = $reviews[$record['id']] ?? null;
        $records[] = $record;
    }
    return ['ok' => true, 'catalog_version' => st_connectors_catalog()['catalog_version'], 'records' => $records];
}

function st_connectors_admin_review(array $body): array
{
    st_connectors_ensure_schema();
    $connectorId = st_text($body, 'connector_id', 3, 80);
    if (!st_connectors_find($connectorId)) st_json(['ok' => false, 'error' => 'connector_not_found'], 404);
    $status = st_text($body, 'review_status', 8, 32);
    if (!in_array($status, ['pending_review', 'source_identified', 'reviewed', 'rejected'], true)) st_json(['ok' => false, 'error' => 'invalid_status'], 422);
    $reviewer = st_text($body, 'reviewer_alias', 2, 40);
    $sourceId = st_text($body, 'evidence_source_id', 0, 80, false);
    $locator = st_text($body, 'evidence_locator', 0, 180, false);
    $notes = st_text($body, 'notes', 0, 3000, false);
    $contacts = !empty($body['contacts_checked']) ? 1 : 0;
    $orientation = !empty($body['orientation_checked']) ? 1 : 0;
    $variants = !empty($body['variants_checked']) ? 1 : 0;
    if ($status === 'reviewed' && ($sourceId === '' || $locator === '' || !$contacts || !$orientation || !$variants)) {
        st_json(['ok' => false, 'error' => 'review_evidence_incomplete'], 422);
    }
    $confidence = max(0, min(1, (float) ($body['confidence'] ?? 0)));
    $catalogVersion = (string) st_connectors_catalog()['catalog_version'];
    $pdo = st_db();
    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare('INSERT INTO st_connector_reviews (connector_id, review_status, confidence, reviewer_alias, evidence_source_id, evidence_locator, notes, contacts_checked, orientation_checked, variants_checked, catalog_version, reviewed_at) VALUES (?, ?, ?, ?, NULLIF(?, \'\'), NULLIF(?, \'\'), NULLIF(?, \'\'), ?, ?, ?, ?, IF(? = \'reviewed\', NOW(), NULL)) ON DUPLICATE KEY UPDATE review_status=VALUES(review_status), confidence=VALUES(confidence), reviewer_alias=VALUES(reviewer_alias), evidence_source_id=VALUES(evidence_source_id), evidence_locator=VALUES(evidence_locator), notes=VALUES(notes), contacts_checked=VALUES(contacts_checked), orientation_checked=VALUES(orientation_checked), variants_checked=VALUES(variants_checked), catalog_version=VALUES(catalog_version), reviewed_at=IF(VALUES(review_status)=\'reviewed\', NOW(), reviewed_at)');
        $stmt->execute([$connectorId, $status, $confidence, $reviewer, $sourceId, $locator, $notes, $contacts, $orientation, $variants, $catalogVersion, $status]);
        $event = $pdo->prepare('INSERT INTO st_connector_review_events (connector_id, review_status, reviewer_alias, evidence_source_id, evidence_locator, details_json) VALUES (?, ?, ?, NULLIF(?, \'\'), NULLIF(?, \'\'), ?)');
        $event->execute([$connectorId, $status, $reviewer, $sourceId, $locator, json_encode(['confidence' => $confidence, 'contacts_checked' => (bool) $contacts, 'orientation_checked' => (bool) $orientation, 'variants_checked' => (bool) $variants, 'notes' => $notes], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)]);
        $pdo->commit();
    } catch (Throwable $error) {
        if ($pdo->inTransaction()) $pdo->rollBack();
        throw $error;
    }
    return ['ok' => true, 'connector_id' => $connectorId, 'review_status' => $status];
}

function st_connectors_admin_history(array $input): array
{
    st_connectors_ensure_schema();
    $connectorId = trim((string) ($input['connector_id'] ?? ''));
    if ($connectorId === '') st_json(['ok' => false, 'error' => 'invalid_connector_id'], 422);
    $stmt = st_db()->prepare('SELECT * FROM st_connector_review_events WHERE connector_id = ? ORDER BY created_at DESC, id DESC LIMIT 100');
    $stmt->execute([$connectorId]);
    return ['ok' => true, 'connector_id' => $connectorId, 'items' => $stmt->fetchAll()];
}

function st_connectors_admin_imports(): array
{
    st_connectors_ensure_schema();
    $items = st_db()->query('SELECT id, original_filename, sha256, media_type, file_size, import_status, summary, created_at, updated_at FROM st_connector_import_batches ORDER BY created_at DESC LIMIT 200')->fetchAll();
    return ['ok' => true, 'items' => $items];
}

function st_connectors_admin_import(): array
{
    st_connectors_ensure_schema();
    if (!isset($_FILES['document']) || !is_array($_FILES['document'])) st_json(['ok' => false, 'error' => 'document_required'], 422);
    $file = $_FILES['document'];
    if (($file['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK) st_json(['ok' => false, 'error' => 'upload_failed'], 422);
    $size = (int) ($file['size'] ?? 0);
    if ($size < 1 || $size > 15 * 1024 * 1024) st_json(['ok' => false, 'error' => 'invalid_file_size'], 422);
    $original = mb_substr(basename((string) ($file['name'] ?? 'documento')), 0, 255);
    $extension = strtolower(pathinfo($original, PATHINFO_EXTENSION));
    $allowed = ['pdf', 'xlsx', 'csv', 'tsv', 'json', 'txt', 'png', 'jpg', 'jpeg', 'webp'];
    if (!in_array($extension, $allowed, true)) st_json(['ok' => false, 'error' => 'unsupported_file_type'], 422);
    $temp = (string) ($file['tmp_name'] ?? '');
    $sha = hash_file('sha256', $temp);
    if (!is_string($sha)) throw new RuntimeException('hash_failed');
    $mime = (new finfo(FILEINFO_MIME_TYPE))->file($temp) ?: 'application/octet-stream';
    $directory = dirname(__DIR__) . '/database/connector-imports';
    if (!is_dir($directory) && !mkdir($directory, 0700, true) && !is_dir($directory)) throw new RuntimeException('import_storage_unavailable');
    $stored = $sha . '.' . $extension;
    $target = $directory . '/' . $stored;
    if (!is_file($target) && !move_uploaded_file($temp, $target)) throw new RuntimeException('import_store_failed');
    $structured = in_array($extension, ['json', 'csv', 'tsv', 'txt', 'xlsx'], true);
    $status = $structured ? 'uploaded' : 'needs_extractor';
    $summary = mb_substr(trim((string) ($_POST['summary'] ?? '')), 0, 500);
    $extractedRaw = (string) ($_POST['extracted_json'] ?? '');
    $extracted = null;
    if ($extractedRaw !== '') {
        $decoded = json_decode($extractedRaw, true);
        if (!is_array($decoded)) st_json(['ok' => false, 'error' => 'invalid_extracted_json'], 422);
        $extracted = json_encode($decoded, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        $status = 'extracted';
    }
    $stmt = st_db()->prepare('INSERT INTO st_connector_import_batches (original_filename, stored_filename, sha256, media_type, file_size, import_status, summary, extracted_json) VALUES (?, ?, ?, ?, ?, ?, NULLIF(?, \'\'), ?) ON DUPLICATE KEY UPDATE original_filename=VALUES(original_filename), summary=COALESCE(NULLIF(VALUES(summary), \'\'), summary), extracted_json=COALESCE(VALUES(extracted_json), extracted_json), import_status=IF(VALUES(extracted_json) IS NULL, import_status, \'extracted\'), updated_at=NOW()');
    $stmt->execute([$original, $stored, $sha, $mime, $size, $status, $summary, $extracted]);
    $id = (int) st_db()->lastInsertId();
    if ($id === 0) {
        $find = st_db()->prepare('SELECT id FROM st_connector_import_batches WHERE sha256 = ?');
        $find->execute([$sha]);
        $id = (int) $find->fetchColumn();
    }
    return ['ok' => true, 'id' => $id, 'sha256' => $sha, 'import_status' => $status, 'stored_privately' => true];
}

function st_connectors_admin_import_update(array $body): array
{
    st_connectors_ensure_schema();
    $id = filter_var($body['id'] ?? null, FILTER_VALIDATE_INT);
    if (!$id) st_json(['ok' => false, 'error' => 'invalid_id'], 422);
    $status = st_text($body, 'import_status', 6, 32);
    if (!in_array($status, ['uploaded', 'needs_extractor', 'extracted', 'ready_for_review', 'merged', 'rejected'], true)) st_json(['ok' => false, 'error' => 'invalid_status'], 422);
    $summary = st_text($body, 'summary', 0, 500, false);
    $stmt = st_db()->prepare('UPDATE st_connector_import_batches SET import_status = ?, summary = NULLIF(?, \'\') WHERE id = ?');
    $stmt->execute([$status, $summary, $id]);
    if ($stmt->rowCount() < 1) {
        $exists = st_db()->prepare('SELECT 1 FROM st_connector_import_batches WHERE id = ?');
        $exists->execute([$id]);
        if (!$exists->fetchColumn()) st_json(['ok' => false, 'error' => 'import_not_found'], 404);
    }
    return ['ok' => true, 'id' => (int) $id, 'import_status' => $status];
}
