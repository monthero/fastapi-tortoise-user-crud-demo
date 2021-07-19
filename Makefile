# HELP
# This will output the help for each task
# thanks to https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


.DEFAULT_GOAL := help


lint: ## Verify if python files are properly linted
	isort --check-only app
	black --check app
	flake8


lint-fix: ## Fix python files linting
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place app
	isort app
	black app


run-tests: ## Run unit tests
	POSTGRES_HOST=localhost APP_ENV=local pytest -c ./pyproject.toml --disable-pytest-warnings


run-dev: ## Start the project in the local environment
	POSTGRES_HOST=localhost uvicorn app.main:app --reload --port 8080


docker-serve: ## Start the project in the local environment through docker
	docker-compose up -d


docker-serve-build:
	docker-compose up -d --build


docker-stop:
	docker-compose down


docker-clean: ## Completely clean the local installation and setup
	docker-compose down -v
	docker-compose rm


docker-run-tests:
	docker-compose exec api pytest -c ./pyproject.toml --disable-pytest-warnings
