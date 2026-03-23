import Fuse from 'fuse.js';
import { useMemo, useState } from 'react';

export type Command = { id: string; label: string; to: string };

const commands: Command[] = [
  { id: 'upload', label: '/upload', to: '/chat' },
  { id: 'scope-all', label: '/scope all', to: '/chat' },
  { id: 'mode-multihop', label: '/mode multihop', to: '/chat?mode=multihop' },
  { id: 'clear', label: '/clear', to: '/chat' },
  { id: 'export-markdown', label: '/export markdown', to: '/chat' },
  { id: 'benchmark', label: '/benchmark', to: '/eval' },
  { id: 'review', label: '/review', to: '/review' },
  { id: 'monitor', label: '/monitor', to: '/monitor' },
  { id: 'settings', label: '/settings', to: '/settings' },
  { id: 'help', label: '/help', to: '/help' },
];

type Props = {
  onClose: () => void;
  onRun: (command: Command) => void;
};

export function CommandPalette({ onClose, onRun }: Props) {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);

  const fuse = useMemo(() => new Fuse(commands, { keys: ['label'], threshold: 0.4 }), []);
  const items = useMemo(() => {
    if (!query.trim()) return commands;
    return fuse.search(query).map((x) => x.item);
  }, [fuse, query]);

  return (
    <div className="fixed inset-0 z-50 bg-black/25 p-6" onClick={onClose}>
      <div className="mx-auto mt-20 max-w-2xl rounded-xl border border-slate-300 bg-surface-primary p-3" onClick={(e) => e.stopPropagation()}>
        <input
          autoFocus
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setSelected(0);
          }}
          onKeyDown={(event) => {
            if (event.key === 'Escape') onClose();
            if (event.key === 'ArrowDown') {
              event.preventDefault();
              setSelected((s) => Math.min(s + 1, items.length - 1));
            }
            if (event.key === 'ArrowUp') {
              event.preventDefault();
              setSelected((s) => Math.max(0, s - 1));
            }
            if (event.key === 'Enter' && items[selected]) {
              event.preventDefault();
              onRun(items[selected]);
              onClose();
            }
          }}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none"
          placeholder="Type a command..."
        />
        <div className="mt-2 max-h-72 overflow-y-auto">
          {items.map((item, index) => (
            <button
              key={item.label}
              className={`block w-full rounded-md px-3 py-2 text-left text-sm ${index === selected ? 'bg-surface-secondary' : ''}`}
              onMouseEnter={() => setSelected(index)}
              onClick={() => {
                onRun(item);
                onClose();
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
