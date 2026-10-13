# Edit and share library figures

Energy figures now have a [dedicated Jupyter workshop](https://github.com/nterrel/early-earth-publication/blob/main/analysis/advisor_figures/notebook/library/energy_evolution.ipynb).
Notebook source lives in Nick's private analysis repository; access and committing
that notebook are separate from viewing this public figure library. The local
file is `early_earth_analysis_v2/analysis/advisor_figures/notebook/library/energy_evolution.ipynb`.
New local work must be committed there before those GitHub source links resolve.

The [category notebook guide](https://github.com/nterrel/early-earth-publication/blob/main/analysis/advisor_figures/notebook/LIBRARY_NOTEBOOKS.md)
maps energy, quench/fragment size and composition/recurrence to editable notebooks.
Other categories retain their script/historical producers; dedicated workshops
are not yet available for every library asset.

Edit controls → rerun the plotting cell → run a separate Save cell → run Refresh
library with optional website staging → inspect → commit and push the figure
repository. Rendering is preview-only. PNG/PDF exports and their catalog copies
retain figure IDs and source provenance, so Adrian can identify exactly which
view needs a change. Website updates do not select final manuscript panels.

The new energy figures offer adjustable 400×400 counts, a finer high-temperature
view and 100/400/800 trials inspired by the original dissertation notebook.
Independent bin controls and log/linear count colors reveal detail; export DPI
sharpens the rendering but does not change scientific resolution.

A complete portable snapshot is staged at `site/` before committing. The active
workflow validates its bytes and links and publishes on every main push. Staging
uses `metadata/public_library_selection.json` and the proposed supplement selection;
new local candidates stay local until selected. See [SHARING.md](SHARING.md).
