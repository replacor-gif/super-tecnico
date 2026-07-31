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
fwrite(STDOUT, "Esquema Super Tecnico actualizado.\n");
