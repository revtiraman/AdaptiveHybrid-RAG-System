import { useEffect, useRef, useState } from "react";

export function useStream() {
	const [events, setEvents] = useState<any[]>([]);
	const [connected, setConnected] = useState(false);
	const sourceRef = useRef<EventSource | null>(null);

	useEffect(() => {
		return () => {
			sourceRef.current?.close();
		};
	}, []);

	const connect = (endpoint: string) => {
		sourceRef.current?.close();
		setEvents([]);
		const source = new EventSource(endpoint);
		source.onopen = () => setConnected(true);
		source.onmessage = (event) => {
			try {
				setEvents((prev) => [...prev, JSON.parse(event.data)]);
			} catch {
				setEvents((prev) => [...prev, { type: "chunk", text: event.data }]);
			}
		};
		source.onerror = () => {
			setConnected(false);
			setEvents((prev) => [...prev, { type: "error", message: "stream_connection_failed" }]);
			source.close();
		};
		sourceRef.current = source;
	};

	const close = () => {
		setConnected(false);
		sourceRef.current?.close();
	};

	return { events, connect, close, connected };
}
