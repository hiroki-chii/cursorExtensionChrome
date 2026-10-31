"""Real Chromium UI/input/canvas tests, with Chrome extension APIs substituted.

The managed Chromium blocks unpacked extensions. This harness deliberately does
not alter policy. It tests actual scripts and trusted pointer/keyboard input on
local HTTP pages; it does not prove Chrome permission/command integration.
Run: python3 tests/browser.py (requires playwright and a Chromium executable).
"""
import base64
import functools
import json
import os
from pathlib import Path
import tempfile
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)

MOCK = r"""(() => {
  // Test-only access to the overlay. Production uses a closed shadow root in
  // an isolated content-script world; no page-visible hooks are shipped.
  const attachShadow = Element.prototype.attachShadow;
  Element.prototype.attachShadow = function(options) { return attachShadow.call(this, { ...options, mode: 'open' }); };
  const runtimeListeners = [], storageListeners = [];
  function dispatch(message) {
    return new Promise((resolve, reject) => {
      for (const fn of runtimeListeners) { const async = fn(message, {}, resolve); if (async) return; }
      setTimeout(() => reject(Error('No receiver')), 1000);
    });
  }
  window.__pc = { dispatch, runtimeListeners, storageListeners, captures: 0, captureFailure: false };
  chrome.runtime = {
    onMessage: { addListener: fn => runtimeListeners.push(fn) },
    sendMessage: async message => {
      if (message.type === 'PC_FRAME_KEY') return window.top.__pc.dispatch(message);
      if (message.type === 'PC_CAPTURE') {
        if (__pc.captureFailure) return { ok: false, error: '撮影テストエラー' };
        __pc.captures++; return { ok: true, image: await window.pcCapture() };
      }
      if (message.type === 'PC_STATUS' || message.type === 'PC_ACTION') {
        if (location.pathname.endsWith('popup.html')) return { ok: true, state: { enabled: true, pen: message.action === 'togglePen', strokeCount: 1, redoCount: 1 } };
        return { ok: true, state: await dispatch(message) };
      }
    },
    openOptionsPage: async () => { __pc.openedOptions = true; }
  };
  chrome.storage = {
    local: {
      get: async key => ({ config: JSON.parse(localStorage.getItem('pc-config') || 'null') || undefined }),
      set: async values => {
        const oldValue = JSON.parse(localStorage.getItem('pc-config') || 'null');
        localStorage.setItem('pc-config', JSON.stringify(values.config));
        for (const fn of storageListeners) fn({ config: { oldValue, newValue: values.config } }, 'local');
      }
    },
    onChanged: { addListener: fn => storageListeners.push(fn) }
  };
  chrome.tabs = { create: async options => { __pc.openedTab = options.url; } };
  addEventListener('storage', event => {
    if (event.key === 'pc-config') for (const fn of storageListeners) fn({ config: { newValue: JSON.parse(event.newValue) } }, 'local');
  });
})();
"""

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{server.server_port}'
checks = []

def passed(label):
    checks.append(label)
    print(f'PASS {label}', flush=True)

