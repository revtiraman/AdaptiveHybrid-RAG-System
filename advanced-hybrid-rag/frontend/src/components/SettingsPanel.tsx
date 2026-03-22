import { useRAGStore } from "../store/ragStore";

export default function SettingsPanel() {
	const { settings, updateSettings } = useRAGStore();
	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Settings</h3>
			<label>
				<input type="checkbox" checked={settings.use_hyde} onChange={(e) => updateSettings({ use_hyde: e.target.checked })} /> HyDE
			</label>
			<br />
			<label>
				<input type="checkbox" checked={settings.use_graph} onChange={(e) => updateSettings({ use_graph: e.target.checked })} /> Graph
			</label>
			<br />
			<label>
				<input
					type="checkbox"
					checked={settings.use_colbert}
					onChange={(e) => updateSettings({ use_colbert: e.target.checked })}
				/>
				ColBERT
			</label>
			<div style={{ marginTop: 8 }}>
				<label>
					Max Sources
					<input
						type="number"
						min={1}
						max={20}
						value={settings.max_sources}
						onChange={(e) => updateSettings({ max_sources: Number(e.target.value) || 5 })}
						style={{ marginLeft: 6, width: 60 }}
					/>
				</label>
			</div>
		</section>
	);
}

