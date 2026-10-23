# $0 showcase and hosting review

Reviewed 2026-10-21 against provider documentation and the current repository.
This is a recommendation and compatibility review, not a deployment test or an
exhaustive search for every free host. Recheck provider terms before publishing.

## Recommended presentation

Use the [project card](project-card.md), [case study](case-study.md), screenshots
and captioned [recorded walkthrough](demo.md) for the public showcase. Link the
source and [local setup](../README.md#start-on-windows) so visitors can reproduce
fresh simulations. The repository already provides these assets without a new
service. The prepared card correctly labels availability as **Local app + recorded
demo** and has no live-demo action.

For a separately authorized static publication, GitHub Pages is the preferred
standalone fallback: it supports public repositories on GitHub Free and supplies a
`github.io` domain. This is our recommendation based on the existing public repo
and static assets, not a provider guarantee about this project. See
[GitHub Pages overview](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).
Existing portfolio integration can use the same assets after its current host and
routing are checked; no assumptions are made about that site's costs or settings.

## Options reviewed

| Option | Published free-plan terms | Fit for AeroTest |
| --- | --- | --- |
| GitHub Pages | Static HTML/CSS/JS; public repositories supported on GitHub Free. Published site <=1 GB; soft bandwidth limit 100 GB/month; deployment timeout 10 minutes. | Suitable for a static project presentation and recorded assets. It does not provide the current API process, C++ subprocess or writable SQLite volume. |
| Cloudflare Pages Free | 500 builds/month, 20000 files and maximum 25 MiB per asset. Static requests/bandwidth advertised as unlimited; Functions count against separate Workers quotas. | Static alternative; the selected assets fit the published file limits. This review does not select a Workers/Functions/backend migration. |
| Render Free web service | Shuts down after 15 idle minutes. Runtime files, including SQLite, disappear on restart/redeploy/shutdown; persistent disks require a paid instance. Usage overages can bill when a payment method exists, or suspend/disable service/builds without one. | Not selected for the current persistent saved-run app under the firm $0 constraint. A stateless/disposable backend or different datastore would change the current behavior and require separate work. |

Primary sources: [GitHub Pages overview](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages),
[GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits),
[Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/),
[Cloudflare Pages product](https://www.cloudflare.com/products/pages/) and
[Render Free limits](https://render.com/docs/free). Fit judgments are inferences
from these terms and the implementation below. Free tiers are bounded services;
this review is not a promise of perpetual pricing or availability.

## Why the full app needs a different serving environment

The [Dockerfile](../Dockerfile) compiles a Linux C++ executable and installs a
Python API. [Compose](../compose.yaml) runs that API plus nginx and mounts a
persistent volume at `/app/runtime` for saved executions. React sends API requests;
publishing its built files alone does not make Run simulation work. Compilation
during a static site's build is different from running a simulator process for a
visitor's request.

The API stores completed executions in SQLite and exposes no authentication or
per-user data separation. Its per-instance run/output limits are local resource
bounds, not a public multi-user service design. Internet backend exposure, storage
changes and any additional access controls remain outside this presentation review.
No claim is made that every possible persistent free backend is unavailable; the
reviewed options do not establish one for the current app without changes.

## Asset-size and provenance check

The six candidate presentation files total **994787 bytes** (about 0.95 MiB).
The largest file is the **760654-byte MP4**, below Cloudflare's 25 MiB per-file
limit. This selected set is also below GitHub Pages' 1 GB site limit. These are
actual local byte counts, not transfer-size or traffic estimates.

| Candidate asset | Bytes |
| --- | ---: |
| Generated card HTML | 4738 |
| Original investigation screenshot | 60328 |
| Captioned walkthrough MP4 | 760654 |
| Video poster | 166122 |
| WebVTT captions | 1347 |
| Plain-text transcript | 1598 |

[Review metadata](assets/hosting-review.json) records exact paths, SHA256 hashes,
review time, source revision and primary-source URLs. Card freshness and source
screenshot provenance passed. The MP4 and original walkthrough manifest still
match the preserved render report. No new encode or playback test is claimed.
The original capture/video dates and browser/device limitations remain in their
own documentation.

## Publication handoff

The reviewed files are inputs to a future static presentation, not a complete
new hosted website. The card currently links to GitHub's case study, recorded-demo
guide and source; these public destinations work independently of a backend.
A future site may adapt those destinations to its own pages. Keep recorded-mode
labels, captions/transcript, original evidence links and scoped-verdict limits.

A publication should copy only selected presentation assets into its output and
verify base paths, image/video MIME types, caption linkage, keyboard navigation and
phone layout on the actual destination. The React app's API-dependent frontend
should not be presented as a working static simulator. Do not require a purchased
domain, paid plan, external model/API, tunnel to a personal computer or paid runner
for this presentation. A richer recorded-data explorer would be a new feature;
it has not been implemented or implied by the card.

No hosting account, payment method, service, DNS setting, deployment workflow or
portfolio-site file was created or changed. Repository commits are the only public
publication authorized here. [Final presentation verification](final-verification.md)
records the completed repository checks; site integration/public hosting requires
separate authorization.
