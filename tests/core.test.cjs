const { test } = require('node:test');
const assert = require('node:assert/strict');
require('../extension/core.js');
const { defaults, normalize, recognizeGesture, rectBetween, zoomRect } = PresenterCore;

test('settings survive upgrades and reject malformed values without mutating defaults', () => {
  const c = normalize({ enabled: false, pen: { width: 900, opacity: NaN, color: 'red' }, ripple: { enabled: 'false' }, spotlight: { radius: 75 }, unknown: 'discard' });
  assert.equal(c.enabled, false); assert.equal(c.pen.width, 30); assert.equal(c.pen.opacity, .8);
  assert.equal(c.pen.color, defaults.pen.color); assert.equal(c.ripple.enabled, true);
  assert.equal(c.spotlight.radius, 75); assert.equal(c.spotlight.opacity, .6);
  assert.equal(c.unknown, undefined); assert.equal(defaults.pen.width, 4);
  assert.deepEqual(normalize(null), defaults);
});
test('zoom limits and shortcuts stay valid', () => {
  const c = normalize({ zoom: { minScale: 3, maxScale: 1, scale: 2 }, shortcuts: { togglePen: 'S' } });
  assert.equal(c.zoom.minScale, 3); assert.equal(c.zoom.maxScale, 3); assert.equal(c.zoom.scale, 3);
  assert.deepEqual(c.shortcuts, defaults.shortcuts);
  assert.equal(normalize({ shortcuts: { togglePen: 'B' } }).shortcuts.togglePen, 'B');
});
function interpolate(vertices) {
  return vertices.flatMap((p, i) => i ? Array.from({ length: 10 }, (_, n) => ({ x: vertices[i - 1][0] + (p[0] - vertices[i - 1][0]) * (n + 1) / 10, y: vertices[i - 1][1] + (p[1] - vertices[i - 1][1]) * (n + 1) / 10 })) : [{ x: p[0], y: p[1] }]);
}
test('recognizes V, swipes and shake with independent paths', () => {
  assert.equal(recognizeGesture(interpolate([[0, 0], [55, 85], [130, 5]])), 'togglePen');
  assert.equal(recognizeGesture(interpolate([[160, 15], [0, 10]])), 'undoDrawing');
  assert.equal(recognizeGesture(interpolate([[0, 10], [180, 15]])), 'redoDrawing');
  assert.equal(recognizeGesture(interpolate([[0, 0], [120, 2], [0, 5], [120, 0], [0, 5]])), 'clearDrawing');
});
test('ignores clicks, jitter, vertical strokes and inverted V', () => {
  for (const vertices of [[[0, 0], [0, 0]], [[0, 0], [5, 3], [0, 4]], [[0, 0], [2, 180]], [[0, 100], [50, 0], [120, 100]]]) assert.equal(recognizeGesture(interpolate(vertices)), null);
});
test('area selection works in every drag direction and zoom stays within the snapshot', () => {
  assert.deepEqual(rectBetween({ x: 100, y: 80 }, { x: 10, y: 20 }), { x: 10, y: 20, width: 90, height: 60 });
  assert.deepEqual(zoomRect(0, 0, 2, 1000, 600), { x: 0, y: 0, width: 500, height: 300 });
  assert.deepEqual(zoomRect(1000, 600, 2, 1000, 600), { x: 500, y: 300, width: 500, height: 300 });
});
