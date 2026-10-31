/* Screenshot-only API fixture; never included in the extension package. */
(() => {
  const messages = [], storageListeners = [];
  let config = { theme: 'dark' };
  const modes = { spotlight: false, area: false, laser: false, pen: false, zoom: false };
  window.storePreview = {
    dispatch: message => new Promise(resolve => {
      for (const listener of messages) if (listener(message, {}, resolve)) return;
    })
  };
  chrome.runtime = {
    onMessage: { addListener: fn => messages.push(fn) },
    sendMessage: async message => {
      if (message.type === 'PC_STATUS') return { ok: true, state: { ...modes, enabled: true, strokeCount: 0, redoCount: 0 } };
      if (message.type === 'PC_ACTION') return { ok: true, state: { ...modes, enabled: true, strokeCount: 0, redoCount: 0 } };
      throw Error('This screenshot fixture does not simulate tab capture.');
    },
    openOptionsPage: async () => {}
  };
  chrome.storage = {
    local: {
      get: async () => ({ config: structuredClone(config) }),
      set: async values => {
        const oldValue = config; config = structuredClone(values.config);
        for (const listener of storageListeners) listener({ config: { oldValue, newValue: config } }, 'local');
      }
    },
    onChanged: { addListener: fn => storageListeners.push(fn) }
  };
  chrome.tabs = { create: async () => {} };
})();
