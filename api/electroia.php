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
    $_SESSION['st_electroia_unlocked'] = true;
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
