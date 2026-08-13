<?php
declare(strict_types=1);

const ST_REGULATION_TOOL_ID = 'supertecnico_search_regulations';
const ST_REGULATION_TOOL_VERSION = '1.0.0';
const ST_REGULATION_SERVICE_VERSION = '0.3.0';

function st_regulations_ensure_schema(): void
{
    static $ready = false;
    if ($ready) return;
    st_db()->exec("CREATE TABLE IF NOT EXISTS st_regulation_search_events (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $ready = true;
}

function st_regulation_normalize(string $value): string
{
    $value = mb_strtolower(trim($value), 'UTF-8');
    $transliterated = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value);
    $value = $transliterated === false ? $value : $transliterated;
    return trim(preg_replace('/[^a-z0-9]+/', ' ', $value) ?? '');
}

function st_regulation_query_sample(string $query): string
{
    $sample = preg_replace('/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/iu', '[correo]', $query) ?? $query;
    $sample = preg_replace('~https?://\S+|www\.\S+~iu', '[enlace]', $sample) ?? $sample;
    $sample = preg_replace('/(?<!\d)(?:\+?\d[\s().-]*){7,}(?!\d)/u', '[numero]', $sample) ?? $sample;
    $sample = trim(preg_replace('/\s+/u', ' ', $sample) ?? $sample);
    return mb_substr($sample, 0, 180, 'UTF-8');
}

function st_regulation_client_type(array $input): string
{
    $explicit = strtolower(trim((string) ($_SERVER['HTTP_X_ST_CLIENT_TYPE'] ?? ($input['client_type'] ?? ''))));
    if (in_array($explicit, ['human', 'ai', 'software'], true)) return $explicit;
    $agent = strtolower((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''));
    if (preg_match('/openai|anthropic|claude|gemini|perplexity|copilot|language-model|\bai[-_ ]agent\b/', $agent) === 1) return 'ai';
    if (preg_match('/curl|wget|python|node-fetch|postman|insomnia|httpie/', $agent) === 1) return 'software';
    if (preg_match('/mozilla|chrome|safari|firefox|edge/', $agent) === 1) return 'human';
    return 'unknown';
}

function st_regulation_load_json(string $path, string $cacheKey): array
{
    if (function_exists('apcu_fetch')) {
        $hit = false;
        $cached = apcu_fetch($cacheKey, $hit);
        if ($hit && is_array($cached)) return $cached;
    }
    $raw = @file_get_contents($path);
    $decoded = $raw === false ? null : json_decode($raw, true);
    if (!is_array($decoded)) throw new RuntimeException('regulation_data_unavailable');
    if (function_exists('apcu_store')) @apcu_store($cacheKey, $decoded, 900);
    return $decoded;
}

function st_regulation_catalog(): array
{
    $path = dirname(__DIR__) . '/data/regulations/catalog.json';
    return st_regulation_load_json($path, 'st-regulations-catalog-' . (string) @filemtime($path));
}

function st_regulation_token_variants(string $token): array
{
    $variants = [$token];
    $length = strlen($token);
    if ($length > 5 && str_ends_with($token, 'es')) $variants[] = substr($token, 0, -2);
    if ($length > 4 && str_ends_with($token, 's')) $variants[] = substr($token, 0, -1);
    return array_values(array_unique(array_filter($variants, static fn(string $value): bool => strlen($value) >= 2)));
}

function st_regulation_terms(string $normalized): array
{
    $stop = ['a','al','ante','bajo','con','contra','de','del','desde','durante','e','el','en','entre','hacia','hasta','la','las','lo','los','o','para','por','que','segun','sin','sobre','tras','un','una','unos','unas','y'];
    $raw = array_values(array_unique(array_filter(explode(' ', $normalized), static fn(string $token): bool => strlen($token) >= 2)));
    $useful = array_values(array_filter($raw, static fn(string $token): bool => !in_array($token, $stop, true)));
    return $useful ?: $raw;
}

function st_regulation_term_position(string $haystack, string $term): int|false
{
    foreach (st_regulation_token_variants($term) as $variant) {
        if (strlen($variant) === 2) {
            $matched = preg_match('/(?:^| )' . preg_quote($variant, '/') . '(?: |$)/', $haystack, $capture, PREG_OFFSET_CAPTURE);
            $position = $matched === 1 ? (int) $capture[0][1] : false;
        } else {
            $position = strpos($haystack, $variant);
        }
        if ($position !== false) return $position;
    }
    return false;
}

