# Import environment variables from .env file
ifneq (,$(wildcard .env))
include .env
export
endif

DOCKER_COMPOSE := docker-compose -f $(or $(DOCKERFILE),docker-compose.yml)

# =================================================================
# INFRASTRUCTURE ACCESS
# =================================================================
connect-dev:
	ssh -i ${SSH_KEY_PATH} ubuntu@${DEV_SERVER_IP}

# =================================================================
# DOCKER COMMANDS
# Commands for managing Docker containers and services
# =================================================================
up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build

refresh: down build up

bash-api:
	$(DOCKER_COMPOSE) exec api bash

# =================================================================
# DATABASE COMMANDS
# Commands for database access and management
# =================================================================
psql:
	$(DOCKER_COMPOSE) exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# =================================================================
# DJANGO COMMANDS
# Commands for Django development and management
# =================================================================
make-migrations:
	$(DOCKER_COMPOSE) exec api python manage.py makemigrations

migrate:
	$(DOCKER_COMPOSE) exec api python manage.py migrate

django-shell:
	$(DOCKER_COMPOSE) exec api python manage.py shell

create-superuser:
	$(DOCKER_COMPOSE) exec api python manage.py createsuperuser

# =================================================================
# TESTING AND QUALITY
# Commands for running tests and code quality checks
# =================================================================
test:
	$(DOCKER_COMPOSE) exec api python src/manage.py test

lint:
	poetry run pre-commit run --all-files

# =================================================================
# LOGS
# Commands for viewing application logs
# =================================================================
logs:
	$(DOCKER_COMPOSE) logs -f

logs-api:
	$(DOCKER_COMPOSE) logs -f api

logs-db:
	$(DOCKER_COMPOSE) logs -f db
