'use strict';
let config = PresenterCore.normalize(), current = null, unavailable = false, busy = false;
const modeFor = { toggleSpotlight: 'spotlight', toggleAreaSpotlight: 'area', toggleLaser: 'laser', togglePen: 'pen', toggleZoom: 'zoom' };
const message = document.querySelector('#message'), status = document.querySelector('#status'), power = document.querySelector('#power');
function notify(text, error = false) { message.textContent = text; message.hidden = !text; message.classList.toggle('error', error); }
function render() {
  applyTheme(config.theme);
  power.setAttribute('aria-pressed', String(config.enabled)); power.setAttribute('aria-label', config.enabled ? '全機能をOFF' : '機能を有効にする'); power.title = power.getAttribute('aria-label');
  status.textContent = unavailable ? '利用できません' : config.enabled ? '使用可能' : 'すべてOFF'; status.classList.toggle('off', unavailable || !config.enabled);
  for (const button of document.querySelectorAll('[data-action]')) {
    const action = button.dataset.action;
    button.disabled = unavailable || !current || !config.enabled || busy;
    if (modeFor[action]) {
      button.setAttribute('aria-pressed', String(!!current?.[modeFor[action]]));
      button.querySelector('.key').textContent = `Ctrl + Shift + ${config.shortcuts[action]}`;
    } else if (action === 'redoDrawing') button.disabled ||= !current?.redoCount;
    else button.disabled ||= !current?.strokeCount;
  }
  for (const button of document.querySelectorAll('[data-setting]')) {
    const [section, key] = button.dataset.setting.split('.'); button.setAttribute('aria-checked', String(config[section][key])); button.disabled = !config.enabled || busy;
  }
}
async function updateConfig(change) {
  // Read immediately before writing, so another settings window's edits survive.
  const saved = await chrome.storage.local.get('config'); config = PresenterCore.normalize(saved.config); change(config); config = PresenterCore.normalize(config); await chrome.storage.local.set({ config }); render();
}
document.querySelector('#open-settings').addEventListener('click', () => chrome.runtime.openOptionsPage());
power.addEventListener('click', async () => { try { await updateConfig(c => { c.enabled = !c.enabled; }); if (!config.enabled) current = null; await refresh(); } catch (e) { notify(e.message, true); } });
document.querySelectorAll('[data-setting]').forEach(button => button.addEventListener('click', async () => {
  const [section, key] = button.dataset.setting.split('.'); try { await updateConfig(c => { c[section][key] = !c[section][key]; }); } catch (e) { notify(e.message, true); }
}));
document.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', async () => {
  busy = true; render();
  try {
    const result = await chrome.runtime.sendMessage({ type: 'PC_ACTION', action: button.dataset.action });
    if (!result?.ok) throw new Error(result?.error || 'ページに接続できません。ページを再読み込みしてください。');
    current = result.state; notify('');
    if (current?.selecting) notify('ページに戻り、明るくする範囲をドラッグしてください。');
    else if (current?.zoom) notify('ページに戻るとズーム表示になります。ホイールで倍率調整、Escで終了。');
  } catch (e) { notify(e.message, true); }
  finally { busy = false; render(); }
}));
async function refresh() {
  try { const result = await chrome.runtime.sendMessage({ type: 'PC_STATUS' }); if (!result?.ok) throw new Error(result?.error || 'ページに接続できません。'); current = result.state; unavailable = false; }
  catch (e) { unavailable = true; notify(e.message, true); }
  render();
}
chrome.storage.onChanged.addListener(changes => { if (changes.config) { config = PresenterCore.normalize(changes.config.newValue); render(); } });
colorScheme.addEventListener('change', () => applyTheme(config.theme));
(async () => { const saved = await chrome.storage.local.get('config'); config = PresenterCore.normalize(saved.config); render(); await refresh(); })();