function st_regulation_snippet(string $text, array $terms, int $max = 900): string
{
    $text = trim(preg_replace('/\s+/u', ' ', $text) ?? $text);
    if (mb_strlen($text, 'UTF-8') <= $max) return $text;
    $normalized = st_regulation_normalize($text);
    $position = false;
    foreach ($terms as $term) {
        $candidate = st_regulation_term_position($normalized, $term);
        if ($candidate !== false && ($position === false || $candidate < $position)) $position = $candidate;
    }
    $start = max(0, (int) ($position === false ? 0 : $position) - 180);
    $snippet = mb_substr($text, $start, $max, 'UTF-8');
    return ($start > 0 ? '…' : '') . trim($snippet) . (mb_strlen($text, 'UTF-8') > $start + $max ? '…' : '');
}

function st_regulations_search(array $input, string $clientHash, bool $recordUsage = true): array
{
    $started = microtime(true);
    $query = trim((string) ($input['query'] ?? $input['q'] ?? ''));
    if (mb_strlen($query, 'UTF-8') < 2 || mb_strlen($query, 'UTF-8') > 300) {
        st_json(['ok' => false, 'error' => 'invalid_field', 'field' => 'query'], 422);
    }
    $normalized = st_regulation_normalize($query);
    $terms = st_regulation_terms($normalized);
    if (!$terms) st_json(['ok' => false, 'error' => 'invalid_field', 'field' => 'query'], 422);

    $documentFilter = preg_replace('/[^a-z0-9-]/', '', strtolower((string) ($input['document_id'] ?? ''))) ?? '';
    $domainFilter = preg_replace('/[^a-z0-9_]/', '', strtolower((string) ($input['domain'] ?? ''))) ?? '';
    $limit = min(20, max(1, (int) ($input['limit'] ?? 10)));
    $exactPhrase = filter_var($input['exact_phrase'] ?? false, FILTER_VALIDATE_BOOLEAN);
    $catalog = st_regulation_catalog();
    $documents = array_values(array_filter($catalog['documents'] ?? [], static function (array $document) use ($documentFilter, $domainFilter): bool {
        if ($documentFilter !== '' && ($document['id'] ?? '') !== $documentFilter) return false;
        if ($domainFilter !== '' && ($document['domain'] ?? '') !== $domainFilter) return false;
        return true;
    }));
    if ($documentFilter !== '' && !$documents) st_json(['ok' => false, 'error' => 'unknown_document'], 422);
    if ($domainFilter !== '' && !$documents) st_json(['ok' => false, 'error' => 'unknown_domain'], 422);

    $candidates = [];
    foreach ($documents as $document) {
        $indexRelative = str_replace(['/', '\\'], DIRECTORY_SEPARATOR, (string) ($document['index_url'] ?? ''));
        $indexPath = dirname(__DIR__) . DIRECTORY_SEPARATOR . $indexRelative;
        $index = st_regulation_load_json($indexPath, 'st-regulations-index-' . ($document['id'] ?? '') . '-' . ($document['content_sha256'] ?? ''));
        $metadata = st_regulation_normalize(implode(' ', [
            $document['short_title'] ?? '', $document['title'] ?? '', $document['legal_reference'] ?? '',
            $document['domain'] ?? '', implode(' ', $document['topics'] ?? []),
        ]));
        foreach ($index['records'] ?? [] as $record) {
            $haystack = (string) ($record['search'] ?? st_regulation_normalize((string) ($record['text'] ?? '')));
            $matched = 0;
            $firstPosition = PHP_INT_MAX;
            foreach ($terms as $term) {
                $position = st_regulation_term_position($haystack, $term);
                if ($position !== false) {
                    $matched++;
                    $firstPosition = min($firstPosition, $position);
                }
            }
            $phraseFound = $normalized !== '' && strpos($haystack, $normalized) !== false;
            if ($exactPhrase && !$phraseFound) continue;
            if (!$exactPhrase && $matched !== count($terms)) continue;
            $score = ($phraseFound ? 160 : 0) + ($matched * 24) + ($firstPosition < 180 ? 8 : 0);
            if (strpos($haystack, $normalized) !== false) $score += 35;
            foreach ($terms as $term) if (st_regulation_term_position($metadata, $term) !== false) $score += 3;
            $candidates[] = ['score' => $score, 'matched' => $matched, 'document' => $document, 'record' => $record];
        }
    }

    $matchMode = $exactPhrase ? 'exact' : 'all_terms';
    if (!$candidates && !$exactPhrase && count($terms) >= 3) {
        $matchMode = 'related';
        foreach ($documents as $document) {
            $indexRelative = str_replace(['/', '\\'], DIRECTORY_SEPARATOR, (string) ($document['index_url'] ?? ''));
            $indexPath = dirname(__DIR__) . DIRECTORY_SEPARATOR . $indexRelative;
            $index = st_regulation_load_json($indexPath, 'st-regulations-index-' . ($document['id'] ?? '') . '-' . ($document['content_sha256'] ?? ''));
            $metadata = st_regulation_normalize(implode(' ', [$document['short_title'] ?? '', $document['title'] ?? '', $document['legal_reference'] ?? '', $document['domain'] ?? '', implode(' ', $document['topics'] ?? [])]));
            foreach ($index['records'] ?? [] as $record) {
                $haystack = (string) ($record['search'] ?? st_regulation_normalize((string) ($record['text'] ?? '')));
                $matched = 0;
                foreach ($terms as $term) if (st_regulation_term_position($haystack, $term) !== false) $matched++;
                if ($matched < max(2, count($terms) - 1)) continue;
                $candidates[] = ['score' => ($matched * 20), 'matched' => $matched, 'document' => $document, 'record' => $record];
            }
        }
    }

    usort($candidates, static fn(array $left, array $right): int => ($right['score'] <=> $left['score']) ?: (($left['record']['page'] ?? 0) <=> ($right['record']['page'] ?? 0)));
    $items = [];
    $seen = [];
    $facets = ['documents' => [], 'domains' => []];
    foreach ($candidates as $candidate) {
        $document = $candidate['document'];
        $record = $candidate['record'];
        $key = ($document['id'] ?? '') . ':' . ($record['page'] ?? 0);
        if (isset($seen[$key])) continue;
        $seen[$key] = true;
        $facets['documents'][$document['id']] = ($facets['documents'][$document['id']] ?? 0) + 1;
        $facets['domains'][$document['domain']] = ($facets['domains'][$document['domain']] ?? 0) + 1;
        if (count($items) >= $limit) continue;
        $page = (int) ($record['page'] ?? 0);
        $items[] = [
            'document_id' => (string) $document['id'],
            'document_title' => (string) $document['title'],
            'short_title' => (string) $document['short_title'],
            'legal_reference' => (string) $document['legal_reference'],
            'authority' => (string) $document['authority'],
            'domain' => (string) $document['domain'],
            'page' => $page,
            'text' => st_regulation_snippet((string) ($record['text'] ?? ''), $terms),
            'local_pdf_path' => (string) $document['local_pdf'],
            'local_pdf_fragment' => '#page=' . $page,
            'official_page_url' => (string) $document['official_page_url'],
            'source_sha256' => (string) $document['sha256'],
            'source_content_sha256' => (string) $document['content_sha256'],
            'evidence_level' => 'document_hit',
            'relevance_score' => min(1, round(((int) $candidate['score']) / 240, 3)),
        ];
    }
    if (!$items) $matchMode = 'none';
    $requestId = bin2hex(random_bytes(16));
    $latencyMs = max(0, (int) round((microtime(true) - $started) * 1000));
    if ($recordUsage) st_regulations_record_search($requestId, $clientHash, $input, $query, $documentFilter, $domainFilter, count($items), $items[0]['document_id'] ?? '', $matchMode, $latencyMs);
    $sourceIds = array_values(array_unique(array_map(static fn(array $item): string => $item['document_id'], $items)));
    $warnings = ['Una coincidencia documental no demuestra por sí sola que la regla sea aplicable al caso concreto. Comprueba vigencia, ámbito y normativa autonómica o local.'];
    if ($matchMode === 'related') $warnings[] = 'No se encontraron todas las palabras juntas; se muestran coincidencias relacionadas y deben revisarse con más cautela.';

    return [
        'ok' => true,
        'status' => $items ? 'success' : 'not_found',
        'request_id' => $requestId,
        'service_version' => ST_REGULATION_SERVICE_VERSION,
        'tool_id' => ST_REGULATION_TOOL_ID,
        'tool_version' => ST_REGULATION_TOOL_VERSION,
        'result' => [
            'query' => $query,
            'filters' => ['jurisdiction' => 'ES', 'document_id' => $documentFilter ?: null, 'domain' => $domainFilter ?: null, 'exact_phrase' => $exactPhrase],
            'match_mode' => $matchMode,
            'candidate_pages' => count($seen),
            'returned' => count($items),
            'items' => $items,
            'facets' => [
                'documents' => array_map(static fn(string $id, int $count): array => ['id' => $id, 'count' => $count], array_keys($facets['documents']), array_values($facets['documents'])),
                'domains' => array_map(static fn(string $id, int $count): array => ['id' => $id, 'count' => $count], array_keys($facets['domains']), array_values($facets['domains'])),
            ],
            'catalog' => ['jurisdiction' => (string) ($catalog['jurisdiction'] ?? 'ES'), 'verified_at' => $catalog['verified_at'] ?? null, 'document_count' => count($catalog['documents'] ?? [])],
        ],
        'confidence' => $matchMode === 'exact' ? 0.98 : ($matchMode === 'all_terms' ? 0.9 : ($matchMode === 'related' ? 0.6 : 0)),
        'source_ids' => $sourceIds,
        'warnings' => $warnings,
        'usage' => ['billing_tier' => 'free_preview', 'billable_units' => 0, 'cache_status' => 'not_applicable', 'latency_ms' => $latencyMs],
    ];
}

