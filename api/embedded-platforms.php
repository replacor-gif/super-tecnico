<?php
declare(strict_types=1);

const ST_EMBEDDED_SERVICE_VERSION = '0.2.0-beta.1';

function st_embedded_catalog(): array
{
    static $catalog = null;
    if (is_array($catalog)) return $catalog;
    $path = dirname(__DIR__) . '/data/embedded-platforms/catalog.json';
    $catalog = json_decode((string) @file_get_contents($path), true);
    if (!is_array($catalog) || !isset($catalog['records']) || !is_array($catalog['records'])) {
        throw new RuntimeException('embedded_platform_catalog_unavailable');
    }
    return $catalog;
}

function st_embedded_fold(string $value): string
{
    $value = function_exists('mb_strtolower') ? mb_strtolower(trim($value), 'UTF-8') : strtolower(trim($value));
    $ascii = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value);
    return preg_replace('/[^a-z0-9]+/', ' ', $ascii === false ? $value : strtolower($ascii)) ?? '';
}

function st_embedded_length(string $value): int
{
    return function_exists('mb_strlen') ? mb_strlen($value, 'UTF-8') : strlen($value);
}

function st_embedded_substr(string $value, int $start, int $length): string
{
    return function_exists('mb_substr') ? mb_substr($value, $start, $length, 'UTF-8') : substr($value, $start, $length);
}

function st_embedded_find(string $id): ?array
{
    foreach (st_embedded_catalog()['records'] as $record) {
        if (hash_equals((string) $record['id'], $id)) return $record;
    }
    return null;
}

function st_embedded_summary(array $record): array
{
    return [
        'id' => $record['id'],
        'name' => $record['name'],
        'manufacturer' => $record['manufacturer'],
        'platform_class' => $record['platform_class'],
        'architecture' => $record['architecture'],
        'logic_and_power' => $record['logic_and_power'],
        'interfaces' => $record['interfaces'],
        'recommended_use' => $record['recommended_use'],
        'primary_risk' => $record['primary_risk'],
        'tags' => $record['tags'],
        'review' => $record['review'],
        'source_refs' => $record['source_refs'],
        'source_locator' => $record['source_locator'],
    ];
}

