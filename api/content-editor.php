<?php
declare(strict_types=1);

function st_content_overrides_ensure_schema(): void
{
    static $ready = false;
    if ($ready) return;
    st_db()->exec(
        "CREATE TABLE IF NOT EXISTS st_content_overrides (
            content_key VARCHAR(120) NOT NULL,
            value_text TEXT NOT NULL,
            updated_by VARCHAR(40) NOT NULL DEFAULT 'Administrador',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (content_key),
            KEY idx_content_overrides_updated (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
    );
    $ready = true;
}

function st_content_key(array $body): string
{
    $key = trim((string) ($body['content_key'] ?? ''));
    if (preg_match('/^[a-z][a-z0-9._-]{1,119}$/', $key) !== 1) {
        st_json(['ok' => false, 'error' => 'invalid_content_key'], 422);
    }
    return $key;
}

function st_content_overrides_public(): array
{
    st_content_overrides_ensure_schema();
    $items = [];
    $updatedAt = null;
    $statement = st_db()->query(
        'SELECT content_key, value_text, updated_at FROM st_content_overrides ORDER BY content_key'
    );
    foreach ($statement->fetchAll() as $row) {
        $items[(string) $row['content_key']] = (string) $row['value_text'];
        if ($updatedAt === null || strcmp((string) $row['updated_at'], $updatedAt) > 0) {
            $updatedAt = (string) $row['updated_at'];
        }
    }
    return ['ok' => true, 'items' => $items, 'updated_at' => $updatedAt];
}

function st_content_overrides_admin(): array
{
    st_content_overrides_ensure_schema();
    $items = st_db()->query(
        'SELECT content_key, value_text, updated_by, created_at, updated_at
         FROM st_content_overrides ORDER BY content_key'
    )->fetchAll();
    return ['ok' => true, 'items' => $items, 'count' => count($items)];
}

function st_content_overrides_save(array $body): array
{
    st_content_overrides_ensure_schema();
    $key = st_content_key($body);
    $value = (string) ($body['value_text'] ?? '');
    if (mb_strlen($value) > 4000) {
        st_json(['ok' => false, 'error' => 'invalid_field', 'field' => 'value_text'], 422);
    }
    $statement = st_db()->prepare(
        "INSERT INTO st_content_overrides (content_key, value_text, updated_by)
         VALUES (?, ?, 'Administrador')
         ON DUPLICATE KEY UPDATE value_text = VALUES(value_text), updated_by = 'Administrador', updated_at = CURRENT_TIMESTAMP"
    );
    $statement->execute([$key, $value]);
    return ['ok' => true, 'content_key' => $key, 'value_text' => $value, 'saved' => true];
}

function st_content_overrides_delete(array $body): array
{
    st_content_overrides_ensure_schema();
    $key = st_content_key($body);
    $statement = st_db()->prepare('DELETE FROM st_content_overrides WHERE content_key = ?');
    $statement->execute([$key]);
    return ['ok' => true, 'content_key' => $key, 'deleted' => $statement->rowCount() === 1];
}
