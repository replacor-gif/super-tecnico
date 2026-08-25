<?php
declare(strict_types=1);

function st_env(string $name, string $default = ''): string
{
    $value = getenv($name);
    return $value === false ? $default : trim((string) $value);
}

$runtimeFile = __DIR__ . '/config.runtime.php';
$runtime = is_file($runtimeFile) ? require $runtimeFile : [];

return array_merge([
    'db_host' => st_env('IONOS_DB_HOST', st_env('DB_HOST')),
    'db_port' => st_env('DB_PORT', '3306'),
    'db_name' => st_env('IONOS_DB_NAME', st_env('DB_NAME')),
    'db_user' => st_env('IONOS_DB_USERNAME', st_env('DB_USER')),
    'db_password' => st_env('IONOS_DB_PASSWORD', st_env('DB_PASSWORD')),
    'app_secret' => st_env('ST_APP_SECRET'),
    'admin_password_hash' => st_env('ST_ADMIN_PASSWORD_HASH'),
    'allowed_origins' => st_env('ST_ALLOWED_ORIGINS'),
    'turnstile_secret' => st_env('ST_TURNSTILE_SECRET'),
    'require_turnstile' => st_env('ST_REQUIRE_TURNSTILE', '0') === '1',
    'electroia_pin_hash' => st_env('ST_ELECTROIA_PIN_HASH'),
    'electroia_public_render_enabled' => st_env('ST_ELECTROIA_PUBLIC_RENDER_ENABLED', '0') === '1',
    'electroia_public_api_key_hashes' => st_env('ST_ELECTROIA_PUBLIC_API_KEY_HASHES'),
    'electroia_emergency_stop' => st_env('ST_ELECTROIA_EMERGENCY_STOP', '1') === '1',
], is_array($runtime) ? $runtime : []);
