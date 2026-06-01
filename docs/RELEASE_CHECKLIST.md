# Release Checklist

Run before publishing a stable local release.

## Commands

```bash
python -m pytest
python -m ruff check .
python -m compileall app.py src tests
streamlit run app.py
```

## Manual Checks

- Open every sidebar page once.
- Confirm normal UI does not show raw tracebacks.
- Confirm provider failures show readable messages.
- Confirm existing `data/quant_replay.db` opens without destructive migration.
- Confirm `data/*.db` is ignored by git.
- Confirm no secrets, tokens, or large cache files are staged.
- Update screenshots in `docs/screenshots/` when the UI materially changes.

## Release Assets

- `VERSION`
- `CHANGELOG.md`
- `README.md`
- `sample_data/watchlist_sample.csv`
- `sample_data/trades_sample.csv`
