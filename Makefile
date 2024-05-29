# Install dependencies
install:
	poetry install

# Run tests with coverage report
test:
	poetry run pytest-cov

# Clean up build artifacts and pytest cache
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf dist
	rm -rf anydata.egg-info
	rm -rf htmlcov
	find anydata -name '__pycache__' -exec rm -rf {} +
