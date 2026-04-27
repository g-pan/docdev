# Archive

This folder contains developmental and test files that are no longer active in the project.

## Contents

- **Old dashboard variants**: dashtests*.html, dashtest*.html
  - Experimental iterations before the template-based regeneration system
  
- **Old Python scripts**: test_extraction.py, PyTester1.py, update_dashtests_4mSum.py
  - Development/testing scripts replaced by current production scripts
  
- **Backup data files**: summary[0-3].html
  - Previous test run backups
  
- **Old HTML pages**: proto-dash.html, indexOG.html, dashtop.html
  - Obsolete prototype pages

- **Reference files**: OBT*.html, *.txt files
  - Historical documentation and notes

## Notes

These files are kept for historical reference but are **not part of the active production pipeline**. The current production system uses:

- `pages/dashtests.TMPL.html` - stable template
- `pages/update_dashtests_from_summary.py` - extraction/generation script
- `pages/fetch_summary.py` - data downloader
- `scripts/publish_public_dashboard.ps1` - orchestrator

See the root `README.md` and `DashTestUpdateNotes.txt` for current workflow details.
