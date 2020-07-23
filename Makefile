VERSION := $(shell poetry version --no-ansi | tr -cd ".0-9")

black:
	poetry run isort -rc manser tests
	poetry run black manser tests

build:
	docker build . -t pavkazzz/manser:$(VERSION)