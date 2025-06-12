run:
	docker compose up

debug:
	docker compose -f docker-compose-debug.yml up

build:
	docker compose up --build

migrate:
	docker compose exec web-project python3 manage.py migrate

static:
	docker compose exec web-project python3 manage.py collectstatic --noinput --verbosity 0
	
clean:
	docker compose down --rmi all --volumes --remove-orphans