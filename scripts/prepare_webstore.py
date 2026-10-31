"""Capture actual bundled UI/renderers and package Chrome Web Store materials.

Chrome APIs are fixture-backed because managed Chromium disallows extension
installation. No product UI is recreated, and no extension API success is implied.
Run from repository root: python3 scripts/prepare_webstore.py
"""
import argparse
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from zipfile import ZipFile, ZIP_DEFLATED
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'store'
ASSETS = STORE / 'assets'
SHOTS = ASSETS / 'screenshots'
RAW = ROOT / 'artifacts' / 'webstore'
VERSION = json.loads((ROOT / 'extension/manifest.json').read_text(encoding='utf-8'))['version']

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def capture_assets():
    for folder in (SHOTS, RAW):
        folder.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p, tempfile.TemporaryDirectory(prefix='presenter-store-') as profile:
            executable = os.environ.get('CHROMIUM') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else p.chromium.executable_path)
            context = p.chromium.launch_persistent_context(profile, executable_path=executable, headless=True, viewport={'width': 1280, 'height': 800}, device_scale_factor=1, args=['--no-sandbox'])
            context.add_init_script(path=str(STORE / 'source/chrome-fixture.js'))
            context.set_default_timeout(10000)
            errors = []
            context.on('page', lambda page: page.on('pageerror', lambda error: errors.append(str(error))))
            def capture(page, target):
                page.evaluate('document.fonts.ready')
                page.screenshot(path=str(target), full_page=False, omit_background=False)
                print(target.relative_to(ROOT), flush=True)
            def demo():
                page = context.new_page(); page.goto(base + '/store/source/demo.html')
                page.add_script_tag(path=str(ROOT / 'extension/core.js'))
                page.add_script_tag(path=str(ROOT / 'extension/content.js'))
                page.evaluate('document.fonts.ready')
                return page
            def configure(page, patch):
                page.evaluate("async patch => {const c=PresenterCore.normalize();c.theme='dark';for(const [s,v] of Object.entries(patch)) Object.assign(c[s],v);await chrome.storage.local.set({config:c});}", patch)
            def action(page, name):
                return page.evaluate("action => storePreview.dispatch({type:'PC_ACTION',action})", name)
            def draw(page, points):
                page.mouse.move(*points[0]); page.mouse.down()
                for point in points[1:]: page.mouse.move(*point, steps=2)
                page.mouse.up()

            overview = context.new_page(); overview.goto(base + '/store/source/overview.html')
            overview.frame_locator('iframe').locator('#status').wait_for()
            overview.wait_for_timeout(200)
            capture(overview, SHOTS / '01-control-panel.png')

            spotlight = demo(); configure(spotlight, {'spotlight': {'radius': 185, 'opacity': .63}, 'ripple': {'enabled': False}})
            action(spotlight, 'toggleSpotlight'); spotlight.mouse.move(638, 529)
            spotlight.wait_for_timeout(70); capture(spotlight, SHOTS / '02-spotlight.png')

            pen = demo(); configure(pen, {'pen': {'color': '#eab308', 'width': 5, 'opacity': .9}, 'ripple': {'enabled': False}})
            action(pen, 'togglePen')
            circle = [(640 + 159 * math.cos(t * math.pi / 30), 349 + 53 * math.sin(t * math.pi / 30)) for t in range(62)]
            draw(pen, circle)
            draw(pen, [(487, 508), (512, 513), (540, 516), (567, 513), (595, 501), (623, 485), (647, 471), (671, 456), (696, 438)])
            draw(pen, [(670, 444), (696, 438), (689, 465)])
            assert action(pen, 'noop')['strokeCount'] == 3
            capture(pen, SHOTS / '03-pen-annotations.png')

            laser = demo(); configure(laser, {'laser': {'radius': 6, 'trailLength': 60}, 'ripple': {'enabled': True, 'radius': 60, 'duration': 1800, 'leftColor': '#60a5fa'}, 'keycast': {'enabled': True, 'duration': 5000}})
            action(laser, 'toggleLaser'); laser.keyboard.press('Control+Alt+k')
            laser.mouse.click(637, 350)
            laser.wait_for_timeout(220)
            laser.mouse.move(483, 540); laser.mouse.move(530, 525, steps=3); laser.mouse.move(575, 500, steps=3); laser.mouse.move(620, 472, steps=3); laser.mouse.move(665, 445, steps=3)
            capture(laser, SHOTS / '04-laser-clicks-keycast.png')

            settings = context.new_page(); settings.goto(base + '/extension/options.html#drawing')
            settings.locator('[data-panel="drawing"]').wait_for(state='visible')
            capture(settings, SHOTS / '05-settings.png')

            promo = context.new_page(); promo.set_viewport_size({'width': 440, 'height': 280}); promo.goto(base + '/store/source/promo.html')
            capture(promo, ASSETS / 'promo-small-440x280.png')
            promo.set_viewport_size({'width': 1400, 'height': 560}); promo.locator('body').evaluate("node => node.className='large'")
            capture(promo, ASSETS / 'promo-marquee-1400x560.png')
            assert not errors, errors
            context.close()
    finally:
        server.shutdown()

def package_materials():
    shutil.copyfile(ROOT / 'extension/icons/128.png', ASSETS / 'icon-128.png')
    listing = (STORE / 'listing.ja.txt').read_text(encoding='utf-8')
    description = listing.split('【詳細説明：この欄の本文をストアの「説明」に貼り付け】\n', 1)[1].split('\n【カテゴリ候補：管理画面で選択】', 1)[0].strip() + '\n'
    (STORE / 'description.ja.txt').write_text(description, encoding='utf-8')
    metadata = {
        'version': VERSION,
        'date_jst': '2026-10-31',
        'capture': 'Actual bundled popup/options UI and canvas renderers in Chromium; Chrome APIs supplied by store/source/chrome-fixture.js. Original fictional demo content. No extension installation or captureVisibleTab success is implied.',
        'screenshots': [f'assets/screenshots/{p.name}' for p in sorted(SHOTS.glob('*.png'))],
        'hashes': {str(p.relative_to(STORE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ASSETS.rglob('*.png'))}
    }
    (STORE / 'asset-manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/package.py')], check=True)
    extension_zip = ROOT / 'dist' / f'presenter-cursor-chrome-{VERSION}.zip'
    kit = ROOT / 'dist' / f'presenter-cursor-webstore-kit-{VERSION}.zip'
    with ZipFile(kit, 'w', ZIP_DEFLATED) as archive:
        for source in sorted(STORE.rglob('*')):
            if source.is_file(): archive.write(source, source.relative_to(STORE))
        archive.write(extension_zip, f'extension-upload/presenter-cursor-chrome-{VERSION}.zip')
    print(f'KIT: {kit}', flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-only', action='store_true', help='Reuse approved screenshots without launching a browser.')
    args = parser.parse_args()
    if not args.package_only:
        capture_assets()
    package_materials()

if __name__ == '__main__':
    main()
