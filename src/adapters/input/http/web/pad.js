import { protocol } from "/protocol.js";
import { Transport } from "/transport.js";
import { TouchGesture, touchGeometry } from "/touch.js";
import { InkPreview } from "/ink.js";

const pad = document.querySelector("#pad");
const cursor = document.querySelector("#cursor");
const status = document.querySelector("#status");
const fullscreen = document.querySelector("#fullscreen");
const navigate = document.querySelector("#navigate");
const movePreview = document.querySelector("#move-preview");
const preview = new InkPreview(document.querySelector("#ink"));
const navigationPointers = new Map();
const OUT = 0, HOVER = 1, DOWN = 2;
let contact = null;
let hovering = null;
let position = [0, 0];
let transport;
let mode = "draw";

function forgetPointer() {
  contact = hovering = null;
  cursor.hidden = true;
  preview.finish();
}

function resetInput() {
  touch.reset();
  forgetPointer();
}

function showStatus(online, message) {
  if (status.textContent !== message) {
    status.dataset.connected = String(online);
    status.textContent = message;
  }
  if (!online) resetInput();
}

function sample(event, state, bounds = pad.getBoundingClientRect()) {
  const unit = (value) => Math.min(1, Math.max(0, value));
  const x = unit((event.clientX - bounds.left) / bounds.width);
  const y = unit((event.clientY - bounds.top) / bounds.height);
  position = [Math.round(x * protocol.maxCoordinate), Math.round(y * protocol.maxCoordinate)];
  cursor.hidden = state === OUT;
  cursor.style.left = `${x * 100}%`;
  cursor.style.top = `${y * 100}%`;
  const pressure = state === DOWN ? Math.max(1, Math.round(
    (event.pointerType === "pen" ? unit(event.pressure) : 0.5) * protocol.maxPressure,
  )) : 0;
  if (!transport.enqueue([state, ...position, pressure], position)) {
    resetInput();
  } else if (state === DOWN) {
    preview.point(x * bounds.width, y * bounds.height);
  } else {
    preview.finish();
  }
}

function releaseInk() {
  if (contact === null && hovering === null) return;
  transport.enqueue([OUT, ...position, 0], position);
  forgetPointer();
}

function beginInk(event) {
  contact = event.pointerId;
  hovering = null;
  sample(event, DOWN);
}

function moveInk(event) {
  if (event.pointerId === contact) {
    const bounds = pad.getBoundingClientRect();
    const points = event.getCoalescedEvents?.();
    for (const point of points?.length ? points.slice(-protocol.maxEvents) : [event]) {
      if (contact === null) break;
      sample(point, DOWN, bounds);
    }
  } else if (contact === null && event.pointerType === "pen" && event.buttons === 0) {
    hovering = event.pointerId;
    sample(event, HOVER);
  }
}

function endInk(event) {
  if (event.pointerId !== contact) return;
  contact = null;
  const bounds = pad.getBoundingClientRect();
  const inside = event.clientX >= bounds.left && event.clientX <= bounds.right
    && event.clientY >= bounds.top && event.clientY <= bounds.bottom;
  const hover = event.pointerType === "pen" && inside;
  hovering = hover ? event.pointerId : null;
  sample(event, hover ? HOVER : OUT, bounds);
}

const touch = new TouchGesture({
  down: beginInk,
  move: moveInk,
  up: endInk,
  release: releaseInk,
  pinch(from, to, factor) {
    preview.move(from, to, factor);
  },
  scroll(x, y) {
    if (!transport.enqueue([protocol.scrollCode, x, y, 0], position)) resetInput();
  },
});

pad.addEventListener("pointerdown", (event) => {
  if (event.button !== 0) return;
  if (mode === "preview") {
    pad.setPointerCapture(event.pointerId);
    navigationPointers.set(event.pointerId, event);
    return;
  }
  if (!transport?.online) return;
  if (event.pointerType === "touch") {
    if (hovering !== null || (contact !== null && !touch.active)) return;
    pad.setPointerCapture(event.pointerId);
    touch.start(event);
  } else if (mode === "draw" && !touch.active && contact === null && (hovering === null || event.pointerType === "pen")) {
    pad.setPointerCapture(event.pointerId);
    beginInk(event);
  }
});

