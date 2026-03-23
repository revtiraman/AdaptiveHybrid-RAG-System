import { useMemo } from 'react';

type Props = { text: string };

export function StreamingText({ text }: Props) {
  const chars = useMemo(() => text.split(''), [text]);

  return (
    <span>
      {chars.map((char, index) => (
        <span key={`${index}-${char}`} className="stream-char" style={{ animationDelay: `${Math.min(index * 12, 480)}ms` }}>
          {char}
        </span>
      ))}
    </span>
  );
}
