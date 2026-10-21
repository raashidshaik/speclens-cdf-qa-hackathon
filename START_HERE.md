# SpecLens submission handoff

Prepared for Raashid Shaik for the CDF Agentic QA Hackathon.

## Included
- SpecLens_Source.zip: official starter kit plus agent source, installation instructions, architecture and CI planner checks. No dependencies, .git directory, credentials, or service logs.
- SpecLens_QA_Audit.pdf: exported findings, coverage, evidence references, costs and limitations.
- SpecLens_Evidence.zip: actual screenshot/text evidence, machine-readable results, and browser-viewable audit.
- SpecLens_Walkthrough.mp4: 3+ minute continuous actual browser run. Silent, with a text introduction and report review. No synthetic result montage.
- Cost_Breakdown.json: no paid model calls; local compute and development costs excluded.

## What still needs your account
1. Fork https://github.com/Community-Dreams-Foundation/Agentic-QA-Hackathon-kit in your GitHub account.
2. Put the supplied agent directory and .github workflow into your fork, then commit and push. Make the repository public.
3. Upload the video, audit PDF and evidence ZIP to your Drive or another supported hosting service. Grant viewer access for anyone with the intended links. Confirm access while signed out.
4. Enter the repository, video and report links at https://forms.gle/qviV38D1uMDir3Pq8.
5. Submit by Wednesday October 21, 2026, 5 PM Central (6 PM Eastern).

## Review before representing this as your entry
This package was prepared with ChatGPT/Codex assistance. Read the code and report, reproduce the run, and confirm organizer rules on assistance. The planner is local NLP retrieval plus authored DemoBank adapters; it is not a general-purpose LLM agent. The run used an unchanged official target with a PGlite compatibility database and serialized pool. It has not been tested against the hosted organizer URL. The report distinguishes full requirement coverage from narrower scenario checks.

## Suggested video description
SpecLens ingests the DemoBank PRD, maps requirements to QA capabilities using local NLP retrieval, executes browser checks, and exports audit evidence. The recording shows an actual local run, including successful paths and observed defects. See the audit for environment details, limitations, and requirement coverage.
