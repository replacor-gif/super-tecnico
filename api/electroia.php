<?php
declare(strict_types=1);

function st_electroia_pin_hash(): string
{
    $hash = trim((string) st_config('electroia_pin_hash'));
    return str_starts_with($hash, '$2y$') || str_starts_with($hash, '$argon2') ? $hash : '';
}

function st_electroia_access_cookie_name(): string
{
    return 'st_electroia_access';
}

function st_electroia_access_secret(): string
{
    return hash('sha256', 'electroia-access|' . (string) st_config('app_secret') . '|' . st_electroia_pin_hash());
}

function st_electroia_base64url_encode(string $value): string
{
    return rtrim(strtr(base64_encode($value), '+/', '-_'), '=');
}

function st_electroia_base64url_decode(string $value): string|false
{
    $padding = (4 - strlen($value) % 4) % 4;
    return base64_decode(strtr($value, '-_', '+/') . str_repeat('=', $padding), true);
}

function st_electroia_access_cookie_is_valid(): bool
{
    $encoded = (string) ($_COOKIE[st_electroia_access_cookie_name()] ?? '');
    if ($encoded === '' || strlen($encoded) > 256) return false;
    $decoded = st_electroia_base64url_decode($encoded);
    if (!is_string($decoded)) return false;
    [$expiresAt, $signature] = array_pad(explode('.', $decoded, 2), 2, '');
    if (!ctype_digit($expiresAt) || strlen($signature) !== 64) return false;
    $expiry = (int) $expiresAt;
    if ($expiry <= time() || $expiry > time() + (31 * 86400)) return false;
    $expected = hash_hmac('sha256', $expiresAt, st_electroia_access_secret());
    return hash_equals($expected, $signature);
}

function st_electroia_set_access_cookie(): void
{
    $expiresAt = time() + (30 * 86400);
    $signature = hash_hmac('sha256', (string) $expiresAt, st_electroia_access_secret());
    $token = st_electroia_base64url_encode($expiresAt . '.' . $signature);
    setcookie(st_electroia_access_cookie_name(), $token, [
        'expires' => $expiresAt,
        'path' => '/',
        'secure' => true,
        'httponly' => true,
        'samesite' => 'Strict',
    ]);
    $_COOKIE[st_electroia_access_cookie_name()] = $token;
}

function st_electroia_start_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) return;
    $lifetime = 30 * 86400;
    ini_set('session.gc_maxlifetime', (string) $lifetime);
    ini_set('session.use_strict_mode', '1');
    session_name('st_electroia');
    session_set_cookie_params([
        'lifetime' => $lifetime,
        'path' => '/',
        'secure' => true,
        'httponly' => true,
        'samesite' => 'Strict',
    ]);
    session_start();
}

function st_electroia_is_unlocked(): bool
{
    if (st_electroia_pin_hash() === '') return true;
    if (st_electroia_access_cookie_is_valid()) return true;
    st_electroia_start_session();
    $unlockedAt = (int) ($_SESSION['electroia_unlocked_at'] ?? 0);
    return ($_SESSION['electroia_unlocked'] ?? false) === true && $unlockedAt > time() - (30 * 86400);
}

function st_electroia_access_status(): array
{
    $required = st_electroia_pin_hash() !== '';
    return ['ok' => true, 'required' => $required, 'unlocked' => !$required || st_electroia_is_unlocked()];
}

function st_electroia_unlock(string $pin): bool
{
    $hash = st_electroia_pin_hash();
    if ($hash === '') return true;
    if (!password_verify($pin, $hash)) return false;
    st_electroia_start_session();
    session_regenerate_id(true);
    $_SESSION['electroia_unlocked'] = true;
    $_SESSION['electroia_unlocked_at'] = time();
    st_electroia_set_access_cookie();
    return true;
}

function st_require_electroia_access(): void
{
    if (!st_electroia_is_unlocked()) {
        st_json(['ok' => false, 'error' => 'electroia_locked'], 401);
    }
}

function st_electroia_tool_manifest(): array
{
    $path = dirname(__DIR__) . '/data/electroia/tool-manifest.json';
    $raw = is_file($path) ? file_get_contents($path) : false;
    if ($raw === false) throw new RuntimeException('electroia_manifest_unavailable');
    $manifest = json_decode($raw, true);
    if (!is_array($manifest)) throw new RuntimeException('electroia_manifest_invalid');
    return ['ok' => true, 'manifest' => $manifest];
}

function st_electroia_status(): array
{
    return [
        'ok' => true,
        'engine' => [
            'mode' => 'provider_neutral',
            'configured' => true,
            'embedded_ai_model' => false,
            'billing_required_by_electroia' => false,
            'interface' => ['browser', 'cli', 'mcp'],
        ],
    ];
}

