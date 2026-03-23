export function ShortcutsModal() {
  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="rounded-lg border border-slate-300 bg-surface-primary p-4">
        <h3 className="font-semibold">Keyboard Shortcuts</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-text-secondary">
          <li>/ focus query input</li>
          <li>Cmd+K command palette</li>
          <li>Cmd+1..7 switch primary views</li>
          <li>Cmd+, open settings</li>
          <li>Escape close active dialog</li>
        </ul>
      </div>
    </div>
  );
}
