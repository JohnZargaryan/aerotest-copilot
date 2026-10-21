# Portfolio presentation plan (not published)

The existing portfolio site is unchanged. Prepare assets here before a separately
authorized integration. Target one project card and one concise case-study page:

1. A 1-sentence problem statement and a screenshot of a real investigation.
   Verified [desktop captures](screenshots.md) and provenance are available in this
   repository. The [project-card bundle](project-card.md) includes canonical copy,
   the verified source image, links and a responsive preview; site integration
   remains planned.
2. A short demo: choose sensor disagreement, run it, inspect requirement results,
   ask for an explanation, and open an evidence reference.
   The [65-second recorded walkthrough](demo.md), captions, transcript and poster
   are available; it uses edited real browser captures in scripted mode.
3. The [engineering case study](case-study.md) and
   [implemented architecture diagram](architecture.md) explain C++/Python
   responsibilities and evidence flow. Prepared here; site integration remains planned.
4. Actual test/evaluation results, with scripted and live results separated.
5. Links to source, setup, demo and limitations.

Keep mobile layout, keyboard access, readable contrast, explicit error states,
and a no-key scripted path as acceptance conditions for the application. The
[bounded mobile/keyboard review](usability-review.md) records implemented fixes
and coverage limits; it does not claim a full accessibility audit.

The [$0 showcase and hosting review](hosting-review.md), checked on 2026-10-21,
recommends the prepared static card/case study/recorded demo with local setup for
fresh runs. GitHub Pages is the preferred standalone static fallback if publishing
is separately authorized; Cloudflare Pages is a reviewed static alternative. The
current C++/Python API and persistent SQLite behavior need a suitable backend
environment. The review explains why Render Free was not selected for that role.
No purchase, deployment, website change or recruiter-impact claim is included.

Position the engineering core first: deterministic behavior, requirements,
tests, independent verification and investigation evidence. AI-assisted explanations
are useful only when the evidence is correct. This complements ClusterPulse's
data-platform focus without duplicating it.
