# a2a-protocol-core

A2A Protocol Family reference implementation.
Specs A2A-001 through A2A-060 + A2A-031 Financial Address Resolution Binding.

Sibling repo to financial-autonomy-stack. A2A-031 is the future bridge.

## Quick start
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

## Tests
pytest tests/ -v
