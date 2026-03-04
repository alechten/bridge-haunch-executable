# CLAUDE.md — Bridge Haunch Executable

This file provides guidance for AI assistants working in this repository.

## Project Overview

**NDOT Preliminary Bridge Haunch and Seat Elevation Calculator** — a standalone Windows desktop application for computing prestressed concrete girder bridge haunches and generating formal engineering reports per Nebraska Department of Transportation (NDOT) guidelines.

- **Version:** V0.5
- **Language:** Python 3.11
- **GUI Framework:** Tkinter (stdlib — no external GUI deps)
- **Distribution:** Single Windows `.exe` via PyInstaller

---

## Repository Structure

```
bridge-haunch-executable/
├── main.py                       # GUI entry point (Tkinter app, 1,349 lines)
├── bridge_haunch_calculator.py   # Core structural calculation engine (860 lines)
├── create_pdf.py                 # PDF report generation (1,368 lines)
├── config_manager.py             # JSON save/load and logo embedding (152 lines)
├── input_data.py                 # Dataclasses and input validation (141 lines)
├── NDOT_logo.png                 # NDOT branding image (embedded at build time)
├── README.md                     # Brief project description
└── .github/workflows/
    └── build-executable.yml      # GitHub Actions CI/CD pipeline
```

There are **no** `requirements.txt`, `setup.py`, `pyproject.toml`, `Makefile`, or test directories. Dependencies are declared only inside the GitHub Actions workflow.

---

## Module Responsibilities

### `main.py` — `BridgeCalculatorApp`
Tkinter GUI with five input tabs:
1. **Project Info** — header metadata (structure number, route, designer, reviewer)
2. **Vertical Curve** — VPI station/elevation, grades, curve length
3. **Substructure** — centerline stations (add/remove rows)
4. **Bridge Info** — geometry, materials, staged construction, median, superimposed loads
5. **Prestressing** — per-span strand layouts, debonding, harping

Key methods:
- `_create_[tab]_tab()` — builds each tab
- `_load_inputs_to_gui()` / `_save_gui_to_inputs()` — two-way data binding
- `run_analysis()` — invokes the calculation engine
- `generate_pdf()` — invokes the PDF engine

Keyboard shortcuts: **F5** (Run Analysis), **Ctrl+P** (Generate PDF), **Ctrl+S** (Save), **Ctrl+O** (Open).

### `bridge_haunch_calculator.py` — Calculation Engine
Key classes:

| Class | Purpose |
|---|---|
| `VerticalCurve` | Elevation at any station along the alignment |
| `beam_rail_info` | Lookup table for NU/IT beam and railing properties |
| `beam_layout` | Beam offsets, flange widths, bearing-to-bearing distances |
| `stations_locations` | Generates 10-ft interval stations |
| `section_properties_dead_loads` | Dead load distribution and moment calculations |
| `PrestressingCamberCalculator` | Strand stress, initial/effective prestress, camber |
| `simple_span` | Single-span deflection and camber |
| `continuous_deflections` | Multi-span Gauss-Seidel solver |
| `variable_haunch` | Haunch height requirements per beam/station |
| `min_camber_check` | Camber validation |
| `seat_elev` | Bearing seat elevation calculations |
| `AnalysisResults` (dataclass) | Stores all calculated outputs |

Helper functions: `gauss()` (Gaussian quadrature), `gauss_seidel()` (iterative solver).

Orchestrator: `run_analysis(inputs: BridgeInputs) -> AnalysisResults`

### `create_pdf.py` — PDF Report
Builds a multi-page engineering report using **ReportLab** and **Matplotlib**.

Key functions:
- `master_create_PDF(inputs, results)` — top-level orchestrator
- `title_block_and_borders()` — NDOT header with embedded logo
- `create_beam_cx()` / `create_rail_cx()` — beam and rail cross-section drawings
- `bridge_figure_sta_elev_points()` — elevation profile plot
- `generate_multi_page_pdf()` / `create_beam_haunch_pdf()` — multi-page haunch tables

### `config_manager.py` — `ConfigManager`
- `save_config(inputs, filepath)` — serialises `BridgeInputs` to JSON
- `load_config(filepath)` — deserialises JSON back to `BridgeInputs`
- `get_embedded_logo()` — returns the NDOT logo as bytes from a base64 constant

**Logo embedding:** `config_manager.py` contains a placeholder string `PLACEHOLDER_FOR_WORKFLOW_REPLACEMENT` that the CI workflow replaces with the actual base64-encoded PNG before bundling the executable.

### `input_data.py` — Data Models
Dataclasses that form the input schema:

```
BridgeInputs
├── HeaderInfo
├── VerticalCurveData
├── SubstructureData
├── BridgeInfo
│   ├── geometry (skew, widths, spacing, beam count)
│   ├── materials (beam_shape, rail_shape, f_c, wearing_surface)
│   ├── staging (staged, stage_start, stg_line_rt/lt)
│   ├── median (med_st, med_width, med_thick)
│   └── w_super (superimposed loads by stage)
└── List[SpanConfig]
    ├── midspan_strands / strand_dist_bot
    ├── List[DebondConfig]
    └── List[HarpConfig]
```

Utilities: `create_default_span_config()`, `create_default_inputs()`, `BridgeInputs.validate()`.

---

