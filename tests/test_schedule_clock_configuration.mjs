import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const configuration = readFileSync(new URL('../deploy/cloudflare-schedule/wrangler.toml', import.meta.url), 'utf8');

function assertPrivateConfiguration(text) {
  const topLevel = text.split(/^\s*\[/m)[0];
  assert.match(topLevel, /^compatibility_date\s*=\s*"2026-11-12"\s*$/m);
  assert.match(topLevel, /^workers_dev\s*=\s*false\s*$/m);
  // Current Wrangler preserves an existing Version/Preview URL setting when omitted.
  assert.match(topLevel, /^preview_urls\s*=\s*false\s*$/m);
  assert.match(text, /^crons\s*=\s*\["7,22,37,52 \* \* \* \*"\]\s*$/m);
  const tables = [...text.matchAll(/^\s*\[([^\]]+)\]\s*$/gm)].map(match => match[1]);
  assert.deepEqual(tables, ['triggers']);
  assert.doesNotMatch(text, /^\s*(?:routes?|kv_namespaces|r2_buckets|vars)\s*=/m);
}

test('clock configuration explicitly disables public URLs and has only the Cron trigger', () => {
  assertPrivateConfiguration(configuration);
});

test('clock configuration checker rejects an omitted preview switch or added route', () => {
  const privateConfiguration = configuration.replace(/^preview_urls.*\n/m, 'preview_urls = false\n');
  assert.throws(() => assertPrivateConfiguration(privateConfiguration.replace('2026-11-12', '2026-11-01')));
  assert.throws(() => assertPrivateConfiguration(privateConfiguration.replace(/^preview_urls.*\n/m, '')));
  assert.throws(() => assertPrivateConfiguration(privateConfiguration.replace(/^preview_urls.*\n/m, '') + '\npreview_urls = false\n'));
  assert.throws(() => assertPrivateConfiguration(privateConfiguration + 'route = "public.example/*"\n'));
});
