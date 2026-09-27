# Digital Exchange Control Management Portal — Prototype

## Prototype Application

This application is a prototype for research, analytical and demonstration purposes. It is not an officially authorised institutional system and should not be interpreted as representing the policies, decisions or systems of any government institution.

## Module 2 — Exchange Control Rules Engine

The application includes a visibly separate **Module 2: Exchange Control Rules Engine** rather than placing the rules engine inside the same Application Portal layout.

### Module 2 structure

1. **Overview** — engine purpose, KPIs, rule domains and decision workflow.
2. **Live Rule Test** — interactive transaction testing against the configured ruleset.
3. **Rule Library** — searchable/filterable rule catalogue.
4. **Regulatory Map** — rules linked to publicly available regulatory source documents/pages.
5. **Decision & Audit** — audit trail for rule/application activity.

### Core workflow

**INGEST → CLASSIFY → TEST → ROUTE**

The engine returns explainable signals including PASS, INFO, REVIEW, BLOCK, ESCALATE and N/A. It is decision-support and does not replace legal interpretation, professional compliance judgement or formal regulatory determinations.

### Current configured reference sources

- Exchange Control Act, Chapter 22:05
- Exchange Control Regulations, 1996 (S.I. 109 of 1996)
- Exchange Control (General) Order, 1996 (S.I. 110 of 1996)
- Exchange Control (Authorised Dealers with Limited Authority) Order, 2015 (S.I. 104 of 2015)
- Foreign Exchange Guidelines FXD5 Version 2.0, March 2026
- Foreign Exchange Directive FXD5/2026
- Foreign Investment & Trade Framework — Imports / Export Facilitation

### Important implementation note

The configured rules are a prototype ruleset. Before any operational deployment, each rule should be independently reviewed against current legislation and regulatory guidance, with formal effective dates, version control, change approval, source-document retention and appropriate governance.

## Authentication

The public prototype intentionally does **not** use a real authentication system. Users select a demonstration role to explore the workflow. Do not submit confidential, personal, financial or operational information to the public prototype.
