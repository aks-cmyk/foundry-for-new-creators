.PHONY: test demo seed clean

test:
	python3 -m pytest tests/ -q || python3 tests/test_smoke.py

demo:
	python3 scripts/demo.py

seed:
	python3 scripts/seed.py

clean:
	rm -f foundry/data/foundry.db dashboard/index.html
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
