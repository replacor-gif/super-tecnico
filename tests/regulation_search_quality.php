<?php
declare(strict_types=1);

if (!function_exists('mb_strlen')) {
    function mb_strlen(string $value, ?string $encoding = null): int { return strlen($value); }
    function mb_strtolower(string $value, ?string $encoding = null): string { return strtolower($value); }
    function mb_substr(string $value, int $offset, ?int $length = null, ?string $encoding = null): string { return substr($value, $offset, $length); }
}

require dirname(__DIR__) . '/api/regulations.php';

function quality_search(string $query, string $documentId = 'rebt'): array
{
    return st_regulations_search([
        'q' => $query,
        'document_id' => $documentId,
        'limit' => 5,
    ], str_repeat('d', 64), false);
}

function quality_fail(string $message): never
{
    fwrite(STDERR, $message . "\n");
    exit(1);
}

$ambiguous = quality_search('que seccion debe tener un cable en una vivienda');
$ambiguousTop = $ambiguous['result']['items'][0] ?? [];
if (($ambiguous['result']['answer_status'] ?? '') !== 'needs_context') {
    quality_fail('The search did not flag the ambiguous cable sizing question.');
}
if ((int) ($ambiguousTop['page'] ?? 0) !== 169 || ($ambiguousTop['record_type'] ?? '') !== 'table' || !str_contains((string) ($ambiguousTop['locator'] ?? ''), 'ITC-BT-25')) {
    $ranking = implode(', ', array_map(static fn(array $item): string => (string) ($item['page'] ?? '?') . '/' . (string) ($item['record_type'] ?? '?') . '/' . (string) ($item['locator'] ?? '?') . '/' . (string) ($item['relevance_score'] ?? '?'), $ambiguous['result']['items'] ?? []));
    quality_fail('The general cable sizing question lost the ITC-BT-19 evidence. Ranking: ' . $ranking);
}

$lighting = quality_search('seccion cable alumbrado vivienda');
$lightingTop = $lighting['result']['items'][0] ?? [];
if ((int) ($lightingTop['page'] ?? 0) !== 169 || ($lightingTop['record_type'] ?? '') !== 'table') {
    $ranking = implode(', ', array_map(static fn(array $item): string => (string) ($item['page'] ?? '?') . '/' . (string) ($item['record_type'] ?? '?') . '/' . (string) ($item['relevance_score'] ?? '?'), $lighting['result']['items'] ?? []));
    quality_fail('The lighting circuit query did not prioritize REBT table 1 on page 169. Got page ' . (string) ($lightingTop['page'] ?? '?') . ', type ' . (string) ($lightingTop['record_type'] ?? '?') . ', locator ' . (string) ($lightingTop['locator'] ?? '?') . '. Ranking: ' . $ranking);
}
if (!str_contains((string) ($lightingTop['locator'] ?? ''), 'ITC-BT-25') || !str_contains((string) ($lightingTop['locator'] ?? ''), 'Tabla 1')) {
    quality_fail('The lighting circuit result lacks its structured ITC/table locator.');
}
if (($lighting['result']['answer_status'] ?? '') !== 'evidence_found' || !empty($lighting['result']['refinement'])) {
    quality_fail('A sufficiently specific circuit query was still treated as ambiguous.');
}

$voltageDrop = quality_search('caida de voltaje instalacion interior');
$voltageTop = $voltageDrop['result']['items'][0] ?? [];
if ((int) ($voltageTop['page'] ?? 0) !== 128 || !str_contains((string) ($voltageTop['locator'] ?? ''), '2.2.2')) {
    quality_fail('Voltage-drop synonym search did not locate ITC-BT-19 section 2.2.2.');
}

$pipe = quality_search('que diametro de tuveria necesito', '');
if (($pipe['result']['answer_status'] ?? '') !== 'needs_context' || empty($pipe['result']['refinement']['required'])) {
    quality_fail('The misspelled ambiguous pipe diameter query did not request the missing service.');
}

foreach (['proteccion', 'cuadro electrico', 'desague'] as $broadQuery) {
    $refinement = st_regulation_refinement(st_regulation_normalize($broadQuery));
    if (empty($refinement['required']) || empty($refinement['suggested_terms'])) {
        quality_fail('The broad query did not request its missing technical scope: ' . $broadQuery);
    }
}
foreach (['proteccion motor', 'cuadro electrico industrial', 'desague condensados climatizacion'] as $specificQuery) {
    if (st_regulation_refinement(st_regulation_normalize($specificQuery)) !== null) {
        quality_fail('A specific query was incorrectly treated as ambiguous: ' . $specificQuery);
    }
}

fwrite(STDOUT, "Regulation search quality: OK\n");
