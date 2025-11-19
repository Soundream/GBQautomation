# 📊 Project Highlights/Overview

This tool implements batch BigQuery queries, automatic data organization, and one-click CSV export. Now it also supports automatically loading CSVs into Tableau and batch updating all data sources, filters, and axes, enabling a fully automated data-to-visualization workflow.

---

## 🛠 Workflow

1. After configuring `queries.json`, simply run `runner.py` in the project root directory (some features are under development, but the main flow is usable).
2. Steps: BigQuery queries → CSV export → Auto-load into Tableau → Replace data source/filter/axis → Tableau visualization.

---

## 🧩 First Time Setup

1. Ensure you have Google BigQuery access permissions.
2. Run `auth.py` for Google account authentication (will open a browser for interaction).
3. Complete `auth_credential/apikey.txt` (see team doc or admin for API key). Keep the key locally and secure (do NOT upload to GitHub).
4. Install dependencies: `pip install -r requirements.txt`
5. Configure `queries.json` as needed, following the example structure.

---

## 📝 Design Logic & How to Modify Code

- Main data processing logic is in `runner.py`. To add/modify queries, edit `queries.json` for flexible expansion.
- All SQL templates are separated and stored in `data_collection/sql`.
- Result files are auto-named and archived under the `output` directory.
- Tableau automation logic is under `tableau_processor/`.
  - New feature: Automatically batch-imports specified CSVs into Tableau and updates all data source mappings, filters, and axis settings.
  - For custom Tableau reports or data mapping, extend scripts in `tableau_processor` as needed.

---

For help or more feature requests, contact the maintainer or submit an issue.
