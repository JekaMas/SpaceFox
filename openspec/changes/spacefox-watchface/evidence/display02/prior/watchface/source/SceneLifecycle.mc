import Toybox.Lang;

// Foreground scene ownership. Display power is separate: only the selected
// scene/asset build advances here. Tokens invalidate callbacks from older scenes.
class SceneLifecycle {
    const EMPTY = 0;
    const FALLBACK_NEW = 1;
    const FALLBACK_PAINTED = 2;
    const WAIT_PAINT = 3;
    const WAIT_BUILD = 4;
    const BUILDING = 5;
    const READY = 6;
    const FAILED = 7;

    var phase as Number = EMPTY;
    var generation as Number = 0;

    function replace(hasScene as Boolean) as Void {
        generation += 1;
        phase = hasScene ? FALLBACK_NEW : EMPTY;
    }
    function bindReady() as Void { phase = READY; }
    function allowRetry() as Void {
        if (phase == FAILED) { phase = FALLBACK_PAINTED; }
    }
    function pending() as Boolean {
        return phase == WAIT_PAINT || phase == WAIT_BUILD || phase == BUILDING;
    }
    function request() as Boolean {
        if (phase == FALLBACK_NEW) { phase = WAIT_PAINT; return true; }
        if (phase == FALLBACK_PAINTED) { phase = WAIT_BUILD; return true; }
        return false;
    }
    function painted() as Void {
        if (phase == FALLBACK_NEW) { phase = FALLBACK_PAINTED; }
        else if (phase == WAIT_PAINT) { phase = WAIT_BUILD; }
    }
    function begin() as Number or Null {
        if (phase != WAIT_BUILD) { return null; }
        phase = BUILDING;
        return generation;
    }
    function complete(token as Number) as Boolean {
        if (phase != BUILDING || token != generation) { return false; }
        phase = READY;
        return true;
    }
    function fail(token as Number) as Void {
        if (phase == BUILDING && token == generation) { phase = FAILED; }
    }
    function cancel() as Void {
        generation += 1;
        if (phase == WAIT_PAINT) { phase = FALLBACK_NEW; }
        else if (phase == WAIT_BUILD || phase == BUILDING) { phase = FALLBACK_PAINTED; }
    }
}
