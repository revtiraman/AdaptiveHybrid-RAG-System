import { FormEvent, useMemo, useState } from "react";

import { useRAGStore } from "../store/ragStore";

export default function AdvancedActionsPanel() {
	const {
		documents,
		planningSteps,
		literatureReview,
		feedbackStats,
		arxivItems,
		annotationsByDoc,
		runPlanning,
		generateLiteratureReview,
		refreshFeedbackStats,
		pollArxiv,
		configureArxiv,
		createAnnotation,
		loadAnnotations,
	} = useRAGStore();

	const [planQuery, setPlanQuery] = useState("Compare retrieval methods for this topic");
	const [topic, setTopic] = useState("Hybrid RAG");
	const [categories, setCategories] = useState("cs.AI,cs.CL");
	const [keywords, setKeywords] = useState("rag,retrieval");
	const [annotationNote, setAnnotationNote] = useState("Useful chunk for summary");

	const firstDoc = documents[0]?.doc_id || "";
	const currentAnnotations = useMemo(() => (firstDoc ? annotationsByDoc[firstDoc] ?? [] : []), [annotationsByDoc, firstDoc]);

	const onConfigureMonitor = async (e: FormEvent) => {
		e.preventDefault();
		await configureArxiv(
			categories
				.split(",")
				.map((v) => v.trim())
				.filter(Boolean),
			keywords
				.split(",")
				.map((v) => v.trim())
				.filter(Boolean),
		);
	};

	const onAnnotate = async () => {
		if (!firstDoc) return;
		await createAnnotation(firstDoc, "chunk-1", annotationNote, "note");
	};

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Advanced Actions</h3>

			<div style={{ marginBottom: 12 }}>
				<strong>Planning</strong>
				<div style={{ display: "flex", gap: 8, marginTop: 6 }}>
					<input value={planQuery} onChange={(e) => setPlanQuery(e.target.value)} style={{ flex: 1 }} />
					<button onClick={() => void runPlanning(planQuery)}>Run</button>
				</div>
				<div style={{ marginTop: 6, fontSize: 13 }}>
					{planningSteps.length === 0 ? "No plan yet." : `${planningSteps.length} planning steps captured.`}
				</div>
			</div>

			<div style={{ marginBottom: 12 }}>
				<strong>Literature Review</strong>
				<div style={{ display: "flex", gap: 8, marginTop: 6 }}>
					<input value={topic} onChange={(e) => setTopic(e.target.value)} style={{ flex: 1 }} />
					<button onClick={() => void generateLiteratureReview(topic)}>Generate</button>
				</div>
				{literatureReview && <pre style={{ whiteSpace: "pre-wrap", maxHeight: 120, overflow: "auto" }}>{literatureReview}</pre>}
			</div>

			<div style={{ marginBottom: 12 }}>
				<strong>Feedback</strong>
				<div style={{ marginTop: 6 }}>
					<button onClick={() => void refreshFeedbackStats()}>Refresh Stats</button>
				</div>
				{feedbackStats && (
					<p style={{ marginTop: 6, fontSize: 13 }}>
						Total: {feedbackStats.total_feedback}, Hard negatives: {feedbackStats.hard_negatives}, High quality: {feedbackStats.high_quality}
					</p>
				)}
			</div>

			<div style={{ marginBottom: 12 }}>
				<strong>arXiv Monitor</strong>
				<form onSubmit={onConfigureMonitor} style={{ marginTop: 6, display: "grid", gap: 6 }}>
					<input value={categories} onChange={(e) => setCategories(e.target.value)} placeholder="categories comma-separated" />
					<input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="keywords comma-separated" />
					<div style={{ display: "flex", gap: 8 }}>
						<button type="submit">Configure</button>
						<button type="button" onClick={() => void pollArxiv()}>
							Poll
						</button>
					</div>
				</form>
				<p style={{ fontSize: 13, marginTop: 6 }}>Items: {arxivItems.length}</p>
			</div>

			<div>
				<strong>Annotations</strong>
				<div style={{ display: "flex", gap: 8, marginTop: 6 }}>
					<button disabled={!firstDoc} onClick={() => firstDoc && void loadAnnotations(firstDoc)}>
						Load Latest Doc Annotations
					</button>
					<button disabled={!firstDoc} onClick={() => void onAnnotate()}>
						Add Note
					</button>
				</div>
				<input
					value={annotationNote}
					onChange={(e) => setAnnotationNote(e.target.value)}
					placeholder="Annotation note"
					style={{ marginTop: 6, width: "100%" }}
				/>
				<p style={{ marginTop: 6, fontSize: 13 }}>Current doc annotations: {currentAnnotations.length}</p>
			</div>
		</section>
	);
}
