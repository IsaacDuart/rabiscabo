const MIN_ZOOM = 0.125;
const MAX_ZOOM = 8;

export class InkPreview {
  constructor(canvas) {
    this.canvas = canvas;
    this.context = canvas.getContext("2d");
    this.strokes = [];
    this.active = null;
    this.x = 0;
    this.y = 0;
    this.zoom = 1;
    this.frame = 0;
    new ResizeObserver(() => this.schedule()).observe(canvas);
  }

  point(x, y) {
    x = (x - this.x) / this.zoom;
    y = (y - this.y) / this.zoom;
    if (this.active) {
      this.active.path.lineTo(x, y);
      this.active.left = Math.min(this.active.left, x);
      this.active.top = Math.min(this.active.top, y);
      this.active.right = Math.max(this.active.right, x);
      this.active.bottom = Math.max(this.active.bottom, y);
    } else {
      const path = new Path2D();
      path.moveTo(x, y);
      this.active = { x, y, path, left: x, top: y, right: x, bottom: y };
      this.strokes.push(this.active);
    }
    this.schedule();
  }

  finish() {
    this.active = null;
  }

  undo() {
    this.finish();
    this.strokes.pop();
    this.schedule();
  }

  move(from, to, factor = 1) {
    const zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, this.zoom * factor));
    this.x = to.x - (from.x - this.x) * zoom / this.zoom;
    this.y = to.y - (from.y - this.y) * zoom / this.zoom;
    this.zoom = zoom;
    this.schedule();
  }

  schedule() {
    if (this.frame) return;
    this.frame = requestAnimationFrame(() => {
      this.frame = 0;
      this.draw();
    });
  }

  draw() {
    const { canvas, context } = this;
    const { width, height } = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    const pixelsWide = Math.round(width * ratio);
    const pixelsHigh = Math.round(height * ratio);
    if (canvas.width !== pixelsWide) canvas.width = pixelsWide;
    if (canvas.height !== pixelsHigh) canvas.height = pixelsHigh;
    context.resetTransform();
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.setTransform(this.zoom * ratio, 0, 0, this.zoom * ratio, this.x * ratio, this.y * ratio);
    context.strokeStyle = context.fillStyle = "#8ae6b8";
    context.lineWidth = 2.5;
    context.lineCap = context.lineJoin = "round";
    const radius = context.lineWidth / 2;
    const left = -this.x / this.zoom - radius;
    const top = -this.y / this.zoom - radius;
    const right = (width - this.x) / this.zoom + radius;
    const bottom = (height - this.y) / this.zoom + radius;
    for (const stroke of this.strokes) {
      if (stroke.right < left || stroke.bottom < top || stroke.left > right || stroke.top > bottom) continue;
      context.stroke(stroke.path);
      context.beginPath();
      context.arc(stroke.x, stroke.y, radius, 0, 2 * Math.PI);
      context.fill();
    }
  }
}
