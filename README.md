# Figure library

Start with **[the visual gallery](index.html)**. Open it in a browser and filter by manuscript theme, figure ID, status or filename. Images open at full resolution; PDF and portable HTML variants are linked alongside them.

The folders follow proposed manuscript themes, not final figure order. Every asset keeps its original filename after a readable source prefix. Copies from multiple generations are deliberately retained so a matching picture does not erase different provenance.

## Choose a reading path

- For Adrian's short reading path, use [advisor-handoff](../advisor-handoff/README.md).
- For current editable figures, use [the maintained notebook guide](../early_earth_analysis_v2/analysis/advisor_figures/notebook/README.md).
- For approval/readiness, use [the publication plan](../early_earth_analysis_v2/docs/PUBLICATION_PLAN.md).
- For exact origin/hash/status mappings, use [catalog.csv](catalog.csv) or [catalog.json](catalog.json).

- [Energy evolution](01_energy_evolution/README.md): 11 files. Energetic evolution through heating, the high-temperature interval and cooling. F09 is source-bound, but the historical displayed-axis transformation remains unresolved; do not compare it numerically with reconstructed raw totals.
- [Alanine and conformations](02_alanine_and_conformations/README.md): 16 files. Alanine orientation, improper torsion and coordinate illustrations. F10 reproduces the 438,986-structure population and modes; it does not assign absolute stereochemistry, equilibrium or stability.
- [Scale, discovery and sampling](03_scale_discovery_and_sampling/README.md): 8 files. Structural coverage, first detection and the effect of sampled cadence. Preserve distinct populations, normalization and restart boundaries; sampled recurrence is not lifetime.
- [Quench and fragment size](04_quench_and_fragment_size/README.md): 76 files. Paired hot/quench sizes and connectivity examples, including heavy-atom alternatives. Production endpoints are independent 25-fs quenches; historical shared-412 comparisons use 250-fs endpoints. Author selection remains open.
- [Composition, recurrence and topology](05_composition_recurrence_and_topology/README.md): 36 files. Variety versus abundance, compositions, architecture, recurrence and topology motifs. Emitted strings, exact graphs and fragment occurrences have different denominators. F18 motifs are topology and clusters are browsing aids.
- [Methods and performance](06_methods_and_performance/README.md): 4 files. Workflow and bounded performance illustrations. Historical measurements or proposed benchmarks do not establish a validated speedup on the current whole-frame workload.
- [Development systems](07_development_systems/README.md): 11 files. 228/228k starting and evolved system views. Figure S1 provides illustrative development context, not molecular-identification evidence.
- [Historical and other context](90_historical_and_other_context/README.md): 89 files. Retained dissertation/ANI/model-context figures and retired HTML views. Their original scope is preserved; they are not automatically current Early Earth manuscript evidence.
- [Withdrawn and encoding diagnostics](99_withdrawn_and_encoding_diagnostics/README.md): 4 files. F15 conventional functional-group counts are withdrawn as a chemical census. SINGLE-edge encoding causes false negatives and misleading matches. These assets support representation diagnosis only.

## Scientific boundaries

F09's historical displayed-axis transformation remains unresolved. F10's modes and population are reconstructed within the stated stereochemical limits. F15 is withdrawn as a chemical-group census and appears only under diagnostics. F18 motifs describe topology; string diversity/occurrence, exact graphs and chemical species are different quantities. Independent quench endpoints do not establish a continuous trajectory, stability, yield, equilibrium, kinetics or mechanism. Older preliminary and retired figures are labeled so they cannot silently substitute for current working views.

## Refresh and verify

```bash
python3 figures/tools/sync_catalog.py --write
python3 figures/tools/sync_catalog.py --check
```

The refresh script copies existing outputs; it does not run production or regenerate scientific plots. It scans the declared scientific output/source folders, excludes AppleDouble metadata, software assets and writing-reference PDFs, and never deletes source assets or prior copies. Use the owning analysis script/notebook to change a figure, then refresh. Do not edit catalog copies as source files. Frozen originals remain retained release members; current paths are recorded separately from their historical paths.
