# Pomodoro Timer — Implementation Plan

## 1. URL + View
Add one route and one trivial view — no server-side logic needed, Alpine handles everything.
- `widgets/urls.py`: `path('pomodoro/', views.pomodoro, name='pomodoro')`
- `widgets/views.py`: `def pomodoro(request): return render(request, 'widgets/pomodoro.html')`

## 2. Tab nav (5 files to update)
Add a "Pomodoro" tab to the tab bar in `estimator.html`, `word_counter.html`, `advice.html`, and `resources.html`. Focus Write uses `focus_base.html` so it's excluded. Order: Time Calculator · Word Counter · Focus Write · **Pomodoro** · Advice · Resources.

## 3. Template — `widgets/templates/widgets/pomodoro.html`

**Alpine.js state:**
```
mode: 'work' | 'short' | 'long'
durations: { work: 25*60, short: 5*60, long: 15*60 }
remaining: (seconds)
running: bool
sessions: int  (completed work sessions; resets every 4 → long break)
```

**Key methods:**
- `tick()` — decrements `remaining` every second, calls `complete()` at zero
- `complete()` — plays a beep via Web Audio API, increments `sessions`, auto-advances to the appropriate next mode (short break → work, every 4th work session → long break)
- `setMode(mode)` — pauses and resets to that mode's duration
- `notify()` — `AudioContext` one-shot oscillator beep, no library needed

**Layout (top to bottom):**
1. Mode selector — three buttons (Work / Short Break / Long Break), active one highlighted
2. Large timer — `MM:SS` in a serif display font, roughly 5–6rem
3. SVG progress ring — thin circle that drains as time elapses, colored by mode (blue for work, green for breaks)
4. Controls — Start/Pause button + Reset button
5. Session tracker — "Session 3 · next: long break" in small grey text

## 4. CSS additions to `app.css`
A handful of classes for the ring, mode buttons, and timer display. No new dependencies.

## Out of scope (for now)
- Persisting session counts across page loads
- Custom duration settings UI
- Browser `Notification` API (audio beep is sufficient and needs no permission prompt)
