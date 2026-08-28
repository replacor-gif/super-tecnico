(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.STDuctDesigner = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const STORAGE_KEY = 'st.ductDesigner.v6';
  const LEGACY_KEYS = ['st.ductDesigner.v5', 'st.ductDesigner.v4', 'st.ductDesigner.v3', 'st.ductDesigner.v2'];
  const CELL_PX = 44;
  const ROUTE_STEP = .5;

  /* Criterios internos del método práctico. No se muestran ni se modifican. */
  const DESIGN = Object.freeze({
    airflowPer9000: 1200,
    ductVelocityMps: 4,
    grilleVelocityMps: 2,
    minimumDuctWidthCm: 10,
    minimumGrilleWidthCm: 20,
  });

  const ROOM_LOADS = Object.freeze({
    bedroom: 1500,
    standard: 2000,
    normal: 3000,
    large: 4500,
    veryLarge: 6000,
  });

  const LOAD_TIERS = Object.freeze({
    normal: { label: 'Normal', loadFg: ROOM_LOADS.normal },
    large: { label: 'Grande', loadFg: ROOM_LOADS.large },
    veryLarge: { label: 'Muy grande', loadFg: ROOM_LOADS.veryLarge },
  });

  const DEFAULTS = Object.freeze({
    schemaVersion: 6,
    phase: 'draw',
    projectName: 'Vivienda',
    cellSizeM: .5,
    gridCols: 24,
    gridRows: 18,
    ductHeightCm: 25,
    grilleHeightCm: 15,
  });

  const ROOM_TYPES = Object.freeze({
    unassigned: { label: 'Elegir estancia', short: 'SIN IDENTIFICAR', color: '#718399' },
    bedroom: { label: 'Dormitorio', short: 'DORMITORIO', color: '#00c8ff' },
    living: { label: 'Salón / comedor', short: 'SALÓN', color: '#ffe438' },
    kitchen: { label: 'Cocina', short: 'COCINA', color: '#ff7a00' },
    office: { label: 'Oficina / despacho', short: 'OFICINA', color: '#00ead0' },
    bathroom: { label: 'Baño', short: 'BAÑO', color: '#8c9aaf' },
    hallway: { label: 'Pasillo / distribuidor', short: 'PASILLO', color: '#9078ff' },
    utility: { label: 'Lavadero / zona técnica', short: 'TÉCNICO', color: '#ff3fa7' },
    other: { label: 'Otra estancia', short: 'ESTANCIA', color: '#51ff7d' },
  });

  function finite(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
  }

  function roundUp(value, step = 1) {
    return Math.ceil((value - 1e-9) / step) * step;
  }

  function point(value, cols = DEFAULTS.gridCols, rows = DEFAULTS.gridRows) {
    return {
      x: clamp(Math.round(finite(value?.x)), 0, cols),
      y: clamp(Math.round(finite(value?.y)), 0, rows),
    };
  }

  function routePoint(value, cols = DEFAULTS.gridCols, rows = DEFAULTS.gridRows) {
    return {
      x: clamp(Math.round(finite(value?.x) / ROUTE_STEP) * ROUTE_STEP, 0, cols),
      y: clamp(Math.round(finite(value?.y) / ROUTE_STEP) * ROUTE_STEP, 0, rows),
    };
  }

  function pointKey(value) {
    const clean = coordinate => Object.is(coordinate, -0) ? 0 : Number(finite(coordinate).toFixed(3));
    return `${clean(value.x)},${clean(value.y)}`;
  }

  function parsePointKey(value) {
    const [x, y] = String(value).split(',').map(Number);
    return { x, y };
  }

  function edgeKey(a, b) {
    const one = pointKey(a);
    const two = pointKey(b);
    return one < two ? `${one}|${two}` : `${two}|${one}`;
  }

  function pointsForRoom(room) {
    if (Array.isArray(room?.points) && room.points.length >= 3) return room.points;
    const x = finite(room?.x), y = finite(room?.y), w = finite(room?.w), h = finite(room?.h);
    return [{ x, y }, { x: x + w, y }, { x: x + w, y: y + h }, { x, y: y + h }];
  }

  function signedPolygonArea(points) {
    return points.reduce((sum, current, index) => {
      const next = points[(index + 1) % points.length];
      return sum + current.x * next.y - next.x * current.y;
    }, 0) / 2;
  }

  function polygonArea(points) {
    return Math.abs(signedPolygonArea(points));
  }

  function polygonBounds(points) {
    const xs = points.map(item => item.x);
    const ys = points.map(item => item.y);
    const x = Math.min(...xs), y = Math.min(...ys);
    return { x, y, width: Math.max(...xs) - x, height: Math.max(...ys) - y };
  }

  function polygonCentroid(points) {
    const areaFactor = signedPolygonArea(points) * 6;
    if (Math.abs(areaFactor) < 1e-8) {
      return {
        x: points.reduce((sum, item) => sum + item.x, 0) / points.length,
        y: points.reduce((sum, item) => sum + item.y, 0) / points.length,
      };
    }
    let x = 0, y = 0;
    points.forEach((current, index) => {
      const next = points[(index + 1) % points.length];
      const factor = current.x * next.y - next.x * current.y;
      x += (current.x + next.x) * factor;
      y += (current.y + next.y) * factor;
    });
    return { x: x / areaFactor, y: y / areaFactor };
  }

  function pointOnSegment(value, a, b, tolerance = 1e-7) {
    const cross = (value.y - a.y) * (b.x - a.x) - (value.x - a.x) * (b.y - a.y);
    if (Math.abs(cross) > tolerance) return false;
    return value.x >= Math.min(a.x, b.x) - tolerance && value.x <= Math.max(a.x, b.x) + tolerance
      && value.y >= Math.min(a.y, b.y) - tolerance && value.y <= Math.max(a.y, b.y) + tolerance;
  }

  function pointInPolygon(value, points, includeBoundary = true) {
    const onBoundary = points.some((current, index) => pointOnSegment(value, current, points[(index + 1) % points.length]));
    if (onBoundary) return includeBoundary;
    let inside = false;
    for (let one = 0, two = points.length - 1; one < points.length; two = one++) {
      const a = points[one], b = points[two];
      if (((a.y > value.y) !== (b.y > value.y))
        && value.x < (b.x - a.x) * (value.y - a.y) / (b.y - a.y) + a.x) inside = !inside;
    }
    return inside;
  }

  function orientation(a, b, c) {
    const value = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
    return Math.abs(value) < 1e-8 ? 0 : Math.sign(value);
  }

  function segmentsCross(a, b, c, d) {
    const o1 = orientation(a, b, c), o2 = orientation(a, b, d);
    const o3 = orientation(c, d, a), o4 = orientation(c, d, b);
    if (o1 !== o2 && o3 !== o4) return true;
    if (o1 === 0 && pointOnSegment(c, a, b)) return true;
    if (o2 === 0 && pointOnSegment(d, a, b)) return true;
    if (o3 === 0 && pointOnSegment(a, c, d)) return true;
    return o4 === 0 && pointOnSegment(b, c, d);
  }

  function polygonSelfIntersects(points) {
    for (let one = 0; one < points.length; one += 1) {
      const a = points[one], b = points[(one + 1) % points.length];
      for (let two = one + 1; two < points.length; two += 1) {
        if (Math.abs(one - two) <= 1 || (one === 0 && two === points.length - 1)) continue;
        const c = points[two], d = points[(two + 1) % points.length];
        if (segmentsCross(a, b, c, d)) return true;
      }
    }
    return false;
  }

  function roomOverlap(one, two) {
    const first = pointsForRoom(one), second = pointsForRoom(two);
    for (let aIndex = 0; aIndex < first.length; aIndex += 1) {
      const a = first[aIndex], b = first[(aIndex + 1) % first.length];
      for (let cIndex = 0; cIndex < second.length; cIndex += 1) {
        const c = second[cIndex], d = second[(cIndex + 1) % second.length];
        const orientations = [orientation(a, b, c), orientation(a, b, d), orientation(c, d, a), orientation(c, d, b)];
        if (orientations[0] * orientations[1] < 0 && orientations[2] * orientations[3] < 0) return true;
      }
    }
    if (first.some(item => pointInPolygon(item, second, false))) return true;
    if (second.some(item => pointInPolygon(item, first, false))) return true;
    return pointInPolygon(polygonCentroid(first), second, false) || pointInPolygon(polygonCentroid(second), first, false);
  }

  function nearestInteriorPoint(room, targetValue) {
    const points = pointsForRoom(room);
    const target = targetValue || polygonCentroid(points);
    if (pointInPolygon(target, points, true)) return target;
    const bounds = polygonBounds(points);
    let best = points[0], distance = Infinity;
    for (let y = Math.ceil(bounds.y); y <= Math.floor(bounds.y + bounds.height); y += 1) {
      for (let x = Math.ceil(bounds.x); x <= Math.floor(bounds.x + bounds.width); x += 1) {
        const candidate = { x, y };
        if (!pointInPolygon(candidate, points, true)) continue;
        const current = Math.abs(candidate.x - target.x) + Math.abs(candidate.y - target.y);
        if (current < distance) { distance = current; best = candidate; }
      }
    }
    return best;
  }

  function renumberRooms(rooms) {
    const totals = rooms.reduce((map, room) => map.set(room.type, (map.get(room.type) || 0) + 1), new Map());
    const counters = new Map();
    return rooms.map((room, index) => {
      counters.set(room.type, (counters.get(room.type) || 0) + 1);
      const definition = ROOM_TYPES[room.type] || ROOM_TYPES.unassigned;
      const name = room.type === 'unassigned' ? `Estancia ${index + 1}`
        : totals.get(room.type) > 1 ? `${definition.label} ${counters.get(room.type)}` : definition.label;
      return { ...room, name };
    });
  }

  function normalizeState(input = {}) {
    const gridCols = clamp(Math.round(finite(input.gridCols, DEFAULTS.gridCols)), 8, 60);
    const gridRows = clamp(Math.round(finite(input.gridRows, DEFAULTS.gridRows)), 8, 50);
    const ids = new Set();
    const rooms = (Array.isArray(input.rooms) ? input.rooms : []).slice(0, 80).map((room, index) => {
      let id = String(room?.id || `room-${index + 1}`).slice(0, 60);
      while (ids.has(id)) id = `${id}-${index + 1}`;
      ids.add(id);
      const type = ROOM_TYPES[room?.type] ? room.type : 'unassigned';
      const rawPoints = pointsForRoom(room).map(item => point(item, gridCols, gridRows));
      const unique = rawPoints.filter((item, itemIndex) => itemIndex === 0 || pointKey(item) !== pointKey(rawPoints[itemIndex - 1]));
      const points = unique.length > 2 && pointKey(unique[0]) === pointKey(unique.at(-1)) ? unique.slice(0, -1) : unique;
      return {
        id,
        type,
        points: points.length >= 3 && polygonArea(points) >= .5 ? points : [{ x: 0, y: 0 }, { x: 2, y: 0 }, { x: 2, y: 2 }, { x: 0, y: 2 }],
        conditioned: Boolean(room?.conditioned),
        loadTier: LOAD_TIERS[room?.loadTier] ? room.loadTier : 'normal',
      };
    });
    const numbered = renumberRooms(rooms);
    const roomById = new Map(numbered.map(room => [room.id, room]));
    const machineRoomId = String(input.machine?.roomId || '');
    const machineRoom = roomById.get(machineRoomId);
    const machine = input.machine ? snapMachineToPlan({ rooms: numbered, gridCols, gridRows }, input.machine, machineRoom) : null;
    const outletOverrides = {};
    Object.entries(input.outletOverrides || {}).forEach(([roomId, value]) => {
      const room = roomById.get(roomId);
      if (!room) return;
      const target = {
        x: clamp(finite(value?.x), 0, gridCols),
        y: clamp(finite(value?.y), 0, gridRows),
      };
      const snapped = snapOutletToWall(room, target, { wallIndex: value?.wallIndex, preservePosition: true });
      if (snapped) outletOverrides[roomId] = { x: snapped.x, y: snapped.y, wallIndex: snapped.wallIndex };
    });
    const branchWaypoints = {};
    const rawBranchWaypoints = input.branchWaypoints || input.branchGuides || {};
    Object.entries(rawBranchWaypoints).forEach(([roomId, value]) => {
      if (!roomById.has(roomId)) return;
      const values = Array.isArray(value) ? value : [value];
      const waypoints = values.filter(Boolean).slice(0, 8).map(item => routePoint(item, gridCols, gridRows));
      if (waypoints.length) branchWaypoints[roomId] = waypoints;
    });
    const rawTrunkWaypoints = Array.isArray(input.trunkWaypoints)
      ? input.trunkWaypoints
      : input.trunkGuide ? [input.trunkGuide] : [];
    const trunkWaypoints = rawTrunkWaypoints.filter(Boolean).slice(0, 12).map(item => routePoint(item, gridCols, gridRows));
    const branchGuides = Object.fromEntries(Object.entries(branchWaypoints).map(([roomId, values]) => [roomId, values[0]]));
    const trunkGuide = trunkWaypoints[0] || null;
    return {
      ...DEFAULTS,
      phase: ['configure', 'layout'].includes(input.phase) ? input.phase : input.workflowStep >= 2 ? 'configure' : 'draw',
      projectName: String(input.projectName || DEFAULTS.projectName).slice(0, 70),
      cellSizeM: [.25, .5, 1].includes(finite(input.cellSizeM)) ? finite(input.cellSizeM) : DEFAULTS.cellSizeM,
      gridCols,
      gridRows,
      ductHeightCm: clamp(roundUp(finite(input.ductHeightCm, DEFAULTS.ductHeightCm), 5), 10, 80),
      grilleHeightCm: clamp(Math.round(finite(input.grilleHeightCm, DEFAULTS.grilleHeightCm)), 8, 60),
      rooms: numbered,
      machine,
      outletOverrides,
      branchGuides,
      trunkGuide,
      branchWaypoints,
      trunkWaypoints,
    };
  }

  function emptyState() {
    return normalizeState(DEFAULTS);
  }

  function exampleState() {
    return normalizeState({
      ...DEFAULTS,
      phase: 'layout',
      rooms: [
        { id: 'bed-1', type: 'bedroom', points: [{ x: 1, y: 1 }, { x: 8, y: 1 }, { x: 8, y: 7 }, { x: 1, y: 7 }], conditioned: true },
        { id: 'bed-2', type: 'bedroom', points: [{ x: 8, y: 1 }, { x: 15, y: 1 }, { x: 15, y: 7 }, { x: 8, y: 7 }], conditioned: true },
        { id: 'kitchen', type: 'kitchen', points: [{ x: 15, y: 1 }, { x: 23, y: 1 }, { x: 23, y: 7 }, { x: 15, y: 7 }], conditioned: false },
        { id: 'bath', type: 'bathroom', points: [{ x: 1, y: 7 }, { x: 7, y: 7 }, { x: 7, y: 12 }, { x: 1, y: 12 }], conditioned: false },
        { id: 'hall', type: 'hallway', points: [{ x: 7, y: 7 }, { x: 11, y: 7 }, { x: 11, y: 17 }, { x: 7, y: 17 }], conditioned: false },
        { id: 'living', type: 'living', points: [{ x: 11, y: 7 }, { x: 23, y: 7 }, { x: 23, y: 17 }, { x: 17, y: 17 }, { x: 17, y: 14 }, { x: 11, y: 14 }], conditioned: true },
      ],
      machine: { roomId: 'hall', x: 9, y: 15 },
    });
  }

  function roomArea(room, state) {
    return polygonArea(room.points) * state.cellSizeM * state.cellSizeM;
  }

  function airflowForLoad(loadFg) {
    return loadFg * DESIGN.airflowPer9000 / 9000;
  }

  function sizeDuct(loadFg, input = {}) {
    const ductHeightCm = clamp(roundUp(finite(input.ductHeightCm, DEFAULTS.ductHeightCm), 5), 10, 80);
    const airflowM3h = airflowForLoad(loadFg);
    const requiredAreaCm2 = airflowM3h > 0 ? airflowM3h / (DESIGN.ductVelocityMps * 3600) * 10000 : 0;
    const rawWidthCm = requiredAreaCm2 / ductHeightCm;
    const widthCm = loadFg > 0 ? roundUp(Math.max(DESIGN.minimumDuctWidthCm, rawWidthCm), 5) : 0;
    const actualAreaM2 = widthCm * ductHeightCm / 10000;
    const velocityMps = actualAreaM2 > 0 ? airflowM3h / (actualAreaM2 * 3600) : 0;
    return { widthCm, heightCm: ductHeightCm, requiredAreaCm2, airflowM3h, velocityMps };
  }

  function loadForRoom(room) {
    if (!room.conditioned) return 0;
    if (room.type === 'bedroom') return ROOM_LOADS.bedroom;
    if (room.type === 'living' || room.type === 'kitchen') return LOAD_TIERS[room.loadTier]?.loadFg || ROOM_LOADS.normal;
    return room.type === 'unassigned' ? 0 : ROOM_LOADS.standard;
  }

  function enrichRoom(room, state) {
    const areaM2 = roomArea(room, state);
    const loadFg = loadForRoom(room);
    const airflowM3h = airflowForLoad(loadFg);
    const branchDuct = sizeDuct(loadFg, state);
    const grilleAreaCm2 = airflowM3h > 0 ? airflowM3h / (DESIGN.grilleVelocityMps * 3600) * 10000 : 0;
    const grilleWidthCm = loadFg > 0 ? roundUp(Math.max(DESIGN.minimumGrilleWidthCm, grilleAreaCm2 / state.grilleHeightCm), 5) : 0;
    return {
      ...room,
      typeLabel: ROOM_TYPES[room.type].label,
      areaM2,
      loadFg,
      loadLabel: room.type === 'living' || room.type === 'kitchen' ? LOAD_TIERS[room.loadTier].label : '',
      airflowM3h,
      branchDuct,
      grille: { widthCm: grilleWidthCm, heightCm: state.grilleHeightCm },
      centroid: nearestInteriorPoint(room, polygonCentroid(room.points)),
    };
  }

  function boundaryPoints(room) {
    const found = new Map();
    room.points.forEach((current, index) => {
      const next = room.points[(index + 1) % room.points.length];
      const dx = next.x - current.x, dy = next.y - current.y;
      const steps = Math.max(Math.abs(dx), Math.abs(dy));
      for (let step = 0; step <= steps; step += 1) {
        const candidate = point({ x: current.x + dx * step / Math.max(steps, 1), y: current.y + dy * step / Math.max(steps, 1) }, 999, 999);
        if (pointOnSegment(candidate, current, next, .12)) found.set(pointKey(candidate), candidate);
      }
    });
    return [...found.values()];
  }

  function closestPointOnSegment(value, a, b) {
    const dx = b.x - a.x, dy = b.y - a.y;
    const lengthSquared = dx * dx + dy * dy;
    if (!lengthSquared) return { x: a.x, y: a.y };
    const ratio = clamp(((value.x - a.x) * dx + (value.y - a.y) * dy) / lengthSquared, 0, 1);
    return { x: a.x + dx * ratio, y: a.y + dy * ratio };
  }

  function distanceToSegment(value, a, b) {
    const closest = closestPointOnSegment(value, a, b);
    return Math.hypot(value.x - closest.x, value.y - closest.y);
  }

  function normalizeWallAngle(value) {
    let angle = value;
    while (angle > 90) angle -= 180;
    while (angle <= -90) angle += 180;
    return Number(angle.toFixed(2));
  }

  function wallSegments(room) {
    const points = pointsForRoom(room);
    return points.map((a, index) => {
      const b = points[(index + 1) % points.length];
      const dx = b.x - a.x, dy = b.y - a.y;
      return {
        index,
        a: { x: a.x, y: a.y },
        b: { x: b.x, y: b.y },
        x: (a.x + b.x) / 2,
        y: (a.y + b.y) / 2,
        length: Math.hypot(dx, dy),
        angleDeg: normalizeWallAngle(Math.atan2(dy, dx) * 180 / Math.PI),
      };
    }).filter(segment => segment.length >= ROUTE_STEP);
  }

  function outletPlacement(segment, position = null) {
    const placed = position || { x: segment.x, y: segment.y };
    const centered = Math.hypot(placed.x - segment.x, placed.y - segment.y) < 1e-7;
    return {
      x: Number(placed.x.toFixed(3)),
      y: Number(placed.y.toFixed(3)),
      wallIndex: segment.index,
      wallAngleDeg: segment.angleDeg,
      wallA: segment.a,
      wallB: segment.b,
      centered,
    };
  }

  function snapOutletToWall(room, targetValue, options = {}) {
    const target = targetValue || polygonCentroid(pointsForRoom(room));
    const walls = wallSegments(room);
    const requestedWall = Number.isInteger(Number(options.wallIndex))
      ? walls.find(item => item.index === Number(options.wallIndex))
      : null;
    const segment = requestedWall || walls.sort((one, two) => {
      const distanceDifference = distanceToSegment(target, one.a, one.b) - distanceToSegment(target, two.a, two.b);
      if (Math.abs(distanceDifference) > 1e-8) return distanceDifference;
      return Math.hypot(target.x - one.x, target.y - one.y) - Math.hypot(target.x - two.x, target.y - two.y);
    })[0];
    if (!segment) return null;
    if (!options.preservePosition) return outletPlacement(segment);
    const closest = closestPointOnSegment(target, segment.a, segment.b);
    const margin = Math.min(.35, segment.length * .18);
    const dx = segment.b.x - segment.a.x;
    const dy = segment.b.y - segment.a.y;
    const length = Math.max(segment.length, 1e-9);
    const rawRatio = ((closest.x - segment.a.x) * dx + (closest.y - segment.a.y) * dy) / (length * length);
    const safeRatio = clamp(rawRatio, margin / length, 1 - margin / length);
    return outletPlacement(segment, {
      x: segment.a.x + dx * safeRatio,
      y: segment.a.y + dy * safeRatio,
    });
  }

  function snapMachineToPlan(state, targetValue, preferredRoom = null) {
    if (!state?.rooms?.length || !targetValue) return null;
    const target = routePoint(targetValue, state.gridCols, state.gridRows);
    const containingRoom = state.rooms.find(room => pointInPolygon(target, room.points, true));
    const room = containingRoom || preferredRoom || [...state.rooms].sort((one, two) => {
      const onePoint = nearestInteriorPoint(one, target);
      const twoPoint = nearestInteriorPoint(two, target);
      return Math.hypot(target.x - onePoint.x, target.y - onePoint.y) - Math.hypot(target.x - twoPoint.x, target.y - twoPoint.y);
    })[0];
    if (!room) return null;
    const position = pointInPolygon(target, room.points, true) ? target : routePoint(nearestInteriorPoint(room, target), state.gridCols, state.gridRows);
    return { roomId: room.id, x: position.x, y: position.y };
  }

  function roomAtMidpoint(a, b, rooms) {
    const midpoint = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    return rooms.find(room => pointInPolygon(midpoint, room.points, false));
  }

  function chooseOutletPlacement(room, state, occupied) {
    const hallwayWalls = state.rooms.filter(item => item.type === 'hallway').flatMap(wallSegments);
    const candidates = wallSegments(room).map(segment => {
      const hallwayDistance = hallwayWalls.length
        ? hallwayWalls.reduce((minimum, hallWall) => Math.min(minimum, distanceToSegment(segment, hallWall.a, hallWall.b)), Infinity)
        : 0;
      const machineDistance = state.machine ? Math.hypot(segment.x - state.machine.x, segment.y - state.machine.y) : 0;
      const occupiedPenalty = occupied.has(pointKey(segment)) ? 1000 : 0;
      const lengthPreference = Math.min(segment.length, 10) * .15;
      return { segment, score: occupiedPenalty + hallwayDistance * 12 + machineDistance * .04 - lengthPreference };
    }).sort((one, two) => one.score - two.score || one.segment.index - two.segment.index);
    return candidates[0] ? outletPlacement(candidates[0].segment) : snapOutletToWall(room, room.points[0]);
  }

  function routeCost(a, b, rooms) {
    const crossed = roomAtMidpoint(a, b, rooms);
    if (!crossed) return 2.5;
    if (crossed.type === 'hallway') return .08;
    if (crossed.type === 'utility' || crossed.type === 'bathroom') return .55;
    if (crossed.type === 'unassigned') return 4;
    return crossed.conditioned ? 40 : 7;
  }

  function findPath(state, starts, targets) {
    const routeStarts = starts.map(value => routePoint(value, state.gridCols, state.gridRows));
    const routeTargets = targets.map(value => routePoint(value, state.gridCols, state.gridRows));
    const targetKeys = new Set(routeTargets.map(pointKey));
    const heuristic = value => routeTargets.reduce((minimum, target) => Math.min(minimum, Math.abs(value.x - target.x) + Math.abs(value.y - target.y)), Infinity);
    const open = [];
    const openKeys = new Set();
    const cost = new Map();
    const previous = new Map();
    routeStarts.forEach(start => {
      const key = pointKey(start);
      if (cost.has(key)) return;
      cost.set(key, 0);
      open.push({ key, point: start, score: heuristic(start) });
      openKeys.add(key);
      previous.set(key, null);
    });
    while (open.length) {
      open.sort((one, two) => one.score - two.score);
      const current = open.shift();
      openKeys.delete(current.key);
      if (targetKeys.has(current.key)) {
        const path = [current.point];
        let cursor = current.key;
        while (previous.get(cursor)) {
          cursor = previous.get(cursor);
          path.push(parsePointKey(cursor));
        }
        return path.reverse();
      }
      const neighbours = [
        { x: current.point.x + ROUTE_STEP, y: current.point.y }, { x: current.point.x - ROUTE_STEP, y: current.point.y },
        { x: current.point.x, y: current.point.y + ROUTE_STEP }, { x: current.point.x, y: current.point.y - ROUTE_STEP },
      ].filter(item => item.x >= 0 && item.y >= 0 && item.x <= state.gridCols && item.y <= state.gridRows);
      neighbours.forEach(next => {
        const nextKey = pointKey(next);
        const stepLength = Math.abs(next.x - current.point.x) + Math.abs(next.y - current.point.y);
        const nextCost = cost.get(current.key) + routeCost(current.point, next, state.rooms) * stepLength;
        if (nextCost >= (cost.get(nextKey) ?? Infinity)) return;
        cost.set(nextKey, nextCost);
        previous.set(nextKey, current.key);
        const score = nextCost + heuristic(next) * .22;
        const existing = open.find(item => item.key === nextKey);
        if (existing) { existing.point = next; existing.score = score; }
        else if (!openKeys.has(nextKey)) { open.push({ key: nextKey, point: next, score }); openKeys.add(nextKey); }
      });
    }
    return null;
  }

  function addPathToNetwork(path, edges, nodes) {
    path.forEach(item => nodes.set(pointKey(item), item));
    for (let index = 1; index < path.length; index += 1) {
      const a = path[index - 1], b = path[index];
      edges.set(edgeKey(a, b), pointKey(a) < pointKey(b) ? { a, b } : { a: b, b: a });
    }
  }

  function automaticNetwork(input = {}) {
    const state = normalizeState(input);
    if (!state.machine || state.phase === 'draw') return { routeEdges: [], outlets: [], trunkKeys: new Set(), trunkHandle: null };
    const selectedRooms = state.rooms.filter(room => room.conditioned && room.type !== 'unassigned');
    if (!selectedRooms.length) return { routeEdges: [], outlets: [], trunkKeys: new Set(), trunkHandle: null };
    const distanceFromMachine = room => {
      const center = polygonCentroid(room.points);
      return Math.abs(center.x - state.machine.x) + Math.abs(center.y - state.machine.y);
    };
    const ordered = [...selectedRooms].sort((one, two) => distanceFromMachine(two) - distanceFromMachine(one));
    const edges = new Map();
    const nodes = new Map([[pointKey(state.machine), { x: state.machine.x, y: state.machine.y }]]);
    const outlets = [];
    const occupiedOutlets = new Set();
    const trunkKeys = new Set();
    let trunkHandle = null;

    ordered.forEach((room, index) => {
      const starts = index === 0 ? [{ x: state.machine.x, y: state.machine.y }] : [...nodes.values()];
      const outlet = state.outletOverrides[room.id]
        ? snapOutletToWall(room, state.outletOverrides[room.id], { wallIndex: state.outletOverrides[room.id].wallIndex, preservePosition: true })
        : chooseOutletPlacement(room, state, occupiedOutlets);
      if (!outlet) return;
      const waypoints = [];
      if (index === 0) waypoints.push(...state.trunkWaypoints);
      waypoints.push(...(state.branchWaypoints[room.id] || []));
      let path = [];
      let segmentStarts = starts;
      for (const destination of [...waypoints, outlet]) {
        const segment = findPath(state, segmentStarts, [destination]);
        if (!segment?.length) { path = null; break; }
        path.push(...(path.length ? segment.slice(1) : segment));
        segmentStarts = [destination];
      }
      if (!path?.length) return;
      addPathToNetwork(path, edges, nodes);
      if (index === 0) {
        for (let pointIndex = 1; pointIndex < path.length; pointIndex += 1) trunkKeys.add(edgeKey(path[pointIndex - 1], path[pointIndex]));
        trunkHandle = state.trunkWaypoints[0] || path[Math.floor(path.length / 2)] || path[0];
      }
      occupiedOutlets.add(pointKey(outlet));
      outlets.push({ id: `outlet-${room.id}`, roomId: room.id, ...outlet });
    });
    return { routeEdges: [...edges.values()], outlets, trunkKeys, trunkHandle, trunkHandles: state.trunkWaypoints.length ? state.trunkWaypoints : [trunkHandle].filter(Boolean) };
  }

  function buildGraph(edges) {
    const graph = new Map();
    const add = (from, to) => {
      if (!graph.has(from)) graph.set(from, []);
      graph.get(from).push(to);
    };
    edges.forEach(edge => {
      const a = pointKey(edge.a), b = pointKey(edge.b);
      add(a, b);
      add(b, a);
    });
    return graph;
  }

  function shortestPath(graph, start, end) {
    if (start === end) return [start];
    if (!graph.has(start) || !graph.has(end)) return null;
    const queue = [start];
    const previous = new Map([[start, null]]);
    for (let index = 0; index < queue.length; index += 1) {
      const current = queue[index];
      for (const next of graph.get(current) || []) {
        if (previous.has(next)) continue;
        previous.set(next, current);
        if (next === end) {
          const path = [end];
          let cursor = current;
          while (cursor !== null) { path.push(cursor); cursor = previous.get(cursor); }
          return path.reverse();
        }
        queue.push(next);
      }
    }
    return null;
  }

  function connectedComponents(edges) {
    const remaining = new Map(edges.map(edge => [edge.key, edge]));
    const components = [];
    while (remaining.size) {
      const first = remaining.values().next().value;
      remaining.delete(first.key);
      const component = [first];
      const nodes = new Set([pointKey(first.a), pointKey(first.b)]);
      let changed = true;
      while (changed) {
        changed = false;
        for (const [key, edge] of [...remaining.entries()]) {
          if (nodes.has(pointKey(edge.a)) || nodes.has(pointKey(edge.b))) {
            component.push(edge);
            nodes.add(pointKey(edge.a));
            nodes.add(pointKey(edge.b));
            remaining.delete(key);
            changed = true;
          }
        }
      }
      components.push(component);
    }
    return components;
  }

  function edgeLengthGrid(edge) {
    return Math.hypot(edge.b.x - edge.a.x, edge.b.y - edge.a.y);
  }

  function calculateProject(input = {}) {
    const state = normalizeState(input);
    const rooms = state.rooms.map(room => enrichRoom(room, state));
    const roomMap = new Map(rooms.map(room => [room.id, room]));
    const generated = automaticNetwork(state);
    const outletMap = new Map(generated.outlets.map(outlet => [outlet.roomId, outlet]));
    const graph = buildGraph(generated.routeEdges);
    const machineKey = state.machine ? pointKey(state.machine) : '';
    const assignments = new Map();
    const roomConnections = new Map();
    rooms.filter(room => room.conditioned && room.type !== 'unassigned').forEach(room => {
      const outlet = outletMap.get(room.id);
      const path = state.machine && outlet ? shortestPath(graph, machineKey, pointKey(outlet)) : null;
      roomConnections.set(room.id, { connected: Boolean(path), path: path || [], outlet: outlet || null });
      if (!path) return;
      for (let index = 1; index < path.length; index += 1) {
        const key = path[index - 1] < path[index] ? `${path[index - 1]}|${path[index]}` : `${path[index]}|${path[index - 1]}`;
        if (!assignments.has(key)) assignments.set(key, new Set());
        assignments.get(key).add(room.id);
      }
    });

    const activeEdges = generated.routeEdges.map(edge => {
      const key = edgeKey(edge.a, edge.b);
      const roomIds = [...(assignments.get(key) || [])].sort();
      const loadFg = roomIds.reduce((sum, id) => sum + (roomMap.get(id)?.loadFg || 0), 0);
      const crossed = roomAtMidpoint(edge.a, edge.b, rooms);
      return {
        ...edge,
        key,
        roomIds,
        loadFg,
        isMain: roomIds.length > 1 || generated.trunkKeys.has(key),
        environment: crossed?.type || 'open',
        ...sizeDuct(loadFg, state),
      };
    });
    const activeEdgeMap = new Map(activeEdges.map(edge => [edge.key, edge]));
    roomConnections.forEach((connection, roomId) => {
      if (!connection.connected || connection.path.length < 2) return;
      if (state.branchWaypoints[roomId]?.length) {
        connection.branchHandles = [...state.branchWaypoints[roomId]];
        connection.branchHandle = connection.branchHandles[0];
        return;
      }
      const exclusiveNodes = [];
      for (let index = 1; index < connection.path.length; index += 1) {
        const a = parsePointKey(connection.path[index - 1]);
        const b = parsePointKey(connection.path[index]);
        if (activeEdgeMap.get(edgeKey(a, b))?.roomIds.length === 1) exclusiveNodes.push(connection.path[index - 1]);
      }
      const candidates = exclusiveNodes.length ? exclusiveNodes : connection.path.slice(1, -1);
      const candidate = candidates[Math.floor(candidates.length / 2)] || connection.path[Math.floor(connection.path.length / 2)];
      connection.branchHandle = parsePointKey(candidate);
      connection.branchHandles = [connection.branchHandle];
    });
    const buckets = new Map();
    activeEdges.filter(edge => edge.loadFg > 0).forEach(edge => {
      const signature = edge.roomIds.join('|');
      if (!buckets.has(signature)) buckets.set(signature, []);
      buckets.get(signature).push(edge);
    });
    const sections = [];
    buckets.forEach(edges => connectedComponents(edges).forEach(component => {
      const sample = component[Math.floor(component.length / 2)];
      const roomIds = sample.roomIds;
      const loadFg = roomIds.reduce((sum, id) => sum + (roomMap.get(id)?.loadFg || 0), 0);
      sections.push({
        id: '',
        roomIds,
        rooms: roomIds.map(id => roomMap.get(id)).filter(Boolean),
        edges: component,
        representative: sample,
        lengthM: component.reduce((sum, edge) => sum + edgeLengthGrid(edge), 0) * state.cellSizeM,
        loadFg,
        isMain: component.some(edge => edge.isMain),
        ...sizeDuct(loadFg, state),
      });
    }));
    let principalIndex = 0, branchIndex = 0;
    sections.sort((one, two) => Number(two.isMain) - Number(one.isMain) || two.loadFg - one.loadFg || two.lengthM - one.lengthM)
      .forEach(section => { section.id = section.isMain ? `P${principalIndex += 1}` : `R${branchIndex += 1}`; });
    const sectionByEdge = new Map();
    sections.forEach(section => section.edges.forEach(edge => sectionByEdge.set(edge.key, section)));
    activeEdges.forEach(edge => { edge.sectionId = sectionByEdge.get(edge.key)?.id || ''; });

    const identified = rooms.filter(room => room.type !== 'unassigned');
    const selectedRooms = identified.filter(room => room.conditioned);
    const connectedRooms = selectedRooms.filter(room => roomConnections.get(room.id)?.connected);
    const loadFg = selectedRooms.reduce((sum, room) => sum + room.loadFg, 0);
    const airflowM3h = selectedRooms.reduce((sum, room) => sum + room.airflowM3h, 0);
    const warnings = [];
    if (!rooms.length) warnings.push({ level: 'info', text: 'Dibuja las estancias para comenzar.' });
    if (rooms.some(room => room.type === 'unassigned')) warnings.push({ level: 'warn', text: 'Falta identificar alguna estancia.' });
    if (identified.length && !selectedRooms.length) warnings.push({ level: 'warn', text: 'Marca al menos una estancia con rejilla.' });
    if (selectedRooms.length && !state.machine) warnings.push({ level: 'info', text: 'Marca la estancia de la unidad interior.' });
    if (state.machine && connectedRooms.length === selectedRooms.length && selectedRooms.length) warnings.push({ level: 'ok', text: 'La red forma un conducto principal y deriva ramales hasta rejillas alineadas con sus paredes.' });
    const constantHeight = activeEdges.every(edge => edge.loadFg <= 0 || edge.heightCm === state.ductHeightCm)
      && sections.every(section => section.heightCm === state.ductHeightCm);
    if (!constantHeight) warnings.push({ level: 'danger', text: 'Se ha detectado una altura incoherente entre tramos. Recalcula el proyecto antes de ejecutarlo.' });
    sections.forEach(section => {
      if (section.velocityMps > 5.2) warnings.push({ level: 'warn', text: `${section.id}: velocidad elevada (${formatNumber(section.velocityMps, 1)} m/s).` });
    });
    return {
      state,
      rooms,
      roomMap,
      outletMap,
      roomConnections,
      trunkHandle: generated.trunkHandle,
      trunkHandles: generated.trunkHandles || [generated.trunkHandle].filter(Boolean),
      activeEdges,
      sections,
      totals: {
        rooms: rooms.length,
        identifiedRooms: identified.length,
        selectedRooms: selectedRooms.length,
        connectedRooms: connectedRooms.length,
        areaM2: rooms.reduce((sum, room) => sum + room.areaM2, 0),
        conditionedAreaM2: selectedRooms.reduce((sum, room) => sum + room.areaM2, 0),
        loadFg,
        airflowM3h,
        suggestedCapacityFg: loadFg > 0 ? roundUp(loadFg, 500) : 0,
        mainDuct: sizeDuct(loadFg, state),
        constantHeightCm: state.ductHeightCm,
        constantHeightVerified: constantHeight,
        hallwayLengthM: activeEdges.filter(edge => edge.environment === 'hallway').reduce((sum, edge) => sum + edgeLengthGrid(edge), 0) * state.cellSizeM,
      },
      warnings: uniqueWarnings(warnings),
    };
  }

  function uniqueWarnings(warnings) {
    const seen = new Set();
    return warnings.filter(item => !seen.has(item.text) && seen.add(item.text));
  }

  function formatNumber(value, decimals = 0) {
    return finite(value).toLocaleString('es-ES', { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function pathData(points, px) {
    return points.map((item, index) => `${index ? 'L' : 'M'} ${px(item.x)} ${px(item.y)}`).join(' ') + ' Z';
  }

  function roomControlPoints(room) {
    const bounds = polygonBounds(room.points);
    const center = nearestInteriorPoint(room, polygonCentroid(room.points));
    return {
      center,
      grille: nearestInteriorPoint(room, { x: bounds.x + bounds.width - .7, y: bounds.y + .7 }),
      machine: nearestInteriorPoint(room, { x: bounds.x + bounds.width - .7, y: bounds.y + bounds.height - .7 }),
    };
  }

  function rectanglesOverlap(one, two, padding = 0) {
    return one.x - padding < two.x + two.width
      && one.x + one.width + padding > two.x
      && one.y - padding < two.y + two.height
      && one.y + one.height + padding > two.y;
  }

  function layoutSectionLabels(result, width = result.state.gridCols * CELL_PX, height = result.state.gridRows * CELL_PX) {
    const labelWidth = 118;
    const labelHeight = 30;
    const occupied = [];
    const routeBounds = result.activeEdges.filter(edge => edge.loadFg > 0).map(edge => {
      const stroke = clamp(7 + edge.widthCm * .28, 9, 24);
      const x1 = edge.a.x * CELL_PX, y1 = edge.a.y * CELL_PX;
      const x2 = edge.b.x * CELL_PX, y2 = edge.b.y * CELL_PX;
      return {
        x: Math.min(x1, x2) - stroke / 2 - 18,
        y: Math.min(y1, y2) - stroke / 2 - 18,
        width: Math.abs(x2 - x1) + stroke + 36,
        height: Math.abs(y2 - y1) + stroke + 36,
      };
    });
    return result.sections.map(section => {
      const edge = section.representative;
      const x1 = edge.a.x * CELL_PX, y1 = edge.a.y * CELL_PX;
      const x2 = edge.b.x * CELL_PX, y2 = edge.b.y * CELL_PX;
      const anchorX = (x1 + x2) / 2, anchorY = (y1 + y2) / 2;
      const dx = x2 - x1, dy = y2 - y1;
      const length = Math.max(1, Math.hypot(dx, dy));
      const normal = { x: -dy / length, y: dx / length };
      const tangent = { x: dx / length, y: dy / length };
      const candidates = [];
      const routeStroke = clamp(7 + section.widthCm * .28, 9, 24);
      const clearance = Math.abs(normal.x) * labelWidth / 2 + Math.abs(normal.y) * labelHeight / 2 + routeStroke / 2 + 22;
      const addCandidate = (centerXValue, centerYValue, baseScore = 0) => {
        const centerX = clamp(centerXValue, labelWidth / 2 + 6, width - labelWidth / 2 - 6);
        const centerY = clamp(centerYValue, labelHeight / 2 + 6, height - labelHeight / 2 - 6);
        const box = { x: centerX - labelWidth / 2, y: centerY - labelHeight / 2, width: labelWidth, height: labelHeight };
        const routeConflicts = routeBounds.filter(route => rectanglesOverlap(box, route, 2)).length;
        const labelConflicts = occupied.filter(previous => rectanglesOverlap(box, previous, 5)).length;
        const distance = Math.hypot(centerX - anchorX, centerY - anchorY);
        candidates.push({ x: centerX, y: centerY, box, score: routeConflicts * 1000000 + labelConflicts * 100000 + distance + baseScore });
      };
      [clearance, -clearance, clearance + 34, -clearance - 34, clearance + 72, -clearance - 72].forEach(offset => {
        [0, 58, -58, 116, -116, 174, -174].forEach(along => {
          addCandidate(anchorX + normal.x * offset + tangent.x * along, anchorY + normal.y * offset + tangent.y * along);
        });
      });
      for (let y = labelHeight / 2 + 9; y <= height - labelHeight / 2 - 9; y += 38) {
        for (let x = labelWidth / 2 + 9; x <= width - labelWidth / 2 - 9; x += 64) addCandidate(x, y, 24);
      }
      const chosen = candidates.sort((one, two) => one.score - two.score || one.y - two.y || one.x - two.x)[0];
      occupied.push(chosen.box);
      return { sectionId: section.id, x: chosen.x, y: chosen.y, anchorX, anchorY, width: labelWidth, height: labelHeight, box: chosen.box };
    });
  }

  function renderPlanSvg(result, options = {}) {
    const { state } = result;
    const drawingPoints = options.drawingPoints || [];
    const selectedAdjustment = options.selectedAdjustment || null;
    const compactConfigure = Boolean(options.compactConfigure);
    const selectedRoomId = options.selectedRoomId || '';
    const width = state.gridCols * CELL_PX;
    const height = state.gridRows * CELL_PX;
    const px = value => value * CELL_PX;
    const hatchPatterns = Object.entries(ROOM_TYPES).map(([type, definition]) => `<pattern id="roomHatch-${type}" width="13" height="13" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><line x1="0" y1="0" x2="0" y2="13" stroke="${definition.color}" stroke-width="4" opacity=".34"/></pattern>`).join('');
    const parts = [
      `<svg class="installation-plan" viewBox="0 0 ${width} ${height}" role="img" aria-label="Plano de ${escapeHtml(state.projectName)}">`,
      `<defs><pattern id="minorGrid" width="${CELL_PX}" height="${CELL_PX}" patternUnits="userSpaceOnUse"><path d="M ${CELL_PX} 0 L 0 0 0 ${CELL_PX}"/></pattern><filter id="planGlow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>${hatchPatterns}</defs>`,
      `<rect class="plan-background" width="${width}" height="${height}"/><rect class="plan-grid" width="${width}" height="${height}"/>`,
    ];

    result.rooms.forEach((room, roomIndex) => {
      const controls = roomControlPoints(room);
      const d = pathData(room.points, px);
      const typeOptions = Object.entries(ROOM_TYPES).map(([value, definition]) => `<option value="${value}"${value === room.type ? ' selected' : ''}>${escapeHtml(definition.label)}</option>`).join('');
      parts.push(`<g class="plan-room room-type-${room.type}${room.conditioned ? ' has-grille' : ' no-grille'}${selectedRoomId === room.id ? ' is-context-selected' : ''}" data-id="${escapeHtml(room.id)}"${state.phase === 'configure' && compactConfigure ? ` data-kind="room-select"` : ''}><path class="room-fill" d="${d}"/>${state.phase !== 'draw' && room.type !== 'unassigned' ? `<path class="room-hatch room-hatch-${room.type}" d="${d}"/>` : ''}<path class="room-wall" d="${d}"/>`);
      if (state.phase === 'draw') {
        parts.push(`<text class="room-number-label" x="${px(controls.center.x)}" y="${px(controls.center.y) + 5}" text-anchor="middle">${roomIndex + 1}</text><g class="room-delete" data-kind="room-delete" data-id="${escapeHtml(room.id)}" transform="translate(${px(controls.machine.x)} ${px(controls.machine.y)})"><circle class="room-delete-hit" r="28"/><circle class="room-delete-button" r="13"/><path d="M-4-4l8 8M4-4l-8 8"/></g>`);
      } else if (state.phase === 'configure') {
        const editorWidth = clamp(polygonBounds(room.points).width * CELL_PX - 36, 112, 190);
        if (compactConfigure) {
          const mobileLabel = room.type === 'unassigned' ? `ESTANCIA ${roomIndex + 1} · TOCA` : room.name.toUpperCase();
          parts.push(`<text class="room-name-label room-context-label" x="${px(controls.center.x)}" y="${px(controls.center.y) + 5}" text-anchor="middle">${escapeHtml(mobileLabel)}</text>`);
        } else {
          parts.push(`<foreignObject class="room-type-editor" x="${px(controls.center.x) - editorWidth / 2}" y="${px(controls.center.y) - 42}" width="${editorWidth}" height="38"><div xmlns="http://www.w3.org/1999/xhtml"><select data-kind="room-type" data-id="${escapeHtml(room.id)}" aria-label="Tipo de ${escapeHtml(room.name)}">${typeOptions}</select></div></foreignObject>`);
        }
        if (!compactConfigure && (room.type === 'living' || room.type === 'kitchen')) {
          const loadOptions = Object.entries(LOAD_TIERS).map(([value, tier]) => `<option value="${value}"${value === room.loadTier ? ' selected' : ''}>${tier.label} · ${formatNumber(tier.loadFg)} frg/h</option>`).join('');
          parts.push(`<foreignObject class="room-load-editor" x="${px(controls.center.x) - editorWidth / 2}" y="${px(controls.center.y) + 2}" width="${editorWidth}" height="34"><div xmlns="http://www.w3.org/1999/xhtml"><select data-kind="room-load" data-id="${escapeHtml(room.id)}" aria-label="Tamaño de ${escapeHtml(room.name)}">${loadOptions}</select></div></foreignObject>`);
        }
        parts.push(`<g class="zone-toggle${room.conditioned ? ' is-checked' : ''}" data-kind="zone-toggle" data-id="${escapeHtml(room.id)}" transform="translate(${px(controls.grille.x)} ${px(controls.grille.y)})"><rect class="control-hit" x="-30" y="-30" width="60" height="60" rx="14"/><rect class="control-box" x="-17" y="-17" width="34" height="34" rx="8"/><path d="M-9-4h18M-9 1h18M-9 6h18"/><title>${room.conditioned ? 'Quitar rejilla' : 'Poner rejilla'} en ${escapeHtml(room.name)}</title></g>`);
        parts.push(`<g class="machine-toggle${state.machine?.roomId === room.id ? ' is-selected' : ''}" data-kind="machine-toggle" data-id="${escapeHtml(room.id)}" transform="translate(${px(controls.machine.x)} ${px(controls.machine.y)})"><rect class="control-hit" x="-30" y="-30" width="60" height="60" rx="14"/><rect class="control-box" x="-17" y="-17" width="34" height="34" rx="8"/><text x="0" y="6" text-anchor="middle">M</text><title>Unidad interior en ${escapeHtml(room.name)}</title></g>`);
      } else {
        parts.push(`<text class="room-name-label" x="${px(controls.center.x)}" y="${px(controls.center.y) - 5}" text-anchor="middle">${escapeHtml(room.name.toUpperCase())}</text>`);
        const demandCopy = room.conditioned ? `${formatNumber(room.loadFg)} FRG/H${room.loadLabel ? ` · ${room.loadLabel.toUpperCase()}` : ''}` : 'SIN REJILLA';
        parts.push(`<text class="room-demand-label" x="${px(controls.center.x)}" y="${px(controls.center.y) + 15}" text-anchor="middle">${escapeHtml(demandCopy)}</text>`);
      }
      parts.push('</g>');
    });

    if (state.phase === 'layout' && state.machine) {
      result.activeEdges.filter(edge => edge.loadFg > 0).forEach(edge => {
        const routeWidth = clamp(7 + edge.widthCm * .28, 9, 24);
        const adjustmentKind = edge.isMain || edge.roomIds.length !== 1 ? 'trunk-drag' : 'branch-drag';
        const adjustmentId = adjustmentKind === 'trunk-drag' ? 'main' : edge.roomIds[0];
        parts.push(`<line class="route-hit" data-kind="${adjustmentKind}" data-id="${escapeHtml(adjustmentId)}" x1="${px(edge.a.x)}" y1="${px(edge.a.y)}" x2="${px(edge.b.x)}" y2="${px(edge.b.y)}"><title>Toca o arrastra este ${adjustmentKind === 'trunk-drag' ? 'conducto principal' : 'ramal'} para ajustar su recorrido</title></line>`);
        parts.push(`<line class="route-edge ${edge.isMain ? 'is-main' : 'is-branch'}${edge.environment === 'hallway' ? ' through-hallway' : ''}" x1="${px(edge.a.x)}" y1="${px(edge.a.y)}" x2="${px(edge.b.x)}" y2="${px(edge.b.y)}" style="--route-width:${routeWidth}px"><title>${edge.isMain ? 'Conducto principal' : 'Ramal'} ${edge.sectionId}: ${edge.widthCm} × ${edge.heightCm} cm · altura común verificada</title></line>`);
      });
      const sectionLabels = layoutSectionLabels(result, width, height);
      result.sections.forEach((section, index) => {
        const label = sectionLabels[index];
        parts.push(`<g class="section-label ${section.isMain ? 'main-label' : ''}" data-section-id="${escapeHtml(section.id)}" transform="translate(${label.x} ${label.y})"><line class="section-leader" x1="${label.anchorX - label.x}" y1="${label.anchorY - label.y}" x2="0" y2="0"/><circle class="section-leader-dot" cx="${label.anchorX - label.x}" cy="${label.anchorY - label.y}" r="3"/><rect x="${-label.width / 2}" y="${-label.height / 2}" width="${label.width}" height="${label.height}" rx="8"/><text x="0" y="4" text-anchor="middle">${section.id} · ${section.widthCm}×${section.heightCm} cm</text><title>${formatNumber(section.airflowM3h)} m³/h · altura ${section.heightCm} cm común a toda la red</title></g>`);
      });
      if (selectedAdjustment?.kind === 'outlet-drag') {
        const selectedRoom = result.roomMap.get(selectedAdjustment.roomId);
        const selectedOutlet = result.outletMap.get(selectedAdjustment.roomId);
        if (selectedRoom) wallSegments(selectedRoom).forEach(wall => {
          const current = selectedOutlet?.wallIndex === wall.index;
          parts.push(`<g class="wall-snap-target${current ? ' is-current' : ''}" data-kind="outlet-wall-target" data-id="${escapeHtml(selectedRoom.id)}" data-wall-index="${wall.index}"><line class="wall-snap-hit" x1="${px(wall.a.x)}" y1="${px(wall.a.y)}" x2="${px(wall.b.x)}" y2="${px(wall.b.y)}"/><line class="wall-snap-line" x1="${px(wall.a.x)}" y1="${px(wall.a.y)}" x2="${px(wall.b.x)}" y2="${px(wall.b.y)}"/><circle cx="${px(wall.x)}" cy="${px(wall.y)}" r="${current ? 9 : 7}"/><title>${current ? 'Pared actual' : 'Colocar la rejilla centrada en esta pared'}</title></g>`);
        });
      }
      result.rooms.forEach(room => {
        const outlet = result.outletMap.get(room.id);
        if (!outlet) return;
        const selected = selectedAdjustment?.kind === 'outlet-drag' && selectedAdjustment.roomId === room.id;
        parts.push(`<g class="plan-outlet is-draggable${selected ? ' is-selected' : ''}" data-kind="outlet-drag" data-id="${escapeHtml(room.id)}" data-wall-index="${outlet.wallIndex}" data-wall-angle="${outlet.wallAngleDeg}" data-centered="${outlet.centered ? 'true' : 'false'}" transform="translate(${px(outlet.x)} ${px(outlet.y)}) rotate(${outlet.wallAngleDeg})"><circle class="drag-hit" r="36"/><rect x="-22" y="-8" width="44" height="16" rx="4"/><path d="M-15-3h30M-15 2h30"/><title>Rejilla ${outlet.centered ? 'centrada automáticamente' : 'ajustada manualmente'} y alineada con la pared · ${escapeHtml(room.name)} · ${room.grille.widthCm} × ${room.grille.heightCm} cm</title></g>`);
      });
      result.roomConnections.forEach((connection, roomId) => {
        if (!connection.branchHandles?.length) return;
        const room = result.roomMap.get(roomId);
        connection.branchHandles.forEach((handle, guideIndex) => {
          const selected = selectedAdjustment?.kind === 'branch-drag' && selectedAdjustment.roomId === roomId && finite(selectedAdjustment.guideIndex) === guideIndex;
          parts.push(`<g class="branch-drag${selected ? ' is-selected' : ''}" data-kind="branch-drag" data-id="${escapeHtml(roomId)}" data-guide-index="${guideIndex}" transform="translate(${px(handle.x)} ${px(handle.y)})"><circle class="drag-hit" r="34"/><path d="M0-10L10 0 0 10-10 0Z"/><circle r="3"/><title>Punto ${guideIndex + 1} del ramal de ${escapeHtml(room?.name || '')} · arrastra o toca para ajustar</title></g>`);
        });
      });
      result.trunkHandles.forEach((handle, guideIndex) => {
        const selected = selectedAdjustment?.kind === 'trunk-drag' && finite(selectedAdjustment.guideIndex) === guideIndex;
        parts.push(`<g class="trunk-drag${selected ? ' is-selected' : ''}" data-kind="trunk-drag" data-id="main" data-guide-index="${guideIndex}" transform="translate(${px(handle.x)} ${px(handle.y)})"><circle class="drag-hit" r="36"/><rect x="-11" y="-11" width="22" height="22" rx="5"/><path d="M-6 0h12M0-6v12"/><title>Punto ${guideIndex + 1} del conducto principal · arrastra o toca para ajustar</title></g>`);
      });
      const machineSelected = selectedAdjustment?.kind === 'machine-drag';
      parts.push(`<g class="plan-machine is-draggable${machineSelected ? ' is-selected' : ''}" data-kind="machine-drag" data-id="machine" transform="translate(${px(state.machine.x)} ${px(state.machine.y)})"><circle class="drag-hit" r="42"/><rect x="-35" y="-27" width="70" height="54" rx="12"/><circle class="machine-fan" cx="0" cy="0" r="15"/><path d="M0-15c9 3 11 8 5 14M15 0c-3 9-8 11-14 5M0 15c-9-3-11-8-5-14M-15 0c3-9 8-11 14-5"/><text x="0" y="-37" text-anchor="middle">UNIDAD INTERIOR</text><title>Arrastra o toca la máquina para situarla en su posición real</title></g>`);
    }

    if (state.phase === 'draw' && drawingPoints.length) {
      const line = drawingPoints.map(item => `${px(item.x)},${px(item.y)}`).join(' ');
      parts.push(`<polyline class="drawing-line" points="${line}"/>`);
      drawingPoints.forEach((item, index) => parts.push(`<g class="drawing-point${index === 0 ? ' first-point' : ''}" ${index === 0 && drawingPoints.length >= 3 ? 'data-kind="close-polygon"' : ''} transform="translate(${px(item.x)} ${px(item.y)})"><circle class="point-hit" r="28"/><circle class="point-dot" r="${index === 0 ? 10 : 7}"/>${index === 0 && drawingPoints.length >= 3 ? '<text x="0" y="-17" text-anchor="middle">CERRAR</text>' : ''}</g>`));
    }
    parts.push(`<g class="scale-marker" transform="translate(${width - 150} ${height - 25})"><line x1="0" y1="0" x2="${CELL_PX * 2}" y2="0"/><path d="M0-6v12M${CELL_PX * 2}-6v12"/><text x="${CELL_PX}" y="-10" text-anchor="middle">${formatNumber(state.cellSizeM * 2, 2)} m</text></g>`);
    parts.push('</svg>');
    return { svg: parts.join(''), width, height };
  }

  function initBrowser() {
    if (typeof document === 'undefined' || !document.getElementById('planStage')) return;
    const $ = id => document.getElementById(id);
    const elements = {
      drawingSettings: $('drawingSettings'), technicalSettings: $('technicalSettings'), cellSize: $('cellSize'), ductHeight: $('ductHeightCm'), grilleHeight: $('grilleHeightCm'),
      phaseBadge: $('phaseBadge'), message: $('assistantMessage'), planStatus: $('planStatus'), planScroll: $('planScroll'), planStage: $('planStage'), planSummary: $('planSummary'), phaseAction: $('phaseAction'),
      automaticResult: $('automaticResult'), networkStatus: $('networkStatus'), resultSummary: $('resultSummary'), alerts: $('ductAlerts'), networkResults: $('networkResults'), roomResults: $('roomResults'),
      legend: $('planControlLegend'), undo: $('undoProject'), redo: $('redoProject'), planFrame: document.querySelector('.plan-frame'), focus: $('planFocusToggle'), cancelAdjustment: $('cancelAdjustment'), resetTrunk: $('resetTrunkGuide'), saveProject: $('saveDuctProject'),
      roomContext: $('ductRoomContext'), contextTitle: $('ductRoomContextTitle'), contextClose: $('ductRoomContextClose'), contextType: $('ductContextType'), contextLoad: $('ductContextLoad'), contextLoadField: $('ductContextLoadField'), contextGrille: $('ductContextGrille'), contextMachine: $('ductContextMachine'),
      adjustmentDock: $('ductAdjustmentDock'), adjustmentTitle: $('ductAdjustmentTitle'), adjustmentHelp: $('ductAdjustmentHelp'), adjustmentClose: $('ductAdjustmentClose'), directionalPad: $('ductDirectionalPad'), outletPad: $('ductOutletPad'), addGuide: $('addAdjustmentGuide'), resetSelected: $('resetSelectedAdjustment'), heightConsistency: $('heightConsistencyBadge'),
    };
    let state = loadState();
    let result = calculateProject(state);
    let drawingPoints = [];
    let transientMessage = '';
    let zoom = 1;
    let drag = null;
    let selectedAdjustment = null;
    let selectedRoomId = '';
    let suppressClick = false;
    let focusMode = false;
    const touchPointers = new Map();
    let pinch = null;
    const history = [];
    const future = [];

    elements.contextType.innerHTML = Object.entries(ROOM_TYPES).map(([value, definition]) => `<option value="${value}">${escapeHtml(definition.label)}</option>`).join('');
    elements.contextLoad.innerHTML = Object.entries(LOAD_TIERS).map(([value, tier]) => `<option value="${value}">${escapeHtml(tier.label)} · ${formatNumber(tier.loadFg)} frg/h</option>`).join('');

    function loadState() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY) || LEGACY_KEYS.map(key => localStorage.getItem(key)).find(Boolean);
        return saved ? normalizeState(JSON.parse(saved)) : emptyState();
      } catch (_) {
        return emptyState();
      }
    }

    function save() {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_) {}
    }

    function commit(next) {
      history.push(JSON.stringify(state));
      if (history.length > 50) history.shift();
      future.length = 0;
      state = normalizeState(next);
      transientMessage = '';
      render();
    }

    function undo() {
      if (drawingPoints.length) {
        drawingPoints.pop();
        transientMessage = '';
        render();
        return;
      }
      if (!history.length) return;
      future.push(JSON.stringify(state));
      state = normalizeState(JSON.parse(history.pop()));
      render();
    }

    function redo() {
      if (!future.length || drawingPoints.length) return;
      history.push(JSON.stringify(state));
      state = normalizeState(JSON.parse(future.pop()));
      render();
    }

    function pointerPoint(event) {
      const svg = elements.planStage.querySelector('svg');
      const svgPoint = svg.createSVGPoint();
      svgPoint.x = event.clientX;
      svgPoint.y = event.clientY;
      const local = svgPoint.matrixTransform(svg.getScreenCTM().inverse());
      return point({ x: local.x / CELL_PX, y: local.y / CELL_PX }, state.gridCols, state.gridRows);
    }

    function adjustmentPosition(adjustment) {
      if (!adjustment) return null;
      const guideIndex = Math.max(0, Math.round(finite(adjustment.guideIndex)));
      if (adjustment.kind === 'outlet-drag') return result.outletMap.get(adjustment.roomId) || null;
      if (adjustment.kind === 'machine-drag') return state.machine;
      if (adjustment.kind === 'branch-drag') return result.roomConnections.get(adjustment.roomId)?.branchHandles?.[guideIndex] || null;
      if (adjustment.kind === 'trunk-drag') return result.trunkHandles?.[guideIndex] || null;
      return null;
    }

    function stateWithMovedAdjustment(currentState, adjustment, position) {
      const guideIndex = Math.max(0, Math.round(finite(adjustment.guideIndex)));
      if (adjustment.kind === 'outlet-drag') {
        const room = currentState.rooms.find(item => item.id === adjustment.roomId);
        if (!room) return currentState;
        const currentOutlet = result.outletMap.get(adjustment.roomId);
        const snapped = snapOutletToWall(room, position, { wallIndex: position?.wallIndex ?? currentOutlet?.wallIndex, preservePosition: true });
        if (!snapped) return currentState;
        return { ...currentState, outletOverrides: { ...currentState.outletOverrides, [adjustment.roomId]: { x: snapped.x, y: snapped.y, wallIndex: snapped.wallIndex } } };
      }
      if (adjustment.kind === 'machine-drag') {
        const machine = snapMachineToPlan(currentState, position, currentState.rooms.find(room => room.id === currentState.machine?.roomId));
        return machine ? { ...currentState, machine } : currentState;
      }
      if (adjustment.kind === 'branch-drag') {
        const nextBranchWaypoints = { ...currentState.branchWaypoints };
        const values = [...(nextBranchWaypoints[adjustment.roomId] || [])];
        values[guideIndex] = routePoint(position, currentState.gridCols, currentState.gridRows);
        nextBranchWaypoints[adjustment.roomId] = values.filter(Boolean).slice(0, 8);
        return { ...currentState, branchWaypoints: nextBranchWaypoints };
      }
      if (adjustment.kind === 'trunk-drag') {
        const values = [...currentState.trunkWaypoints];
        values[guideIndex] = routePoint(position, currentState.gridCols, currentState.gridRows);
        return { ...currentState, trunkWaypoints: values.filter(Boolean).slice(0, 12) };
      }
      return currentState;
    }

    function beginPlanDrag(event) {
      if (state.phase !== 'layout') return;
      const target = event.target.closest('[data-kind="outlet-drag"], [data-kind="branch-drag"], [data-kind="trunk-drag"], [data-kind="machine-drag"]');
      if (!target) return;
      event.preventDefault();
      const adjustment = { kind: target.dataset.kind, roomId: target.dataset.id, guideIndex: Math.max(0, Math.round(finite(target.dataset.guideIndex))) };
      const current = adjustmentPosition(adjustment);
      drag = { ...adjustment, pointerId: event.pointerId, initial: JSON.stringify(state), moved: false, lastPoint: current ? pointKey(current) : '' };
      document.body.classList.add('is-dragging-duct');
    }

    function movePlanDrag(event) {
      if (!drag) return;
      event.preventDefault();
      let position = pointerPoint(event);
      if (drag.kind === 'outlet-drag') {
        const room = state.rooms.find(item => item.id === drag.roomId);
        if (!room) return;
        const currentOutlet = result.outletMap.get(drag.roomId);
        position = snapOutletToWall(room, position, { wallIndex: currentOutlet?.wallIndex, preservePosition: true });
        if (!position) return;
      } else if (drag.kind === 'machine-drag') {
        position = snapMachineToPlan(state, position, state.rooms.find(room => room.id === state.machine?.roomId));
        if (!position) return;
      }
      const positionKey = pointKey(position);
      if (positionKey === drag.lastPoint) return;
      drag.lastPoint = positionKey;
      if (!drag.moved) {
        try { elements.planStage.setPointerCapture(drag.pointerId); } catch (_) {}
        history.push(drag.initial);
        if (history.length > 50) history.shift();
        future.length = 0;
        drag.moved = true;
      }
      state = normalizeState(stateWithMovedAdjustment(state, drag, position));
      if (drag.kind === 'outlet-drag') {
        transientMessage = '<strong>Rejilla ajustada a la pared.</strong> Conserva su alineación y toda la red se recalcula.';
      } else if (drag.kind === 'branch-drag') {
        transientMessage = '<strong>Ajustando ramal.</strong> Suelta el rombo cuando el conducto pase por el lugar real.';
      } else if (drag.kind === 'trunk-drag') {
        transientMessage = '<strong>Ajustando el principal.</strong> Suelta el cuadrado sobre el pasillo o paso real; los ramales se recalculan.';
      } else {
        transientMessage = '<strong>Moviendo la unidad interior.</strong> La red completa se redibuja desde su nueva posición.';
      }
      render();
    }

    function endPlanDrag(event) {
      if (!drag) return;
      const moved = drag.moved;
      const pointerId = drag.pointerId;
      drag = null;
      try { if (elements.planStage.hasPointerCapture(pointerId)) elements.planStage.releasePointerCapture(pointerId); } catch (_) {}
      document.body.classList.remove('is-dragging-duct');
      suppressClick = moved;
      if (moved) {
        selectedAdjustment = null;
        transientMessage = '';
        render();
      }
      if (moved) setTimeout(() => { suppressClick = false; }, 120);
    }

    function applyZoom() {
      const svg = elements.planStage.querySelector('svg');
      if (!svg) return;
      const width = finite(elements.planStage.dataset.width, 900);
      svg.style.width = `${Math.max(520, width * zoom)}px`;
      svg.style.maxWidth = 'none';
    }

    function fitPlan() {
      const width = finite(elements.planStage.dataset.width, 900);
      const minimumZoom = window.innerWidth < 760 ? .55 : .34;
      zoom = clamp(Math.max(300, elements.planScroll.clientWidth - 12) / width, minimumZoom, 1.35);
      applyZoom();
      requestAnimationFrame(() => { elements.planScroll.scrollLeft = Math.max(0, (elements.planScroll.scrollWidth - elements.planScroll.clientWidth) / 2); });
    }

    function renderPlan() {
      const rendered = renderPlanSvg(result, { drawingPoints, selectedAdjustment, selectedRoomId, compactConfigure: window.matchMedia('(max-width: 760px)').matches });
      elements.planStage.innerHTML = rendered.svg;
      elements.planStage.dataset.width = rendered.width;
      applyZoom();
    }

    function renderControls() {
      const drawing = state.phase === 'draw';
      elements.drawingSettings.hidden = !drawing;
      elements.technicalSettings.hidden = drawing;
      elements.legend.hidden = drawing;
      elements.phaseBadge.textContent = drawing ? 'DIBUJANDO EL PLANO' : state.phase === 'configure' ? 'IDENTIFICA Y MARCA SOBRE EL PLANO' : 'AJUSTA LA INSTALACIÓN REAL';
      elements.phaseBadge.classList.toggle('is-configuring', !drawing);
      elements.cellSize.value = String(state.cellSizeM);
      elements.ductHeight.value = state.ductHeightCm;
      elements.grilleHeight.value = state.grilleHeightCm;
      const identified = state.rooms.length > 0 && state.rooms.every(room => room.type !== 'unassigned');
      const ready = identified && result.totals.selectedRooms > 0 && Boolean(state.machine);
      elements.phaseAction.disabled = drawing ? !state.rooms.length || drawingPoints.length > 0 : state.phase === 'configure' ? !ready : false;
      elements.phaseAction.classList.toggle('is-complete', !drawing);
      elements.phaseAction.classList.toggle('is-layout', state.phase === 'layout');
      elements.phaseAction.querySelector('span').textContent = drawing ? 'He terminado de dibujar' : state.phase === 'configure' ? 'Calcular y ajustar' : 'Editar estancias';
      elements.cancelAdjustment.hidden = !selectedAdjustment;
      elements.resetTrunk.hidden = state.phase !== 'layout' || !state.trunkWaypoints.length;
      elements.saveProject.disabled = state.phase !== 'layout' || !ready;
      elements.legend.innerHTML = state.phase === 'layout'
        ? '<span><i class="legend-grille">▤</i><b>Desliza la rejilla</b></span><span><i class="legend-branch">◆</i><b>Mueve cada ramal</b></span><span><i class="legend-main">＋</i><b>Mueve el principal</b></span><span><i class="legend-machine">M</i><b>Mueve la máquina</b></span><span><i class="legend-live">↻</i><b>Recálculo inmediato</b></span>'
        : '<span><i class="legend-type">▼</i><b>Qué estancia es</b></span><span><i class="legend-grille">▤</i><b>Lleva rejilla</b></span><span><i class="legend-machine">M</i><b>Aquí va la máquina</b></span>';
    }

    function renderAdjustmentDock() {
      const visible = state.phase === 'layout' && Boolean(selectedAdjustment);
      elements.adjustmentDock.hidden = !visible;
      if (!visible) return;
      const room = result.roomMap.get(selectedAdjustment.roomId);
      const guideIndex = Math.max(0, Math.round(finite(selectedAdjustment.guideIndex)));
      const labels = {
        'outlet-drag': `Rejilla · ${room?.name || 'estancia'}`,
        'branch-drag': `Ramal de ${room?.name || 'estancia'} · punto ${guideIndex + 1}`,
        'trunk-drag': `Conducto principal · punto ${guideIndex + 1}`,
        'machine-drag': 'Unidad interior',
      };
      elements.adjustmentTitle.textContent = labels[selectedAdjustment.kind] || 'Elemento seleccionado';
      const stepCm = Math.round(ROUTE_STEP * state.cellSizeM * 100);
      elements.adjustmentHelp.textContent = selectedAdjustment.kind === 'outlet-drag'
        ? `Desliza la rejilla ${stepCm} cm por la pared, céntrala o toca otra pared del plano. Siempre conservará su alineación.`
        : `Muévelo en pasos de ${stepCm} cm o toca directamente su nueva posición. Todas las secciones se recalculan al instante.`;
      const outlet = selectedAdjustment.kind === 'outlet-drag';
      elements.outletPad.hidden = !outlet;
      elements.directionalPad.hidden = outlet;
      elements.addGuide.hidden = !['branch-drag', 'trunk-drag'].includes(selectedAdjustment.kind);
      elements.resetSelected.textContent = selectedAdjustment.kind === 'machine-drag' ? '◎ Centrar en estancia' : '↺ Recuperar automático';
      const centerButton = elements.directionalPad.querySelector('[data-adjust-action="center"]');
      centerButton.disabled = selectedAdjustment.kind !== 'machine-drag';
      centerButton.title = selectedAdjustment.kind === 'machine-drag' ? 'Centrar la máquina en su estancia actual' : 'Usa las flechas para desplazar';
    }

    function renderRoomContext() {
      const room = state.rooms.find(item => item.id === selectedRoomId);
      const visible = state.phase === 'configure' && Boolean(room) && window.matchMedia('(max-width: 760px)').matches;
      elements.roomContext.hidden = !visible;
      if (!visible) return;
      elements.contextTitle.textContent = room.name || `Estancia ${state.rooms.indexOf(room) + 1}`;
      elements.contextType.value = room.type;
      const adjustableLoad = room.type === 'living' || room.type === 'kitchen';
      elements.contextLoadField.hidden = !adjustableLoad;
      elements.contextLoad.value = room.loadTier || 'normal';
      elements.contextGrille.classList.toggle('is-active', room.conditioned);
      elements.contextMachine.classList.toggle('is-active', state.machine?.roomId === room.id);
      elements.contextGrille.querySelector('span').textContent = room.conditioned ? 'Con rejilla' : 'Sin rejilla';
      elements.contextMachine.querySelector('span').textContent = state.machine?.roomId === room.id ? 'Máquina aquí' : 'Poner máquina';
    }

    function renderMessage() {
      const icon = elements.message.querySelector('span');
      const copy = elements.message.querySelector('p');
      if (transientMessage) {
        icon.textContent = '!';
        copy.innerHTML = transientMessage;
        return;
      }
      if (state.phase === 'draw') {
        icon.textContent = drawingPoints.length ? drawingPoints.length : '✦';
        if (!drawingPoints.length) copy.innerHTML = '<strong>Toca todas las esquinas de una estancia.</strong> Puede tener ángulos y diagonales; no hace falta decir todavía qué estancia es.';
        else if (drawingPoints.length < 3) copy.innerHTML = `<strong>${drawingPoints.length} ${drawingPoints.length === 1 ? 'esquina marcada' : 'esquinas marcadas'}.</strong> Continúa recorriendo el contorno.`;
        else copy.innerHTML = '<strong>Continúa o toca de nuevo el primer punto para cerrar.</strong> Después puedes dibujar la siguiente estancia.';
        elements.planStatus.textContent = drawingPoints.length ? 'Dibujando una estancia' : `${state.rooms.length} estancias dibujadas`;
      } else if (state.phase === 'configure') {
        const pending = state.rooms.filter(room => room.type === 'unassigned').length;
        icon.textContent = pending ? pending : '✓';
        copy.innerHTML = pending
          ? `<strong>Elige el tipo de las ${pending} ${pending === 1 ? 'estancia pendiente' : 'estancias pendientes'}.</strong> En cada estancia también tienes una casilla rosa para rejilla y otra naranja para la máquina.`
          : '<strong>Plano identificado.</strong> Marca las rejillas y una única ubicación de máquina; después pulsa «Calcular y ajustar».';
        elements.planStatus.textContent = state.machine && result.totals.selectedRooms ? 'Listo para calcular y ajustar' : 'Configurando la instalación';
      } else {
        icon.textContent = '↔';
        if (selectedAdjustment) {
          const item = selectedAdjustment.kind === 'outlet-drag' ? 'rejilla' : selectedAdjustment.kind === 'branch-drag' ? 'ramal' : selectedAdjustment.kind === 'machine-drag' ? 'máquina' : 'principal';
          copy.innerHTML = `<strong>${item === 'rejilla' ? 'Rejilla seleccionada' : item === 'ramal' ? 'Ramal seleccionado' : item === 'máquina' ? 'Unidad interior seleccionada' : 'Conducto principal seleccionado'}.</strong> ${item === 'rejilla' ? 'Toca la posición exacta sobre una pared o usa el ajuste preciso.' : 'Toca en el plano el lugar real o utiliza las flechas grandes.'}`;
        } else copy.innerHTML = '<strong>Ajusta la instalación a la obra real.</strong> Puedes tocar o arrastrar cualquier conducto, rejilla o la máquina. Los rótulos quedan fuera del trazado para no ocultarlo.';
        elements.planStatus.textContent = drag ? 'Recalculando mientras mueves' : selectedAdjustment ? 'Toca la nueva posición' : 'Plano calculado y ajustable';
      }
    }

    function renderSummary() {
      const pending = state.rooms.filter(room => room.type === 'unassigned').length;
      elements.planSummary.innerHTML = `<span><b>${result.totals.rooms}</b> estancias</span>${state.phase !== 'draw' ? `<span><b>${result.totals.selectedRooms}</b> con rejilla</span><span><b>${state.machine ? '1' : '0'}</b> máquina</span><span><b>${formatNumber(result.totals.loadFg)}</b> frg/h</span>${pending ? `<span class="pending-summary"><b>${pending}</b> sin identificar</span>` : ''}` : ''}`;
    }

    function metric(label, value, note, color) {
      return `<article style="--metric-color:${color}"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`;
    }

    function renderResults() {
      const ready = state.phase === 'layout' && state.machine && result.totals.selectedRooms > 0 && result.totals.identifiedRooms === result.totals.rooms;
      elements.automaticResult.hidden = !ready;
      if (!ready) return;
      elements.networkStatus.textContent = result.totals.connectedRooms === result.totals.selectedRooms ? 'RED COMPLETA' : 'REVISAR RECORRIDO';
      elements.resultSummary.innerHTML = [
        metric('Zonas con rejilla', `${result.totals.selectedRooms} estancias`, 'Demanda asignada por uso', '#00c8ff'),
        metric('Necesidad estimada', `${formatNumber(result.totals.suggestedCapacityFg)} frg/h`, 'Dato para seleccionar la máquina', '#ff7a00'),
        metric('Caudal de impulsión', `${formatNumber(result.totals.airflowM3h)} m³/h`, 'Distribuido entre las rejillas', '#51ff7d'),
        metric('Salida principal', `${result.totals.mainDuct.widthCm} × ${result.totals.mainDuct.heightCm} cm`, `${formatNumber(result.totals.mainDuct.velocityMps, 1)} m/s`, '#ff3fa7'),
      ].join('');
      elements.alerts.innerHTML = result.warnings.filter(item => item.level !== 'info').map(item => `<p class="alert-${item.level}"><span>${item.level === 'ok' ? '✓' : '!'}</span>${escapeHtml(item.text)}</p>`).join('');
      elements.heightConsistency.innerHTML = result.totals.constantHeightVerified
        ? `<span>✓</span><strong>Altura única verificada: ${result.totals.constantHeightCm} cm en principal y ramales</strong><small>Solo cambia el ancho, siempre en escalones comerciales de 5 cm.</small>`
        : '<span>!</span><strong>Revisar altura de la red</strong><small>Hay un tramo incoherente y no debe ejecutarse.</small>';
      elements.heightConsistency.classList.toggle('is-error', !result.totals.constantHeightVerified);
      elements.networkResults.innerHTML = result.sections.map(section => `<div class="result-row ${section.isMain ? 'main-section' : ''}"><b>${section.id}</b><span><strong>${section.isMain ? 'Conducto principal' : section.rooms.map(room => escapeHtml(room.name)).join(' · ')}</strong><small>${formatNumber(section.lengthM, 1)} m · ${formatNumber(section.airflowM3h)} m³/h</small></span><em>${section.widthCm} × ${section.heightCm} cm</em></div>`).join('');
      elements.roomResults.innerHTML = result.rooms.filter(room => room.conditioned && room.type !== 'unassigned').map(room => `<div class="result-row room-result"><b>▥</b><span><strong>${escapeHtml(room.name)} · ${formatNumber(room.loadFg)} frg/h</strong><small>${formatNumber(room.airflowM3h)} m³/h · ramal ${room.branchDuct.widthCm} × ${room.branchDuct.heightCm} cm</small></span><em>${room.grille.widthCm} × ${room.grille.heightCm} cm</em></div>`).join('');
    }

    function render() {
      result = calculateProject(state);
      renderControls();
      renderMessage();
      renderPlan();
      renderAdjustmentDock();
      renderRoomContext();
      renderSummary();
      renderResults();
      elements.undo.disabled = !history.length && !drawingPoints.length;
      elements.redo.disabled = !future.length || drawingPoints.length > 0;
      save();
    }

    function closePolygon() {
      if (drawingPoints.length < 3) return;
      if (polygonArea(drawingPoints) < 1) {
        transientMessage = '<strong>La estancia es demasiado pequeña.</strong> Marca un contorno mayor.';
        render();
        return;
      }
      if (polygonSelfIntersects(drawingPoints)) {
        transientMessage = '<strong>El contorno se cruza consigo mismo.</strong> Deshaz el último punto y corrígelo.';
        render();
        return;
      }
      const candidate = { points: [...drawingPoints] };
      if (state.rooms.some(room => roomOverlap(candidate, room))) {
        transientMessage = '<strong>Esta estancia invade otra.</strong> Puedes compartir paredes, pero no superponerlas.';
        render();
        return;
      }
      const id = `room-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`;
      drawingPoints = [];
      commit({ ...state, rooms: [...state.rooms, { id, type: 'unassigned', points: candidate.points, conditioned: false }] });
    }

    function handlePlanClick(event) {
      if (suppressClick) return;
      const target = event.target.closest('[data-kind]');
      if (state.phase === 'draw') {
        if (target?.dataset.kind === 'room-delete') {
          commit({ ...state, rooms: state.rooms.filter(room => room.id !== target.dataset.id), machine: state.machine?.roomId === target.dataset.id ? null : state.machine });
          return;
        }
        if (target?.dataset.kind === 'close-polygon') { closePolygon(); return; }
        const position = pointerPoint(event);
        if (drawingPoints.length >= 3 && pointKey(position) === pointKey(drawingPoints[0])) { closePolygon(); return; }
        if (drawingPoints.length && pointKey(position) === pointKey(drawingPoints.at(-1))) return;
        drawingPoints.push(position);
        transientMessage = '';
        render();
        return;
      }
      if (state.phase === 'layout') {
        if (target && ['outlet-drag', 'branch-drag', 'trunk-drag', 'machine-drag'].includes(target.dataset.kind)) {
          const next = { kind: target.dataset.kind, roomId: target.dataset.id, guideIndex: Math.max(0, Math.round(finite(target.dataset.guideIndex))) };
          selectedAdjustment = selectedAdjustment?.kind === next.kind && selectedAdjustment.roomId === next.roomId && finite(selectedAdjustment.guideIndex) === next.guideIndex ? null : next;
          transientMessage = '';
          render();
          if (selectedAdjustment && window.matchMedia('(max-width: 760px)').matches && !focusMode) toggleFocus(true);
          return;
        }
        if (!selectedAdjustment) return;
        let position = pointerPoint(event);
        if (selectedAdjustment.kind === 'outlet-drag') {
          const room = state.rooms.find(item => item.id === selectedAdjustment.roomId);
          if (!room) return;
          position = snapOutletToWall(room, position, { wallIndex: target?.dataset.kind === 'outlet-wall-target' ? target.dataset.wallIndex : undefined, preservePosition: true });
          if (!position) return;
          const adjustment = selectedAdjustment;
          selectedAdjustment = null;
          commit(stateWithMovedAdjustment(state, adjustment, position));
        } else if (selectedAdjustment.kind === 'machine-drag') {
          const adjustment = selectedAdjustment;
          selectedAdjustment = null;
          commit(stateWithMovedAdjustment(state, adjustment, position));
        } else {
          const adjustment = selectedAdjustment;
          selectedAdjustment = null;
          commit(stateWithMovedAdjustment(state, adjustment, position));
        }
        return;
      }
      if (state.phase !== 'configure') return;
      if (!target) return;
      if (target.dataset.kind === 'room-select') {
        selectedRoomId = target.dataset.id;
        render();
      } else if (target.dataset.kind === 'zone-toggle') {
        commit({ ...state, rooms: state.rooms.map(room => room.id === target.dataset.id ? { ...room, conditioned: !room.conditioned } : room) });
      } else if (target.dataset.kind === 'machine-toggle') {
        const room = state.rooms.find(item => item.id === target.dataset.id);
        if (!room) return;
        const machinePoint = point(roomControlPoints(room).machine, state.gridCols, state.gridRows);
        commit({ ...state, machine: state.machine?.roomId === room.id ? null : { roomId: room.id, ...machinePoint } });
        setTimeout(() => { if (!elements.automaticResult.hidden) elements.automaticResult.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 250);
      }
    }

    function toggleFocus(force) {
      focusMode = typeof force === 'boolean' ? force : !focusMode;
      elements.planFrame.classList.toggle('is-focus-mode', focusMode);
      document.body.classList.toggle('duct-plan-focus', focusMode);
      elements.focus.setAttribute('aria-pressed', String(focusMode));
      elements.focus.textContent = focusMode ? 'Cerrar plano' : 'Plano grande';
      setTimeout(fitPlan, 50);
    }

    function touchDistance(points) {
      const [a, b] = [...points.values()];
      return Math.hypot(a.x - b.x, a.y - b.y);
    }

    function touchMidpoint(points) {
      const [a, b] = [...points.values()];
      return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    }

    function trackTouchStart(event) {
      if (event.pointerType !== 'touch' || !focusMode) return;
      touchPointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (touchPointers.size === 2) {
        pinch = { distance: touchDistance(touchPointers), zoom, midpoint: touchMidpoint(touchPointers), left: elements.planScroll.scrollLeft, top: elements.planScroll.scrollTop };
        suppressClick = true;
      }
    }

    function trackTouchMove(event) {
      if (!touchPointers.has(event.pointerId) || !pinch) return;
      event.preventDefault();
      touchPointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (touchPointers.size < 2) return;
      const midpoint = touchMidpoint(touchPointers);
      zoom = clamp(pinch.zoom * touchDistance(touchPointers) / Math.max(1, pinch.distance), .3, 2.2);
      applyZoom();
      elements.planScroll.scrollLeft = pinch.left - (midpoint.x - pinch.midpoint.x);
      elements.planScroll.scrollTop = pinch.top - (midpoint.y - pinch.midpoint.y);
    }

    function trackTouchEnd(event) {
      touchPointers.delete(event.pointerId);
      if (touchPointers.size < 2 && pinch) {
        pinch = null;
        setTimeout(() => { suppressClick = false; }, 160);
      }
    }

    function moveSelectedWithButton(action) {
      if (!selectedAdjustment) return;
      const current = adjustmentPosition(selectedAdjustment);
      if (!current) return;
      let target = { x: current.x, y: current.y };
      if (selectedAdjustment.kind === 'outlet-drag') {
        const room = state.rooms.find(item => item.id === selectedAdjustment.roomId);
        const walls = room ? wallSegments(room) : [];
        const wallPosition = walls.findIndex(item => item.index === current.wallIndex);
        const wall = walls[wallPosition];
        if (!wall) return;
        if (action === 'wall-previous' || action === 'wall-next') {
          const direction = action === 'wall-previous' ? -1 : 1;
          const nextWall = walls[(wallPosition + direction + walls.length) % walls.length];
          target = { x: nextWall.x, y: nextWall.y, wallIndex: nextWall.index };
        } else if (action === 'center') target = { x: wall.x, y: wall.y, wallIndex: wall.index };
        else {
          const direction = action === 'outlet-back' ? -1 : action === 'outlet-forward' ? 1 : 0;
          if (!direction) return;
          target = {
            x: current.x + (wall.b.x - wall.a.x) / wall.length * ROUTE_STEP * direction,
            y: current.y + (wall.b.y - wall.a.y) / wall.length * ROUTE_STEP * direction,
            wallIndex: wall.index,
          };
        }
      } else if (selectedAdjustment.kind === 'machine-drag' && action === 'center') {
        const room = state.rooms.find(item => item.id === state.machine?.roomId);
        if (!room) return;
        target = nearestInteriorPoint(room, polygonCentroid(room.points));
      } else {
        const deltas = { up: [0, -ROUTE_STEP], down: [0, ROUTE_STEP], left: [-ROUTE_STEP, 0], right: [ROUTE_STEP, 0] };
        const delta = deltas[action];
        if (!delta) return;
        target = { x: current.x + delta[0], y: current.y + delta[1] };
      }
      commit(stateWithMovedAdjustment(state, selectedAdjustment, target));
    }

    function addSelectedGuide() {
      if (!selectedAdjustment || !['branch-drag', 'trunk-drag'].includes(selectedAdjustment.kind)) return;
      const isBranch = selectedAdjustment.kind === 'branch-drag';
      const existing = isBranch
        ? [...(state.branchWaypoints[selectedAdjustment.roomId] || result.roomConnections.get(selectedAdjustment.roomId)?.branchHandles || [])]
        : [...(state.trunkWaypoints.length ? state.trunkWaypoints : result.trunkHandles || [])];
      const base = existing.at(-1) || state.machine;
      if (!base) return;
      const candidate = routePoint({ x: base.x + (base.x + ROUTE_STEP <= state.gridCols ? ROUTE_STEP : -ROUTE_STEP), y: base.y }, state.gridCols, state.gridRows);
      existing.push(candidate);
      const guideIndex = existing.length - 1;
      if (isBranch) {
        const branchWaypoints = { ...state.branchWaypoints, [selectedAdjustment.roomId]: existing.slice(0, 8) };
        selectedAdjustment = { ...selectedAdjustment, guideIndex };
        commit({ ...state, branchWaypoints });
      } else {
        selectedAdjustment = { ...selectedAdjustment, guideIndex };
        commit({ ...state, trunkWaypoints: existing.slice(0, 12) });
      }
      transientMessage = '<strong>Nuevo punto de paso añadido.</strong> Muévelo hasta el siguiente codo o paso obligado de la obra.';
      render();
    }

    function resetCurrentAdjustment() {
      if (!selectedAdjustment) return;
      let next = state;
      if (selectedAdjustment.kind === 'outlet-drag') {
        const outletOverrides = { ...state.outletOverrides };
        delete outletOverrides[selectedAdjustment.roomId];
        next = { ...state, outletOverrides };
      } else if (selectedAdjustment.kind === 'branch-drag') {
        const branchWaypoints = { ...state.branchWaypoints };
        delete branchWaypoints[selectedAdjustment.roomId];
        next = { ...state, branchWaypoints };
      } else if (selectedAdjustment.kind === 'trunk-drag') {
        next = { ...state, trunkWaypoints: [], trunkGuide: null };
      } else if (selectedAdjustment.kind === 'machine-drag') {
        const room = state.rooms.find(item => item.id === state.machine?.roomId);
        if (room) next = { ...state, machine: { roomId: room.id, ...routePoint(nearestInteriorPoint(room, polygonCentroid(room.points)), state.gridCols, state.gridRows) } };
      }
      selectedAdjustment = null;
      commit(next);
    }

    function saveInProject() {
      const API = window.SuperTecnicoProjects;
      if (!API || state.phase !== 'layout') return;
      const measurements = [];
      result.sections.forEach(section => measurements.push({ code: `DUCT-RECT-${section.widthCm}X${section.heightCm}`, description: `Conducto rectangular ${section.widthCm} × ${section.heightCm} cm`, unit: 'm', quantity: section.lengthM }));
      result.rooms.filter(room => room.conditioned && room.type !== 'unassigned').forEach(room => measurements.push({ code: `GRILLE-${room.grille.widthCm}X${room.grille.heightCm}`, description: `Rejilla ${room.grille.widthCm} × ${room.grille.heightCm} cm`, unit: 'ud', quantity: 1 }));
      const saved = API.attachArtifact({
        module_id: 'ducts', discipline: 'climatizacion', title: state.projectName || 'Diseño de conductos', source_page: 'conductos.html', status: 'predesign',
        summary: `${result.totals.selectedRooms} zonas · ${formatNumber(result.totals.airflowM3h)} m³/h · principal ${result.totals.mainDuct.widthCm} × ${result.totals.mainDuct.heightCm} cm`,
        warnings: result.warnings.map(item => item.text), measurements,
        snapshot: { state, totals: result.totals, sections: result.sections.map(section => ({ id: section.id, lengthM: section.lengthM, airflowM3h: section.airflowM3h, widthCm: section.widthCm, heightCm: section.heightCm, rooms: section.rooms.map(room => room.name) })), rooms: result.rooms.map(room => ({ id: room.id, name: room.name, type: room.type, conditioned: room.conditioned, loadFg: room.loadFg, airflowM3h: room.airflowM3h, branchDuct: room.branchDuct, grille: room.grille })) },
      });
      transientMessage = `<strong>Guardado en «${escapeHtml(saved.project.name)}».</strong> Puedes abrir Mis proyectos para reunirlo con otras herramientas.`;
      render();
    }

    elements.planStage.addEventListener('pointerdown', beginPlanDrag);
    elements.planStage.addEventListener('click', handlePlanClick);
    elements.planStage.addEventListener('change', event => {
      const typeSelect = event.target.closest('[data-kind="room-type"]');
      if (typeSelect) {
        commit({ ...state, rooms: state.rooms.map(room => room.id === typeSelect.dataset.id ? { ...room, type: typeSelect.value, loadTier: 'normal' } : room) });
        return;
      }
      const loadSelect = event.target.closest('[data-kind="room-load"]');
      if (loadSelect) commit({ ...state, rooms: state.rooms.map(room => room.id === loadSelect.dataset.id ? { ...room, loadTier: loadSelect.value } : room) });
    });
    elements.phaseAction.addEventListener('click', () => {
      if (state.phase === 'draw') {
        if (!state.rooms.length || drawingPoints.length) return;
        commit({ ...state, phase: 'configure' });
      } else if (state.phase === 'configure') {
        const ready = state.rooms.length && state.rooms.every(room => room.type !== 'unassigned') && result.totals.selectedRooms && state.machine;
        if (!ready) return;
        commit({ ...state, phase: 'layout' });
      } else commit({ ...state, phase: 'configure' });
    });
    elements.cellSize.addEventListener('change', () => commit({ ...state, cellSizeM: elements.cellSize.value }));
    elements.ductHeight.addEventListener('change', () => commit({ ...state, ductHeightCm: elements.ductHeight.value }));
    elements.grilleHeight.addEventListener('change', () => commit({ ...state, grilleHeightCm: elements.grilleHeight.value }));
    window.addEventListener('pointermove', movePlanDrag, { passive: false });
    window.addEventListener('pointerup', endPlanDrag);
    window.addEventListener('pointercancel', endPlanDrag);
    window.addEventListener('pointerup', trackTouchEnd);
    window.addEventListener('pointercancel', trackTouchEnd);
    elements.undo.addEventListener('click', undo);
    elements.redo.addEventListener('click', redo);
    elements.focus.addEventListener('click', () => toggleFocus());
    elements.cancelAdjustment.addEventListener('click', () => { selectedAdjustment = null; render(); });
    elements.resetTrunk.addEventListener('click', () => { selectedAdjustment = null; commit({ ...state, trunkWaypoints: [], trunkGuide: null }); });
    elements.adjustmentClose.addEventListener('click', () => { selectedAdjustment = null; render(); });
    elements.adjustmentDock.addEventListener('click', event => {
      const actionButton = event.target.closest('[data-adjust-action]');
      if (actionButton) moveSelectedWithButton(actionButton.dataset.adjustAction);
    });
    elements.addGuide.addEventListener('click', addSelectedGuide);
    elements.resetSelected.addEventListener('click', resetCurrentAdjustment);
    elements.contextClose.addEventListener('click', () => { selectedRoomId = ''; render(); });
    elements.contextType.addEventListener('change', () => {
      const roomId = selectedRoomId;
      commit({ ...state, rooms: state.rooms.map(room => room.id === roomId ? { ...room, type: elements.contextType.value, loadTier: 'normal' } : room) });
    });
    elements.contextLoad.addEventListener('change', () => {
      const roomId = selectedRoomId;
      commit({ ...state, rooms: state.rooms.map(room => room.id === roomId ? { ...room, loadTier: elements.contextLoad.value } : room) });
    });
    elements.contextGrille.addEventListener('click', () => {
      const roomId = selectedRoomId;
      commit({ ...state, rooms: state.rooms.map(room => room.id === roomId ? { ...room, conditioned: !room.conditioned } : room) });
    });
    elements.contextMachine.addEventListener('click', () => {
      const room = state.rooms.find(item => item.id === selectedRoomId);
      if (!room) return;
      const machinePoint = point(roomControlPoints(room).machine, state.gridCols, state.gridRows);
      commit({ ...state, machine: state.machine?.roomId === room.id ? null : { roomId: room.id, ...machinePoint } });
    });
    elements.saveProject.addEventListener('click', saveInProject);
    elements.planScroll.addEventListener('pointerdown', trackTouchStart);
    elements.planScroll.addEventListener('pointermove', trackTouchMove, { passive: false });
    $('zoomIn').addEventListener('click', () => { zoom = clamp(zoom + .12, .3, 2); applyZoom(); });
    $('zoomOut').addEventListener('click', () => { zoom = clamp(zoom - .12, .3, 2); applyZoom(); });
    $('zoomFit').addEventListener('click', fitPlan);
    $('loadExample').addEventListener('click', () => { if (state.rooms.length && !confirm('¿Sustituir el plano actual por el ejemplo?')) return; drawingPoints = []; commit(exampleState()); setTimeout(fitPlan, 40); });
    $('clearProject').addEventListener('click', () => { if (state.rooms.length && !confirm('¿Empezar un plano nuevo?')) return; drawingPoints = []; commit(emptyState()); });
    $('printProject').addEventListener('click', () => window.print());
    window.addEventListener('resize', () => { if (window.innerWidth < 760) fitPlan(); });
    window.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); event.shiftKey ? redo() : undo(); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); redo(); }
      if (event.key === 'Escape' && focusMode) { toggleFocus(false); return; }
      if (event.key === 'Escape' && selectedAdjustment) { selectedAdjustment = null; render(); return; }
      if (event.key === 'Escape' && drawingPoints.length) { drawingPoints = []; render(); }
    });

    render();
    requestAnimationFrame(fitPlan);
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initBrowser);
    else initBrowser();
  }

  return {
    DESIGN,
    DEFAULTS,
    ROOM_TYPES,
    ROOM_LOADS,
    LOAD_TIERS,
    normalizeState,
    emptyState,
    exampleState,
    polygonArea,
    polygonSelfIntersects,
    pointInPolygon,
    roomOverlap,
    wallSegments,
    snapOutletToWall,
    snapMachineToPlan,
    sizeDuct,
    loadForRoom,
    automaticNetwork,
    calculateProject,
    layoutSectionLabels,
    renderPlanSvg,
    roundUp,
    geometry: Object.freeze({
      point,
      routePoint,
      pointKey,
      parsePointKey,
      edgeKey,
      polygonBounds,
      polygonCentroid,
      nearestInteriorPoint,
      roomAtMidpoint,
      findPath,
      addPathToNetwork,
      buildGraph,
      shortestPath,
      connectedComponents,
      edgeLengthGrid,
    }),
  };
});
