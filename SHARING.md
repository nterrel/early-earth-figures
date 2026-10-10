# Share the figure library or proposed supplement

The [public figure library](https://nterrel.github.io/early-earth-figures/) is live, with a link to the [proposed supplement](https://nterrel.github.io/early-earth-figures/supplement/). Share those addresses with collaborators. The local `localhost` preview works on Nick's computer; ZIPs provide a fixed downloadable snapshot.

## Share a review snapshot now

From the project root, create a new package and ZIP:

```bash
python3 figures/tools/export_share.py --output /tmp/early-earth-figure-library --zip
```

Give collaborators the ZIP through your chosen file-sharing channel. They extract
the complete folder and open `index.html`; `START_HERE.html` supplies a short
reading/commenting guide. Titles, descriptions, status labels and full-resolution
assets are preserved. Copied HTML links are repaired and their local dependencies
are included. Some notebook HTML views retain external MathJax/RequireJS libraries
and may need internet access. The export reports those links and checks every
local HTML link. Source files and the maintained gallery are not modified.

The package is a snapshot. Refresh the catalog after changing figures, then make
a new export with a new directory name. `export_manifest.json` binds the catalog,
source hashes, share-copy hashes and repaired links. Comments should identify the
figure ID, title and exact download filename; final selection remains in the
publication plan.

## Preview the proposed supplemental material

The maintained [supplement selection](metadata/supplement_selection.json) lists
the proposed assets with publication-friendly titles and descriptions. It is a
review draft; final manuscript/SI selection and scientific approval remain open. Build a
smaller standalone gallery from that list:

```bash
python3 figures/tools/export_share.py --selection figures/metadata/supplement_selection.json --output /tmp/early-earth-supplement --zip
```

The selected gallery places the figures and their descriptions first. Technical
status, internal figure IDs and origin details remain collapsed, with the full
source/export manifest available separately. Only explicitly selected format
variants are included. Edit the selection and caption metadata, refresh the
library, then export to a new directory to review the next version.

## GitHub backup and collaborator access

Nick selected **[github.com/nterrel](https://github.com/nterrel)** for the figure
and documentation repositories. [early-earth-figures](https://github.com/nterrel/early-earth-figures) is public; [early-earth-publication](https://github.com/nterrel/early-earth-publication) is private. Both local histories and their backup tags are uploaded and verified. The [publication plan](../early_earth_analysis_v2/docs/PUBLICATION_PLAN.md) records the backup boundaries. A private repository can give selected
collaborators access to the files and ZIP without publicly publishing the library.
GitHub does not render the interactive HTML gallery directly in repository file
views; recipients can download and open the portable package.
Personal-repository collaborators also receive write access; a privately shared
ZIP is suitable for viewers who only need to review the figures. See
[GitHub's personal-repository permissions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/permission-levels-for-a-personal-account-repository).

Git backup tracks the individual figure files. The complete collaborator ZIP is
about 126 MiB, so distribute that archive through your file-sharing channel or
attach it as a GitHub release asset after repository creation; it exceeds
GitHub's 100 MiB ordinary Git file limit. The smaller supplemental ZIP is about
7.4 MiB. GitHub release assets may be up to 2 GiB each. See
[large-file guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
and [release-asset limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

## A shared browser link with GitHub Pages

The approved website uses the D20-curated library homepage (157 assets/126 groups) and a linked proposed supplement. The 89 approved public groups were removed with original sources preserved; the 19 optional historical Early Earth groups remain. See the [A31 results](../early_earth_analysis_v2/docs/WEBSITE_CURATION_RESULTS_20261010.md). The final manuscript/SI selection remains under review. The site deploys the verified `site/` snapshot through GitHub Actions after each push to `main`. Maintained figure sources, captions and tools remain on `main`; the earlier `gh-pages` history is retained.

Prepare a new verified website from the current local workspace:

```bash
python3 figures/tools/sync_catalog.py --write
python3 figures/tools/sync_catalog.py --check
python3 figures/tools/prepare_pages.py --output figures/build/pages-YYYYMMDD
python3 figures/tools/prepare_pages.py --check figures/build/pages-YYYYMMDD
```

Choose a fresh output name for each version. Inspect `index.html` and `supplement/index.html`, archive the previous managed `site/` snapshot, then stage the reviewed bundle under `site/` and commit/push `main`. Preserve the approved curated membership when preparing a targeted replacement. The bundle includes physical copies, relative links, `.nojekyll`, source/export manifests and reading guides. Its generator reads the owning local sources and their display dependencies; a figure-repository clone alone does not include the sibling retained inputs needed to regenerate every report.

The site is configured in **Settings → Pages → GitHub Actions**. No framework build is required. The published source/manifest hashes and GitHub build commit are bound in the central [backup/Pages receipt](../early_earth_analysis_v2/docs/records/GITHUB_BACKUP_PAGES_20261004.json).

**GitHub Pages on a personal account is publicly accessible, including when its
source repository is private.** Private hosted Pages access requires an
organization using GitHub Enterprise Cloud. Private Git backup and public website
visibility are separate choices. GitHub Free supports Pages from public
repositories; paid plans can support a private source repository. These conditions
come from [GitHub's publishing-source documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
and [Pages access-control documentation](https://docs.github.com/en/enterprise-cloud%40latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site).

GitHub Pages permits a published site up to 1 GB, with a 100 GB/month soft bandwidth
limit. The current catalog is comfortably below the site-size limit. See
[Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
and [project-site URL conventions](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).
ZIP or Pages-bundle generation is local; publishing happens when the reviewed `site/` snapshot is committed and pushed to `main`.

## Notebook editing and automatic main-branch deployment (A30)

The [editing guide](EDITING.md) and [energy workshop](../early_earth_analysis_v2/analysis/advisor_figures/notebook/library/energy_evolution.ipynb)
provide a direct preview → optional save → optional sync/stage path. Their default
cells do not save or publish. A31 published the approved 89-group cleanup on the retained `gh-pages` branch.
A32 replaces only F09 in that curated snapshot and activates automatic deployment
from `main` on 2026-10-10.

For the new workflow, the last notebook cell stages a verified complete website
under `figures/site/`. Equivalent command after catalog sync/check:

```bash
python3 figures/tools/stage_notebook_site.py
python3 figures/tools/prepare_pages.py --check figures/site
```

An existing managed snapshot is validated and archived under ignored `build/`
before replacement. Unmanifested or hand-edited snapshot changes are refused.
Staging exports the entire current catalog and proposed supplement, including
currently local candidates. A31 subsequently replaced `site/` with the exact
curated public 610-file snapshot (157 assets/126 groups), excluding local/A32
candidates. If the default helper is run again, inspect `site/index.html` and
`site/supplement/index.html` and approve that broader membership before committing. It does not run a Git command, change sharing or upload anything.

**Activation:** GitHub Pages uses **GitHub Actions**, and the `github-pages`
environment allows `main`. `.github/workflows/publish-library.yml` validates the
committed snapshot before publishing it on every push to `main`; it also accepts
manual workflow runs. Earlier `gh-pages` history remains available. See the
[GitHub workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
Thereafter, save and stage after each edit, inspect the diff, and commit/push
`main`. Every push to `main` runs snapshot validation and deployment;
caption/source-only commits need restaging before they reach the website. Check
the Actions result instead of assuming a fixed build time. The public URL and
linked supplement layout stay the same. Deploying a full snapshot will include
all staged library candidates, not only the new energy views.

CI runs `python tools/prepare_pages.py --check site --portable` in a clean figure
repository checkout. That mode checks exact membership, every file's size/hash,
exported asset bindings and every local HTML link. It reports that original
source hashes were **not rechecked** in CI; those were verified locally during
staging. CI does not need the private analysis repository, logs, scientific Python
packages or symlinks into another checkout. `site/` is deliberately tracked;
`build/` remains ignored. Notebook/cache/input receipts stay in the private
analysis repository and selected manuscript files remain separately controlled.
