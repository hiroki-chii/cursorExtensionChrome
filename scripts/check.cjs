const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../extension');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json')));
if (manifest.manifest_version !== 3) throw Error('Expected MV3');
const refs = [manifest.background.service_worker, manifest.action.default_popup, manifest.options_page, ...Object.values(manifest.icons), ...Object.values(manifest.action.default_icon), ...manifest.content_scripts.flatMap(x => x.js)];
for (const name of fs.readdirSync(root)) {
  if (name.endsWith('.js')) new vm.Script(fs.readFileSync(path.join(root, name), 'utf8'), { filename: name });
  if (name.endsWith('.html')) for (const match of fs.readFileSync(path.join(root, name), 'utf8').matchAll(/(?:src|href)="([^"#]+)"/g)) if (!/^(https?:|chrome:)/.test(match[1])) refs.push(match[1]);
}
for (const ref of refs) if (!fs.existsSync(path.join(root, ref))) throw Error(`Missing extension resource: ${ref}`);
const assigned = Object.values(manifest.commands).filter(c => c.suggested_key).length;
if (assigned > 4) throw Error('Chrome allows only four suggested shortcuts');
console.log(`MV3 manifest, JavaScript syntax and ${new Set(refs).size} referenced resources: OK`);
