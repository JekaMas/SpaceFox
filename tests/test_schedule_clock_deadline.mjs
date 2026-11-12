import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import worker from '../deploy/cloudflare-schedule/worker.mjs';

const endpoint = 'https://api.github.com/repos/JekaMas/SpaceFox/actions/workflows/update-feed.yml/dispatches';
const cron = '7,22,37,52 * * * *';
const token = 'independent-local-test-secret';
const realFetch = globalThis.fetch;

async function invoke(expression = cron, secret = token) {
  let retryCalls = 0;
  let waited;
  const result = worker.scheduled({cron: expression, noRetry() { retryCalls++; }},
    {GITHUB_DISPATCH_TOKEN: secret}, {waitUntil(promise) { waited = promise; }});
  // The platform observes waitUntil rejection independently of the returned promise.
  const observed = waited.then(() => 'accepted', error => error.message);
  try {
    await result;
    assert.equal(await observed, 'accepted');
  } catch (error) {
    assert.equal(await observed, error.message);
    assert.ok(!error.message.includes(token));
    throw error;
  } finally {
    assert.equal(retryCalls, 1);
  }
}

async function listen(server) {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  return `http://127.0.0.1:${server.address().port}`;
}

async function close(server) {
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
}

test('clock aborts a stalled real HTTP dispatch near ten seconds', {timeout: 16000}, async () => {
  let count = 0;
  let signal;
  const server = http.createServer(async req => {
    for await (const _ of req) { /* Consume the actual POST, then never send headers. */ }
    count++;
  });
  const base = await listen(server);
  globalThis.fetch = (url, options) => {
    assert.equal(url, endpoint);
    signal = options.signal;
    return realFetch(base + new URL(url).pathname, options);
  };
  const started = performance.now();
  try {
    await assert.rejects(invoke(), {message: 'Dispatch transport failed'});
    const elapsed = performance.now() - started;
    assert.ok(elapsed >= 9500 && elapsed < 14000, `actual deadline elapsed ${elapsed}ms`);
    assert.equal(count, 1);
    assert.equal(signal.aborted, true);
    assert.equal(signal.reason.name, 'TimeoutError');
    console.log(`real AbortSignal timeout: ${elapsed.toFixed(1)}ms; one POST; no application retry`);
  } finally {
    globalThis.fetch = realFetch;
    await close(server);
  }
});

test('clock isolates rejected wakeups and never follows redirect destinations', async () => {
  let accepted = 0;
  let redirected = 0;
  let sinkRequests = 0;
  const sink = http.createServer((_, res) => { sinkRequests++; res.writeHead(204); res.end(); });
  const sinkBase = await listen(sink);
  const server = http.createServer(async (req, res) => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    assert.equal(req.method, 'POST');
    assert.equal(req.headers.authorization, `Bearer ${token}`);
    assert.equal(req.headers['x-github-api-version'], '2022-11-28');
    assert.deepEqual(JSON.parse(Buffer.concat(chunks).toString()), {ref: 'main'});
    if (req.url.startsWith('/redirect/')) {
      redirected++;
      res.writeHead(Number(req.url.split('/').at(-1)), {Location: sinkBase + '/credential-sink'}); res.end(token);
    } else {
      accepted++;
      res.writeHead(204); res.end();
    }
  });
  const base = await listen(server);
  let outgoing = 0;
  globalThis.fetch = (url, options) => {
    assert.equal(url, endpoint);
    assert.equal(options.redirect, 'manual');
    outgoing++;
    return realFetch(base + (outgoing <= 5 ? `/redirect/${[301, 302, 303, 307, 308][outgoing - 1]}` : outgoing === 6 ? '/redirect/307' : '/accepted'), options);
  };
  try {
    assert.deepEqual(Object.keys(worker), ['scheduled']);
    for (const status of [301, 302, 303, 307, 308]) {
      await assert.rejects(invoke(), {message: `Dispatch rejected (HTTP ${status})`});
      assert.equal(outgoing, redirected); // exactly one POST per wakeup, no retry
      assert.equal(sinkRequests, 0);
    }
    const outcomes = await Promise.allSettled([
      invoke(), invoke(), invoke('* * * * *'), invoke(cron, ''), invoke(cron, 'bad secret'),
    ]);
    assert.deepEqual(outcomes.map(row => row.status), ['rejected', 'fulfilled', 'rejected', 'rejected', 'rejected']);
    assert.equal(outcomes[0].reason.message, 'Dispatch rejected (HTTP 307)');
    assert.equal(outgoing, 7);
    assert.equal(accepted, 1);
    assert.equal(redirected, 6);
    assert.equal(sinkRequests, 0);
    // A distinct later wakeup remains able to dispatch after rejection.
    await invoke();
    assert.equal(outgoing, 8);
    assert.equal(accepted, 2);
  } finally {
    globalThis.fetch = realFetch;
    await close(server);
    await close(sink);
  }
});
