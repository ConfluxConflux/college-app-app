/* HIPPOMODORO — global background timer engine.
 *
 * Runs on every page (loaded from both base.html and focus_base.html). Because the
 * app does hard page navigations (no SPA), all timer state lives in localStorage keyed
 * by an ABSOLUTE end timestamp, so the countdown stays correct across reloads/navigation.
 *
 * Responsibilities:
 *   - own the localStorage state + expose window.Hippomodoro for the Timer page
 *   - tick once/second, render the top-right chip, handle phase expiry (park the
 *     session and raise the corner alert — expiry never navigates for you)
 *   - enforce Hippomodoro deterrents (snort, tab title/favicon flip, enraged-Potamus interstitial,
 *     beforeunload close-dialog) and the neutral plain-Pomodoro Focus-Write guard
 */
(function () {
  'use strict';

  var KEY = 'hippomodoro';
  var cfg = document.getElementById('hippo-engine');
  var TIMER_URL  = (cfg && cfg.getAttribute('data-timer-url'))  || '/widgets/pomodoros/';
  var SNORT_URL  = (cfg && cfg.getAttribute('data-snort-url'))  || '';
  var ANGRY_IMG  = (cfg && cfg.getAttribute('data-angry-img'))  || '';

  var PENALTY_TEXT = "Dear Professor Potamus, I failed in my duty. I promise to spend my break " +
    "resetting myself. When I come back for my next pomodoro, I will put my distracted era behind " +
    "me and enter my locked-in era.";

  var TIMER_PATH = new URL(TIMER_URL, window.location.href).pathname;

  // ---------------------------------------------------------------- state I/O
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; }
  }
  function save(s) {
    if (s) { localStorage.setItem(KEY, JSON.stringify(s)); }
    else   { localStorage.removeItem(KEY); }
    notify(s);
  }
  function notify(s) {
    try {
      window.dispatchEvent(new CustomEvent('hippomodoro:change', { detail: s || load() }));
    } catch (e) {}
    render();
  }

  function isActive(s) { return !!(s && (s.running || s.pausedRemainingMs || s.event)); }

  function remainingMs(s) {
    if (!s) return 0;
    if (s.running && s.endAt) return Math.max(0, s.endAt - Date.now());
    if (s.pausedRemainingMs) return s.pausedRemainingMs;
    return 0;
  }

  // ---------------------------------------------------------------- controls (API)
  function start(opts) {
    opts = opts || {};
    var work = Math.max(0.02, parseFloat(opts.workMin) || 25);
    var brk  = Math.max(0.02, parseFloat(opts.breakMin) || 5);
    var s = {
      mode: opts.mode === 'hippomodoro' ? 'hippomodoro' : 'pomodoro',
      task: (opts.task || '').trim(),
      phase: 'work',
      workMin: work,
      breakMin: brk,
      endAt: Date.now() + work * 60000,
      running: true,
      pausedRemainingMs: null,
      hidden: false,
      event: null,
      pendingBreak: false,
      // "Leaving the tab is part of my task" only holds for the pomodoro you
      // said it in. Set explicitly rather than relying on a fresh object, so
      // this path and the break_done path below can't drift apart again.
      leaveOk: false
    };
    unlockAudio();
    save(s);
    return s;
  }
  function pause() {
    var s = load();
    if (!s || !s.running) return;
    s.pausedRemainingMs = remainingMs(s);
    s.running = false;
    s.endAt = null;
    save(s);
  }
  function resume() {
    var s = load();
    if (!s || s.running || !s.pausedRemainingMs) return;
    s.endAt = Date.now() + s.pausedRemainingMs;
    s.pausedRemainingMs = null;
    s.running = true;
    save(s);
  }
  function reset() { restoreChrome(); save(null); }

  // Hippomodoro: after the focus check-in resolves, begin the break.
  function startBreak() {
    var s = load();
    if (!s) return;
    s.phase = 'break';
    s.endAt = Date.now() + s.breakMin * 60000;
    s.running = true;
    s.pausedRemainingMs = null;
    s.event = null;
    s.pendingBreak = false;
    save(s);
  }
  // After a break_done, start a fresh work session with the same settings.
  function startAnother() {
    var s = load();
    if (!s) return;
    return start({ mode: s.mode, task: s.task, workMin: s.workMin, breakMin: s.breakMin });
  }
  function setTask(task) {
    var s = load();
    if (!s) return;
    s.task = (task || '').trim();
    save(s);
  }
  function setHidden(hidden) {
    var s = load();
    if (!s) return;
    s.hidden = !!hidden;
    save(s);
  }

  // ---------------------------------------------------------------- tick / expiry
  function tick() {
    var s = load();
    if (!s) { render(); return; }
    if (s.running && s.endAt && Date.now() >= s.endAt) { handleExpiry(s); return; }
    render();
  }

  function handleExpiry(s) {
    if (s.phase === 'work') {
      s.event = 'work_done';
      // Both modes hold: the break starts when you say so, not when the clock
      // says so. Plain Pomodoro used to start it here, which meant the break
      // burned down while you kept working and "keep working" was a lie.
      // Hippomodoro additionally gates it behind the focus check-in.
      s.running = false;
      s.endAt = null;
      s.pendingBreak = true;
    } else {
      s.event = 'break_done';
      s.running = false;
      s.endAt = null;
      s.phase = 'work';
      s.pendingBreak = false;
      // A new work period, so the hippo gets to ask again. Without this, a
      // break that expired on its own carried leaveOk forward and the guard
      // stayed silent forever — while clicking "start another" reset it. Which
      // path you took is invisible, so the hippo looked arbitrary.
      s.leaveOk = false;
    }
    restoreChrome();
    save(s);
    playDing();
    announceExpiry(s);
  }

  // Expiry never navigates. It parks the session and says so; you decide when
  // to move. s.event is the unresolved marker that outlives the alert — it
  // keeps the chip reading "time's up" and the timer page showing the choice,
  // so dismissing the alert defers the decision instead of losing it.
  function announceExpiry(s) {
    // On the timer page the page itself already shows the choice.
    if (window.location.pathname === TIMER_PATH) { notify(); return; }
    showAlert(s);
    notify();
  }

  // ---------------------------------------------------------------- navigation guards
  function zoneOf(path) {
    if (path === '/widgets/focus-write/') return 'focus_write';
    if (path === '/widgets/word-counter/') return 'word_counter';
    if (path.indexOf('/activities/') === 0) return 'activities';
    if (path.indexOf('/essays/') === 0) return 'essays';
    return null;
  }
  function isLeavingZone(curPath, destPath) {
    var cz = zoneOf(curPath), dz = zoneOf(destPath);
    if (!cz) return false;
    if (cz === dz) return false;
    if (cz === 'essays' && dz === 'focus_write') return false; // only exempt hop
    return true;
  }
  // Would navigating to destPath pop a guard right now?
  function shouldIntercept(destPath, s) {
    if (!s || !s.running || s.phase === 'break' || s.leaveOk) return false;
    if (destPath === TIMER_PATH) return false;
    if (s.mode === 'hippomodoro') return isLeavingZone(window.location.pathname, destPath);
    return zoneOf(window.location.pathname) === 'focus_write' && zoneOf(destPath) !== 'focus_write';
  }

  var pendingNav = null;

  // Entry point also used by focus_write.html's back button (JS-driven navigation).
  function attemptNavigate(url) {
    var destPath = new URL(url, window.location.href).pathname;
    var s = load();
    if (!shouldIntercept(destPath, s)) { doNavigate(url); return; }
    pendingNav = url;
    if (s.mode === 'hippomodoro') { playSnort(); showLock(); }
    else { showConfirm(); }
  }

  function doNavigate(url) {
    suppressUnload = true;
    window.location.href = url;
  }

  // Intercept in-app link clicks (unmodified left-clicks on same-origin <a>).
  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a || a.closest('[data-hippo-ui]')) return;
    if (a.target === '_blank' || a.hasAttribute('download')) return;
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) === '#' || href.indexOf('javascript:') === 0) return;
    var url;
    try { url = new URL(href, window.location.href); } catch (err) { return; }
    if (url.origin !== window.location.origin) return; // external → beforeunload handles it
    var s = load();
    if (shouldIntercept(url.pathname, s)) {
      e.preventDefault();
      attemptNavigate(url.href);
    } else {
      // A navigation we allow — mark it so the beforeunload guard stays quiet.
      suppressUnload = true;
      setTimeout(function () { suppressUnload = false; }, 2000);
    }
  }, true);

  // ---------------------------------------------------------------- tab-away deterrents
  var pendingAmbush = false;
  document.addEventListener('visibilitychange', function () {
    var s = load();
    var armed = s && s.running && s.phase === 'work' && s.mode === 'hippomodoro' && !s.leaveOk;
    if (document.hidden) {
      if (!armed) return;
      startSnortLoop();
      setChrome();
      pendingAmbush = true;
    } else {
      stopSnortLoop();
      restoreChrome();
      if (pendingAmbush && armed) { pendingAmbush = false; showLock(); }
      else { pendingAmbush = false; }
    }
  });

  var origTitle = null, origFavicon = null, faviconEl = null;
  function setChrome() {
    if (origTitle === null) origTitle = document.title;
    document.title = '🦛 GET BACK TO WORK';
    if (ANGRY_IMG) {
      faviconEl = document.querySelector('link[rel~="icon"]');
      if (faviconEl && origFavicon === null) origFavicon = faviconEl.getAttribute('href');
      if (faviconEl) faviconEl.setAttribute('href', ANGRY_IMG);
    }
  }
  function restoreChrome() {
    if (origTitle !== null) { document.title = origTitle; origTitle = null; }
    if (faviconEl && origFavicon !== null) { faviconEl.setAttribute('href', origFavicon); origFavicon = null; }
  }

  // ---------------------------------------------------------------- hard-exit dialog
  var suppressUnload = false;
  window.addEventListener('beforeunload', function (e) {
    if (suppressUnload) return;
    var s = load();
    if (s && s.running && s.phase === 'work' && s.mode === 'hippomodoro' && !s.leaveOk) {
      e.preventDefault();
      e.returnValue = '';
      return '';
    }
  });

  // ---------------------------------------------------------------- audio
  var audioCtx = null, snort = null;
  function unlockAudio() {
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      if (audioCtx.state === 'suspended') audioCtx.resume();
    } catch (e) {}
  }
  function playSnort(vol) {
    if (!SNORT_URL) return;
    try {
      if (!snort) snort = new Audio(SNORT_URL);
      snort.volume = (typeof vol === 'number') ? Math.max(0, Math.min(1, vol)) : 1;
      snort.currentTime = 0;
      var p = snort.play();
      if (p && p.catch) p.catch(function () {});
    } catch (e) {}
  }

  // Escalating snort loop while the user is off the tab (~15s, growing louder, until return).
  var snortTimer = null, snortStart = 0;
  var SNORT_MS = 15000;
  function startSnortLoop() {
    stopSnortLoop();
    snortStart = Date.now();
    (function once() {
      var elapsed = Date.now() - snortStart;
      if (elapsed > SNORT_MS) { stopSnortLoop(); return; }
      playSnort(0.25 + (elapsed / SNORT_MS) * 0.75); // ramp 0.25 → 1.0
      snortTimer = setTimeout(once, 1100);
    })();
  }
  function stopSnortLoop() { if (snortTimer) { clearTimeout(snortTimer); snortTimer = null; } }
  function beep(freq, dur, delay) {
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      var t = audioCtx.currentTime + (delay || 0);
      var o = audioCtx.createOscillator(), g = audioCtx.createGain();
      o.type = 'sine'; o.frequency.value = freq;
      o.connect(g); g.connect(audioCtx.destination);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.25, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.start(t); o.stop(t + dur);
    } catch (e) {}
  }
  function playDing() { beep(660, 0.16, 0); beep(880, 0.22, 0.16); }

  // ---------------------------------------------------------------- interstitials
  function showLock() {
    var el = document.getElementById('hippo-lock');
    if (el) el.style.display = 'flex';
  }
  // "Leaving the tab is part of my task" — quiet all Hippomodoro deterrents for this work session.
  function allowLeaving() {
    var s = load();
    if (s) { s.leaveOk = true; save(s); }
    stopSnortLoop();
    restoreChrome();
  }
  function hideLock() {
    var el = document.getElementById('hippo-lock');
    if (el) el.style.display = 'none';
  }
  // Timer-done alert: a corner card, not an overlay — it announces, it doesn't
  // seize. Wording and buttons flex between the two things that can expire.
  function showAlert(s) {
    var el = document.getElementById('hippo-alert');
    if (!el) return;
    var workDone = s.event === 'work_done';
    var title = document.getElementById('hippo-alert-title');
    var sub = document.getElementById('hippo-alert-sub');
    var go = document.getElementById('hippo-alert-go');
    var stay = document.getElementById('hippo-alert-stay');
    if (title) title.textContent = workDone ? "Time's up." : "Break's over.";
    if (sub) sub.textContent = workDone ? (s.task || '') : '';
    if (sub) sub.style.display = (workDone && s.task) ? '' : 'none';
    if (go) go.textContent = workDone ? 'Start break' : 'Start another';
    if (stay) stay.textContent = workDone ? 'Keep working' : 'Dismiss';
    el.style.display = 'flex';
  }
  function hideAlert() {
    var el = document.getElementById('hippo-alert');
    if (el) el.style.display = 'none';
  }

  function showConfirm() {
    var el = document.getElementById('hippo-confirm');
    if (el) el.style.display = 'flex';
  }
  function hideConfirm() {
    var el = document.getElementById('hippo-confirm');
    if (el) el.style.display = 'none';
  }
  function wireButtons() {
    var lockStay = document.getElementById('hippo-lock-stay');
    var lockAllow = document.getElementById('hippo-lock-allow');
    var lockLeave = document.getElementById('hippo-lock-leave');
    var confStay = document.getElementById('hippo-confirm-stay');
    var confLeave = document.getElementById('hippo-confirm-leave');
    if (lockStay) lockStay.addEventListener('click', function () { pendingNav = null; hideLock(); });
    if (lockAllow) lockAllow.addEventListener('click', function () {
      allowLeaving();
      hideLock();
      if (pendingNav) { var u = pendingNav; pendingNav = null; doNavigate(u); }
    });
    if (lockLeave) lockLeave.addEventListener('click', function () {
      hideLock();
      if (pendingNav) { var u = pendingNav; pendingNav = null; doNavigate(u); }
    });
    var alertGo = document.getElementById('hippo-alert-go');
    var alertStay = document.getElementById('hippo-alert-stay');
    if (alertGo) alertGo.addEventListener('click', function () {
      hideAlert();
      var s = load();
      // Plain Pomodoro has no gate, so the button means what it says: the break
      // starts here and you land on it running. Hippomodoro's break waits for
      // the check-in the timer page puts in front of you.
      if (s && s.event === 'work_done' && s.mode === 'pomodoro') startBreak();
      doNavigate(TIMER_URL);
    });
    // Leaves s.event set on purpose — see announceExpiry.
    if (alertStay) alertStay.addEventListener('click', function () { hideAlert(); });

    if (confStay) confStay.addEventListener('click', function () { pendingNav = null; hideConfirm(); });
    if (confLeave) confLeave.addEventListener('click', function () {
      hideConfirm();
      if (pendingNav) { var u = pendingNav; pendingNav = null; doNavigate(u); }
    });
  }

  // ---------------------------------------------------------------- chip render
  function fmt(ms) {
    var total = Math.round(ms / 1000);
    var m = Math.floor(total / 60), s = total % 60;
    return m + ':' + (s < 10 ? '0' : '') + s;
  }
  function render() {
    var chip = document.getElementById('hippo-chip');
    var showBtn = document.getElementById('hippo-chip-show');
    var s = load();
    // The alert never outlives the event it announces — resolving or resetting
    // in another tab lands here via the storage listener.
    if (!s || !s.event) hideAlert();
    if (!chip) return;
    if (!isActive(s)) {
      chip.style.display = 'none';
      if (showBtn) showBtn.style.display = 'none';
      return;
    }
    if (s.hidden) {
      chip.style.display = 'none';
      if (showBtn) showBtn.style.display = 'inline-flex';
    } else {
      chip.style.display = 'inline-flex';
      if (showBtn) showBtn.style.display = 'none';
    }
    var task = document.getElementById('hippo-chip-task');
    var icon = document.getElementById('hippo-chip-icon');
    var clock = document.getElementById('hippo-chip-clock');
    if (task) task.textContent = s.phase === 'break' ? 'Break' : (s.task || '(no goal)');
    if (icon) icon.textContent = s.mode === 'hippomodoro' ? '🦛' : '⏳';
    if (clock) clock.textContent = s.event ? "time's up" : fmt(remainingMs(s));
    chip.classList.toggle('pomo-chip--break', s.phase === 'break');
    chip.classList.toggle('pomo-chip--hippo', s.mode === 'hippomodoro');
  }

  function wireChip() {
    var toggle = document.getElementById('hippo-chip-toggle');
    var showBtn = document.getElementById('hippo-chip-show');
    var main = document.getElementById('hippo-chip-main');
    if (toggle) toggle.addEventListener('click', function (e) { e.preventDefault(); setHidden(true); });
    if (showBtn) showBtn.addEventListener('click', function (e) { e.preventDefault(); setHidden(false); });
    // Going to the timer via the chip is always allowed — don't let beforeunload nag.
    if (main) main.addEventListener('click', function () { suppressUnload = true; });
  }

  // ---------------------------------------------------------------- boot
  window.Hippomodoro = {
    start: start, pause: pause, resume: resume, reset: reset,
    startBreak: startBreak, startAnother: startAnother,
    setTask: setTask, setHidden: setHidden,
    getState: load, remainingMs: remainingMs, attemptNavigate: attemptNavigate,
    unlockAudio: unlockAudio, playSnort: playSnort, PENALTY_TEXT: PENALTY_TEXT
  };

  // On focus pages (no navbar), dock the chip inside the focus toolbar so it flows
  // beside the existing buttons instead of floating over them.
  function dockChipInFocusBar() {
    if (!document.body.classList.contains('focus-mode')) return;
    var bar = document.querySelector('.focus-topbar');
    var group = bar ? bar.querySelector(':scope > div') : null;
    var chip = document.getElementById('hippo-chip');
    var showBtn = document.getElementById('hippo-chip-show');
    if (!group || !chip) return;
    chip.classList.add('pomo-chip--inline');
    group.appendChild(chip);
    if (showBtn) { showBtn.classList.add('pomo-chip--inline'); group.appendChild(showBtn); }
  }

  function boot() {
    wireButtons();
    wireChip();
    dockChipInFocusBar();
    render();
    setInterval(tick, 1000);
    window.addEventListener('storage', function (e) { if (e.key === KEY) notify(); });
    window.addEventListener('pageshow', function () { render(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
