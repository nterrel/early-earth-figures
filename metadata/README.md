# Figure captions and collection choices

Edit `title`, `description` and optional `note` in [current_figures.json](current_figures.json) or [historical_figures.json](historical_figures.json), then run `python3 figures/tools/sync_catalog.py --write` from the project root. Keys are historical source paths without the final extension; PNG/PDF variants share a caption. The title and description address readers; notes retain scientific or provenance details in expandable sections. Filenames and source images stay unchanged.

[Collection settings](collection.json) preserve author-requested exclusions so synchronization does not reintroduce them. [Supplement selection](supplement_selection.json) is a proposed review set, not a publication approval; edit its exact source paths when choosing panels. Export the selected collection with the command in [sharing instructions](../SHARING.md).

State comparisons use blue `#1f77b4` for original/hot/before and orange
`#ff7f0e` for quenched/after (D15). Preserve the mapping in exported figures
and captions; density and molecular element colors encode other quantities.

Exact duplicates are excluded by exact source-path rules in `collection.json`, with byte/pixel proof in [the A28 audit](../../early_earth_analysis_v2/analysis/figure_review/results/duplicate_audit.json). This removes redundant catalog copies, never authoritative manuscript, frozen or historical sources. Scaling, labels, palettes, different views and nonidentical data remain for [author review](../../early_earth_analysis_v2/docs/FIGURE_VARIANTS_REVIEW_20261005.md).

Approved complementary panels can share one card through `gallery_bundles` in `collection.json`. This does not exclude or delete their source assets: the combined preview retains individual panel links, captions and source hashes. A29/F23 keeps the two historical fragments misidentified as alanine in the alanine category. See [the source explanation](../../early_earth_analysis_v2/analysis/alanine_matching_diagnostic/README.md).

D20/A31 author-approved curation adds 89 exact public source-path exclusions to
`collection.json`; originals and central local copies remain preserved. The live
gallery and curated stage retain 157 assets/126 groups, the 19 optional historical
Early Earth groups and the unchanged supplement.
[Execution results](../../early_earth_analysis_v2/docs/WEBSITE_CURATION_RESULTS_20261010.md)
bind the membership and hosted checks. Separate local/A32 candidates remain local.

The [public allowlist](public_library_selection.json) owns exact hosted membership;
Pages preparation and notebook staging use it automatically. `gallery_order` and
`gallery_sections` in `collection.json` keep related views adjacent and place HTML
and GIFs first. A source with `scope: public-library` is omitted from that public
selection while remaining available to the proposed supplement (currently F10's
reconstruction PNG). Source removal is not part of gallery curation.

Reader-facing titles, categories and captions present one ongoing project. Use
analysis stages or documented dates when chronology matters; preserve source
paths, version lineage and scientific qualifications in the provenance records.
The A33 follow-up groups RMSD with alanine, keeps the static 96-atom views in the
figure collection and records the author-selected energy order in `gallery_order`.
