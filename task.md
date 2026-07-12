# Task: Review, Stabilization & Finalization (Day 7)

## Objective
Stabilize the scientific codebase, clean up comments/formatting, finalize documentation, and prepare for the Week 1 sprint review and database validation demo.

## Tasks
- [x] Run formatting and checks on scientific modules
  - [x] Install `ruff` and `black` in the backend virtual environment
  - [x] Run `ruff check scientific --fix` to resolve unused imports
  - [x] Run `black scientific` to format all python modules in the scientific package
  - [x] Verify that all 323 tests continue to pass successfully
- [x] Perform documentation updates and clear deprecated files
  - [x] Delete deprecated sample files under `automation/sprint/` (`sample_WORKFLOW.md`, `sample_config_template.json`, `sample_sprint_engine.py`)
  - [x] Update root `README.md` to show the correct count of 323 tests and verify sections
  - [x] Update `docs/README.md` to show the correct count of 323 tests and verify structure
  - [x] Create `scientific/README.md` for standalone scientific module documentation
- [x] Document scientific checklist for Week 2
  - [x] Link and summarize `Plans/week2_scientific_checklist.md` in scientific documentation
  - [x] Ensure all placeholders in `scientific/simulation/` and `scientific/pipeline/` are cleanly documented
- [x] Assist in the sprint review and database validation demo
  - [x] Prepare a database validation demo script/guide
  - [x] Verify that database schemas (including Cases, Scenarios, and the new Towers model) are fully consistent
  - [x] Run the backend and frontend to verify the system launches and displays correctly

## Deliverables
- [x] Finalized scientific package structure and documentation (`scientific/README.md`)
- [x] Cleaned-up and formatted codebase (Ruff/Black passing, 323 tests passing)
- [x] Updated project documentation (`README.md`, `docs/README.md`)
- [x] Week 2 Scientific Checklist confirmed
- [x] Demo script for database validation and sprint review
