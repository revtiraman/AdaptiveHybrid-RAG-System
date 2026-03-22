import ChatInterface from "./components/ChatInterface";
import CitationViewer from "./components/CitationViewer";
import DocumentUpload from "./components/DocumentUpload";
import EvalDashboard from "./components/EvalDashboard";
import GraphViewer from "./components/GraphViewer";
import ReasoningTrace from "./components/ReasoningTrace";
import SettingsPanel from "./components/SettingsPanel";

export default function App() {
	return (
		<div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #fdf6e3, #e8f4f8)", padding: 16 }}>
			<div style={{ maxWidth: 1300, margin: "0 auto", display: "grid", gap: 16 }}>
				<header>
					<h1 style={{ margin: 0 }}>Advanced Hybrid RAG</h1>
					<p style={{ marginTop: 6 }}>Adaptive research assistant with hybrid retrieval, verification, and citations.</p>
				</header>
				<div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 16 }}>
					<div style={{ display: "grid", gap: 16 }}>
						<DocumentUpload />
						<SettingsPanel />
						<EvalDashboard />
					</div>
					<div style={{ display: "grid", gap: 16 }}>
						<ChatInterface />
						<ReasoningTrace />
						<CitationViewer />
						<GraphViewer />
					</div>
				</div>
			</div>
		</div>
	);
}
