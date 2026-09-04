# Project Work 2 – Review 1 presentation content

The ready-to-present deck is generated at `deliverables/PolicyGPT_Project_Work_2_Review_1.pptx` by `python scripts/generate_deliverables.py`. The outline below documents the content and is retained for review/editing.

Copy these entries into the supplied PPT template.

1. **Title:** PolicyGPT: An AI-Driven Policy Intelligence and Assistance Platform for Government Schemes. Guide: Sanket S. Kulkarni, Assistant Professor, Department of Machine Learning. Presented by Sahana B.K. (1BM23AI162), Shamratha G. (1BM23AI173), and Suniksha Priya (1BM23AI192). Semester VII, Section C. Date: [presentation date].
2. **Agenda:** Introduction; proposed system; methodology; module development; implementation progress; model/retrieval implementation; testing and validation; preliminary results.
3. **Problem and motivation:** Official schemes are scattered across long documents. Citizens need plain-language eligibility and application guidance, while analysts need comparison, gap and overlap analysis. Unverified chatbot answers are unsafe, so every answer must show evidence and uncertainty.
4. **Proposed system:** A citizen assistant and analyst workspace share a versioned policy corpus. The API routes the query, retrieves evidence, generates a response, audits claims, and exports a report.
5. **Architecture:** Browser UI → FastAPI → PolicyGPT orchestrator → domain router → discovery → hybrid retrieval → generation → validation → report. SQLite stores sessions and reports.
6. **Methodology:** Lexical TF-IDF-style relevance is combined with deterministic semantic bigram hashing (`0.35 lexical + 0.65 semantic`). Missing profile fields remain unknown. A bounded repair pass broadens retrieval when confidence is low.
7. **Modules completed:** six-domain seed corpus, routing, retrieval, citations, profile-aware checks, claim audits, confidence/risk metrics, Markdown export, session history, and Docker setup.
8. **Testing and validation:** retrieval ranking tests, deterministic repeatability test, API health/query smoke test, citation presence checks, and workbook/report review checklist. Demo: ask the scholarship question, show sources and download the report.
9. **Preliminary results:** prototype returns a grounded answer with source links and a claim audit in one request. Report latency depends on corpus size and provider; the offline fallback has no external API dependency.
10. **Limitations and next steps:** seed records are illustrative; add verified official documents, multilingual support, embeddings, authentication, human review, richer analyst charts and user evaluation before deployment.
11. **Questions to prepare:** Why hybrid retrieval? (Exact policy terms and paraphrases require different signals.) Why validation? (A fluent answer can still be unsupported.) Why not replace portals? (The tool explains and traces information; the issuing agency controls the rule.)
12. **Team contribution:** Sahana – corpus and API contracts; Shamratha – retrieval and orchestration; Suniksha – UI, testing and documentation. Each member should run one live query and explain one design choice.
