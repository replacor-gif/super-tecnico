'use strict';

const assert = require('node:assert/strict');

global.window = {};
global.document = {documentElement: {lang: 'es'}};
require('../assets/datasheet-finder.js');

const finder = global.window.ST_DATASHEETS;
assert.ok(finder);

const ti = finder.sources('NE555P', 'Texas Instruments');
assert.ok(ti.some(item => item.confidence === 'official' && item.url.includes('site%3Ati.com')));
assert.ok(ti.some(item => item.name === 'Mouser'));
assert.ok(ti.some(item => item.name === 'DigiKey'));
assert.ok(ti.some(item => item.name === 'Farnell'));
assert.ok(ti.some(item => item.name === 'TME'));
assert.ok(ti.some(item => item.name === 'Octopart'));

const unknown = finder.sources('XYZ-123', '');
assert.ok(unknown.length >= 6);
assert.ok(unknown.every(item => item.url.startsWith('https://')));

const known = finder.sources('IRFP460', 'Infineon', 'https://example.com/irfp460.pdf');
assert.equal(known[0].confidence, 'official');
assert.equal(known[0].url, 'https://example.com/irfp460.pdf');

const html = finder.render('<script>alert(1)</script>', '', 'javascript:alert(1)');
assert.ok(!html.includes('<script>'));
assert.ok(!html.includes('javascript:'));

console.log('Datasheet finder tests: OK');
