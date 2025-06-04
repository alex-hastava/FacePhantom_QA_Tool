# FacePhantom QA Tool

A Python-based QA automation tool for analyzing light and radiation field coincidence using DICOM images acquired from an EPID. This tool uses the proprietary Face Phantom device to determine light field geometry via BB detection and compares it with radiation field boundaries obtained via PyLinac. Results are saved as a detailed visual PDF report and a structured CSV table.

---

## Features

- Detects BB markers using Hough Circle Transform
- Extracts radiation field edges using PyLinac’s FieldAnalysis
- Performs SID/SAD-based geometric scaling for accurate comparison
- Generates annotated PDF reports with overlays and pass/fail criteria
- Outputs CSV results of field edge distances and tolerances

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/alex-hastava/FacePhantom_QA_Tool.git
cd FacePhantom_QA_Tool
pip install -r requirements.txt
```

> Python 3.8+ is required.

---

## Usage

### Option 1: Run as Python Script

From the project root:

```bash
python facephantom_qa/main.py
```

You will be prompted to select one or more DICOM files. After processing, the following files will be generated in the same directory:

- `FieldCoincidenceQA_Report.pdf`
- `FieldCoincidenceQA_Results.csv`

### Option 2: Run Executable (No Python Needed)

If using the built executable:

1. Download `FacePhantomQA.exe` from the latest [GitHub Release](https://github.com/alex-hastava/FacePhantom_QA_Tool/releases)
2. Double-click to launch
3. Select your `.dcm` files from the file dialog
4. Wait for the report and results to appear

---

## File Structure

```
FacePhantom_QA_Tool/
├── facephantom_qa/
│   ├── __init__.py
│   ├── main.py
│   └── qa_gant_col_img/        # (optional: sample .dcm images)
├── requirements.txt
├── setup.py
├── README.md
└── dist/                       # contains FacePhantomQA.exe (not tracked in repo)
```

---

## Output Files

- **PDF**: Visual overlays of radiation and light fields with crosshairs and measurements
- **CSV**: Tabulated edge distances and QA pass/fail results for each field side

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## Author

**Alex Hastava**  
Stony Brook Medicine  
Department of Radiation Oncology

---

## Acknowledgments

- [PyLinac](https://github.com/jrkerns/pylinac) for field analysis methods  
- OpenCV for image processing  
- Pydicom for DICOM parsing