function st_embedded_ensure_schema(): void
{
    static $ready = false;
    if ($ready) return;
    st_db()->exec("CREATE TABLE IF NOT EXISTS st_embedded_usage_events (id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, action_name ENUM('search','get','recommend') NOT NULL, client_hash CHAR(64) NOT NULL, client_type ENUM('human','ai','software','unknown') NOT NULL DEFAULT 'unknown', query_hash CHAR(64) NULL, query_sample VARCHAR(160) NULL, platform_id VARCHAR(100) NULL, result_count SMALLINT UNSIGNED NOT NULL DEFAULT 0, latency_ms INT UNSIGNED NOT NULL DEFAULT 0, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (id), KEY idx_embedded_usage_date (created_at), KEY idx_embedded_usage_platform (platform_id, created_at), KEY idx_embedded_usage_client (client_type, created_at)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $ready = true;
}

function st_embedded_client_type(): string
{
    $type = strtolower((string) ($_SERVER['HTTP_X_ST_CLIENT_TYPE'] ?? ($_GET['client_type'] ?? 'unknown')));
    return in_array($type, ['human', 'ai', 'software'], true) ? $type : 'unknown';
}

function st_embedded_log(string $action, string $clientHash, string $query, ?string $platformId, int $count, int $startedAt): void
{
    try {
        st_embedded_ensure_schema();
        $stmt = st_db()->prepare('INSERT INTO st_embedded_usage_events (action_name, client_hash, client_type, query_hash, query_sample, platform_id, result_count, latency_ms) VALUES (?, ?, ?, NULLIF(?, \'\'), NULLIF(?, \'\'), NULLIF(?, \'\'), ?, ?)');
        $sample = st_embedded_substr(trim($query), 0, 160);
        $stmt->execute([$action, $clientHash, st_embedded_client_type(), $query === '' ? '' : hash('sha256', st_embedded_fold($query)), $sample, $platformId ?? '', $count, max(0, (int) round(microtime(true) * 1000) - $startedAt)]);
    } catch (Throwable $error) {
        error_log('Embedded usage log: ' . $error->getMessage());
    }
}

function st_embedded_haystack(array $record): string
{
    return st_embedded_fold(implode(' ', array_merge([
        $record['id'], $record['name'], $record['manufacturer'], $record['platform_class'],
        $record['architecture'], $record['logic_and_power'], $record['recommended_use'], $record['primary_risk'],
    ], $record['interfaces'] ?? [], $record['tags'] ?? [])));
}

function st_embedded_matches_query(array $record, string $query): bool
{
    $terms = st_embedded_terms($query);
    $haystack = st_embedded_haystack($record);
    foreach ($terms as $term) if (!str_contains($haystack, $term)) return false;
    return count($terms) > 0;
}

function st_embedded_terms(string $value): array
{
    $ignored = ['a', 'al', 'de', 'del', 'la', 'las', 'el', 'los', 'y', 'o', 'u', 'con', 'para', 'por', 'en', 'un', 'una', 'unos', 'unas', 'que', 'como', 'quiero', 'necesito', 'the', 'and', 'with', 'for', 'from', 'to', 'an', 'of', 'on', 'in'];
    return array_values(array_unique(array_filter(
        explode(' ', st_embedded_fold($value)),
        fn(string $term): bool => strlen($term) >= 2 && !in_array($term, $ignored, true)
    )));
}

function st_embedded_search(array $input, string $clientHash): array
{
    $startedAt = (int) round(microtime(true) * 1000);
    $query = trim((string) ($input['q'] ?? $input['query'] ?? ''));
    if (st_embedded_length($query) < 1 || st_embedded_length($query) > 160) st_json(['ok' => false, 'error' => 'invalid_query'], 422);
    $needle = st_embedded_fold($query);
    $manufacturer = st_embedded_fold((string) ($input['manufacturer'] ?? ''));
    $class = st_embedded_fold((string) ($input['platform_class'] ?? ''));
    $limit = min(20, max(1, (int) ($input['limit'] ?? 8)));
    $matches = [];
    foreach (st_embedded_catalog()['records'] as $record) {
        if (!st_embedded_matches_query($record, $needle)) continue;
        if ($manufacturer !== '' && !str_contains(st_embedded_fold((string) $record['manufacturer']), $manufacturer)) continue;
        if ($class !== '' && st_embedded_fold((string) $record['platform_class']) !== $class) continue;
        $matches[] = st_embedded_summary($record);
        if (count($matches) >= $limit) break;
    }
    st_embedded_log('search', $clientHash, $query, null, count($matches), $startedAt);
    return ['ok' => true, 'tool' => 'supertecnico_search_embedded_platforms', 'service_version' => ST_EMBEDDED_SERVICE_VERSION, 'catalog_version' => st_embedded_catalog()['catalog_version'], 'query' => $query, 'total' => count($matches), 'items' => $matches];
}

function st_embedded_get(array $input, string $clientHash): array
{
    $startedAt = (int) round(microtime(true) * 1000);
    $id = trim((string) ($input['platform_id'] ?? $input['id'] ?? ''));
    $record = st_embedded_find($id);
    if (!$record) st_json(['ok' => false, 'error' => 'embedded_platform_not_found'], 404);
    st_embedded_log('get', $clientHash, '', $id, 1, $startedAt);
    return ['ok' => true, 'tool' => 'supertecnico_get_embedded_platform', 'service_version' => ST_EMBEDDED_SERVICE_VERSION, 'catalog_version' => st_embedded_catalog()['catalog_version'], 'record' => $record, 'reception_checks' => st_embedded_catalog()['shared_reception_checks'], 'integration_requirements' => st_embedded_catalog()['shared_integration_requirements']];
}

function st_embedded_recommend(array $input, string $clientHash): array
{
    $startedAt = (int) round(microtime(true) * 1000);
    $useCase = trim((string) ($input['use_case'] ?? $input['q'] ?? ''));
    if (st_embedded_length($useCase) < 3 || st_embedded_length($useCase) > 300) st_json(['ok' => false, 'error' => 'invalid_use_case'], 422);
    $required = trim((string) ($input['required_interfaces'] ?? ''));
    $queryTerms = st_embedded_terms($useCase . ' ' . $required);
    $needsLinux = filter_var($input['needs_linux'] ?? false, FILTER_VALIDATE_BOOLEAN) || in_array('linux', $queryTerms, true);
    $ranked = [];
    foreach (st_embedded_catalog()['records'] as $record) {
        $haystack = st_embedded_haystack($record);
        $matched = array_values(array_filter($queryTerms, fn(string $term): bool => str_contains($haystack, $term)));
        $linuxClass = in_array($record['platform_class'], ['single_board_computer', 'system_on_module', 'edge_ai_computer', 'soc_fpga_board'], true);
        if ($needsLinux && !$linuxClass) continue;
        $score = count($matched) * 10 + ($needsLinux && $linuxClass ? 8 : 0);
        if ($score < 1) continue;
        $ranked[] = ['score' => $score, 'matched_terms' => $matched, 'platform' => st_embedded_summary($record)];
    }
    usort($ranked, fn(array $a, array $b): int => $b['score'] <=> $a['score'] ?: strcmp($a['platform']['name'], $b['platform']['name']));
    $limit = min(10, max(1, (int) ($input['limit'] ?? 5)));
    $items = array_slice($ranked, 0, $limit);
    st_embedded_log('recommend', $clientHash, $useCase . ' ' . $required, null, count($items), $startedAt);
    return [
        'ok' => true,
        'tool' => 'supertecnico_recommend_embedded_platforms',
        'service_version' => ST_EMBEDDED_SERVICE_VERSION,
        'catalog_version' => st_embedded_catalog()['catalog_version'],
        'total' => count($items),
        'items' => $items,
        'decision_status' => count($items) ? 'preselection_only' : 'insufficient_context',
        'warnings' => [
            'La puntuación solo ordena coincidencias documentales; no demuestra que una placa sea adecuada.',
            'Confirma revisión exacta, pinout, niveles, memoria, radio, carrier, software, ciclo de vida y condiciones ambientales.',
        ],
    ];
}
