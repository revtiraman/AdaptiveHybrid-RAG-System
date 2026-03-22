dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

prod:
	docker-compose up -d

ingest:
	curl -X POST http://127.0.0.1:8000/api/ingest/url -H "Content-Type: application/json" -d '{"url":"$(URL)"}'

benchmark:
	curl http://127.0.0.1:8000/api/evaluate/benchmark

test:
	pytest tests/

logs:
	docker-compose logs -f backend

shell:
	docker exec -it advanced-hybrid-rag-backend-1 bash

clean:
	docker-compose down -v --remove-orphans
