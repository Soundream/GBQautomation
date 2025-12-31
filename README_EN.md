# 📊 Project Highlights/Overview

This tool (semi-finished, not fully validated) implements batch BigQuery queries, automatic data organization, and one-click CSV export. It also automatically imports CSVs into Tableau and batch replaces all data sources, filters, and axes, enabling full automation from BigQuery queries to Tableau visualization for monthly competitor analysis.

---

## 🛠 Tool Introduction

1. The program's original design goal: Automate the workflow: BigQuery queries → CSV export → Auto-load CSV into Tableau → Replace data source → Update filters and axes for the most recent three months → Repackage as new TWBX file.
2. Since the entire program **has not been tested end-to-end**, it's recommended to first learn the manual Tableau operations for monthly reports in the handover document `Business Analyst Guide`.
3. Since the entire program has not been tested end-to-end, it's currently recommended to keep the "Auto-load CSV into Tableau → Replace data source" steps as manual operations to ensure correct data import.
    - Since the entire program is written as functional modules, any step can be replaced with manual operation, and then resume from the next step.
    - Make sure to open the `GBQautomation` **folder** (not individual PY files) with a code editor to understand the project development logic and ensure correct module paths.
    - **Recommended specific workflow**:
        1. Run `data_collection/bq_runner.py` to query and download the latest data
        2. Open Tableau, **manually** import files from the download folder `output/csv` into Tableau one by one
        3. **Manually** use the "Replace Data Source" feature to update data references in Tableau tables (requires long Tableau loading time)
        4. Run `tableau_processor/filter_axis_updater.py` to update filter conditions and axis ranges
        5. Finally, **manually** adjust **company logo positions** in the main charts of each category, and modify the report month on the cover
        6. Run `tableau_processor/twbx_packager.py` to repackage the project file as a TWBX file
        7. Open the TWBX file in `output/twbx` with Tableau for verification, export to PDF, and quickly flip through pages to check for errors
4. The `key brands` report has been on hold for a long time, so the project has not truly validated support for `key brands` and may have unexpected errors.
5. Reminder: you still need to **manually adjust** the **company logo positions** in the main charts of each category at the end.

Even though the end-to-end workflow hasn't been validated, the most tedious steps of querying BigQuery data and modifying chart filters and axes on each page have been safely automated.

---

## 🧩 First Time Setup

1. Ensure you have Google BigQuery access permissions (need to apply via Jira).
    - You can try running some SQL statements in the web BigQuery interface to test if you can access the database normally
2. Use Github Desktop or a code editor (recommended: Cursor or VScode) to clone the project locally.
    - Recommended to fork this project to your own repository for easy modification
    - You can also directly clone this project, but you'll only be able to modify local code and won't be able to push changes to my Github project
3. Open the `GBQautomation` folder with a code editor.
4. Create `apikey.txt` (the actual apikey) next to `auth_credential/apikey.txt.sample` (which is just a placeholder file to remind you to create the apikey) and fill in the API key (see team documentation, TXT key **will not and cannot be uploaded to GitHub**).
5. Place the Tableau template (last month's finished product) into `tableau_processor/tableau_files/templates`
6. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
7. Open `runner.py` and run it. It will automatically help you execute Google account authentication (will redirect to browser, need to log in and authorize).

---

## 📝 Code Logic

- Modular design, main workflow (query data + import tableau) is in `runner.py` (not yet in use), this file will import and execute 2 functional modules (since main workflow is not in use, currently run module PY files directly).

- Module 0: Authentication. All authentication modules are in `auth_credential/`, using Google CLI authentication and Similar Web API key authentication.

- Module 1: Query data `data_collection/`
    - The main workflow of this module is `bq_runner.py`, export path is `output/csv`
    - SQL stored separately: All SQL templates and file naming rules are in `sql/queries.json`, can add/delete/modify as needed.
    - Workflow and sub-modules:
        1. Clear current `output/csv` folder
        2. Complete special SQL statements (`sql_processor.py` updates dates in two complex SQL files in `sql/`)
        3. Iterate through all SQL statements in `sql/queries.json`, download data, rename according to rules, and export as CSV (`bq_runner.py`)
        4. `simple_bq.py` is not used by this project. I kept this file for you to run it separately for other data query tasks.

- Module 2: Import tableau `tableau_processor/`
    - The main workflow of this module is `tableau_pipeline.py` (not yet in use), export path is `output/twbx`
    - The last mile of automation: Batch import specified CSVs into Tableau, and automatically replace existing data sources, synchronize filter and axis configurations.
    - Workflow and sub-modules:
        1. Unzip Tableau into data files and TWB (xml format) file, and save to `xml_of_twbx/` (`xml_of_twbx/twbx2xml.py`)
        2. Generate HYPER files (Tableau's efficient data format) corresponding to CSV files, and save to `output/hyper` (`hyper_generator.py`)
        3. Move CSV and HYPER into Tableau's Data folder (`csv_hyper_mover.py`)
        4. Point Tableau tables to new data files (`smart_meta_replacer.py`)
            - Note 1: This step **modifies in-place** all metadata belonging to the original data to the new data's metadata, achieving loading in a roundabout way.
            - Note 2: Use `xml_metadata_extractor.py` to identify "all metadata belonging to the original data", stored in `template_metadata.json`; use `csv_hyper_mover.py` to generate random numbers as "new data's metadata", stored in `current_metadata.json`
            - Note 3: Use `compare_keys.py` to check for missing metadata
        5. Update "most recent three months" month filters and axis ranges (`filter_axis_updater.py`)
        6. Delete `.DS_Store` generated from unpacking, and repackage back to Tableau's TWBX file (`twbx_packager.py`)

- After everything is done, you still need to manually adjust company logo positions.
    - You can visit the free website [Photopea](https://www.photopea.com/) to remove white backgrounds from logos and save as PNG
    - Sometimes, you need to pay attention to whether the logo structure is appropriate. For example, a taller rectangular shape is best suited for top-bottom structured logos, while flatter ones use left-right structures
    - Note: JPEG does not support vector format and will always have a white background, so you need to save as PNG
    - Note: Don't just change the file extension of a JPEG web image to PNG and then remove the background, as it will still have a white background. You should visit [Photopea](https://www.photopea.com/) and use the official save as PNG feature.

---

For help or more feature requests, contact the maintainer (soundream0502@gmail.com) or submit an issue.
