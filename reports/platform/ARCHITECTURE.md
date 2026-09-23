# Research Platform Architecture

## Overview
The research platform architecture enforces complete data-readiness awareness, modularity, and reproducible research standards. It isolates unverified datasets while unlocking verified data for statistical research.

## Core Architectural Components
```text
src/platform/
├── capabilities.py            # Unified Data Contract & Capability Registry
├── providers/                 # Plug-and-Play Provider Interfaces & Adapters
│   ├── base.py
│   ├── daily_provider.py
│   ├── intraday_provider.py
│   ├── equity_panel_provider.py
│   └── options_quote_provider.py
├── gates/                     # Automatic Data-Readiness & Execution Gates
│   ├── readiness_gate.py
│   └── execution_gate.py
├── research_registry/         # Canonical Research Registry & Preregistration
│   └── registry.py
├── pipeline/                  # Disciplined Experiment Pipeline
│   └── experiment_pipeline.py
├── execution_models/          # Modular Execution & Cost Models
│   └── cost_models.py
├── onboarding/                # Data-Arrival & Ingestion Validation Pipeline
│   └── data_arrival_validator.py
├── status.py                  # System Status & Diagnostic Reporter
└── generate_platform_reports.py
```

## Data Flow & Gating Logic
```text
Incoming Hypothesis
         ↓
Preregistration Check
         ↓
ReadinessGate (Prerequisites Check)
         ↓
  [PASS] ──→ Feature Generation ──→ Train/Val/OOS ──→ Cost Model ──→ Robustness ──→ Report
         │
 [BLOCKED] ──→ Structured Rejection Report (Reason, Required, Available, Action)
```
