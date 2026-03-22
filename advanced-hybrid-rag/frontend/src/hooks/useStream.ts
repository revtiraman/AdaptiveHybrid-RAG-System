import { useEffect, useRef, useState } from "react";

export function useStream(endpoint: string) {
	const [events, setEvents] = useState<any[]>([]);
	const sourceRef = useRef<EventSource | null>(null);

	useEffect(() => {
		return () => {
			sourceRef.current?.close();
		};
	}, []);

	const connect = () => {
		sourceRef.current?.close();
		const source = new EventSource(endpoint);
		source.onmessage = (event) => {
			try {
				setEvents((prev) => [...prev, JSON.parse(event.data)]);
			} catch {
				setEvents((prev) => [...prev, { type: "chunk", text: event.data }]);
			}
		};
		source.onerror = () => source.close();
		sourceRef.current = source;
	};

	const close = () => sourceRef.current?.close();

	return { events, connect, close };
}
