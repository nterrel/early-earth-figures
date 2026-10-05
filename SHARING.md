# Share the figure library or proposed supplement

The gallery is a static HTML library. Its current `localhost` link works on
Nick's computer. Collaborators need a portable copy or a hosted web address.

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
review draft; author selection and publication approval remain open. Build a
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
and documentation repositories. Repository creation/visibility choices are tracked
in the [author inbox](../NICK_TODO.md). A private repository can give selected
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

Once Nick approves public visibility and the figure repository exists, the
selected supplemental export can become its GitHub Pages publication content. The export uses
relative links, includes `.nojekyll`, and needs no framework build. A dedicated
publication branch or a custom Pages workflow can keep generated publication
files separate from the source catalog. The usual project address would be
`https://nterrel.github.io/<figure-repository-name>/`; it does not exist until
publication is configured and completes.

For a simple publication branch, place the export contents at that branch's root,
including `index.html` and `.nojekyll`. In the repository's **Settings → Pages**,
choose **Deploy from a branch**, then select that branch and **/(root)**. The
selected branch is a publication surface: subsequent pushes update the site.
The maintained catalog can stay on `main`. Creating the branch, pushing it and
enabling Pages remain separate author-approved publication steps.

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
No repository creation, upload or publication follows from generating the ZIP.
