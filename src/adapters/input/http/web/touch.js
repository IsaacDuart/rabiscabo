import { protocol } from "/protocol.js";

const DRAW_DELAY_MS = 95;
const GESTURE_THRESHOLD_PX = 8;
const SCROLL_UNITS_PER_PIXEL = 120 / 48;
const MAX_SCROLL = protocol.maxScroll;

export function touchGeometry(first, second) {
  if (!second) return { x: first.clientX, y: first.clientY, distance: 1 };
  return {
    x: (first.clientX + second.clientX) / 2,
    y: (first.clientY + second.clientY) / 2,
    distance: Math.max(1, Math.hypot(first.clientX - second.clientX, first.clientY - second.clientY)),
  };
}

export class TouchGesture {
  constructor({ down, move, up, release, scroll, pinch }) {
    this.ink = { down, move, up, release };
    this.scroll = scroll;
    this.pinch = pinch;
    this.points = new Map();
    this.scrollWithOneFinger = false;
    this.reset();
  }

  get active() {
    return this.points.size > 0;
  }

  start(event) {
    this.points.set(event.pointerId, event);
    if (this.points.size === 1) {
      if (this.scrollWithOneFinger) {
        this.gesture = "scroll";
        this.rebase();
        return;
      }
      this.gesture = null;
      this.pending = [event];
      this.timer = setTimeout(() => this.commit(), DRAW_DELAY_MS);
      return;
    }
    if (!this.multiTouch) {
      this.clearPending();
      this.multiTouch = true;
      this.gesture = null;
      this.ink.release();
    }
    this.rebase();
  }

  move(event) {
    if (!this.points.has(event.pointerId)) return;
    this.points.set(event.pointerId, event);
    if (this.multiTouch || this.scrollWithOneFinger) {
      if (this.anchor && !this.frame) this.frame = requestAnimationFrame(() => this.flush());
    } else if (this.pending) {
      if (this.pending.length === protocol.maxEvents) this.pending.splice(1, 1);
      this.pending.push(event);
    } else {
      this.ink.move(event);
    }
  }

  end(event, cancelled = false) {
    if (!this.points.has(event.pointerId)) return;
    if (this.multiTouch || this.scrollWithOneFinger) {
      if (!cancelled && this.anchor) {
        this.points.set(event.pointerId, event);
        this.flush();
      }
    } else if (cancelled) {
      this.clearPending();
      this.ink.release();
    } else {
      this.commit();
      this.ink.up(event);
    }
    this.points.delete(event.pointerId);
    this.rebase();
    if (!this.active) this.multiTouch = false;
  }

  reset() {
    this.points.clear();
    this.multiTouch = false;
    this.clearPending();
    this.rebase();
  }

  clearPending() {
    clearTimeout(this.timer);
    this.pending = null;
  }

  commit() {
    if (!this.pending) return;
    const [first, ...moves] = this.pending;
    this.clearPending();
    this.ink.down(first);
    for (const event of moves) this.ink.move(event);
  }

  rebase() {
    cancelAnimationFrame(this.frame);
    this.frame = 0;
    const singleFingerScroll = this.scrollWithOneFinger && !this.multiTouch && this.points.size === 1;
    this.anchor = this.points.size === 2 || singleFingerScroll ? touchGeometry(...this.points.values()) : null;
    this.remainder = [0, 0];
  }

  flush() {
    cancelAnimationFrame(this.frame);
    this.frame = 0;
    if (!this.anchor) return;
    const previous = this.anchor;
    const current = touchGeometry(...this.points.values());
    const dx = current.x - previous.x;
    const dy = current.y - previous.y;
    if (!this.gesture) {
      const travel = Math.hypot(dx, dy);
      const spread = Math.abs(current.distance - previous.distance);
      if (spread >= GESTURE_THRESHOLD_PX && spread > travel * 1.25) {
        this.gesture = "pinch";
      } else if (travel >= GESTURE_THRESHOLD_PX) {
        this.gesture = "scroll";
      } else {
        return;
      }
    }
    this.anchor = current;
    if (this.gesture === "pinch") {
      this.pinch(previous, current, current.distance / previous.distance);
      return;
    }
    const exact = [dx, dy].map((value, axis) => value * SCROLL_UNITS_PER_PIXEL + this.remainder[axis]);
    const units = exact.map(Math.trunc);
    this.remainder = exact.map((value, axis) => value - units[axis]);
    const [x, y] = units.map((value) => Math.max(-MAX_SCROLL, Math.min(MAX_SCROLL, value)));
    if (x || y) this.scroll(x, y);
  }
}
