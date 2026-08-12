<?php
declare(strict_types=1);

function st_rating_ensure_schema(): void
{
    static $ready = false;
    if ($ready) return;
    $pdo = st_db();
    $pdo->exec("CREATE TABLE IF NOT EXISTS st_page_ratings (
      page_key VARCHAR(64) NOT NULL,
      likes BIGINT UNSIGNED NOT NULL DEFAULT 0,
      dislikes BIGINT UNSIGNED NOT NULL DEFAULT 0,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (page_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $pdo->exec("CREATE TABLE IF NOT EXISTS st_page_rating_votes (
      page_key VARCHAR(64) NOT NULL,
      client_hash CHAR(64) NOT NULL,
      vote ENUM('like','dislike') NOT NULL,
      feedback VARCHAR(600) NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (page_key, client_hash),
      KEY idx_rating_feedback (vote, updated_at),
      CONSTRAINT fk_rating_page FOREIGN KEY (page_key) REFERENCES st_page_ratings(page_key) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $ready = true;
}

function st_rating_validate_page(string $page): string
{
    if (preg_match('/^[a-z0-9][a-z0-9-]{0,63}$/', $page) !== 1) {
        st_json(['ok' => false, 'error' => 'invalid_page'], 422);
    }
    return $page;
}

function st_rating_summary(string $page, array $body = []): array
{
    st_rating_ensure_schema();
    $page = st_rating_validate_page($page);
    $pdo = st_db();
    $counter = $pdo->prepare('SELECT likes, dislikes FROM st_page_ratings WHERE page_key = ?');
    $counter->execute([$page]);
    $counts = $counter->fetch() ?: ['likes' => 0, 'dislikes' => 0];
    $vote = $pdo->prepare('SELECT vote FROM st_page_rating_votes WHERE page_key = ? AND client_hash = ?');
    $vote->execute([$page, st_client_hash($body)]);
    return [
        'ok' => true,
        'page' => $page,
        'likes' => (int) $counts['likes'],
        'dislikes' => (int) $counts['dislikes'],
        'user_vote' => $vote->fetchColumn() ?: null,
    ];
}

function st_rating_vote(string $page, string $vote, string $feedback, array $body): array
{
    st_rating_ensure_schema();
    $page = st_rating_validate_page($page);
    if (!in_array($vote, ['like', 'dislike'], true)) {
        st_json(['ok' => false, 'error' => 'invalid_vote'], 422);
    }
    $feedback = trim($feedback);
    if (mb_strlen($feedback) > 600) {
        st_json(['ok' => false, 'error' => 'invalid_feedback'], 422);
    }
    if ($vote === 'like') $feedback = '';
    $clientHash = st_client_hash($body);
    $pdo = st_db();
    $pdo->beginTransaction();
    try {
        $pdo->prepare('INSERT IGNORE INTO st_page_ratings (page_key, likes, dislikes) VALUES (?, 0, 0)')->execute([$page]);
        $existing = $pdo->prepare('SELECT vote FROM st_page_rating_votes WHERE page_key = ? AND client_hash = ? FOR UPDATE');
        $existing->execute([$page, $clientHash]);
        $previous = $existing->fetchColumn();
        if (!$previous) {
            $insert = $pdo->prepare("INSERT INTO st_page_rating_votes (page_key, client_hash, vote, feedback) VALUES (?, ?, ?, NULLIF(?, ''))");
            $insert->execute([$page, $clientHash, $vote, $feedback]);
            $column = $vote === 'like' ? 'likes' : 'dislikes';
            $pdo->prepare("UPDATE st_page_ratings SET {$column} = {$column} + 1 WHERE page_key = ?")->execute([$page]);
        } elseif ($previous !== $vote) {
            $update = $pdo->prepare("UPDATE st_page_rating_votes SET vote = ?, feedback = NULLIF(?, ''), updated_at = CURRENT_TIMESTAMP WHERE page_key = ? AND client_hash = ?");
            $update->execute([$vote, $feedback, $page, $clientHash]);
            $increase = $vote === 'like' ? 'likes' : 'dislikes';
            $decrease = $vote === 'like' ? 'dislikes' : 'likes';
            $pdo->prepare("UPDATE st_page_ratings SET {$increase} = {$increase} + 1, {$decrease} = GREATEST(0, {$decrease} - 1) WHERE page_key = ?")->execute([$page]);
        } elseif ($vote === 'dislike' && $feedback !== '') {
            $update = $pdo->prepare('UPDATE st_page_rating_votes SET feedback = ?, updated_at = CURRENT_TIMESTAMP WHERE page_key = ? AND client_hash = ?');
            $update->execute([$feedback, $page, $clientHash]);
        }
        $counter = $pdo->prepare('SELECT likes, dislikes FROM st_page_ratings WHERE page_key = ?');
        $counter->execute([$page]);
        $counts = $counter->fetch() ?: ['likes' => 0, 'dislikes' => 0];
        $pdo->commit();
        return [
            'ok' => true,
            'page' => $page,
            'likes' => (int) $counts['likes'],
            'dislikes' => (int) $counts['dislikes'],
            'user_vote' => $vote,
            'feedback_saved' => $feedback !== '',
        ];
    } catch (Throwable $error) {
        if ($pdo->inTransaction()) $pdo->rollBack();
        throw $error;
    }
}

function st_rating_admin_summary(): array
{
    st_rating_ensure_schema();
    $pdo = st_db();
    $pages = array_map(static fn(array $row): array => [
        'page_key' => (string) $row['page_key'],
        'likes' => (int) $row['likes'],
        'dislikes' => (int) $row['dislikes'],
        'updated_at' => (string) $row['updated_at'],
    ], $pdo->query('SELECT page_key, likes, dislikes, updated_at FROM st_page_ratings ORDER BY (likes + dislikes) DESC, page_key')->fetchAll());
    $feedback = array_map(static fn(array $row): array => [
        'page_key' => (string) $row['page_key'],
        'feedback' => (string) $row['feedback'],
        'updated_at' => (string) $row['updated_at'],
    ], $pdo->query("SELECT page_key, feedback, updated_at FROM st_page_rating_votes WHERE vote = 'dislike' AND feedback IS NOT NULL AND feedback <> '' ORDER BY updated_at DESC LIMIT 100")->fetchAll());
    return [
        'likes' => array_sum(array_column($pages, 'likes')),
        'dislikes' => array_sum(array_column($pages, 'dislikes')),
        'pages' => $pages,
        'feedback' => $feedback,
    ];
}
