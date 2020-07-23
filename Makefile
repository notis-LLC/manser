VERSION := $(shell poetry version --no-ansi | tr -cd ".0-9")
HASH := $(shell git rev-parse --short HEAD)


black:
	poetry run isort manser tests
	poetry run black manser tests

build:
	docker build -t pavkazzz/manser:$(VERSION)-$(HASH) .

upload: build
	docker push pavkazzz/manser:$(VERSION)-$(HASH)