function st_regulations_record_search(string $requestId, string $clientHash, array $input, string $query, string $documentFilter, string $domainFilter, int $resultCount, string $topDocument, string $matchMode, int $latencyMs): void
{
    try {
        st_regulations_ensure_schema();
        $statement = st_db()->prepare('INSERT INTO st_regulation_search_events (request_id, client_hash, client_type, query_hash, query_sample, document_filter, domain_filter, result_count, top_document_id, match_mode, latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
        $statement->execute([
            $requestId, $clientHash, st_regulation_client_type($input), hash('sha256', st_regulation_normalize($query)),
            st_regulation_query_sample($query), $documentFilter ?: null, $domainFilter ?: null, $resultCount,
            $topDocument ?: null, $matchMode, $latencyMs,
        ]);
        if (random_int(1, 100) === 1) st_db()->exec('DELETE FROM st_regulation_search_events WHERE created_at < DATE_SUB(NOW(), INTERVAL 180 DAY)');
    } catch (Throwable $error) {
        error_log('Super Tecnico regulation analytics: ' . $error->getMessage());
    }
}

function st_regulations_record_open(array $input, string $clientHash): array
{
    $requestId = strtolower(trim((string) ($input['request_id'] ?? '')));
    if (preg_match('/^[a-f0-9]{32}$/', $requestId) !== 1) st_json(['ok' => false, 'error' => 'invalid_request_id'], 422);
    st_regulations_ensure_schema();
    $statement = st_db()->prepare('UPDATE st_regulation_search_events SET opened_count = LEAST(65535, opened_count + 1) WHERE request_id = ? AND client_hash = ?');
    $statement->execute([$requestId, $clientHash]);
    return ['ok' => true, 'recorded' => $statement->rowCount() === 1];
}

function st_regulations_analytics_summary(int $days): array
{
    st_regulations_ensure_schema();
    $days = min(90, max(7, $days));
    $since = (new DateTimeImmutable('today'))->modify('-' . ($days - 1) . ' days')->format('Y-m-d');
    $pdo = st_db();
    $totalsQuery = $pdo->prepare("SELECT COUNT(*) searches, COUNT(DISTINCT client_hash) clients, SUM(client_type = 'ai') ai_searches, SUM(client_type = 'human') human_searches, SUM(result_count = 0) no_result_searches, SUM(opened_count) result_opens, AVG(latency_ms) average_latency_ms FROM st_regulation_search_events WHERE created_at >= ?");
    $totalsQuery->execute([$since . ' 00:00:00']);
    $totals = $totalsQuery->fetch() ?: [];
    $popularQuery = $pdo->prepare('SELECT query_hash, MAX(query_sample) query_sample, COUNT(*) searches, SUM(result_count = 0) no_results, SUM(opened_count) result_opens, MAX(created_at) last_seen FROM st_regulation_search_events WHERE created_at >= ? GROUP BY query_hash ORDER BY searches DESC, last_seen DESC LIMIT 20');
    $popularQuery->execute([$since . ' 00:00:00']);
    $popular = array_map(static fn(array $row): array => [
        'query' => (string) ($row['query_sample'] ?? ''), 'searches' => (int) $row['searches'], 'no_results' => (int) $row['no_results'],
        'result_opens' => (int) $row['result_opens'], 'last_seen' => (string) $row['last_seen'],
    ], $popularQuery->fetchAll());
    $documentsQuery = $pdo->prepare('SELECT top_document_id document_id, COUNT(*) appearances FROM st_regulation_search_events WHERE created_at >= ? AND top_document_id IS NOT NULL GROUP BY top_document_id ORDER BY appearances DESC LIMIT 12');
    $documentsQuery->execute([$since . ' 00:00:00']);
    $documents = array_map(static fn(array $row): array => ['document_id' => (string) $row['document_id'], 'appearances' => (int) $row['appearances']], $documentsQuery->fetchAll());
    return [
        'period_days' => $days,
        'totals' => [
            'searches' => (int) ($totals['searches'] ?? 0), 'clients' => (int) ($totals['clients'] ?? 0),
            'ai_searches' => (int) ($totals['ai_searches'] ?? 0), 'human_searches' => (int) ($totals['human_searches'] ?? 0),
            'no_result_searches' => (int) ($totals['no_result_searches'] ?? 0), 'result_opens' => (int) ($totals['result_opens'] ?? 0),
            'average_latency_ms' => (int) round((float) ($totals['average_latency_ms'] ?? 0)),
        ],
        'popular_queries' => $popular,
        'top_documents' => $documents,
        'privacy' => 'No se guardan direcciones IP. Los identificadores son seudónimos y las consultas eliminan correos, enlaces y números largos; se conservan como máximo 180 días.',
    ];
}
