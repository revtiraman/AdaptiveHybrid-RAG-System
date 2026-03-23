import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRagStore } from '../store/ragStore';

export function useKeyboardShortcuts(queryInputId = 'global-query-input'): void {
  const navigate = useNavigate();
  const toggleCommandPalette = useRagStore((s) => s.toggleCommandPalette);
  const setActiveView = useRagStore((s) => s.setActiveView);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const isInInput = Boolean(target && ['INPUT', 'TEXTAREA'].includes(target.tagName));
      const meta = event.metaKey || event.ctrlKey;

      if (event.key === '/' && !isInInput) {
        event.preventDefault();
        document.getElementById(queryInputId)?.focus();
      }

      if (event.key === 'Escape') {
        document.activeElement instanceof HTMLElement && document.activeElement.blur();
      }

      if (meta && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        toggleCommandPalette();
      }

      if (meta && event.key === ',') {
        event.preventDefault();
        setActiveView('settings');
        navigate('/settings');
      }

      if (meta && /^[1-7]$/.test(event.key)) {
        event.preventDefault();
        const routes = ['chat', 'structure', 'claims', 'graph', 'eval', 'review', 'annotate'];
        const route = routes[Number(event.key) - 1] ?? 'chat';
        setActiveView(route);
        navigate(`/${route}`);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [navigate, queryInputId, setActiveView, toggleCommandPalette]);
}
