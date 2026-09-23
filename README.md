# polymarket_history

![Python](https://img.shields.io/badge/python-3.11+-blue)

Polymarket wallet history via Polygon RPC (no Polymarket API).

## Usage

```bash
poetry run polymarket-history balance
poetry run polymarket-history history --from-block 91000000 --to-block 91030000
poetry run polymarket-history check --from-block 91000000 --to-block 91030000

poetry run polymarket-history ctf-balance --token-id 123
poetry run polymarket-history ctf-history --from-block 91000000 --to-block 91030000
poetry run polymarket-history ctf-check --from-block 91000000 --to-block 91030000

poetry run polymarket-history check --from-block 80813662 --to-block 94298158 --batch-size 5000 # full wallet
poetry run polymarket-history ctf-check --from-block 80813662 --to-block 94298158 --batch-size 5000 # full wallet
```

## Example

Look at [playbook.ipynb](playbook.ipynb).
