import { useEffect, useMemo, useState } from 'react';

type Props = {
  id: string;
  min?: number;
  max?: number;
  initial?: number;
  left: React.ReactNode;
  right: React.ReactNode;
};

export function ResizablePanel({ id, min = 220, max = 520, initial = 320, left, right }: Props) {
  const key = useMemo(() => `panel:${id}`, [id]);
  const [size, setSize] = useState(() => Number(localStorage.getItem(key) ?? initial));

  useEffect(() => {
    localStorage.setItem(key, String(size));
  }, [key, size]);

  return (
    <div className="flex h-full">
      <div style={{ width: size }} className="min-w-0">{left}</div>
      <div
        className="w-1 cursor-col-resize bg-slate-300"
        onMouseDown={(event) => {
          const startX = event.clientX;
          const startSize = size;
          const onMove = (ev: MouseEvent) => setSize(Math.max(min, Math.min(max, startSize + ev.clientX - startX)));
          const onUp = () => {
            window.removeEventListener('mousemove', onMove);
            window.removeEventListener('mouseup', onUp);
          };
          window.addEventListener('mousemove', onMove);
          window.addEventListener('mouseup', onUp);
        }}
      />
      <div className="min-w-0 flex-1">{right}</div>
    </div>
  );
}