function st_electroia_read_json_file(string $relativePath): array
{
    $path = dirname(__DIR__) . '/' . ltrim($relativePath, '/');
    $raw = is_file($path) ? file_get_contents($path) : false;
    if ($raw === false) throw new RuntimeException('electroia_public_data_unavailable');
    $data = json_decode($raw, true);
    if (!is_array($data)) throw new RuntimeException('electroia_public_data_invalid');
    return $data;
}

function st_electroia_usage_ensure_schema(): void
{
    static $ready = false;
    if ($ready) return;
    st_db()->exec("CREATE TABLE IF NOT EXISTS st_electroia_usage_events (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      action_name ENUM('public_status','symbol_search') NOT NULL,
      client_hash CHAR(64) NOT NULL,
      client_type ENUM('human','ai','software','unknown') NOT NULL DEFAULT 'unknown',
      client_detection ENUM('declared','user_agent','fallback') NOT NULL DEFAULT 'fallback',
      query_hash CHAR(64) NULL,
      query_sample VARCHAR(120) NULL,
      result_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
      latency_ms INT UNSIGNED NOT NULL DEFAULT 0,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      KEY idx_electroia_usage_date (created_at),
      KEY idx_electroia_usage_action (action_name, created_at),
      KEY idx_electroia_usage_client (client_type, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $ready = true;
}

function st_electroia_query_sample(string $value): string
{
    $sample = preg_replace('/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/iu', '[correo]', $value) ?? $value;
    $sample = preg_replace('~https?://\S+|www\.\S+~iu', '[enlace]', $sample) ?? $sample;
    $sample = preg_replace('/(?<!\d)(?:\+?\d[\s().-]*){7,}(?!\d)/u', '[numero]', $sample) ?? $sample;
    return mb_substr(trim(preg_replace('/\s+/u', ' ', $sample) ?? $sample), 0, 120, 'UTF-8');
}

function st_electroia_record_usage(string $action, string $clientHash, array $input, int $resultCount, int $latencyMs): void
{
    try {
        st_electroia_usage_ensure_schema();
        $classification = st_client_classification($input);
        $query = trim((string) ($input['q'] ?? ''));
        $statement = st_db()->prepare("INSERT INTO st_electroia_usage_events (action_name, client_hash, client_type, client_detection, query_hash, query_sample, result_count, latency_ms) VALUES (?, ?, ?, ?, NULLIF(?, ''), NULLIF(?, ''), ?, ?)");
        $statement->execute([
            $action,
            $clientHash,
            $classification['type'],
            $classification['detection'],
            $query === '' ? '' : hash('sha256', st_electroia_search_normalize($query)),
            $query === '' ? '' : st_electroia_query_sample($query),
            max(0, $resultCount),
            max(0, $latencyMs),
        ]);
        if (random_int(1, 100) === 1) st_db()->exec('DELETE FROM st_electroia_usage_events WHERE created_at < DATE_SUB(NOW(), INTERVAL 180 DAY)');
    } catch (Throwable $error) {
        error_log('ElectroIA usage analytics: ' . $error->getMessage());
    }
}

function st_electroia_analytics_summary(int $days): array
{
    st_electroia_usage_ensure_schema();
    $days = min(90, max(7, $days));
    $since = (new DateTimeImmutable('today'))->modify('-' . ($days - 1) . ' days')->format('Y-m-d 00:00:00');
    $query = st_db()->prepare("SELECT COUNT(*) api_calls, COUNT(DISTINCT client_hash) clients, SUM(action_name = 'public_status') status_requests, SUM(action_name = 'symbol_search') symbol_searches, SUM(client_type = 'human') human_calls, SUM(client_type = 'ai') ai_calls, SUM(client_type = 'software') software_calls, SUM(client_type = 'unknown') unknown_calls, SUM(client_type = 'ai' AND client_detection = 'declared') declared_ai_calls, SUM(client_type = 'ai' AND client_detection = 'user_agent') detected_ai_calls, SUM(result_count = 0 AND action_name = 'symbol_search') empty_searches, AVG(latency_ms) average_latency_ms FROM st_electroia_usage_events WHERE created_at >= ?");
    $query->execute([$since]);
    $totals = $query->fetch() ?: [];
    $popularQuery = st_db()->prepare("SELECT query_hash, MAX(query_sample) query_sample, COUNT(*) searches, SUM(result_count = 0) empty_searches, MAX(created_at) last_seen FROM st_electroia_usage_events WHERE created_at >= ? AND action_name = 'symbol_search' AND query_hash IS NOT NULL GROUP BY query_hash ORDER BY searches DESC, last_seen DESC LIMIT 15");
    $popularQuery->execute([$since]);
    return [
        'period_days' => $days,
        'totals' => [
            'api_calls' => (int) ($totals['api_calls'] ?? 0),
            'clients' => (int) ($totals['clients'] ?? 0),
            'status_requests' => (int) ($totals['status_requests'] ?? 0),
            'symbol_searches' => (int) ($totals['symbol_searches'] ?? 0),
            'human_calls' => (int) ($totals['human_calls'] ?? 0),
            'ai_calls' => (int) ($totals['ai_calls'] ?? 0),
            'software_calls' => (int) ($totals['software_calls'] ?? 0),
            'unknown_calls' => (int) ($totals['unknown_calls'] ?? 0),
            'declared_ai_calls' => (int) ($totals['declared_ai_calls'] ?? 0),
            'detected_ai_calls' => (int) ($totals['detected_ai_calls'] ?? 0),
            'empty_searches' => (int) ($totals['empty_searches'] ?? 0),
            'average_latency_ms' => (int) round((float) ($totals['average_latency_ms'] ?? 0)),
        ],
        'popular_symbol_queries' => array_map(static fn(array $row): array => [
            'query' => (string) ($row['query_sample'] ?? ''),
            'searches' => (int) ($row['searches'] ?? 0),
            'empty_searches' => (int) ($row['empty_searches'] ?? 0),
            'last_seen' => (string) ($row['last_seen'] ?? ''),
        ], $popularQuery->fetchAll()),
        'attribution' => 'La atribución IA exige X-ST-Client-Type: ai o una identificación reconocible. Software y clientes desconocidos se separan para evitar inflar el dato.',
        'scope' => 'Se registran llamadas a la API de estado y búsqueda de símbolos. Las lecturas de archivos estáticos no pueden contabilizarse con fiabilidad.',
    ];
}

function st_electroia_public_status(): array
{
    $release = st_electroia_read_json_file('data/electroia/public-release-readiness.json');
    $manifest = st_electroia_read_json_file('data/electroia/tool-manifest.json');
    $executionPolicy = st_electroia_read_json_file('data/electroia/public-execution-policy.json');
    $summary = is_array($release['summary'] ?? null) ? $release['summary'] : [];
    $capabilities = is_array($manifest['capabilities'] ?? null) ? $manifest['capabilities'] : [];
    return [
        'ok' => true,
        'service' => 'electroia-public-discovery',
        'release_stage' => (string) ($release['release_stage'] ?? 'unknown'),
        'public_execution_available' => false,
        'private_preview_available' => ($summary['private_human_preview_ready'] ?? false) === true,
        'provider_neutral' => true,
        'embedded_ai_model' => false,
        'engine_version' => (string) ($manifest['diagram_engine_version'] ?? ''),
        'document_kinds' => array_values($capabilities['document_kinds'] ?? []),
        'standard_profiles' => array_values($capabilities['standard_profiles'] ?? []),
        'quality' => [
            'reviewed_symbols' => (int) ($summary['reviewed_symbols'] ?? 0),
            'professional_examples' => (int) ($summary['professional_examples'] ?? 0),
            'component_overlaps' => (int) ($summary['component_overlaps'] ?? 0),
            'wire_component_conflicts' => (int) ($summary['wire_component_conflicts'] ?? 0),
            'dangerous_warnings' => (int) ($summary['dangerous_warnings'] ?? 0),
        ],
        'field_validation' => [
            'recorder_ready' => ($summary['field_validation_recorder_ready'] ?? false) === true,
            'target' => (int) ($summary['field_validation_target'] ?? 20),
            'progress_is_private' => true,
        ],
        'execution_guardrails' => [
            'policy_ready' => ($summary['public_execution_policy_ready'] ?? false) === true,
            'enabled' => false,
            'api_key_required' => ($executionPolicy['authentication']['required'] ?? false) === true,
            'anonymous_execution_allowed' => false,
            'limits' => is_array($executionPolicy['limits'] ?? null) ? $executionPolicy['limits'] : [],
        ],
        'responsibility_boundary' => [
            'calling_ai' => 'Interpreta, calcula, selecciona componentes y entrega un documento estructurado.',
            'electroia' => 'Valida símbolos, terminales y redes y genera el plano determinista.',
        ],
        'ai_bridge' => [
            'contract_ready' => true,
            'private_json_import_ready' => true,
            'local_mcp_ready' => true,
            'internal_provider_configured' => false,
            'contract' => 'data/electroia/ai-bridge.json',
        ],
        'notice' => 'La consulta pública es informativa. El renderizado remoto continúa privado hasta completar validación de campo y límites operativos.',
    ];
}

function st_electroia_search_normalize(string $value): string
{
    $value = strtr(trim($value), [
        'á' => 'a', 'é' => 'e', 'í' => 'i', 'ó' => 'o', 'ú' => 'u', 'ü' => 'u', 'ñ' => 'n',
        'Á' => 'A', 'É' => 'E', 'Í' => 'I', 'Ó' => 'O', 'Ú' => 'U', 'Ü' => 'U', 'Ñ' => 'N',
    ]);
    $transliterated = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value);
    $value = $transliterated === false ? $value : $transliterated;
    $value = strtoupper($value);
    return trim(preg_replace('/[^A-Z0-9]+/', ' ', $value) ?? '');
}

function st_electroia_public_symbol_search(array $input): array
{
    $query = trim((string) ($input['q'] ?? ''));
    if (strlen($query) < 2 || strlen($query) > 80) {
        st_json(['ok' => false, 'error' => 'invalid_query'], 422);
    }
    $limit = min(12, max(1, (int) ($input['limit'] ?? 8)));
    $category = st_electroia_search_normalize(trim((string) ($input['category'] ?? '')));
    if (strlen($category) > 80) st_json(['ok' => false, 'error' => 'invalid_category'], 422);
    $normalizedQuery = st_electroia_search_normalize($query);
    $terms = array_values(array_filter(explode(' ', $normalizedQuery), static fn(string $term): bool => strlen($term) > 1));
    if (!$terms) st_json(['ok' => false, 'error' => 'invalid_query'], 422);

    $library = st_electroia_read_json_file('data/electroia/symbol-library.json');
    $matches = [];
    foreach (($library['symbols'] ?? []) as $symbol) {
        if (!is_array($symbol) || empty($symbol['catalog_id']) || ($symbol['review_status'] ?? '') !== 'engine_reviewed') continue;
        $symbolCategory = st_electroia_search_normalize((string) ($symbol['category'] ?? ''));
        if ($category !== '' && !str_contains($symbolCategory, $category)) continue;
        $id = (string) ($symbol['id'] ?? '');
        $name = (string) ($symbol['name'] ?? '');
        $haystack = st_electroia_search_normalize(implode(' ', [
            $id,
            $name,
            (string) ($symbol['category'] ?? ''),
            (string) ($symbol['subcategory'] ?? ''),
            (string) ($symbol['aliases'] ?? ''),
            (string) ($symbol['keywords'] ?? ''),
            (string) ($symbol['description'] ?? ''),
        ]));
        if (!array_reduce($terms, static fn(bool $found, string $term): bool => $found && str_contains($haystack, $term), true)) continue;
        $normalizedName = st_electroia_search_normalize($name);
        $score = $normalizedQuery === st_electroia_search_normalize($id) ? 1000 : 0;
        if ($normalizedQuery === $normalizedName) $score += 500;
        elseif (str_starts_with($normalizedName, $normalizedQuery)) $score += 250;
        foreach ($terms as $term) {
            if (str_contains($normalizedName, $term)) $score += 50;
            if (str_contains(st_electroia_search_normalize((string) ($symbol['aliases'] ?? '')), $term)) $score += 20;
        }
        $ports = is_array($symbol['ports'] ?? null) ? $symbol['ports'] : [];
        $matches[] = [
            'score' => $score,
            'id' => $id,
            'name' => $name,
            'category' => (string) ($symbol['category'] ?? ''),
            'subcategory' => (string) ($symbol['subcategory'] ?? ''),
            'designator' => (string) ($symbol['designator'] ?? ''),
            'terminal_names' => array_values(array_map('strval', array_keys($ports))),
            'terminal_count' => count($ports),
            'terminal_model' => (string) ($symbol['terminal_model'] ?? 'explicit'),
            'requires_exact_model' => ($symbol['requires_exact_model'] ?? false) === true,
        ];
    }
    usort($matches, static function(array $left, array $right): int {
        return ($right['score'] <=> $left['score']) ?: strnatcasecmp($left['name'], $right['name']);
    });
    $items = array_slice($matches, 0, $limit);
    foreach ($items as &$item) unset($item['score']);
    unset($item);
    return [
        'ok' => true,
        'query' => $query,
        'total' => count($matches),
        'limit' => $limit,
        'items' => $items,
        'notice' => 'Resultados limitados a símbolos públicos revisados. Los bloques funcionales con requires_exact_model=true no representan un pinout físico.',
    ];
}
