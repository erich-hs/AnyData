# Install dependencies
install:
	poetry install

install-complete:
	poetry install --extras "guidance"

# Run tests
test:
	poetry run pytest --cov

# Run tests with coverage report
test-coverage:
	poetry run pytest --cov --cov-report=xml

# Clean up build artifacts and pytest cache
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf dist
	rm -rf anydata.egg-info
	rm -rf htmlcov
	find anydata -name '__pycache__' -exec rm -rf {} +
