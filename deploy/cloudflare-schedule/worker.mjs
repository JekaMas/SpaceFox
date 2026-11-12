// A clock only: the existing Actions publisher owns cadence, quota and state.
const CRON = '7,22,37,52 * * * *';
const ENDPOINT = 'https://api.github.com/repos/JekaMas/SpaceFox/actions/workflows/update-feed.yml/dispatches';

export default {
  async scheduled(controller, env, ctx) {
    controller.noRetry(); // An ambiguous POST may already have created a run.
    const dispatch = (async () => {
      if (controller.cron !== CRON || typeof env.GITHUB_DISPATCH_TOKEN !== 'string' ||
          !env.GITHUB_DISPATCH_TOKEN.trim() || /\s/.test(env.GITHUB_DISPATCH_TOKEN)) {
        throw new Error('Invalid schedule or dispatch secret');
      }
      let response;
      try {
        response = await fetch(ENDPOINT, {
          method: 'POST', redirect: 'error', signal: AbortSignal.timeout(10000),
          headers: {
            'Accept': 'application/vnd.github+json',
            'Authorization': `Bearer ${env.GITHUB_DISPATCH_TOKEN}`,
            'Content-Type': 'application/json',
            'User-Agent': 'SpaceFox-schedule-clock',
            'X-GitHub-Api-Version': '2022-11-28',
          },
          body: JSON.stringify({ref: 'main'}),
        });
      } catch (_) {
        // Never print network errors, headers or provider response bodies: they may contain secrets.
        throw new Error('Dispatch transport failed');
      }
      if (response.status !== 204) throw new Error(`Dispatch rejected (HTTP ${response.status})`);
    })();
    ctx.waitUntil(dispatch);
    await dispatch;
  },
};
