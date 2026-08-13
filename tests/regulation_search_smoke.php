<?php
declare(strict_types=1);

// The production host provides mbstring. These tiny fallbacks keep the smoke
// test runnable with the minimal Windows CLI package used in local validation.
if (!function_exists('mb_strlen')) {
    function mb_strlen(string $value, ?string $encoding = null): int { return strlen($value); }
    function mb_strtolower(string $value, ?string $encoding = null): string { return strtolower($value); }
    function mb_substr(string $value, int $offset, ?int $length = null, ?string $encoding = null): string { return substr($value, $offset, $length); }
}

require dirname(__DIR__) . '/api/regulations.php';

$result = st_regulations_search([
    'q' => 'caida de tension',
    'document_id' => 'rebt',
    'limit' => 3,
], str_repeat('a', 64), false);

$items = $result['result']['items'] ?? [];
if (($result['status'] ?? '') !== 'success' || count($items) !== 3) {
    fwrite(STDERR, "Regulation search did not return three results.\n");
    exit(1);
}
foreach ($items as $item) {
    if (($item['document_id'] ?? '') !== 'rebt' || (int) ($item['page'] ?? 0) < 1) {
        fwrite(STDERR, "Regulation search returned an invalid document or page.\n");
        exit(1);
    }
    if (strlen((string) ($item['source_sha256'] ?? '')) !== 64 || strlen((string) ($item['source_content_sha256'] ?? '')) !== 64) {
        fwrite(STDERR, "Regulation search did not preserve source fingerprints.\n");
        exit(1);
    }
}
fwrite(STDOUT, "Regulation search smoke: OK\n");
