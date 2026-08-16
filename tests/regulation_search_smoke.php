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

$naturalQuestion = st_regulations_search([
    'q' => 'que seccion debe tener un cable en una vivienda',
    'document_id' => 'rebt',
    'limit' => 5,
], str_repeat('b', 64), false);
$naturalItems = $naturalQuestion['result']['items'] ?? [];
if (($naturalQuestion['status'] ?? '') !== 'success' || !$naturalItems) {
    fwrite(STDERR, "Natural-language regulation search returned no results.\n");
    exit(1);
}
if ((float) ($naturalItems[0]['term_coverage'] ?? 0) < 0.99 || !array_key_exists('locator', $naturalItems[0])) {
    fwrite(STDERR, "Natural-language search did not preserve coverage or locator metadata.\n");
    exit(1);
}
if (st_regulation_term_position('todo conductor debe poder seccionarse', 'seccion') !== false) {
    fwrite(STDERR, "Word-boundary search confused seccion with seccionarse.\n");
    exit(1);
}
if ((int) ($naturalItems[0]['page'] ?? 0) !== 128 || ($naturalItems[0]['scope_hint'] ?? '') !== '') {
    fwrite(STDERR, 'Natural-language ranking did not prioritize the general conductor rule. First page: ' . (string) ($naturalItems[0]['page'] ?? '?') . '; scope: ' . (string) ($naturalItems[0]['scope_hint'] ?? '') . "\n");
    exit(1);
}
if (empty($naturalQuestion['result']['refinement']['suggested_terms'] ?? [])) {
    fwrite(STDERR, "Ambiguous technical query did not return refinement suggestions.\n");
    exit(1);
}

$synonymQuestion = st_regulations_search([
    'q' => 'caida de voltaje',
    'document_id' => 'rebt',
    'limit' => 3,
], str_repeat('c', 64), false);
if (($synonymQuestion['status'] ?? '') !== 'success' || (float) ($synonymQuestion['result']['items'][0]['term_coverage'] ?? 0) < 0.99) {
    fwrite(STDERR, "Technical synonym expansion did not find voltage-drop evidence.\n");
    exit(1);
}
fwrite(STDOUT, "Regulation search smoke: OK\n");
