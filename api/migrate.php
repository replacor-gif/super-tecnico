<?php
declare(strict_types=1);
require __DIR__ . '/bootstrap.php';

if (PHP_SAPI !== 'cli') {
    st_json(['ok' => false, 'error' => 'not_available'], 404);
}

$sql = file_get_contents(dirname(__DIR__) . '/database/schema.sql');
if ($sql === false) {
    fwrite(STDERR, "No se pudo leer database/schema.sql\n");
    exit(1);
}

$statements = preg_split('/;\s*(?:\r?\n|$)/', $sql) ?: [];
foreach ($statements as $statement) {
    $statement = trim($statement);
    if ($statement !== '') {
        st_db()->exec($statement);
    }
}

$regulationDetection = st_db()->query("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'st_regulation_search_events' AND COLUMN_NAME = 'client_detection'");
if ((int) $regulationDetection->fetchColumn() === 0) {
    st_db()->exec("ALTER TABLE st_regulation_search_events ADD COLUMN client_detection ENUM('declared','user_agent','fallback') NOT NULL DEFAULT 'fallback' AFTER client_type");
}
fwrite(STDOUT, "Esquema Super Tecnico actualizado.\n");
