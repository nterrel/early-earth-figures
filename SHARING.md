# Share the figure library or proposed supplement

The [public figure library](https://nterrel.github.io/early-earth-figures/) is live, with a link to the [proposed supplement](https://nterrel.github.io/early-earth-figures/supplement/). Share those addresses with collaborators. The local `localhost` preview works on Nick's computer; ZIPs provide a fixed downloadable snapshot.

## Current caption, media and cleanup review — 25 October 2026

[Figure cleanup audit](https://nterrel.github.io/early-earth-figures/cleanup-audit.html)
records Nick’s returned choices: nine approved groups move twelve alternate cards
out of the main view, leaving 99 main cards. All twelve remain under **View →
Hidden / restore**, with original assets and feedback intact. Mean-fragment traces
45/46 stay visible pending a revised grouping. Further audit edits are browser-local
drafts and require export before application. The grouped 26-figure discussion set
remains a proposal, separate from manuscript acceptance.

All five gallery animations now use MP4 pause/seek players. Choose **Enlarge
animation** for the same clean popup as static figures; Escape closes it and
returns the paused position to the card. Caption-only image margins are displayed
as HTML underneath, preserving original artwork/downloads and feedback identities.
Axes, legends and meaningful frame annotations stay with the visual.

Ratings now label the 1–5 usefulness scale. Choose a score, **Copy rating text**,
paste into Comments, sign in and post with GitHub. Preparing/copying is not saving;
the shared score updates after the website rebuild, then **Refresh saved review**
loads it. **Clear prepared score** clears only the unsent/prepared UI state, not a
posted vote. The [owning packet](../early_earth_analysis_v2/analysis/gallery_cleanup_20261025/README.md)
records verification, source preservation and remaining acceptance limits.

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

## Shared public review through GitHub Discussions

Nick selected the public model on 2026-10-21. The shared review interface uses
the existing **Comments** beneath each figure, with GitHub sign-in. It has a
discussion set and a smaller priority set. The eventual goal is to agree on about
20–30 high-value figures; this is not a page limit or an enforced selection cap.
All matching library cards appear together. **Later** and **Hidden / restore**
set cards aside without deleting any artwork. Alanine/glycine formation cards
provide MP4 pause, seek and full-screen controls, plus original GIF/PNG downloads.

Start with **Adrian’s review**, the current seven-question document. It brings
the historical Energy/Size/CHN choices, labeled alternatives, formation movies,
initial-species-excluded discovery counts, and quench/abundance companions together. The
hot/quenched frame-447 and representative graph galleries have their own section.
Five previous notebook exports are under **Previous notebook reading exports**
at the bottom, with their original links, references and Comments preserved.
All previous artwork and feedback identities remain. Three newly linked review
candidates have their own versioned cards (Figures 99–101); they are separately
manifested display dependencies. The canonical 152-asset catalog and 29-asset
supplement remain unchanged.

Choose a card’s meeting selection or rating. The Comments dialog prepares short
text for you: choose **Copy text**, paste it into the comment box and post with
GitHub. **Post note in Comments** prepares your written note in the same way.
Preparing/copying text does not save a comment. Notes appear in the discussion
immediately after posting. The shared selection, rating summary and note preview
update after the automatic Pages rebuild; choose **Refresh saved review** to load
the latest snapshot. Its synchronization time is displayed. A retained note draft
can be cleared with **Clear draft** once posted.

Nick (`nterrel`) and Adrian (`roitberg`) curate the shared selection and order.
Signed-in GitHub reviewers can add ordinary notes and 1–5 ratings; each reviewer’s
latest valid rating replaces their earlier one for that artwork version. New
artwork starts a separate population. PNG/PDF and matching supplement cards share
the existing exact artwork identity. Selection requests from other accounts
remain in GitHub but are not applied; the gallery links the reason.
Editing/deleting a command recomputes the saved view from remaining comments.
Closed threads keep the existing history/hidden-composer behavior; the owner can
reopen their discussion on GitHub when further feedback is needed.

**Export JSON** and **Export notes** download the latest shared review. Selections
are provisional and do not approve manuscript panels. Existing local reviewer
accounts, passwords and ratings are not uploaded or converted into public posts.

The [workflow](.github/workflows/publish-library.yml) reads Discussions after
discussion/comment changes and before publication, verifies the complete artifact
and deploys it. It has read access to Discussions, holds its token only in the
runner, and neither posts feedback nor writes commits. A failed read/check retains
the previous deployment. GitHub documents the supported
[discussion/comment events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#discussion_comment).

To prepare another selected public overlay, first prepare the desired local
meeting snapshot, then run `figures/tools/prepare_public_review.py --source
LOCAL_SNAPSHOT --output FRESH_PUBLIC_DIRECTORY --feedback-source SOURCE_JSON`.
Fetch current feedback with `discussion_review.fetch_source` or use the owning
source snapshot; the publishing workflow always fetches current comments again.
The public preparation command applies the consolidated navigation automatically.
For an existing prepared bundle, run `python3 figures/tools/reading_navigation.py
--site PREPARED_DIRECTORY`, then verify it with `prepare_pages.py --check
PREPARED_DIRECTORY --portable` before publishing.
Use this overlay step after catalog/Pages regeneration to retain the shared
review controls. Verify it with `prepare_pages.py --check DIRECTORY --portable`.
The [owning record](../early_earth_analysis_v2/docs/WEBSITE_PREVIEW_A37_20261012.md#2026-10-21--public-discussions-selected-for-shared-review)
holds release/validation evidence.

## A37 local ratings and enlarged previews

### Saved figure meeting workspace (2026-10-21)

The newest local preview adds a saved discussion set, priorities, ordered cards,
reviewer notes and reversible hiding. Start it from the project root:

```bash
python3 figures/tools/serve_gallery_preview.py --directory figures/build/meeting-review-20261021 --port 8772
```

Open `http://127.0.0.1:8772/` and use the existing local reviewer account, or
choose **Set up local reviewer** on first use. The existing feedback database and
ratings are retained. Choose **Browse library**, then set cards to **Priority**,
**Discuss**, **Later** or **Hidden**. **Discussion set** shows the ordered meeting
selection; **Priorities only** isolates the most important figures. The shared
local set has no enforced size cap. About 20–30 high-value figures and a smaller
priority set are eventual selection goals. Newly generated previews show all
matching cards together, without pagination.
**Hidden / restore** restores set-aside cards without deleting their files or notes.

Expand **Meeting notes**, type, and choose **Save note**. Notes are append-only,
attributed to the signed-in reviewer and tied to the artwork version. Refresh
loads changes from another local page; conflicting writes preserve note drafts.
**Export JSON** and **Export notes** download selections and notes with source and
artwork identifiers. These are exports, not an import/synchronization service.
They contain no passwords or sessions. Meeting selection is provisional and
does not approve manuscript panels.

Alanine and glycine formation cards in this preview use MP4 players with pause,
seeking and full-screen controls. Original GIF/PNG downloads remain available.
The [movie receipt](../early_earth_analysis_v2/analysis/alanine_illustrations/results/review_movies_20261021/movies.json)
binds the unchanged source GIFs, all frame-transition comparisons and exact timing.

Selections, notes and stars persist on this computer for configured local
reviewers. They are not yet shared remotely with Adrian. Existing public giscus
Comments remain available; D25 still owns shared hosting/access. The public
site and original A37 snapshot are unchanged. See the
[owning implementation record](../early_earth_analysis_v2/docs/WEBSITE_PREVIEW_A37_20261012.md#2026-10-21--saved-figure-meeting-and-movie-preview).

To rebuild in a fresh directory, run `gallery_preview.py --output NEW_DIRECTORY`,
then `stage_review_movies.py --directory NEW_DIRECTORY --movies
early_earth_analysis_v2/analysis/alanine_illustrations/results/review_movies_20261021/movies.json`
(both scripts are under `figures/tools/`). Do not run the public Pages producer
to prepare this local review overlay.

The original local A37 preview is a retained review snapshot. New previews use
the current staged gallery and unchanged proposed supplement figure membership.
It preserves source figures, the existing Comments controls and download links.
Click a figure image to enlarge it; Escape closes the popup and returns focus.
The 228k system image supplies the background behind opaque cards.
The local preview also displays one primary Figure reference per card, with shareable anchors. Lettered
sets contain two or three related figures; Galleries are broad topic sections.
Search exact references such as Figure 6a; prior Gallery references remain search
aliases. Figure details links only to files in this repository's site/ tree.
Website references remain separate from manuscript/SI numbering.
Public builds use an explicit 80%-opacity background layer and versioned CSS/JS
URLs. Public star ratings remain deferred; public Comments retain giscus.

From the project root:

```bash
python3 figures/tools/gallery_preview.py --output figures/build/a37-preview
python3 figures/tools/serve_gallery_preview.py
```

The prepared preview already exists in this workspace; run only the server to
use it. Open `http://127.0.0.1:8765/` and choose **Set up local reviewer** on first
use. Choose a name and password. The preview owner can add further accounts:

```bash
python3 figures/tools/serve_gallery_preview.py --add-reviewer Adrian
python3 figures/tools/serve_gallery_preview.py --add-reviewer Richard
```

These commands prompt for passwords and exit; restart the server if needed.
One reviewer can save one 1–5 star rating per figure artwork version. Choosing
another star replaces that reviewer's prior rating. The displayed average and
reviewer count include all saved local votes; **Your rating** is account-specific.
PNG/PDF and matching supplement cards share the comment source/version identity.
Changed artwork starts a separate rating population and preserves old votes.

Ratings and accounts persist in ignored `build/a37-feedback.sqlite`, outside the
served snapshot; restarting the server or refreshing the page retains them.
The server accepts only loopback connections. This is local review storage, not
shared advisor feedback. Hosted ratings/access integration awaits A36/D25; static
GitHub Pages alone cannot save these ratings. Existing Comments still use the
public GitHub/giscus model. The public presentation includes the popup, background, labels and approved cuts; reviewer ratings remain local until D25 selects shared access/storage.
Opening its HTML directly provides the gallery and popup but disables saving.

For interface-only revisions use `gallery_preview.py --refresh-interface
figures/build/a37-preview`; for a new baseline choose a fresh output directory
and pass it to the server with `--directory`. Keep the feedback database path
stable to retain votes. See the [A37 implementation record](../early_earth_analysis_v2/docs/WEBSITE_PREVIEW_A37_20261012.md).

## Comments directly in the hosted gallery

Discussion titles use the Figure reference and title, with a short version suffix
when artwork changes. Full source/artwork identifiers stay in the hidden matching
metadata. Existing threads are looked up first; ordinary captions/renumbering do
not reset feedback. `metadata/gallery_discussion_titles.json` retains each assigned
term. Run `python3 figures/tools/gallery_feedback.py rename-titles --use-git-credential`
to update old titles while preserving bodies, replies and closure state.


Choose **Comments** beneath a figure, sign in with GitHub, and leave feedback or
reply in the gallery. Comments are public and stored in this repository's GitHub
Discussions through giscus; saving does not require a commit or website rebuild.
Matching PNG/PDF and supplement cards share a discussion. Threads are tied to
the published preview's SHA-256 and source-group identity, so changed artwork
gets its own thread. Unsent drafts survive switching figures within the same page.

`metadata/gallery_comments.json` contains public repository/category identifiers;
`giscus.json` limits embedding origins. No repository token is shipped. Future
`tools/prepare_pages.py` builds include the controls automatically; portable ZIP
exports keep their offline behavior. The comments-only overlay can preserve an
already published snapshot without refreshing unpublished plots:

```bash
python3 figures/tools/gallery_comments.py --stage figures/build/comments-preview
```

Use this overlay only on a snapshot without comments. Inspect/validate the
result before staging it under `site/`. GitHub moderates the discussions;
review feedback does not itself select or approve manuscript figures.

For a prompted correction pass, Codex reads the complete version-bound thread,
revises the figure, checks and publishes the correction, then closes resolved
requests through GitHub CLI. Closed discussions remain on GitHub; their comments
are hidden in the gallery after the refreshed status snapshot deploys. Current
artwork receives its own discussion when its SHA-256 changes.

Use `python3 figures/tools/gallery_feedback.py list --use-git-credential` and
`read --number N --use-git-credential` to retrieve feedback. After a verified
correction, use `close --number N --verified-change RECEIPT_OR_COMMIT --site figures/site --use-git-credential`,
then commit/push the updated status and manifests. `sync` refreshes status without
closing anything; `reopen --number N` reverses closure. Credentials stay in memory.

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

The public library uses the explicit [public selection](metadata/public_library_selection.json):
149 assets in 113 groups after the approved A37 cuts and retirement of two superseded preliminary cards; all retained artwork and scientific captions remain unchanged. Clickable HTML
panels form a horizontal reading strip, followed by animations and related still
figures. The proposed supplement retains its 29 assets; final manuscript/SI
selection remains A19. The site deploys the verified `site/` snapshot through
GitHub Actions after every push to `main`. Original sources remain preserved. See
[the curation record](../early_earth_analysis_v2/docs/WEBSITE_REORGANIZATION_20261010.md) and [the five energy additions](../early_earth_analysis_v2/docs/ENERGY_FIGURES_WEBSITE_20261012.md).

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
Staging reads `metadata/public_library_selection.json` for exact public membership
and `metadata/supplement_selection.json` for the proposed supplement. New local
candidates do not enter either list automatically. Inspect both galleries before
committing. This prevents a targeted edit from restoring excluded figures or
publishing unrelated local trials. Preparation does not run Git commands or upload.

**Activation:** GitHub Pages uses **GitHub Actions**, and the `github-pages`
environment allows `main`. `.github/workflows/publish-library.yml` validates the
committed snapshot before publishing it on every push to `main`; it also accepts
manual workflow runs. Earlier `gh-pages` history remains available. See the
[GitHub workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
Thereafter, save and stage after each edit, inspect the diff, and commit/push
`main`. Every push to `main` runs snapshot validation and deployment;
caption/source-only commits need restaging before they reach the website. Check
the Actions result instead of assuming a fixed build time. The public URL and
linked supplement layout stay the same. Deployment publishes the exact staged, selected snapshot. Update the public
selection deliberately when adding an approved figure.

CI runs `python tools/prepare_pages.py --check site --portable` in a clean figure
repository checkout. That mode checks exact membership, every file's size/hash,
exported asset bindings and every local HTML link. It reports that original
source hashes were **not rechecked** in CI; those were verified locally during
staging. CI does not need the private analysis repository, logs, scientific Python
packages or symlinks into another checkout. `site/` is deliberately tracked;
`build/` remains ignored. Notebook/cache/input receipts stay in the private
analysis repository and selected manuscript files remain separately controlled.


## Refresh the current advisor brief

The selected sources and evidence hashes are in `metadata/advisor_review_selection.json`.
`tools/advisor_review.py` uses the current A38 template and accepted artwork; it
adds display dependencies without syncing unrelated local catalog changes:

```bash
python3 figures/tools/advisor_review.py --source figures/site --output figures/build/FRESH_REVIEW --handoff advisor-handoff
python3 figures/tools/prepare_pages.py --check figures/build/FRESH_REVIEW --portable
```

A fresh public preparation also applies the selected advisor brief automatically.
Keep the complete `advisor-review/` folder for its portable figures, movies and
source manifest. Feedback and library curation require the hosted site. Saved
notebook exports retain their original URLs and discussion identities.
