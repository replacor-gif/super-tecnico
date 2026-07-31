<?php
declare(strict_types=1);

$ST_CONFIG = require __DIR__ . '/config.php';

function st_json(array $data, int $status = 200): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function st_config(string $key): mixed
{
    global $ST_CONFIG;
    return $ST_CONFIG[$key] ?? null;
}

function st_origin_headers(): bool
{
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    if ($origin === '') {
        return true;
    }
    $self = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' ? 'https' : 'http') . '://' . ($_SERVER['HTTP_HOST'] ?? '');
    $allowed = array_filter(array_map('trim', explode(',', (string) st_config('allowed_origins'))));
    if ($origin === $self || in_array($origin, $allowed, true)) {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Access-Control-Allow-Credentials: true');
        header('Vary: Origin');
        header('Access-Control-Allow-Headers: Content-Type, X-ST-Client, X-CSRF-Token');
        header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
        return true;
    }
    return false;
}

$stOriginAllowed = st_origin_headers();
if (!$stOriginAllowed && ($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    st_json(['ok' => false, 'error' => 'origin_not_allowed'], 403);
}
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

function st_db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }
    foreach (['db_host', 'db_name', 'db_user', 'db_password', 'app_secret'] as $required) {
        if (!st_config($required)) {
            st_json(['ok' => false, 'error' => 'server_not_configured'], 503);
        }
    }
    $dsn = sprintf('mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4', st_config('db_host'), st_config('db_port'), st_config('db_name'));
    try {
        $pdo = new PDO($dsn, (string) st_config('db_user'), (string) st_config('db_password'), [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
    } catch (Throwable $error) {
        error_log('Super Tecnico DB: ' . $error->getMessage());
        st_json(['ok' => false, 'error' => 'database_unavailable'], 503);
    }
    return $pdo;
}

function st_body(): array
{
    $raw = file_get_contents('php://input');
    $data = json_decode($raw ?: '{}', true);
    if (!is_array($data)) {
        st_json(['ok' => false, 'error' => 'invalid_json'], 400);
    }
    return $data;
}

function st_text(array $data, string $key, int $min, int $max, bool $required = true): string
{
    $value = trim((string) ($data[$key] ?? ''));
    $length = mb_strlen($value);
    if (($required && $length < $min) || $length > $max) {
        st_json(['ok' => false, 'error' => 'invalid_field', 'field' => $key], 422);
    }
    return $value;
}

function st_normalize(string $value): string
{
    $value = mb_strtoupper(trim($value), 'UTF-8');
    $transliterated = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value);
    $value = $transliterated === false ? $value : $transliterated;
    return preg_replace('/[^A-Z0-9]+/', '', $value) ?? '';
}

function st_client_hash(array $body = []): string
{
    $client = substr((string) ($_SERVER['HTTP_X_ST_CLIENT'] ?? ($body['client_token'] ?? '')), 0, 100);
    $ip = (string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown');
    return hash_hmac('sha256', $client . '|' . $ip, (string) st_config('app_secret'));
}

function st_rate_limit(string $action, string $clientHash, int $limit = 8, int $windowSeconds = 3600): void
{
    $pdo = st_db();
    $pdo->beginTransaction();
    try {
        $query = $pdo->prepare('SELECT window_start, hits FROM st_rate_limits WHERE action_key = ? AND client_hash = ? FOR UPDATE');
        $query->execute([$action, $clientHash]);
        $row = $query->fetch();
        $expired = !$row || strtotime((string) $row['window_start']) < time() - $windowSeconds;
        if ($expired) {
            $upsert = $pdo->prepare('INSERT INTO st_rate_limits (action_key, client_hash, window_start, hits) VALUES (?, ?, NOW(), 1) ON DUPLICATE KEY UPDATE window_start = NOW(), hits = 1');
            $upsert->execute([$action, $clientHash]);
        } elseif ((int) $row['hits'] >= $limit) {
            $pdo->rollBack();
            st_json(['ok' => false, 'error' => 'rate_limited'], 429);
        } else {
            $update = $pdo->prepare('UPDATE st_rate_limits SET hits = hits + 1 WHERE action_key = ? AND client_hash = ?');
            $update->execute([$action, $clientHash]);
        }
        $pdo->commit();
    } catch (Throwable $error) {
        if ($pdo->inTransaction()) {
            $pdo->rollBack();
        }
        throw $error;
    }
}

function st_verify_turnstile(array $body): void
{
    $secret = (string) st_config('turnstile_secret');
    if ($secret === '' && !st_config('require_turnstile')) {
        return;
    }
    $token = (string) ($body['turnstile_token'] ?? '');
    if ($secret === '' || $token === '') {
        st_json(['ok' => false, 'error' => 'verification_required'], 403);
    }
    $payload = http_build_query(['secret' => $secret, 'response' => $token, 'remoteip' => $_SERVER['REMOTE_ADDR'] ?? '']);
    $context = stream_context_create(['http' => ['method' => 'POST', 'header' => "Content-Type: application/x-www-form-urlencoded\r\n", 'content' => $payload, 'timeout' => 8]]);
    $response = @file_get_contents('https://challenges.cloudflare.com/turnstile/v0/siteverify', false, $context);
    $result = json_decode($response ?: '{}', true);
    if (!is_array($result) || ($result['success'] ?? false) !== true) {
        st_json(['ok' => false, 'error' => 'verification_failed'], 403);
    }
}

function st_start_admin_session(): void
{
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_name('st_admin');
        session_set_cookie_params(['httponly' => true, 'secure' => true, 'samesite' => 'Strict', 'path' => '/']);
        session_start();
    }
}

function st_require_admin(bool $csrf = false): void
{
    st_start_admin_session();
    if (($_SESSION['st_admin'] ?? false) !== true) {
        st_json(['ok' => false, 'error' => 'unauthorized'], 401);
    }
    if ($csrf && !hash_equals((string) ($_SESSION['csrf'] ?? ''), (string) ($_SERVER['HTTP_X_CSRF_TOKEN'] ?? ''))) {
        st_json(['ok' => false, 'error' => 'invalid_csrf'], 403);
    }
}