pad.addEventListener("pointermove", (event) => {
  if (mode === "preview") {
    if (!navigationPointers.has(event.pointerId)) return;
    const previous = touchGeometry(...navigationPointers.values());
    navigationPointers.set(event.pointerId, event);
    const current = touchGeometry(...navigationPointers.values());
    preview.move(previous, current, current.distance / previous.distance);
    return;
  }
  if (!transport?.online) return;
  if (event.pointerType === "touch") touch.move(event);
  else if (mode === "draw" && !touch.active) moveInk(event);
});

pad.addEventListener("pointerup", (event) => {
  if (navigationPointers.delete(event.pointerId)) return;
  if (event.pointerType === "touch") touch.end(event);
  else endInk(event);
});

pad.addEventListener("pointerleave", (event) => {
  if (event.pointerId === hovering) releaseInk();
});
for (const name of ["pointercancel", "lostpointercapture"]) {
  pad.addEventListener(name, (event) => {
    if (navigationPointers.delete(event.pointerId)) return;
    if (event.pointerType === "touch") {
      touch.end(event, true);
    } else if (event.pointerId === contact || (name === "pointercancel" && event.pointerId === hovering)) {
      releaseInk();
    }
  });
}
pad.addEventListener("contextmenu", (event) => event.preventDefault());

function stopInput() {
  navigationPointers.clear();
  touch.reset();
  releaseInk();
}

function toggleMode(selected) {
  stopInput();
  mode = mode === selected ? "draw" : selected;
  touch.scrollWithOneFinger = mode === "scroll";
  navigate.setAttribute("aria-pressed", String(mode === "scroll"));
  movePreview.setAttribute("aria-pressed", String(mode === "preview"));
}

navigate.addEventListener("click", () => toggleMode("scroll"));
movePreview.addEventListener("click", () => toggleMode("preview"));

function zoomPreview(factor) {
  stopInput();
  const { width, height } = pad.getBoundingClientRect();
  const center = { x: width / 2, y: height / 2 };
  preview.move(center, center, factor);
}

document.querySelector("#zoom-out").addEventListener("click", () => zoomPreview(0.8));
document.querySelector("#zoom-in").addEventListener("click", () => zoomPreview(1.25));
document.querySelector("#undo").addEventListener("click", () => {
  stopInput();
  preview.undo();
});

let fullscreenOnFirstInteraction = document.fullscreenEnabled;
fullscreen.hidden = !fullscreenOnFirstInteraction;

async function enterFullscreen() {
  fullscreenOnFirstInteraction = false;
  try {
    await document.documentElement.requestFullscreen({ navigationUI: "hide" });
    fullscreen.textContent = "Tela cheia";
  } catch {
    fullscreen.textContent = "Tentar tela cheia";
  }
}

fullscreen.addEventListener("click", enterFullscreen);

function enterFullscreenOnFirstInteraction(event) {
  if (fullscreenOnFirstInteraction && event.isTrusted && contact === null && !touch.active && !navigationPointers.size) {
    void enterFullscreen();
  }
}

pad.addEventListener("pointerup", enterFullscreenOnFirstInteraction);
document.addEventListener("click", enterFullscreenOnFirstInteraction);

function start() {
  const token = location.hash.slice(1);
  if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
    showStatus(false, "Abra a sessão pelo computador.");
    return;
  }
  try {
    transport = new Transport(token, showStatus);
  } catch {
    showStatus(false, "Reabra a sessão pelo computador.");
    return;
  }
  void transport.flush();
  setInterval(() => void transport.flush(), 350);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stopInput();
    void transport.flush();
  });
  window.addEventListener("blur", stopInput);
}

start();
