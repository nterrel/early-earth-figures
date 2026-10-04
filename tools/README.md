# Figure catalog maintenance

[`sync_catalog.py`](sync_catalog.py) discovers the declared project figure-output folders, copies assets into manuscript-theme directories, and records source paths, SHA-256 hashes and scientific status. It builds a local gallery and README navigation.

Run `python3 figures/tools/sync_catalog.py --write` from the project root after existing figures change. Run the same command with `--check` to verify source/copy hashes, catalog membership and gallery links. This is a documentation/output synchronization step; it never reruns analysis or production. Update `SOURCE_ROOTS` and `CURRENT_PREFIXES` only when an approved folder move or new output family changes navigation. Historical paths are never overwritten.
