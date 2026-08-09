<?php
declare(strict_types=1);

function st_electroia_pin_hash(): string
{
    return trim((string) st_config('electroia_pin_hash'));
}

function st_electroia_start_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) return;
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || ((string) ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https');
    session_name('st_electroia');
    session_set_cookie_params([
        'lifetime' => 86400,
        'path' => '/',
        'secure' => $secure,
        'httponly' => true,
        'samesite' => 'Strict',
    ]);
    session_start();
}

function st_electroia_is_unlocked(): bool
{
    if (st_electroia_pin_hash() === '') return true;
    st_electroia_start_session();
    return !empty($_SESSION['st_electroia_unlocked']);
}

function st_electroia_access_status(): array
{
    $required = st_electroia_pin_hash() !== '';
    return ['ok' => true, 'required' => $required, 'unlocked' => !$required || st_electroia_is_unlocked()];
}

function st_electroia_unlock(string $pin): bool
{
    $hash = st_electroia_pin_hash();
    if ($hash !== '' && !password_verify($pin, $hash)) return false;
    st_electroia_start_session();
    session_regenerate_id(true);
    $_SESSION['st_electroia_unlocked'] = true;
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
