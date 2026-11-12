import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import worker from '../deploy/cloudflare-schedule/worker.mjs';

const cron = '7,22,37,52 * * * *';
const token = 'test-secret-never-real';
const realFetch = globalThis.fetch;

test('scheduled boundary, failures, concurrency and secret safety', async () => {
  const requests = [];
  let status = 204;
  const server = http.createServer(async (req, res) => {
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    requests.push({method: req.method, url: req.url, headers: req.headers, body: Buffer.concat(chunks).toString()});
    res.writeHead(status); res.end(status === 204 ? undefined : token);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  globalThis.fetch = (url, options) => {
    assert.equal(url, 'https://api.github.com/repos/JekaMas/SpaceFox/actions/workflows/update-feed.yml/dispatches');
    assert.equal(options.redirect, 'error');
    assert.ok(options.signal instanceof AbortSignal);
    return realFetch(base + new URL(url).pathname, options);
  };
  const invoke = async (env = {GITHUB_DISPATCH_TOKEN: token}, expression = cron) => {
    let noRetry = 0; let waited;
    const promise = worker.scheduled({cron: expression, noRetry() { noRetry++; }}, env, {waitUntil(p) { waited = p; }});
    try { await promise; } finally { assert.equal(noRetry, 1); assert.ok(waited); }
  };
  try {
    assert.deepEqual(Object.keys(worker), ['scheduled']);
    await invoke();
    assert.equal(requests.length, 1);
    assert.equal(requests[0].method, 'POST');
    assert.equal(requests[0].headers.authorization, `Bearer ${token}`);
    assert.deepEqual(JSON.parse(requests[0].body), {ref: 'main'});
    assert.equal(requests[0].headers['content-type'], 'application/json');
    await assert.rejects(invoke({}, cron), /Invalid schedule/);
    await assert.rejects(invoke({GITHUB_DISPATCH_TOKEN: 'bad secret'}, cron), /Invalid schedule/);
    await assert.rejects(invoke({GITHUB_DISPATCH_TOKEN: token}, '* * * * *'), /Invalid schedule/);
    assert.equal(requests.length, 1);
    status = 500;
    await assert.rejects(invoke(), error => error.message === 'Dispatch rejected (HTTP 500)' && !error.message.includes(token));
    assert.equal(requests.length, 2); // no application retry
    status = 429;
    await assert.rejects(invoke(), /HTTP 429/);
    status = 302;
    await assert.rejects(invoke(), /Dispatch transport failed/);
    assert.equal(requests.length, 4);
    status = 204;
    await Promise.all([invoke(), invoke()]);
    assert.equal(requests.length, 6); // separate events can dispatch; publisher serializes them
    globalThis.fetch = async () => { throw new Error(token); };
    await assert.rejects(invoke(), error => error.message === 'Dispatch transport failed' && !error.message.includes(token));
  } finally {
    globalThis.fetch = realFetch;
    await new Promise(resolve => server.close(resolve));
  }
});
