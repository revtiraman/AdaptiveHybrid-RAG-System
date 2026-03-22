import { Suspense, lazy } from "react";

import AdvancedActionsPanel from "./components/AdvancedActionsPanel";
import ChatInterface from "./components/ChatInterface";
import CitationViewer from "./components/CitationViewer";
import DocumentUpload from "./components/DocumentUpload";
import SettingsPanel from "./components/SettingsPanel";

const EvalDashboard = lazy(() => import("./components/EvalDashboard"));
const GraphViewer = lazy(() => import("./components/GraphViewer"));
const ReasoningTrace = lazy(() => import("./components/ReasoningTrace"));

function PanelFallback({ label }: { label: string }) {
	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14, border: "1px solid #e5e7eb" }}>
			<h3 style={{ marginTop: 0, marginBottom: 6 }}>{label}</h3>
			<p style={{ margin: 0, color: "#6b7280", fontSize: 14 }}>Loading panel...</p>
		</section>
	);
}

export default function App() {
	return (
		<div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #fdf6e3, #e8f4f8)", padding: 16 }}>
			<div style={{ maxWidth: 1300, margin: "0 auto", display: "grid", gap: 16 }}>
				<header>
					<h1 style={{ margin: 0 }}>Advanced Hybrid RAG</h1>
					<p style={{ marginTop: 6 }}>Adaptive research assistant with hybrid retrieval, verification, and citations.</p>
				</header>
				<div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
					<div style={{ display: "grid", gap: 16, alignContent: "start" }}>
						<DocumentUpload />
						<SettingsPanel />
						<AdvancedActionsPanel />
						<Suspense fallback={<PanelFallback label="Evaluation" />}>
							<EvalDashboard />
						</Suspense>
					</div>
					<div style={{ display: "grid", gap: 16, alignContent: "start" }}>
						<ChatInterface />
						<Suspense fallback={<PanelFallback label="Reasoning Trace" />}>
							<ReasoningTrace />
						</Suspense>
						<CitationViewer />
						<Suspense fallback={<PanelFallback label="Knowledge Graph" />}>
							<GraphViewer />
						</Suspense>
					</div>
				</div>
			</div>
		</div>
	);
}
