# FacePhantom QA Tool

A Python-based QA tool for analyzing light and radiation field coincidence on DICOM images acquired using an EPID. This tool leverages the proprietary **Face Phantom** device to determine light field geometry via BB marker detection, and compares it with radiation field boundaries extracted using PyLinac. The output includes a detailed visual PDF report and a structured CSV results table.

---

## Features

- Automated BB detection via Hough Circle Transform
- Radiation field analysis using PyLinac's `FieldAnalysis`
- Geometric scaling based on SAD/SID distances
- Annotated PDF reports with overlays and pass/fail indicators
- CSV output with quantitative edge comparison results

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/alex-hastava/FacePhantom_QA_Tool.git
cd FacePhantom_QA_Tool
pip install -r requirements.txt
```

> Requires Python 3.8 or later.

---

## Usage

### Option 1: Run as Python Script

From the project root directory:

```bash
python facephantom_qa/main.py
```

A file dialog will appear prompting you to select one or more `.dcm` files.

**Output Files:**

- `FieldCoincidenceQA_Report.pdf` — Annotated report with light/radiation field overlays
- `FieldCoincidenceQA_Results.csv` — Summary table of measurements and QA results

These files are saved in the same directory from which the script or executable is run.

---

### Option 2: Run as Executable (No Python Required)

1. Download `FacePhantomQA.exe` from the latest [GitHub Release](https://github.com/alex-hastava/FacePhantom_QA_Tool/releases)
2. Double-click the executable
3. Select one or more `.dcm` files via the file dialog
4. Wait for analysis to complete; output files will appear in the same folder

---

## File Structure

```
FacePhantom_QA_Tool/
├── facephantom_qa/
│   ├── __init__.py
│   ├── main.py
│   └── qa_gant_col_img/        # Optional: sample .dcm images
├── requirements.txt
├── setup.py
├── README.md
└── dist/                       # Contains FacePhantomQA.exe (not tracked)
```

---

## Naming Convention

Couch angle is determined automatically by inspecting the DICOM filename. Include one of the following substrings in your filenames to assign the correct rotation:

| Filename Tag    | Assigned Couch Angle |
|----------------|----------------------|
| `45_couch`     | +45°                 |
| `90_couch`     | +90°                 |
| `180_couch`    | +180°                |
| `45m_couch`    | -45°                 |
| `90m_couch`    | -90°                 |
| `180m_couch`   | -180°                |

If no valid tag is found, a default of `0°` is used.

---

## Output Files

- **FieldCoincidenceQA_Report.pdf**: Annotated EPID image with crosshairs, BB markers, and field boundaries
- **FieldCoincidenceQA_Results.csv**: Table of edge distances (light field vs radiation field) and pass/fail status per edge and center

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Alex Hastava**  
Department of Radiation Oncology  
Stony Brook Medicine

---

## Acknowledgments

- [PyLinac](https://github.com/jrkerns/pylinac) – Field analysis tools
- [OpenCV](https://opencv.org) – BB marker detection
- [Pydicom](https://pydicom.github.io) – DICOM parsing and metadata extraction
