import { beforeEach, describe, expect, it, vi } from 'vitest';
import { EditorState } from '@codemirror/state';
import type { ActivityBatch } from '../../api/types';
const post = vi.hoisted(() => vi.fn());
vi.mock('../../api/activity', () => ({ postActivity: post, sendActivityOnExit: vi.fn() }));
import { ActivityRecorder, eventKind } from './activity-recorder';
const memory = new Map<string, string>();
beforeEach(() => {
  memory.clear(); post.mockReset();
  vi.stubGlobal('localStorage', { getItem: (key: string) => memory.get(key) ?? null, setItem: (key: string, value: string) => memory.set(key, value) });
});
describe('capture and upload', () => {
  it('replays multiple changes with UTF-16 positions in sequential order', () => {
    const initial = 'A😀BCDE';
    const transaction = EditorState.create({ doc: initial }).update({ changes: [{ from: 1, to: 3, insert: '🙂!' }, { from: 5, to: 6, insert: 'XYZ' }] });
    let replay = initial;
    transaction.changes.iterChanges((fromA, toA, fromB, _toB, inserted) => {
      replay = replay.slice(0, fromB) + inserted.toString() + replay.slice(fromB + toA - fromA);
    });
    expect(replay).toBe(transaction.newDoc.toString());
    expect(eventKind('input.paste')).toBe('paste');
    expect(eventKind('delete.cut')).toBe('cut');
    expect(eventKind('input.drop')).toBe('drop');
    expect(eventKind('undo')).toBe('undo');
  });
  it('keeps failed events and retries the identical sequence', async () => {
    const recorder = new ActivityRecorder('s_1');
    recorder.record('paste', 0, 0, 'pasted text');
    post.mockRejectedValueOnce(new Error('offline'));
    await expect(recorder.flush()).rejects.toThrow('offline');
    expect([...memory.values()].join('')).toContain('pasted text');
    post.mockImplementation((_id: string, batch: ActivityBatch) => Promise.resolve({ received: batch.events.length, last_seq: batch.events.at(-1)!.seq }));
    await recorder.flush();
    expect(post.mock.calls[0][1]).toEqual(post.mock.calls[1][1]);
    expect([...memory.values()].join('')).toBe('[]');
  });
  it('does not lose edits captured while an upload is in flight', async () => {
    const recorder = new ActivityRecorder('s_1');
    let acknowledge!: (value: { received: number; last_seq: number }) => void;
    post.mockReturnValueOnce(new Promise(resolve => { acknowledge = resolve; }));
    const pending = recorder.flush();
    recorder.record('type', 0, 0, 'new');
    acknowledge({ received: 1, last_seq: 0 });
    await pending;
    expect([...memory.values()].join('')).toContain('new');
    post.mockResolvedValueOnce({ received: 1, last_seq: 1 });
    await recorder.flush();
    expect(post.mock.calls[1][1].events).toHaveLength(1);
    expect(post.mock.calls[1][1].events[0].text).toBe('new');
  });
});
