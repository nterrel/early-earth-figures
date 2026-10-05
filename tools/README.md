# Figure catalog maintenance

[`sync_catalog.py`](sync_catalog.py) discovers the declared project figure-output folders, copies assets into manuscript-theme directories, and records source paths, SHA-256 hashes and scientific status. It builds a local gallery and README navigation using the reader-facing titles and descriptions in [metadata](../metadata/README.md).

Run `python3 figures/tools/sync_catalog.py --write` from the project root after existing figures change. Run the same command with `--check` to verify source/copy hashes, catalog membership and gallery links. This is a documentation/output synchronization step; it never reruns analysis or production. Update `SOURCE_ROOTS` and `CURRENT_PREFIXES` only when an approved folder move or new output family changes navigation. Historical paths are never overwritten. Add a title and specific description for each new source stem before refreshing; generation fails if a caption is missing.

[`export_share.py`](export_share.py) builds self-contained collaborator or proposed supplement packages from this library. See [SHARING.md](../SHARING.md) for the commands, visibility choices and later GitHub Pages setup. Exports are derived, ignored build outputs; they do not alter original scientific assets.
