import { useRagStore } from '../../store/ragStore';

export function SettingsPanel() {
  const settings = useRagStore((s) => s.settings);
  const updateSettings = useRagStore((s) => s.updateSettings);

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="rounded-lg border border-slate-300 bg-surface-primary p-4">
        <h3 className="font-semibold">Settings</h3>
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={settings.enableAdaptive} onChange={(e) => updateSettings({ enableAdaptive: e.target.checked })} />
          Enable adaptive corrective retrieval
        </label>
      </div>
    </div>
  );
}
