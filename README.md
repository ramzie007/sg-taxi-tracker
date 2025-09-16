
# sg-taxi-tracker

[![CI](https://github.com/ramzie007/sg-taxi-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/ramzie007/sg-taxi-tracker/actions/workflows/ci.yml)

**A Python tool to analyze and display Singapore’s busiest taxi areas, with Google Maps links and area descriptions.**

## Features
- Fetches real-time taxi locations from Data.gov.sg
- Maps taxis to Singapore planning areas using OneMap
- Outputs top 10 areas with the most taxis
- Provides human-readable area descriptions and Google Maps links

## Requirements
- Python 3.11
- See `requirements.txt` and `dev-requirements.txt`

## Setup
1. Clone the repository:
	```sh
	git clone https://github.com/ramzie007/sg-taxi-tracker.git
	cd sg-taxi-tracker
	```
2. Install dependencies:
	```sh
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
	```
3. Set environment variables:
	- `ONE_MAP_API_TOKEN`: API token for OneMap Singapore
	- `DATA_SG_API`: API key for Data.gov.sg
	You can use a `.env` file or export them in your shell.

## Usage
Run the main script:
```sh
python main.py
```

## Development
Use the provided `Makefile` for common tasks:
```sh
make install   # Install dependencies
make lint      # Lint code with flake8
make format    # Format code with black
make test      # Run tests
make all       # Run all
```

## Testing & CI
- Formatting and linting are enforced via [Black](https://black.readthedocs.io/) and [Flake8](https://flake8.pycqa.org/)
- GitHub Actions CI runs on every push and PR
