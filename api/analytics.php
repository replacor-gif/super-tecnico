<?php
declare(strict_types=1);

function st_analytics_ensure_schema(): void
{
    static $ready = false;
    if ($ready) return;
    $pdo = st_db();
    $pdo->exec("CREATE TABLE IF NOT EXISTS st_page_counters (
      page_key VARCHAR(64) NOT NULL,
      views BIGINT UNSIGNED NOT NULL DEFAULT 0,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (page_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $pdo->exec("CREATE TABLE IF NOT EXISTS st_page_daily (
      page_key VARCHAR(64) NOT NULL,
      view_date DATE NOT NULL,
      views BIGINT UNSIGNED NOT NULL DEFAULT 0,
      unique_visitors BIGINT UNSIGNED NOT NULL DEFAULT 0,
      mobile_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
      tablet_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
      desktop_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
      internal_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
      external_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
      direct_views BIGINT UNSIGNED NOT NULL DEFAULT 0,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (page_key, view_date),
      KEY idx_page_daily_date (view_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $pdo->exec("CREATE TABLE IF NOT EXISTS st_page_daily_visitors (
      page_key VARCHAR(64) NOT NULL,
      view_date DATE NOT NULL,
      client_hash CHAR(64) NOT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (page_key, view_date, client_hash),
      KEY idx_daily_visitors_date (view_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
    $ready = true;
}

function st_analytics_device(): string
{
    $agent = strtolower((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''));
    if (preg_match('/ipad|tablet|kindle|silk|playbook/', $agent) === 1) return 'tablet';
    if (preg_match('/mobile|iphone|ipod|android.*mobile|windows phone/', $agent) === 1) return 'mobile';
    return 'desktop';
}

function st_analytics_source(): string
{
    $referrer = trim((string) ($_SERVER['HTTP_REFERER'] ?? ''));
    if ($referrer === '') return 'direct';
    $referrerHost = strtolower((string) parse_url($referrer, PHP_URL_HOST));
    $currentHost = strtolower(preg_replace('/:\d+$/', '', (string) ($_SERVER['HTTP_HOST'] ?? '')) ?? '');
    return $referrerHost !== '' && $referrerHost === $currentHost ? 'internal' : 'external';
}

function st_analytics_record(string $page, array $body): int
{
    st_analytics_ensure_schema();
    $pdo = st_db();
    $clientHash = st_client_hash($body);
    $device = st_analytics_device();
    $source = st_analytics_source();
    $unique = 0;
    $pdo->beginTransaction();
    try {
        $visitor = $pdo->prepare('INSERT IGNORE INTO st_page_daily_visitors (page_key, view_date, client_hash) VALUES (?, CURRENT_DATE, ?)');
        $visitor->execute([$page, $clientHash]);
        $unique = $visitor->rowCount() === 1 ? 1 : 0;

        $counter = $pdo->prepare('INSERT INTO st_page_counters (page_key, views) VALUES (?, 1) ON DUPLICATE KEY UPDATE views = views + 1');
        $counter->execute([$page]);

        $daily = $pdo->prepare(
            'INSERT INTO st_page_daily (page_key, view_date, views, unique_visitors, mobile_views, tablet_views, desktop_views, internal_views, external_views, direct_views)
             VALUES (?, CURRENT_DATE, 1, ?, ?, ?, ?, ?, ?, ?)
             ON DUPLICATE KEY UPDATE views = views + 1,
               unique_visitors = unique_visitors + VALUES(unique_visitors),
               mobile_views = mobile_views + VALUES(mobile_views),
               tablet_views = tablet_views + VALUES(tablet_views),
               desktop_views = desktop_views + VALUES(desktop_views),
               internal_views = internal_views + VALUES(internal_views),
               external_views = external_views + VALUES(external_views),
               direct_views = direct_views + VALUES(direct_views)'
        );
        $daily->execute([
            $page,
            $unique,
            $device === 'mobile' ? 1 : 0,
            $device === 'tablet' ? 1 : 0,
            $device === 'desktop' ? 1 : 0,
            $source === 'internal' ? 1 : 0,
            $source === 'external' ? 1 : 0,
            $source === 'direct' ? 1 : 0,
        ]);
        $query = $pdo->prepare('SELECT views FROM st_page_counters WHERE page_key = ?');
        $query->execute([$page]);
        $views = (int) $query->fetchColumn();
        $pdo->commit();
        return $views;
    } catch (Throwable $error) {
        if ($pdo->inTransaction()) $pdo->rollBack();
        throw $error;
    }
}

function st_analytics_summary(int $days): array
{
    st_analytics_ensure_schema();
    $days = min(90, max(7, $days));
    $pdo = st_db();
    $since = (new DateTimeImmutable('today'))->modify('-' . ($days - 1) . ' days')->format('Y-m-d');

    $pages = $pdo->prepare(
        'SELECT c.page_key, c.views AS lifetime_views, c.updated_at,
                COALESCE(SUM(d.views), 0) AS period_views,
                COALESCE(SUM(d.unique_visitors), 0) AS period_unique
         FROM st_page_counters c
         LEFT JOIN st_page_daily d ON d.page_key = c.page_key AND d.view_date >= ?
         GROUP BY c.page_key, c.views, c.updated_at
         ORDER BY period_views DESC, lifetime_views DESC, c.page_key ASC'
    );
    $pages->execute([$since]);
    $pageRows = array_map(static fn(array $row): array => [
        'page_key' => (string) $row['page_key'],
        'lifetime_views' => (int) $row['lifetime_views'],
        'period_views' => (int) $row['period_views'],
        'period_unique' => (int) $row['period_unique'],
        'updated_at' => (string) $row['updated_at'],
    ], $pages->fetchAll());

    $dailyQuery = $pdo->prepare(
        'SELECT view_date, SUM(views) AS views, SUM(unique_visitors) AS unique_visitors
         FROM st_page_daily WHERE view_date >= ? GROUP BY view_date ORDER BY view_date'
    );
    $dailyQuery->execute([$since]);
    $dailyRows = [];
    foreach ($dailyQuery->fetchAll() as $row) {
        $dailyRows[(string) $row['view_date']] = ['views' => (int) $row['views'], 'unique_visitors' => (int) $row['unique_visitors']];
    }
    $daily = [];
    $cursor = new DateTimeImmutable($since);
    $today = new DateTimeImmutable('today');
    while ($cursor <= $today) {
        $key = $cursor->format('Y-m-d');
        $daily[] = ['date' => $key] + ($dailyRows[$key] ?? ['views' => 0, 'unique_visitors' => 0]);
        $cursor = $cursor->modify('+1 day');
    }

    $breakdown = $pdo->prepare(
        'SELECT COALESCE(SUM(views), 0) AS views,
                COALESCE(SUM(unique_visitors), 0) AS unique_visitors,
                COALESCE(SUM(mobile_views), 0) AS mobile_views,
                COALESCE(SUM(tablet_views), 0) AS tablet_views,
                COALESCE(SUM(desktop_views), 0) AS desktop_views,
                COALESCE(SUM(internal_views), 0) AS internal_views,
                COALESCE(SUM(external_views), 0) AS external_views,
                COALESCE(SUM(direct_views), 0) AS direct_views
         FROM st_page_daily WHERE view_date >= ?'
    );
    $breakdown->execute([$since]);
    $totals = $breakdown->fetch() ?: [];
    $lifetime = (int) $pdo->query('SELECT COALESCE(SUM(views), 0) FROM st_page_counters')->fetchColumn();
    $firstDate = $pdo->query('SELECT MIN(view_date) FROM st_page_daily')->fetchColumn();

    return [
        'ok' => true,
        'days' => $days,
        'since' => $since,
        'generated_at' => gmdate('c'),
        'tracking_since' => $firstDate ?: null,
        'totals' => [
            'lifetime_views' => $lifetime,
            'period_views' => (int) ($totals['views'] ?? 0),
            'period_unique' => (int) ($totals['unique_visitors'] ?? 0),
            'active_pages' => count(array_filter($pageRows, static fn(array $row): bool => $row['period_views'] > 0)),
        ],
        'devices' => [
            'mobile' => (int) ($totals['mobile_views'] ?? 0),
            'tablet' => (int) ($totals['tablet_views'] ?? 0),
            'desktop' => (int) ($totals['desktop_views'] ?? 0),
        ],
        'sources' => [
            'internal' => (int) ($totals['internal_views'] ?? 0),
            'external' => (int) ($totals['external_views'] ?? 0),
            'direct' => (int) ($totals['direct_views'] ?? 0),
        ],
        'daily' => $daily,
        'pages' => $pageRows,
        'ratings' => st_rating_admin_summary(),
        'regulation_search' => st_regulations_analytics_summary($days),
    ];
}
