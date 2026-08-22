<?php
declare(strict_types=1);
require __DIR__ . '/bootstrap.php';
require __DIR__ . '/electroia.php';
require __DIR__ . '/ratings.php';
require __DIR__ . '/regulations.php';
require __DIR__ . '/analytics.php';
require __DIR__ . '/connectors.php';

$action = preg_replace('/[^a-z0-9-]/', '', strtolower((string) ($_GET['action'] ?? 'health')));
$method = strtoupper((string) ($_SERVER['REQUEST_METHOD'] ?? 'GET'));

try {
    if ($action === 'electroia-access' && $method === 'GET') {
        st_json(st_electroia_access_status());
    }

    if ($action === 'electroia-unlock' && $method === 'POST') {
        $body = st_body();
        st_rate_limit('electroia-unlock', st_client_hash($body), 10, 1800);
        $pin = st_text($body, 'pin', 4, 4);
        if (preg_match('/^[0-9]{4}$/', $pin) !== 1) st_json(['ok' => false, 'error' => 'invalid_pin'], 422);
        if (!st_electroia_unlock($pin)) st_json(['ok' => false, 'error' => 'invalid_pin'], 401);
        st_json(['ok' => true, 'unlocked' => true]);
    }

    if ($action === 'electroia-status' && $method === 'GET') {
        st_require_electroia_access();
        st_json(st_electroia_status());
    }

    if ($action === 'electroia-tools' && $method === 'GET') {
        st_require_electroia_access();
        st_json(st_electroia_tool_manifest());
    }

    if ($action === 'health' && $method === 'GET') {
        st_db()->query('SELECT 1');
        st_json(['ok' => true, 'service' => 'super-tecnico-api', 'version' => ST_REGULATION_SERVICE_VERSION, 'public_tools' => [ST_REGULATION_TOOL_ID, 'supertecnico_search_connectors', 'supertecnico_get_connector', 'supertecnico_resolve_connector_contact']]);
    }

    if ($action === 'regulation-search' && in_array($method, ['GET', 'POST'], true)) {
        $input = $method === 'POST' ? st_body() : $_GET;
        $clientHash = st_client_hash($input);
        st_rate_limit('regulation-search', $clientHash, 120, 3600);
        st_json(st_regulations_search($input, $clientHash));
    }

    if ($action === 'regulation-result-open' && $method === 'POST') {
        $input = st_body();
        $clientHash = st_client_hash($input);
        st_rate_limit('regulation-result-open', $clientHash, 240, 86400);
        st_json(st_regulations_record_open($input, $clientHash));
    }

    if ($action === 'connector-search' && $method === 'GET') {
        $clientHash = st_client_hash($_GET);
        st_rate_limit('connector-search', $clientHash, 240, 3600);
        st_json(st_connectors_search($_GET, $clientHash));
    }

    if ($action === 'connector-get' && $method === 'GET') {
        $clientHash = st_client_hash($_GET);
        st_rate_limit('connector-get', $clientHash, 240, 3600);
        st_json(st_connectors_get($_GET, $clientHash));
    }

    if ($action === 'connector-resolve' && $method === 'GET') {
        $clientHash = st_client_hash($_GET);
        st_rate_limit('connector-resolve', $clientHash, 240, 3600);
        st_json(st_connectors_resolve($_GET, $clientHash));
    }

    if ($action === 'page-view' && $method === 'POST') {
        $body = st_body();
        $page = st_text($body, 'page_key', 1, 64);
        if (preg_match('/^[a-z0-9][a-z0-9-]*$/', $page) !== 1) st_json(['ok' => false, 'error' => 'invalid_page'], 422);
        st_rate_limit('view-' . substr(hash('sha256', $page), 0, 16), st_client_hash($body), 120, 3600);
        st_json(['ok' => true, 'page' => $page, 'views' => st_analytics_record($page, $body)]);
    }

    if ($action === 'page-rating' && $method === 'GET') {
        $page = (string) ($_GET['page_key'] ?? '');
        st_json(st_rating_summary($page));
    }

    if ($action === 'page-rating' && $method === 'POST') {
        $body = st_body();
        $page = st_text($body, 'page_key', 1, 64);
        $vote = st_text($body, 'vote', 4, 7);
        $feedback = st_text($body, 'feedback', 0, 600, false);
        st_rate_limit('rating-' . substr(hash('sha256', $page), 0, 16), st_client_hash($body), 20, 86400);
        st_json(st_rating_vote($page, $vote, $feedback, $body));
    }

    if ($action === 'analytics-summary' && $method === 'GET') {
        st_require_electroia_access();
        st_json(st_analytics_summary((int) ($_GET['days'] ?? 30)));
    }

    if ($action === 'fault-search' && $method === 'GET') {
        $query = trim((string) ($_GET['q'] ?? ''));
        $normalized = st_normalize($query);
        if (strlen($normalized) < 2) {
            st_json(['ok' => true, 'items' => []]);
        }
        $stmt = st_db()->prepare(
            "SELECT c.id, c.board_reference, c.brand, c.equipment_type, c.symptom, c.notes, c.nickname, c.published_at,
                    s.id AS solution_id, s.solution, s.nickname AS solution_nickname, s.confirmations_count
             FROM st_fault_cases c
             JOIN st_fault_solutions s ON s.fault_case_id = c.id AND s.status = 'published'
             WHERE c.status = 'published' AND c.board_reference_normalized LIKE ?
             ORDER BY (c.board_reference_normalized = ?) DESC, c.board_reference_normalized, s.confirmations_count DESC
             LIMIT 100"
        );
        $stmt->execute(['%' . $normalized . '%', $normalized]);
        $cases = [];
        foreach ($stmt->fetchAll() as $row) {
            $id = (string) $row['id'];
            if (!isset($cases[$id])) {
                $cases[$id] = [
                    'id' => (int) $row['id'],
                    'board_reference' => $row['board_reference'],
                    'brand' => $row['brand'],
                    'equipment_type' => $row['equipment_type'],
                    'symptom' => $row['symptom'],
                    'notes' => $row['notes'],
                    'nickname' => $row['nickname'],
                    'published_at' => $row['published_at'],
                    'solutions' => [],
                ];
            }
            $cases[$id]['solutions'][] = [
                'id' => (int) $row['solution_id'],
                'solution' => $row['solution'],
                'nickname' => $row['solution_nickname'],
                'confirmations' => (int) $row['confirmations_count'],
            ];
        }
        st_json(['ok' => true, 'items' => array_values($cases)]);
    }

    if ($action === 'fault-browse' && $method === 'GET') {
        $page = max(1, (int) ($_GET['page'] ?? 1));
        $perPage = min(24, max(6, (int) ($_GET['per_page'] ?? 12)));
        $brand = trim((string) ($_GET['brand'] ?? ''));
        $equipment = trim((string) ($_GET['equipment'] ?? ''));
        $query = trim((string) ($_GET['q'] ?? ''));
        $where = ["c.status = 'published'", "EXISTS (SELECT 1 FROM st_fault_solutions sx WHERE sx.fault_case_id = c.id AND sx.status = 'published')"];
        $params = [];
        if ($brand !== '') {
            $where[] = 'c.brand = ?';
            $params[] = $brand;
        }
        if ($equipment !== '') {
            $where[] = 'c.equipment_type = ?';
            $params[] = $equipment;
        }
        if ($query !== '') {
            $where[] = '(c.board_reference_normalized LIKE ? OR c.brand LIKE ? OR c.equipment_type LIKE ? OR c.symptom LIKE ?)';
            $like = '%' . $query . '%';
            $params[] = '%' . st_normalize($query) . '%';
            $params[] = $like;
            $params[] = $like;
            $params[] = $like;
        }
        $whereSql = implode(' AND ', $where);
        $countStmt = st_db()->prepare("SELECT COUNT(*) FROM st_fault_cases c WHERE $whereSql");
        $countStmt->execute($params);
        $total = (int) $countStmt->fetchColumn();
        $pages = max(1, (int) ceil($total / $perPage));
        $page = min($page, $pages);
        $offset = ($page - 1) * $perPage;
        $caseStmt = st_db()->prepare(
            "SELECT c.id, c.board_reference, c.brand, c.equipment_type, c.symptom, c.notes, c.nickname, c.published_at
             FROM st_fault_cases c
             WHERE $whereSql
             ORDER BY COALESCE(c.brand, ''), c.board_reference_normalized, c.published_at DESC
             LIMIT $perPage OFFSET $offset"
        );
        $caseStmt->execute($params);
        $rows = $caseStmt->fetchAll();
        $cases = [];
        $ids = [];
        foreach ($rows as $row) {
            $id = (int) $row['id'];
            $ids[] = $id;
            $cases[$id] = [
                'id' => $id,
                'board_reference' => $row['board_reference'],
                'brand' => $row['brand'],
                'equipment_type' => $row['equipment_type'],
                'symptom' => $row['symptom'],
                'notes' => $row['notes'],
                'nickname' => $row['nickname'],
                'published_at' => $row['published_at'],
                'solutions' => [],
            ];
        }
        if ($ids) {
            $placeholders = implode(',', array_fill(0, count($ids), '?'));
            $solutionStmt = st_db()->prepare(
                "SELECT id, fault_case_id, solution, nickname, confirmations_count
                 FROM st_fault_solutions
                 WHERE status = 'published' AND fault_case_id IN ($placeholders)
                 ORDER BY confirmations_count DESC, published_at DESC"
            );
            $solutionStmt->execute($ids);
            foreach ($solutionStmt->fetchAll() as $solution) {
                $caseId = (int) $solution['fault_case_id'];
                $cases[$caseId]['solutions'][] = [
                    'id' => (int) $solution['id'],
                    'solution' => $solution['solution'],
                    'nickname' => $solution['nickname'],
                    'confirmations' => (int) $solution['confirmations_count'],
                ];
            }
        }
        $facetSql = "FROM st_fault_cases c WHERE c.status = 'published' AND EXISTS (SELECT 1 FROM st_fault_solutions sx WHERE sx.fault_case_id = c.id AND sx.status = 'published')";
        $brands = st_db()->query("SELECT DISTINCT c.brand $facetSql AND c.brand IS NOT NULL AND c.brand <> '' ORDER BY c.brand")->fetchAll(PDO::FETCH_COLUMN);
        $equipmentTypes = st_db()->query("SELECT DISTINCT c.equipment_type $facetSql AND c.equipment_type IS NOT NULL AND c.equipment_type <> '' ORDER BY c.equipment_type")->fetchAll(PDO::FETCH_COLUMN);
        st_json([
            'ok' => true,
            'items' => array_values($cases),
            'pagination' => ['page' => $page, 'pages' => $pages, 'per_page' => $perPage, 'total' => $total],
            'filters' => ['brands' => $brands, 'equipment_types' => $equipmentTypes],
        ]);
    }

    if ($action === 'fault-submit' && $method === 'POST') {
        $body = st_body();
        st_verify_turnstile($body);
        $clientHash = st_client_hash($body);
        st_rate_limit('fault-submit', $clientHash, 4, 3600);
        $reference = st_text($body, 'board_reference', 2, 120);
        $symptom = st_text($body, 'symptom', 12, 1800);
        $solution = st_text($body, 'solution', 12, 2400);
        $nickname = st_text($body, 'nickname', 2, 40);
        $brand = st_text($body, 'brand', 0, 80, false);
        $equipment = st_text($body, 'equipment_type', 0, 80, false);
        $notes = st_text($body, 'notes', 0, 1200, false);
        $pdo = st_db();
        $pdo->beginTransaction();
        try {
            $contentHash = hash('sha256', st_normalize($reference) . '|' . st_normalize($symptom) . '|' . st_normalize($solution));
            $stmt = $pdo->prepare('INSERT INTO st_fault_cases (board_reference, board_reference_normalized, brand, equipment_type, symptom, notes, nickname, content_hash) VALUES (?, ?, NULLIF(?, \'\'), NULLIF(?, \'\'), ?, NULLIF(?, \'\'), ?, ?)');
            $stmt->execute([$reference, st_normalize($reference), $brand, $equipment, $symptom, $notes, $nickname, $contentHash]);
            $caseId = (int) $pdo->lastInsertId();
            $stmt = $pdo->prepare('INSERT INTO st_fault_solutions (fault_case_id, solution, nickname) VALUES (?, ?, ?)');
            $stmt->execute([$caseId, $solution, $nickname]);
            $pdo->commit();
        } catch (PDOException $error) {
            if ($pdo->inTransaction()) $pdo->rollBack();
            if ((string) $error->getCode() === '23000') st_json(['ok' => false, 'error' => 'duplicate_submission'], 409);
            throw $error;
        }
        st_json(['ok' => true, 'id' => $caseId, 'status' => 'pending'], 201);
    }

    if ($action === 'fault-alternative' && $method === 'POST') {
        $body = st_body();
        st_verify_turnstile($body);
        $clientHash = st_client_hash($body);
        st_rate_limit('fault-alternative', $clientHash, 6, 3600);
        $caseId = filter_var($body['case_id'] ?? null, FILTER_VALIDATE_INT);
        if (!$caseId) {
            st_json(['ok' => false, 'error' => 'invalid_case'], 422);
        }
        $solution = st_text($body, 'solution', 12, 2400);
        $nickname = st_text($body, 'nickname', 2, 40);
        $exists = st_db()->prepare("SELECT id FROM st_fault_cases WHERE id = ? AND status = 'published'");
        $exists->execute([$caseId]);
        if (!$exists->fetchColumn()) {
            st_json(['ok' => false, 'error' => 'case_not_found'], 404);
        }
        $stmt = st_db()->prepare('INSERT INTO st_fault_solutions (fault_case_id, solution, nickname) VALUES (?, ?, ?)');
        $stmt->execute([$caseId, $solution, $nickname]);
        st_json(['ok' => true, 'status' => 'pending'], 201);
    }

    if ($action === 'fault-confirm' && $method === 'POST') {
        $body = st_body();
        $clientHash = st_client_hash($body);
        st_rate_limit('fault-confirm', $clientHash, 30, 86400);
        $solutionId = filter_var($body['solution_id'] ?? null, FILTER_VALIDATE_INT);
        if (!$solutionId) {
            st_json(['ok' => false, 'error' => 'invalid_solution'], 422);
        }
        $pdo = st_db();
        $pdo->beginTransaction();
        try {
            $stmt = $pdo->prepare('INSERT INTO st_fault_confirmations (solution_id, client_hash) SELECT s.id, ? FROM st_fault_solutions s WHERE s.id = ? AND s.status = \'published\'');
            $stmt->execute([$clientHash, $solutionId]);
            if ($stmt->rowCount() !== 1) {
                $pdo->rollBack();
                st_json(['ok' => false, 'error' => 'solution_not_found'], 404);
            }
            $pdo->prepare('UPDATE st_fault_solutions SET confirmations_count = confirmations_count + 1 WHERE id = ?')->execute([$solutionId]);
            $pdo->commit();
        } catch (PDOException $error) {
            if ($pdo->inTransaction()) $pdo->rollBack();
            if ((string) $error->getCode() === '23000') st_json(['ok' => false, 'error' => 'already_confirmed'], 409);
            throw $error;
        }
        st_json(['ok' => true]);
    }

    if ($action === 'proposals' && $method === 'GET') {
        $stmt = st_db()->query("SELECT id, nickname, type, area, context, title, description, proposed_change, language, source_page, status, supports_count, official_note, created_at FROM st_proposals WHERE is_public = 1 ORDER BY supports_count DESC, created_at DESC LIMIT 250");
        st_json(['ok' => true, 'items' => $stmt->fetchAll()]);
    }

    if ($action === 'proposal-submit' && $method === 'POST') {
        $body = st_body();
        st_verify_turnstile($body);
        $clientHash = st_client_hash($body);
        st_rate_limit('proposal-submit', $clientHash, 5, 3600);
        $types = ['idea', 'change', 'bug', 'technical'];
        $type = (string) ($body['type'] ?? '');
        if (!in_array($type, $types, true)) st_json(['ok' => false, 'error' => 'invalid_type'], 422);
        if (trim((string) ($body['nickname'] ?? '')) === '') $body['nickname'] = 'Usuario anónimo';
        $nickname = st_text($body, 'nickname', 2, 40);
        $area = st_text($body, 'area', 2, 100);
        $context = st_text($body, 'context', 0, 160, false);
        $title = st_text($body, 'title', 5, 100);
        $description = st_text($body, 'description', 20, 1800);
        $change = st_text($body, 'proposed_change', 0, 1200, false);
        $language = in_array(($body['language'] ?? 'es'), ['es', 'en', 'pt', 'fr'], true) ? $body['language'] : 'es';
        $page = st_text($body, 'source_page', 0, 500, false);
        $contentHash = hash('sha256', st_normalize($area) . '|' . st_normalize($title) . '|' . st_normalize($description));
        $stmt = st_db()->prepare('INSERT INTO st_proposals (nickname, type, area, context, title, description, proposed_change, language, source_page, content_hash) VALUES (?, ?, ?, NULLIF(?, \'\'), ?, ?, NULLIF(?, \'\'), ?, NULLIF(?, \'\'), ?)');
        try {
            $stmt->execute([$nickname, $type, $area, $context, $title, $description, $change, $language, $page, $contentHash]);
        } catch (PDOException $error) {
            if ((string) $error->getCode() === '23000') st_json(['ok' => false, 'error' => 'duplicate_submission'], 409);
            throw $error;
        }
        st_json(['ok' => true, 'id' => (int) st_db()->lastInsertId(), 'status' => 'pending'], 201);
    }

    if ($action === 'proposal-support' && $method === 'POST') {
        $body = st_body();
        $clientHash = st_client_hash($body);
        st_rate_limit('proposal-support', $clientHash, 40, 86400);
        $proposalId = filter_var($body['proposal_id'] ?? null, FILTER_VALIDATE_INT);
        if (!$proposalId) st_json(['ok' => false, 'error' => 'invalid_proposal'], 422);
        $pdo = st_db();
        $pdo->beginTransaction();
        try {
            $stmt = $pdo->prepare('INSERT INTO st_proposal_supports (proposal_id, client_hash) SELECT p.id, ? FROM st_proposals p WHERE p.id = ? AND p.is_public = 1');
            $stmt->execute([$clientHash, $proposalId]);
            if ($stmt->rowCount() !== 1) {
                $pdo->rollBack();
                st_json(['ok' => false, 'error' => 'proposal_not_found'], 404);
            }
            $pdo->prepare('UPDATE st_proposals SET supports_count = supports_count + 1 WHERE id = ?')->execute([$proposalId]);
            $pdo->commit();
        } catch (PDOException $error) {
            if ($pdo->inTransaction()) $pdo->rollBack();
            if ((string) $error->getCode() === '23000') st_json(['ok' => false, 'error' => 'already_supported'], 409);
            throw $error;
        }
        st_json(['ok' => true]);
    }

    if ($action === 'admin-login' && $method === 'POST') {
        $body = st_body();
        st_rate_limit('admin-login', st_client_hash($body), 8, 1800);
        $password = (string) ($body['password'] ?? '');
        $hash = (string) st_config('admin_password_hash');
        if ($hash === '' || !password_verify($password, $hash)) {
            st_json(['ok' => false, 'error' => 'invalid_credentials'], 401);
        }
        st_start_admin_session();
        session_regenerate_id(true);
        $_SESSION['st_admin'] = true;
        $_SESSION['csrf'] = bin2hex(random_bytes(24));
        st_json(['ok' => true, 'csrf' => $_SESSION['csrf']]);
    }

    if ($action === 'admin-session' && $method === 'GET') {
        st_require_admin();
        st_json(['ok' => true, 'csrf' => $_SESSION['csrf']]);
    }

    if ($action === 'admin-connector-catalog' && $method === 'GET') {
        st_require_admin();
        st_json(st_connectors_admin_catalog($_GET));
    }

    if ($action === 'admin-connector-review' && $method === 'POST') {
        st_require_admin(true);
        st_json(st_connectors_admin_review(st_body()));
    }

    if ($action === 'admin-connector-history' && $method === 'GET') {
        st_require_admin();
        st_json(st_connectors_admin_history($_GET));
    }

    if ($action === 'admin-connector-imports' && $method === 'GET') {
        st_require_admin();
        st_json(st_connectors_admin_imports());
    }

    if ($action === 'admin-connector-import' && $method === 'POST') {
        st_require_admin(true);
        st_json(st_connectors_admin_import(), 201);
    }

    if ($action === 'admin-connector-import-update' && $method === 'POST') {
        st_require_admin(true);
        st_json(st_connectors_admin_import_update(st_body()));
    }

    if ($action === 'admin-logout' && $method === 'POST') {
        st_require_admin(true);
        $_SESSION = [];
        session_destroy();
        st_json(['ok' => true]);
    }

    if ($action === 'admin-list' && $method === 'GET') {
        st_require_admin();
        $kind = (string) ($_GET['kind'] ?? 'proposals');
        if ($kind === 'faults') {
            $sql = "SELECT c.*, GROUP_CONCAT(CONCAT(s.id, '::', s.status, '::', s.nickname, '::', REPLACE(s.solution, '\n', ' ')) ORDER BY s.id SEPARATOR '\n') AS solutions FROM st_fault_cases c LEFT JOIN st_fault_solutions s ON s.fault_case_id = c.id GROUP BY c.id ORDER BY c.created_at DESC LIMIT 500";
        } elseif ($kind === 'solutions') {
            $sql = 'SELECT s.*, c.board_reference, c.symptom FROM st_fault_solutions s JOIN st_fault_cases c ON c.id = s.fault_case_id ORDER BY s.created_at DESC LIMIT 500';
        } else {
            $kind = 'proposals';
            $sql = 'SELECT * FROM st_proposals ORDER BY created_at DESC LIMIT 500';
        }
        st_json(['ok' => true, 'kind' => $kind, 'items' => st_db()->query($sql)->fetchAll()]);
    }

    if ($action === 'admin-update' && $method === 'POST') {
        st_require_admin(true);
        $body = st_body();
        $kind = (string) ($body['kind'] ?? '');
        $id = filter_var($body['id'] ?? null, FILTER_VALIDATE_INT);
        $status = (string) ($body['status'] ?? '');
        if (!$id) st_json(['ok' => false, 'error' => 'invalid_id'], 422);
        if ($kind === 'fault' || $kind === 'solution') {
            if (!in_array($status, ['pending', 'published', 'rejected'], true)) st_json(['ok' => false, 'error' => 'invalid_status'], 422);
            $table = $kind === 'fault' ? 'st_fault_cases' : 'st_fault_solutions';
            $stmt = st_db()->prepare("UPDATE {$table} SET status = ?, reviewed_at = NOW(), published_at = IF(? = 'published', COALESCE(published_at, NOW()), published_at) WHERE id = ?");
            $stmt->execute([$status, $status, $id]);
        } elseif ($kind === 'proposal') {
            $valid = ['pending','study','accepted','planned','development','applied','duplicate','discarded'];
            if (!in_array($status, $valid, true)) st_json(['ok' => false, 'error' => 'invalid_status'], 422);
            $isPublic = !empty($body['is_public']) ? 1 : 0;
            $note = st_text($body, 'official_note', 0, 1600, false);
            $stmt = st_db()->prepare('UPDATE st_proposals SET status = ?, is_public = ?, official_note = NULLIF(?, \'\'), reviewed_at = NOW(), published_at = IF(? = 1, COALESCE(published_at, NOW()), published_at) WHERE id = ?');
            $stmt->execute([$status, $isPublic, $note, $isPublic, $id]);
        } else {
            st_json(['ok' => false, 'error' => 'invalid_kind'], 422);
        }
        $log = st_db()->prepare('INSERT INTO st_moderation_log (entity_type, entity_id, action_name, details_json) VALUES (?, ?, \'update\', ?)');
        $log->execute([$kind, $id, json_encode(['status' => $status], JSON_UNESCAPED_UNICODE)]);
        st_json(['ok' => true]);
    }

    st_json(['ok' => false, 'error' => 'not_found'], 404);
} catch (Throwable $error) {
    error_log('Super Tecnico API: ' . $error->getMessage());
    st_json(['ok' => false, 'error' => 'server_error'], 500);
}
