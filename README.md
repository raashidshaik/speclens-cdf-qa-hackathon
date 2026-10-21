# SpecLens — CDF Agentic QA Hackathon

Submission by Raashid Shaik. Built with ChatGPT/Codex assistance.

- [Agent architecture, setup and limitations](agent/README.md)
- [3:07 browser walkthrough](SpecLens_Walkthrough.mp4) (download to play if GitHub does not preview it)
- [QA audit report](SpecLens_QA_Audit.pdf)
- [API/token cost breakdown](Cost_Breakdown.json)
- [Reproducible evidence](SpecLens_Evidence.zip)
- [Source archive](SpecLens_Source.zip)

22 executed scenarios: 18 passed, 4 failed. Full PRD coverage: 9 passed, 3 failed, 20 unverified. The report distinguishes scenario outcomes from requirement-level verdicts.

The planner uses local TF-IDF/cosine matching with authored capability adapters, not an LLM. Validation used a local PGlite PostgreSQL runtime, not the organizers’ hosted deployment. Model API usage was $0; other costs are excluded as described in the cost file.

Target application and PRD originate from [CDF’s official hackathon kit](https://github.com/Community-Dreams-Foundation/Agentic-QA-Hackathon-kit), commit c7b856cc0d7cfb367e96fda0e5c291eba10cbb10. The original target business logic is retained; the agent directory contains the submission implementation.
