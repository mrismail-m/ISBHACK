import { useEffect, useRef } from 'react';
import { EditorState, Transaction } from '@codemirror/state';
import { EditorView, keymap, lineNumbers } from '@codemirror/view';
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands';
import { markdown } from '@codemirror/lang-markdown';
import { eventKind, type ActivityRecorder } from './activity-recorder';
export function MarkdownEditor({ initial, recorder, onChange }: { initial: string; recorder: ActivityRecorder; onChange: (value: string) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const change = useRef(onChange);
  const initialDocument = useRef(initial);
  useEffect(() => { change.current = onChange; }, [onChange]);
  useEffect(() => {
    if (!host.current) return;
    const view = new EditorView({ parent: host.current, state: EditorState.create({ doc: initialDocument.current, extensions: [
      markdown(), history(), lineNumbers(), keymap.of([...defaultKeymap, ...historyKeymap]), EditorView.lineWrapping,
      EditorView.contentAttributes.of({ 'aria-label': 'Your markdown answer', spellcheck: 'true' }),
      EditorView.theme({ '&': { minHeight: '400px', fontSize: '16px' }, '.cm-content': { padding: '20px 12px', fontFamily: 'ui-monospace, monospace', lineHeight: '1.7' }, '.cm-gutters': { backgroundColor: '#fafafc', border: 'none', color: '#7a7a7a' }, '&.cm-focused': { outline: '2px solid #0071e3', outlineOffset: '-2px' } }),
      EditorView.updateListener.of(update => {
        for (const tr of update.transactions) {
          if (!tr.docChanged) continue;
          const kind = eventKind(tr.annotation(Transaction.userEvent));
          tr.changes.iterChanges((fromA, toA, fromB, _toB, inserted) => recorder.record(kind, fromB, fromB + toA - fromA, inserted.toString()));
        }
        if (update.docChanged) change.current(update.state.doc.toString());
      }),
    ] }) });
    return () => view.destroy();
  }, [recorder]);
  return <div ref={host} className="writing-editor" />;
}
