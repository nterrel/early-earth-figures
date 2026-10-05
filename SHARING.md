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

The approved website uses the full-library homepage and a linked proposed supplement. The final manuscript/SI selection remains under review. GitHub Pages publishes `gh-pages` from **/(root)**; maintained figure sources, captions and tools remain on `main`. Publishing a new `gh-pages` commit updates the site. A push to `main` updates the source backup.

Prepare a new verified website from the current local workspace:

```bash
python3 figures/tools/sync_catalog.py --write
python3 figures/tools/sync_catalog.py --check
python3 figures/tools/prepare_pages.py --output figures/build/pages-YYYYMMDD
python3 figures/tools/prepare_pages.py --check figures/build/pages-YYYYMMDD
```

Choose a fresh output name for each version. Inspect `index.html` and `supplement/index.html`, then replace the publication-branch contents with that verified bundle, commit and push `gh-pages`. Keep the maintained source checkout on `main`; use a separate publication checkout or temporary Git index. The bundle includes physical copies, relative links, `.nojekyll`, source/export manifests and reading guides. Its generator reads the owning local sources and their display dependencies; a figure-repository clone alone does not include the sibling retained inputs needed to regenerate every report.

The site is configured in **Settings → Pages → Deploy from a branch → gh-pages → /(root)**. No framework build is required. The published source/manifest hashes and GitHub build commit are bound in the central [backup/Pages receipt](../early_earth_analysis_v2/docs/records/GITHUB_BACKUP_PAGES_20261004.json).

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
ZIP or Pages-bundle generation is local; publishing happens when the reviewed bundle is pushed to the configured `gh-pages` branch.
