import {
	Bar,
	BarChart,
	CartesianGrid,
	Legend,
	PolarAngleAxis,
	PolarGrid,
	Radar,
	RadarChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

import { useRAGStore } from "../store/ragStore";

export default function EvalDashboard() {
	const { evaluationResults } = useRAGStore();
	const metrics = evaluationResults ?? {
		faithfulness: 0.72,
		answer_relevancy: 0.78,
		context_precision: 0.68,
		context_recall: 0.74,
	};

	const chartData = [
		{ metric: "Faithfulness", score: Number(metrics.faithfulness.toFixed(3)) },
		{ metric: "Answer Relevancy", score: Number(metrics.answer_relevancy.toFixed(3)) },
		{ metric: "Context Precision", score: Number(metrics.context_precision.toFixed(3)) },
		{ metric: "Context Recall", score: Number(metrics.context_recall.toFixed(3)) },
	];

	return (
		<section style={{ background: "white", borderRadius: 12, padding: 14 }}>
			<h3>Evaluation</h3>
			{!evaluationResults && <p style={{ marginTop: 0, color: "#6b7280" }}>Showing sample metrics until backend evaluation is available.</p>}
			<div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
				<div style={{ width: "100%", height: 220 }}>
					<ResponsiveContainer>
						<BarChart data={chartData}>
							<CartesianGrid strokeDasharray="3 3" />
							<XAxis dataKey="metric" hide />
							<YAxis domain={[0, 1]} />
							<Tooltip />
							<Legend />
							<Bar dataKey="score" fill="#2563eb" />
						</BarChart>
					</ResponsiveContainer>
				</div>
				<div style={{ width: "100%", height: 220 }}>
					<ResponsiveContainer>
						<RadarChart data={chartData}>
							<PolarGrid />
							<PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
							<Radar name="Score" dataKey="score" stroke="#0f766e" fill="#14b8a6" fillOpacity={0.35} />
						</RadarChart>
					</ResponsiveContainer>
				</div>
			</div>
		</section>
	);
}

