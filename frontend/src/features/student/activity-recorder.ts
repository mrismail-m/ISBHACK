import type { ActivityBatch, ActivityEvent } from '../../api/types';
import { postActivity, sendActivityOnExit } from '../../api/activity';
export function eventKind(userEvent: string | undefined): ActivityEvent['k'] {
  if (userEvent === 'input.paste') return 'paste';
  if (userEvent === 'input.drop') return 'drop';
  if (userEvent === 'delete.cut') return 'cut';
  if (userEvent?.startsWith('delete.')) return 'del';
  if (userEvent === 'undo' || userEvent === 'redo') return userEvent;
  return 'type';
}
export class ActivityRecorder {
  private batches: ActivityBatch[];
  private current: ActivityBatch;
  private started = performance.now();
  private seq = 0;
  private sending: Promise<void> | null = null;
  private key: string;
  private submissionId: string;
  constructor(submissionId: string) {
    this.submissionId = submissionId;
    this.key = `vivagrade:pending:${localStorage.getItem('currentUserId')}:${submissionId}`;
    this.batches = JSON.parse(localStorage.getItem(this.key) || '[]') as ActivityBatch[];
    this.current = { session_id: crypto.randomUUID(), session_started_at: new Date().toISOString(), events: [] };
    this.batches.push(this.current);
    this.record('start');
  }
  record(k: ActivityEvent['k'], from = 0, to = 0, text = '') {
    this.current.events.push({ seq: this.seq++, t: Math.round(performance.now() - this.started), k, from, to, text });
    this.persist();
  }
  private persist() { localStorage.setItem(this.key, JSON.stringify(this.batches.filter(b => b.events.length))); }
  flush(): Promise<void> {
    if (this.sending) return this.sending.then(() => this.flush());
    if (!this.batches.some(b => b.events.length)) return Promise.resolve();
    const send = async () => {
      for (const batch of this.batches) {
        if (!batch.events.length) continue;
        const snapshot = { ...batch, events: [...batch.events] };
        const receipt = await postActivity(this.submissionId, snapshot);
        batch.events = batch.events.filter(e => e.seq > receipt.last_seq);
        this.persist();
      }
    };
    this.sending = send().finally(() => { this.sending = null; });
    return this.sending;
  }
  exit() {
    this.record('end');
    for (const batch of this.batches) if (batch.events.length) sendActivityOnExit(this.submissionId, batch);
  }
}
