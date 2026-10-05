# Figure library

Start with **[the visual gallery](index.html)**. Open it in a browser and filter by topic or search by title, figure ID or filename. Each figure has a specific caption; scientific caveats and provenance are under Figure details. Images open at full resolution; PDF and HTML variants are linked alongside them. Local HTML links open the original reading views so neighboring previews and data resolve; portable exports include repaired copies and their dependencies.

The folders follow proposed manuscript themes, not final figure order. Every asset keeps its original filename after a readable source prefix. Copies from multiple generations are deliberately retained so a matching picture does not erase different provenance.

## Choose a reading path

- For collaborators, browse [the public figure library](https://nterrel.github.io/early-earth-figures/) or [the proposed supplement](https://nterrel.github.io/early-earth-figures/supplement/).
- For portable collaborator packages and the proposed supplement, use [the sharing guide](SHARING.md).
- To edit captions or add future figures, use [the editorial metadata guide](metadata/README.md).
- For Adrian's short reading path, use [advisor-handoff](../advisor-handoff/README.md).
- For current editable figures, use [the maintained notebook guide](../early_earth_analysis_v2/analysis/advisor_figures/notebook/README.md).
- For approval/readiness, use [the publication plan](../early_earth_analysis_v2/docs/PUBLICATION_PLAN.md).
- For exact origin/hash/status mappings, use [catalog.csv](catalog.csv) or [catalog.json](catalog.json).

- [Energy evolution](01_energy_evolution/README.md): 11 files. Energy and temperature changes during heating, the hot interval, and cooling.
- [Alanine and conformations](02_alanine_and_conformations/README.md): 16 files. Alanine structures, molecular orientations, and distributions of torsion angles.
- [Scale, discovery and sampling](03_scale_discovery_and_sampling/README.md): 8 files. How simulation size and sampling intervals affect the structures observed.
- [Quench and fragment size](04_quench_and_fragment_size/README.md): 76 files. Fragment sizes and connectivity before and after cooling, including comparisons based on heavy atoms.
- [Composition, recurrence and topology](05_composition_recurrence_and_topology/README.md): 32 files. Elemental composition, structural variety, recurring fragments, and connectivity patterns.
- [Methods and performance](06_methods_and_performance/README.md): 4 files. Analysis workflows, computational measurements, and method comparisons.
- [Development systems](07_development_systems/README.md): 11 files. Starting configurations and evolved structures from the development simulations.
- [Earlier work and model context](90_historical_and_other_context/README.md): 89 files. Earlier simulations, model evaluations, and exploratory views that provide background for this project.
- [Representation checks](99_withdrawn_and_encoding_diagnostics/README.md): 4 files. Examples showing how a connectivity representation affects structural searches and apparent group counts.

## Scientific boundaries

F09's historical displayed-axis transformation remains unresolved. F10's modes and population are reconstructed within the stated stereochemical limits. F15 is withdrawn as a chemical-group census and appears only under diagnostics. F18 motifs describe topology; string diversity/occurrence, exact graphs and chemical species are different quantities. Independent quench endpoints do not establish a continuous trajectory, stability, yield, equilibrium, kinetics or mechanism. Older preliminary and retired figures are labeled so they cannot silently substitute for current working views.

## Refresh and verify

```bash
python3 figures/tools/sync_catalog.py --write
python3 figures/tools/sync_catalog.py --check
```

The refresh script copies existing outputs; it does not run production or regenerate scientific plots. It scans the declared scientific output/source folders, excludes AppleDouble metadata, software assets and writing-reference PDFs, and never deletes source assets. Explicit collection exclusions are tracked in `metadata/collection.json`; the separate isolator work is preserved in the graveyard rather than shown here. Use the owning analysis script/notebook to change a figure, then refresh. Do not edit catalog copies as source files. Frozen originals remain retained release members; current paths are recorded separately from their historical paths.