with sync_playwright() as p, tempfile.TemporaryDirectory(prefix='presenter-ui-') as profile:
    executable = os.environ.get('CHROMIUM') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else p.chromium.executable_path)
    context = p.chromium.launch_persistent_context(profile, executable_path=executable, headless=True, viewport={'width': 1280, 'height': 1000}, args=['--no-sandbox'])
    context.set_default_timeout(5000)
    context.add_init_script(MOCK)
    errors = []
    context.on('page', lambda page: page.on('pageerror', lambda error: errors.append(str(error))))
    page = context.new_page()
    snapshot_data = {'value': ''}
    context.expose_binding('pcCapture', lambda source: snapshot_data['value'])
    page.goto(BASE + '/demo/index.html')
    # Top-level and embedded content scripts are loaded as they would be at idle.
    for frame in page.frames:
        frame.add_script_tag(path=str(ROOT / 'extension/core.js'))
        frame.add_script_tag(path=str(ROOT / 'extension/content.js'))
    page.wait_for_selector('#presenter-cursor-overlay', state='attached')

    def state(): return page.evaluate("__pc.dispatch({type:'PC_STATUS'})")
    def action(name): return page.evaluate("action => __pc.dispatch({type:'PC_ACTION',action})", name)
    def configure(change):
        page.evaluate("async patch => { const {config} = await chrome.storage.local.get('config'); const c=PresenterCore.normalize(config); for (const [section, values] of Object.entries(patch)) { if (typeof values === 'object') Object.assign(c[section],values); else c[section]=values; } await chrome.storage.local.set({config:c}); }", change)
    def pixel(x, y):
        page.wait_for_timeout(40)
        return page.evaluate("([x,y]) => {const c=document.querySelector('#presenter-cursor-overlay').shadowRoot.querySelector('canvas'); return [...c.getContext('2d').getImageData(x*devicePixelRatio,y*devicePixelRatio,1,1).data]}", [x, y])
    def draw(vertices, button='left'):
        page.mouse.move(*vertices[0]); page.mouse.down(button=button)
        for a, b in zip(vertices, vertices[1:]): page.mouse.move(*b, steps=12)
        page.mouse.up(button=button)

    page.locator('#test-button').click()
    expect(page.locator('#counter')).to_have_text('1 clicks')
    passed('通常のクリックを妨げない')

    action('toggleSpotlight'); page.mouse.move(400, 300)
    assert pixel(400, 300)[3] == 0
    assert pixel(20, 20)[3] > 100
    page.screenshot(path=str(ARTIFACTS / 'spotlight.png'))
    page.keyboard.press('Escape'); assert not state()['spotlight']
    passed('スポットライトの描画とEsc解除')

    action('toggleAreaSpotlight'); draw([(600, 450), (300, 200)])
    assert not state()['selecting'] and state()['area']
    assert pixel(400, 300)[3] == 0 and pixel(20, 20)[3] > 100
    page.screenshot(path=str(ARTIFACTS / 'area.png'))
    page.keyboard.press('Escape')
    passed('逆方向ドラッグの範囲強調')

    action('togglePen'); draw([(250, 300), (380, 320), (500, 280)])
    assert state()['strokeCount'] == 1 and pixel(380, 320)[3] > 80
    action('undoDrawing'); assert state()['strokeCount'] == 0 and state()['redoCount'] == 1
    action('redoDrawing'); assert state()['strokeCount'] == 1
    page.screenshot(path=str(ARTIFACTS / 'pen.png'))
    action('clearDrawing'); assert state()['strokeCount'] == 0
    page.mouse.move(100, 350); page.keyboard.down('Shift'); page.mouse.move(300, 400, steps=10); page.keyboard.up('Shift')
    assert state()['strokeCount'] == 1
    page.keyboard.press('Escape'); assert not state()['pen'] and state()['strokeCount'] == 1
    passed('ペン・Undo/Redo・全消去・トリガー描画・Escで線を保持')

    action('clearDrawing')
    draw([(200, 200), (255, 285), (330, 205)], button='middle')
    assert state()['pen']
    draw([(250, 300), (380, 320)])
    draw([(500, 400), (320, 400)], button='middle'); assert state()['strokeCount'] == 0
    draw([(320, 400), (500, 400)], button='middle'); assert state()['strokeCount'] == 1
    draw([(200, 400), (340, 402), (200, 403), (340, 400), (200, 401)], button='middle'); assert state()['strokeCount'] == 0
    page.keyboard.press('Escape')
    passed('中ボタンでV字・左右スワイプ・シェイク')

    configure({'keycast': {'enabled': True, 'duration': 500}})
    page.keyboard.press('Control+Alt+k')
    expect(page.locator('#presenter-cursor-overlay .keycast')).to_have_text('Ctrl + Alt + K')
    page.wait_for_timeout(600)
    page.locator('#password-input').click(); page.keyboard.type('secret-value'); page.keyboard.press('Control+Alt+k')
    expect(page.locator('#presenter-cursor-overlay .keycast')).to_be_hidden()
    page.locator('#text-input').click(); page.keyboard.type('ordinary-text'); page.keyboard.press('Control+Alt+k')
    expect(page.locator('#presenter-cursor-overlay .keycast')).to_be_hidden()
    page.locator('h1').click(); page.keyboard.type('ordinary')
    expect(page.locator('#presenter-cursor-overlay .keycast')).to_be_hidden()
    passed('キー表示とパスワード・テキスト入力の非表示')

    action('toggleLaser')
    frame_box = page.locator('iframe').bounding_box()
    x, y = round(frame_box['x'] + 50), round(frame_box['y'] + 40)
    page.mouse.move(x, y); page.wait_for_timeout(100)
    assert pixel(x, y)[0] > 180
    iframe = page.frame_locator('iframe'); iframe.locator('input').click(); page.keyboard.press('Control+Alt+k')
    expect(page.locator('#presenter-cursor-overlay .keycast')).to_be_hidden()
    action('toggleLaser')
    passed('iframeからのカーソル座標中継と入力保護')

    page.locator('h1').click(); page.keyboard.press('Control+Shift+a')
    assert state()['selecting']; page.keyboard.press('Escape')
    configure({'shortcuts': {'toggleAreaSpotlight': 'B'}})
    page.keyboard.press('Control+Shift+b'); assert state()['selecting']; page.keyboard.press('Escape')
    passed('ページ内ショートカットの変更')

    page.evaluate("dispatchEvent(new KeyboardEvent('keydown',{key:'m',code:'KeyM',ctrlKey:true,shiftKey:true,bubbles:true}))")
    page.frames[1].evaluate("parent.postMessage({tag:'presenter-cursor:frame-input:v1',event:{kind:'key',action:'toggleZoom'}},'*')")
    page.wait_for_timeout(80)
    assert not state()['zoom'] and page.evaluate('__pc.captures') == 0
    passed('ページの合成キーや偽のiframeメッセージで撮影を起動しない')

    # pcCapture returns a real screenshot but substitutes captureVisibleTab's API.
    configure({'keycast': {'enabled': False}})
    snapshot_data['value'] = 'data:image/png;base64,' + base64.b64encode(page.screenshot()).decode()
    page.mouse.move(600, 350); action('toggleZoom')
    assert state()['zoom'] and page.evaluate('__pc.captures') == 1
    initial = state()['scale']; page.mouse.wheel(0, -250); page.wait_for_timeout(50)
    assert state()['scale'] > initial
    page.screenshot(path=str(ARTIFACTS / 'zoom.png'))
    page.keyboard.press('Escape'); assert not state()['zoom']
    page.evaluate('__pc.captureFailure = true'); action('toggleZoom')
    assert not state()['zoom']
    expect(page.locator('#presenter-cursor-overlay .toast')).to_have_text('撮影テストエラー')
    page.evaluate('__pc.captureFailure = false')
    passed('実画像のズーム描画・ホイール倍率・撮影失敗の復帰（撮影APIは代替）')

    action('togglePen'); draw([(100, 200), (300, 200)]); action('toggleSpotlight')
    configure({'enabled': False}); assert not any(state()[k] for k in ['spotlight', 'pen', 'laser', 'zoom', 'area'])
    assert state()['strokeCount'] == 0
    page.locator('#test-button').click(); expect(page.locator('#counter')).to_have_text('2 clicks')
    configure({'enabled': True})
    passed('全機能OFFで描画を消去し通常操作に復帰')

    popup = context.new_page(); popup.goto(BASE + '/extension/popup.html')
    expect(popup.locator('#status')).to_have_text('使用可能')
    popup.locator('[data-action="togglePen"]').click()
    expect(popup.locator('[data-action="togglePen"]')).to_have_attribute('aria-pressed', 'true')
    popup.locator('[data-setting="ripple.enabled"]').click()
    expect(popup.locator('[data-setting="ripple.enabled"]')).to_have_attribute('aria-checked', 'false')
    popup.locator('#open-settings').click(); assert popup.evaluate('__pc.openedOptions')
    popup_height = popup.evaluate('document.body.scrollHeight')
    assert popup_height <= 600, f'Popup is taller than Chrome limit: {popup_height}'
    popup.screenshot(path=str(ARTIFACTS / 'popup.png'), clip={'x': 0, 'y': 0, 'width': 380, 'height': popup_height})
    passed('ポップアップのツール・トグル・設定リンク')

    options = context.new_page(); options.goto(BASE + '/extension/options.html')
    options.locator('[data-tab="drawing"]').click()
    options.locator('[data-field="pen.color"]').fill('#ff00aa')
    expect(options.locator('#save-status')).to_have_text('保存しました')
    options.reload(); expect(options.locator('[data-field="pen.color"]')).to_have_value('#ff00aa')
    options.locator('[data-tab="controls"]').click()
    options.locator('[data-field="shortcuts.togglePen"]').select_option('S')
    expect(options.locator('#settings-message')).to_contain_text('すでに使われています')
    options.locator('[data-tab="guide"]').click(); options.locator('#theme').select_option('light')
    expect(options.locator('html')).to_have_attribute('data-theme', 'light')
    options.locator('#reset').click(); options.locator('#reset-apply').click()
    expect(options.locator('#reset-confirm')).to_be_hidden()
    options.locator('[data-tab="effects"]').click()
    options.evaluate('scrollTo(0,0)')
    options.screenshot(path=str(ARTIFACTS / 'settings.png'), full_page=True)
    options.set_viewport_size({'width': 600, 'height': 900})
    assert options.evaluate('document.documentElement.scrollWidth <= innerWidth')
    passed('詳細設定の保存・再読込・キー重複・テーマ・リセット・狭い画面')

    assert not errors, errors
    passed('全テストでJavaScript実行エラーなし')
    context.close()

server.shutdown()
(ARTIFACTS / 'browser-results.json').write_text(json.dumps({'mode': 'Chromium with substituted extension APIs', 'passed': checks, 'limitations': ['unpacked extension loading blocked by managed policy', 'activeTab grants and native command dispatch require manual Chrome verification']}, ensure_ascii=False, indent=2))
print(f'{len(checks)} browser checks passed. Screenshots: {ARTIFACTS}', flush=True)
