import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { labApi } from './learning-lab';

vi.mock('./client', () => ({ USE_FIXTURES: true, apiClient: vi.fn(), ApiError: class extends Error {} }));
vi.mock('./student', () => ({ studentApi: { submission: vi.fn(async (id: string) => ({
  id, assessment_id: 'a_1', status: 'submitted', content_md: '# Collisions\nTwo keys can map to the same index.\nChaining keeps a list of entries.',
})) } }));

beforeEach(() => {
  const data = new Map<string, string>();
  vi.stubGlobal('localStorage', {
    get length() { return data.size; }, key: (i: number) => [...data.keys()][i] || null,
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => { data.set(key, value); },
    removeItem: (key: string) => { data.delete(key); },
  });
});
afterEach(() => vi.unstubAllGlobals());
it('starts a collision submission without requiring the literal word hash', async () => {
  const initial = await labApi.start('s');
  expect(initial.mode).toBe('fixture');
  expect(initial.anchor_quote).toBe('Two keys can map to the same index.');
  expect(initial.recovery).toBeNull();
  expect(await labApi.start('s')).toEqual(initial);
});
it('persists real fixture interactions rather than pre-filling teacher outcomes', async () => {
  expect((await labApi.report('a_1')).sessions).toEqual([]);
  await labApi.start('s');
  await expect(labApi.answer('s', 'recovery', 'skip')).rejects.toThrow('already completed');
  const first = await labApi.answer('s', 'challenge', 'Hashing is always constant time.');
  expect(first.initial?.level).toBe(0);
  expect(await labApi.answer('s', 'challenge', first.initial_answer)).toEqual(first);
  const final = await labApi.answer('s', 'recovery', 'The same bucket still requires a linear scan of the chain in O(n).');
  expect(final.final?.level).toBe(2);
  expect((await labApi.report('a_1')).sessions).toEqual([final]);
  expect((await labApi.report('different-assessment')).sessions).toEqual([]);
});
