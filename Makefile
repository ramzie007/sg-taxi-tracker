# Makefile for sg-taxi-tracker

.PHONY: install lint format test all

install:
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
lint:
	flake8 planning_areas.py

format:
	black planning_areas.py

test:
	pytest tests

all: install lint format test