## Supported Engineering Options

**Beam shapes (13):**
- NU series: NU35, NU43, NU53, NU63, NU70, NU78
- IT series: IT13, IT17, IT21, IT25, IT29, IT33, IT39

**Rail shapes (11):**
39_SSCR, 39_OCR, 42_NU_O, 42_NU_C, 42_NU_M, 34_NU_O, 34_NU_C, 29_NE_O, 29_NE_C, 32_NJ, 42_NJ

**Concrete strength:** 8 ksi or 10 ksi (`f_c_beam`)

---

## Naming Conventions

| Convention | Examples |
|---|---|
| Classes — PascalCase | `VerticalCurve`, `BridgeInfo`, `PrestressingCamberCalculator` |
| Functions & variables — snake_case | `run_analysis()`, `sta_VPI`, `elev_VPC` |
| Constants — UPPER_SNAKE_CASE | `NDOT_LOGO_BASE64`, `STRAND_CONSTRAINTS` |

**Civil engineering prefixes used throughout:**
- `sta_` — station (ft along alignment)
- `elev_` — elevation (ft vertical)
- `brg_` — bearing
- `_VPC` / `_VPT` — Vertical Parabolic Curve / Tangent
- `_CL` — centerline
- `n_beams` — count of beams
- `f_c` / `E_c` — concrete strength / elastic modulus (ksi)

---

## Development Workflow

### Running Locally (development)
```bash
# Install dependencies (Python 3.11 required)
pip install numpy pandas matplotlib reportlab pillow

# Launch the GUI
python main.py
```

### Building the Windows Executable
The CI/CD pipeline (`.github/workflows/build-executable.yml`) handles the full build:
1. Sets up Python 3.11 on a Windows runner
2. Installs all pip dependencies
3. Embeds the NDOT logo into `config_manager.py` (PowerShell base64 replacement)
4. Verifies all module imports succeed
5. Runs PyInstaller with `--onefile --noconsole`
6. Uploads the `.exe` as an artifact; creates a GitHub Release on version tags

To build manually:
```bash
pip install pyinstaller numpy pandas matplotlib reportlab pillow
python -c "import main, bridge_haunch_calculator, create_pdf, config_manager, input_data"
pyinstaller --onefile --noconsole --name "NDOT Preliminary Bridge Haunch and Seat Elevation Calculator V0.5" main.py
```

The output appears in `dist/`.

### CI/CD Triggers
- Push to `main` or `master`
- Pull requests to `main` or `master`
- Tags matching `v*` (creates a GitHub Release)
- Manual workflow dispatch

---

## Key Architectural Decisions

- **Tkinter** was chosen for zero-dependency GUI (ships with Python).
- **Single-file modules** — each major concern lives in its own file; avoid splitting further unless a file grows very large.
- **Dataclasses** in `input_data.py` are the single source of truth for the data schema; all GUI ↔ calculation ↔ PDF communication goes through `BridgeInputs` / `AnalysisResults`.
- **No automated tests** exist. Validation is done by running the application manually and checking PDF output against known results.
- **JSON project files** are human-readable and version-control friendly.
- **Base64 logo** is injected at build time; do not hard-code binary data in source.

---

## Important Constraints

- **Windows-only distribution.** The PyInstaller config targets Windows x64; do not introduce platform-specific paths that break on Linux during development.
- **Python 3.11 required.** The CI pins this version; avoid language features above 3.11.
- **No new dependencies without updating the workflow.** Any new `pip install` must also be added to `build-executable.yml`.
- **No external test framework.** Do not add pytest or similar unless also wiring it into CI.
- **Logo placeholder must not be removed.** The string `PLACEHOLDER_FOR_WORKFLOW_REPLACEMENT` in `config_manager.py` is replaced by the build workflow; removing or reformatting it will break logo embedding in the executable.

---

## Common Tasks for AI Assistants

### Adding a new beam shape
1. Add the shape name to the options list in `main.py` (Bridge Info tab combo box).
2. Add its geometric properties (height, flange width, web width, moment of inertia, area, centroid) to `beam_rail_info` in `bridge_haunch_calculator.py`.
3. Add the corresponding cross-section drawing logic to `create_beam_cx()` in `create_pdf.py`.
4. Update `input_data.py` validation if shape lists are checked there.

### Adding a new input field
1. Define the field in the appropriate dataclass in `input_data.py`.
2. Add the widget to the relevant tab in `main.py`.
3. Wire it in `_load_inputs_to_gui()` and `_save_gui_to_inputs()`.
4. Update `ConfigManager._inputs_to_dict()` and `_dict_to_inputs()` for JSON persistence.
5. Use the value in `bridge_haunch_calculator.py` and/or `create_pdf.py` as needed.

### Modifying the PDF report
- Work inside `create_pdf.py`. Each page/section has a dedicated function.
- `master_create_PDF()` is the orchestrator — add new sections by calling new helpers from there.
- Use ReportLab's `canvas` API for precise layout; use Matplotlib only for plots/drawings.

### Debugging calculation issues
- `run_analysis()` in `bridge_haunch_calculator.py` is the entry point.
- Intermediate class instances (`VerticalCurve`, `beam_layout`, etc.) can be instantiated standalone for unit-level debugging.
- `AnalysisResults` stores the full output; print its fields to inspect values.
