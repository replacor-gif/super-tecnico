<?php
declare(strict_types=1);

function st_private_backlog_ensure_schema(): void
{
    static $ready = false;
    if ($ready) return;
    st_db()->exec(
        "CREATE TABLE IF NOT EXISTS st_private_backlog (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            item_type ENUM('idea','improvement','bug','content') NOT NULL DEFAULT 'idea',
            area VARCHAR(100) NOT NULL,
            title VARCHAR(140) NOT NULL,
            details TEXT NULL,
            priority ENUM('normal','high','urgent') NOT NULL DEFAULT 'normal',
            status ENUM('pending','in_progress','done','archived') NOT NULL DEFAULT 'pending',
            author_alias VARCHAR(40) NOT NULL DEFAULT 'Administrador',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL,
            PRIMARY KEY (id),
            KEY idx_private_backlog_status_priority (status, priority, updated_at),
            KEY idx_private_backlog_area (area, updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
    );
    $ready = true;
}

function st_private_backlog_list(array $input): array
{
    st_private_backlog_ensure_schema();
    $where = [];
    $params = [];
    $status = trim((string) ($input['status'] ?? 'active'));
    if ($status === 'active') {
        $where[] = "status <> 'archived'";
    } elseif ($status !== 'all') {
        if (!in_array($status, ['pending', 'in_progress', 'done', 'archived'], true)) {
            st_json(['ok' => false, 'error' => 'invalid_status'], 422);
        }
        $where[] = 'status = ?';
        $params[] = $status;
    }
    $area = trim((string) ($input['area'] ?? ''));
    if ($area !== '') {
        $where[] = 'area = ?';
        $params[] = mb_substr($area, 0, 100);
    }
    $query = trim((string) ($input['q'] ?? ''));
    if ($query !== '') {
        $where[] = '(title LIKE ? OR details LIKE ? OR area LIKE ?)';
        $like = '%' . mb_substr($query, 0, 120) . '%';
        array_push($params, $like, $like, $like);
    }
    $whereSql = $where ? 'WHERE ' . implode(' AND ', $where) : '';
    $stmt = st_db()->prepare(
        "SELECT id, item_type, area, title, details, priority, status, author_alias,
                created_at, updated_at, completed_at
         FROM st_private_backlog
         $whereSql
         ORDER BY FIELD(status, 'in_progress', 'pending', 'done', 'archived'),
                  FIELD(priority, 'urgent', 'high', 'normal'), updated_at DESC, id DESC
         LIMIT 1000"
    );
    $stmt->execute($params);
    $items = $stmt->fetchAll();
    $counts = ['pending' => 0, 'in_progress' => 0, 'done' => 0, 'archived' => 0];
    foreach (st_db()->query('SELECT status, COUNT(*) AS total FROM st_private_backlog GROUP BY status')->fetchAll() as $row) {
        $counts[(string) $row['status']] = (int) $row['total'];
    }
    return [
        'ok' => true,
        'items' => $items,
        'counts' => $counts,
        'updated_at' => $items[0]['updated_at'] ?? null,
        'privacy' => 'private_owner_backlog',
    ];
}

function st_private_backlog_create(array $body): array
{
    st_private_backlog_ensure_schema();
    $type = (string) ($body['item_type'] ?? 'idea');
    $priority = (string) ($body['priority'] ?? 'normal');
    if (!in_array($type, ['idea', 'improvement', 'bug', 'content'], true)) {
        st_json(['ok' => false, 'error' => 'invalid_type'], 422);
    }
    if (!in_array($priority, ['normal', 'high', 'urgent'], true)) {
        st_json(['ok' => false, 'error' => 'invalid_priority'], 422);
    }
    $area = st_text($body, 'area', 2, 100);
    $title = st_text($body, 'title', 3, 140);
    $details = st_text($body, 'details', 0, 5000, false);
    $author = trim((string) ($body['author_alias'] ?? 'Administrador'));
    if ($author === '') $author = 'Administrador';
    if (mb_strlen($author) > 40) st_json(['ok' => false, 'error' => 'invalid_field', 'field' => 'author_alias'], 422);
    $stmt = st_db()->prepare(
        "INSERT INTO st_private_backlog (item_type, area, title, details, priority, author_alias)
         VALUES (?, ?, ?, NULLIF(?, ''), ?, ?)"
    );
    $stmt->execute([$type, $area, $title, $details, $priority, $author]);
    return ['ok' => true, 'id' => (int) st_db()->lastInsertId(), 'status' => 'pending'];
}

function st_private_backlog_update(array $body): array
{
    st_private_backlog_ensure_schema();
    $id = filter_var($body['id'] ?? null, FILTER_VALIDATE_INT);
    if (!$id) st_json(['ok' => false, 'error' => 'invalid_id'], 422);
    $status = (string) ($body['status'] ?? '');
    $priority = (string) ($body['priority'] ?? '');
    $type = (string) ($body['item_type'] ?? '');
    if (!in_array($status, ['pending', 'in_progress', 'done', 'archived'], true)) {
        st_json(['ok' => false, 'error' => 'invalid_status'], 422);
    }
    if (!in_array($priority, ['normal', 'high', 'urgent'], true)) {
        st_json(['ok' => false, 'error' => 'invalid_priority'], 422);
    }
    if (!in_array($type, ['idea', 'improvement', 'bug', 'content'], true)) {
        st_json(['ok' => false, 'error' => 'invalid_type'], 422);
    }
    $area = st_text($body, 'area', 2, 100);
    $title = st_text($body, 'title', 3, 140);
    $details = st_text($body, 'details', 0, 5000, false);
    $stmt = st_db()->prepare(
        "UPDATE st_private_backlog
         SET item_type = ?, area = ?, title = ?, details = NULLIF(?, ''), priority = ?, status = ?,
             completed_at = IF(? = 'done', COALESCE(completed_at, NOW()), NULL)
         WHERE id = ?"
    );
    $stmt->execute([$type, $area, $title, $details, $priority, $status, $status, $id]);
    if ($stmt->rowCount() === 0) {
        $exists = st_db()->prepare('SELECT id FROM st_private_backlog WHERE id = ?');
        $exists->execute([$id]);
        if (!$exists->fetchColumn()) st_json(['ok' => false, 'error' => 'not_found'], 404);
    }
    return ['ok' => true, 'id' => (int) $id, 'status' => $status];
}
