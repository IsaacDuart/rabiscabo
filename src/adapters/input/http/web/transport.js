import { protocol } from "/protocol.js";

const BATCH = protocol.maxEvents;
const QUEUE_LIMIT = BATCH * 4;

export class Transport {
  constructor(token, onStatus) {
    this.token = token;
    this.onStatus = onStatus;
    this.client = crypto.randomUUID();
    this.sequence = 0;
    this.queue = [];
    this.online = false;
    this.sending = false;
    this.frame = 0;
  }

  enqueue(sample, position) {
    if (!this.online) return false;
    if (this.queue.length === QUEUE_LIMIT) {
      this.queue = [[0, ...position, 0]];
      this.schedule();
      return false;
    }
    this.queue.push(sample);
    this.schedule();
    return true;
  }

  schedule() {
    if (!this.frame && !this.sending) {
      this.frame = requestAnimationFrame(() => {
        this.frame = 0;
        void this.flush();
      });
    }
  }

  async flush() {
    if (this.sending || (document.hidden && !this.queue.length)) return;
    this.sending = true;
    const packet = [this.client, ++this.sequence, this.queue.splice(0, BATCH)];
    const abort = new AbortController();
    const timeout = setTimeout(() => abort.abort(), 650);
    try {
      const response = await fetch("/events", {
        method: "POST",
        headers: { "Authorization": "Bearer " + this.token, "Content-Type": "application/json" },
        body: JSON.stringify(packet),
        cache: "no-store",
        redirect: "error",
        signal: abort.signal,
      });
      if (!response.ok) {
        const message = response.status === 403 ? "Reabra a sessão pelo computador."
          : response.status === 409 ? "Aguardando a mesa ficar disponível…"
            : "Aguardando conexão USB…";
        this.disconnect(message);
        return;
      }
      this.online = true;
      this.onStatus(true, "Conectado por USB");
    } catch {
      this.disconnect("Aguardando conexão USB…");
    } finally {
      clearTimeout(timeout);
      this.sending = false;
      if (this.queue.length) {
        if (document.hidden) void this.flush();
        else this.schedule();
      }
    }
  }

  disconnect(message) {
    if (this.online) {
      this.client = crypto.randomUUID();
      this.sequence = 0;
    }
    this.online = false;
    this.queue = [];
    this.onStatus(false, message);
  }
}
