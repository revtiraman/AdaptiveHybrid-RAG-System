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
			<br />
			<label>
				<input
					type="checkbox"
					checked={Boolean(settings.enable_planning)}
					onChange={(e) => updateSettings({ enable_planning: e.target.checked })}
				/>
				Planning Agent
			</label>
			<br />
			<label>
				<input
					type="checkbox"
					checked={Boolean(settings.enable_verification)}
					onChange={(e) => updateSettings({ enable_verification: e.target.checked })}
				/>
				Verification
			</label>
			<br />
			<label>
				<input
					type="checkbox"
					checked={Boolean(settings.enable_adaptive)}
					onChange={(e) => updateSettings({ enable_adaptive: e.target.checked })}
				/>
				Adaptive Control
			</label>
			<div style={{ marginTop: 8 }}>
				<label>
					Max Sources: {settings.max_sources}
					<input
						type="range"
						min={1}
						max={20}
						value={settings.max_sources}
						onChange={(e) => updateSettings({ max_sources: Number(e.target.value) || 5 })}
						style={{ display: "block", width: "100%", marginTop: 6 }}
					/>
				</label>
			</div>
			<div style={{ marginTop: 8 }}>
				<label>
					Citation Style
					<select
						value={settings.citation_style || "inline"}
						onChange={(e) => updateSettings({ citation_style: e.target.value as "inline" | "footnote" })}
						style={{ marginLeft: 6 }}
					>
						<option value="inline">Inline</option>
						<option value="footnote">Footnote</option>
					</select>
				</label>
			</div>
			<div style={{ marginTop: 8 }}>
				<label>
					Model
					<input
						type="text"
						value={settings.model || ""}
						onChange={(e) => updateSettings({ model: e.target.value || undefined })}
						placeholder="gemini-2.0-flash"
						style={{ marginLeft: 6, width: "60%" }}
					/>
				</label>
			</div>
		</section>
	);
}

