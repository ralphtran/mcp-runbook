#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit  # Navigate to project root
PYTHONPATH=. python src/main.py --server -f test/data/sample-runbook.yaml
