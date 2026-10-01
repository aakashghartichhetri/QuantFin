# Data Assets

This directory contains deterministic datasets used for model validation and reproducible analytics.

## `validation/market_returns_validation.csv`

A compact return series used to exercise the historical VaR/CVaR workflow and verify that portfolio-risk calculations behave consistently across local, CI, and containerized runs.

The dataset is a validation fixture for software and model checks. It is not presented as live exchange data or as an investable-market history.

For institutional use, this layer would be replaced by governed market-data feeds with source metadata, timestamps, quality checks, lineage, and reconciliation controls.
