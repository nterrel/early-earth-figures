# Figure captions and collection choices

Edit `title`, `description` and optional `note` in [current_figures.json](current_figures.json) or [historical_figures.json](historical_figures.json), then run `python3 figures/tools/sync_catalog.py --write` from the project root. Keys are historical source paths without the final extension; PNG/PDF variants share a caption. The title and description address readers; notes retain scientific or provenance details in expandable sections. Filenames and source images stay unchanged.

[Collection settings](collection.json) preserve author-requested exclusions so synchronization does not reintroduce them. [Supplement selection](supplement_selection.json) is a proposed review set, not a publication approval; edit its exact source paths when choosing panels. Export the selected collection with the command in [sharing instructions](../SHARING.md).
