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
