import { useRAGStore } from "../store/ragStore";

export default function EvalDashboard() {
	const { evaluationResults } = useRAGStore();
	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Evaluation</h3>
			{evaluationResults ? (
				<ul>
					<li>Faithfulness: {evaluationResults.faithfulness}</li>
					<li>Answer relevancy: {evaluationResults.answer_relevancy}</li>
					<li>Context precision: {evaluationResults.context_precision}</li>
					<li>Context recall: {evaluationResults.context_recall}</li>
				</ul>
			) : (
				<p>No evaluation metrics yet.</p>
			)}
		</section>
	);
}

