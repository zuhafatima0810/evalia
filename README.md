# Evalia — Academic Evaluation & Transcript Engine

Evalia is a production-grade web application designed for academic departments, universities, and examination boards. It automates student score evaluation, dynamic course credit allocation, weighted GPA calculation, tie-aware ranking, single-page vector A4 transcript generation, and multi-sheet analytical Excel reporting.

---

## Table of Contents
1. [Key Features](#key-features)
2. [How to Run Locally](#how-to-run-locally)
3. [How to Use the Application](#how-to-use-the-application)
4. [CSV Data Schema & Guidelines](#csv-data-schema--guidelines)
5. [Grading Scheme & Weighted GPA Formula](#grading-scheme--weighted-gpa-formula)
6. [Automated Test Suite](#automated-test-suite)
7. [Repository Structure](#repository-structure)

---

## Key Features

- **Automated CSV Ingestion & Dynamic Subject Detection**:
  - Automatically identifies student metadata (`Student_ID`, `Name`, `Class`, etc.) and grades any number of academic subjects.
  - Automatically isolates non-subject metadata (such as `Year`, `Semester`, `Batch`, `Section`, `Roll_No`) and preserves them as cohort tags without treating them as failing courses.
- **Course Credit Hours & Weighted GPA**:
  - Automatically parses credit hours from column headers (e.g. `Python (4)`, `DAA (3 Cr)`) or defaults to standard `4.0` credits per subject.
  - Interactive **Course Credits Drawer** in the UI allows instructors to customize credit allocations for Theory, Lab, or Elective courses.
  - Computes credit-weighted GPA on both **10.0** and **4.0** scales using standard institutional weighting:
    $$\text{Weighted GPA} = \frac{\sum (\text{Grade Points} \times \text{Credits})}{\sum \text{Credits}}$$
- **Strict Minimum Subject Threshold (Remediation Flagging)**:
  - Any score below 40% in a subject marks the student as `FAILED` (Remediation Needed), listing the specific failing course(s).
- **Tie-Aware Competition Ranking**:
  - Implements standard competition ranking (`1, 2, 2, 4...`) based on cumulative percentages.
- **Vector A4 PDF Report Cards (`reportlab`)**:
  - Strictly fits on **1 page** with zero overflow.
  - Contains student profile, subject breakdown with **Credits** and **Credit Points**, weighted GPA summary, institutional remarks, and three formal signature lines (Class Teacher, Controller of Examinations, Principal).
  - Single student preview modal and **Download All Report Cards (.ZIP)** batch archive.
- **Consolidated Excel Workbooks (`openpyxl`)**:
  - **Sheet 1 (Results Summary)**: Full roster with frozen headers, zebra striping, credit columns, and conditional status fills.
  - **Sheet 2 (Class Analytics)**: Executive metrics, grade distribution breakdown, and subject-wise curriculum performance table.
- **Mobile-Responsive Editorial UI**:
  - Built to a clean editorial aesthetic (Inter typography, quiet tones, zero emojis).
  - Fully responsive on mobile phones and tablets with native touch-scroll data tables (`-webkit-overflow-scrolling: touch`), full-screen modal previews, and stacked touch controls.

---

## How to Run Locally

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14 installed.
- Git installed.

### Step 1: Clone or Navigate to the Project Folder
```bash
git clone https://github.com/zuhafatima0810/evalia.git
cd evalia
```
*(Or navigate to `E:\Evalia` if already on your machine)*

### Step 2: Create and Activate a Virtual Environment
- **On Windows (PowerShell / Command Prompt)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **On macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Automated Tests (Optional but Recommended)
```bash
python test_evalia.py
```
*(All 7 unit tests covering CSV parsing, validation, credit calculation, PDF generation, and Excel export will execute and pass)*

### Step 5: Start the Development Server
```bash
python app.py
```

### Step 6: Open in Your Browser
- On your computer: Open [http://127.0.0.1:5000](http://127.0.0.1:5000)
- On your mobile phone (on the same Wi-Fi network):
  1. Find your computer's IP address with `ipconfig` (Windows) or `ifconfig` (macOS/Linux).
  2. Open `http://<YOUR-COMPUTER-IP>:5000` on your mobile browser.

---

## How to Use the Application

### 1. Ingesting Student Data
- **Load Sample Cohort**: Click **"Load Sample Cohort"** in the top navigation or dropzone to test with pre-configured student records.
- **Upload Your Own CSV**: Click **"Select CSV File"** or drag-and-drop a `.csv` file onto the dropzone.
- **Download Sample Template**: Click **"Download Sample CSV"** to get a clean, ready-to-fill spreadsheet template.

### 2. Customizing Course Credits
- Click the **"Course Credits"** button in the control bar.
- The **Course Credit Weight Allocation** drawer expands.
- Adjust credit hours for any course (e.g. `4.0` for Core Courses, `3.0` for Electives, `1.5` for Practical Labs).
- Click **"Apply Credits & Recalculate"** to instantly update the weighted GPA across the cohort and recalculate ranks and analytics.

### 3. Toggling GPA Scales
- Switch between **Standard 10.0 Scale** (A+: 10, A: 9, B+: 8, B: 7, C: 6, D: 5, F: 0) and **Standard 4.0 Scale** (A+: 4.0, A: 3.7, B+: 3.3, B: 3.0, C: 2.0, D: 1.0, F: 0.0) with a single click.

### 4. Searching and Filtering
- Type any student name, ID, or class section in the search bar.
- Filter by status using the **All**, **Passed**, and **Failed** pills.

### 5. Official PDF Report Cards
- Click the **Eye icon** on any student row to preview their official vector A4 transcript modal.
- Click the **Download icon** to save an individual student transcript.
- Click **"Download All PDF Reports (.ZIP)"** in the top control bar to download an archive containing individual PDFs for every student in the cohort.

### 6. Excel Roster Export
- Click **"Export Excel Report (.XLSX)"** to generate a formatted two-sheet analytical workbook.

---

## CSV Data Schema & Guidelines

Your uploaded CSV file should contain student identifier columns and numerical marks (`0` to `100`):

| Column Type | Accepted Header Names | Description | Example |
|---|---|---|---|
| **Student ID** | `Student_ID`, `Roll_No`, `ID`, `Admission_No`, `Roll_Number` | Unique student identifier | `EVA-2025-001`, `B24DS101` |
| **Name** | `Name`, `Student_Name`, `Full_Name`, `Candidate_Name` | Student's full name | `Eleanor Vance` |
| **Class** | `Class`, `Grade`, `Department`, `Branch`, `Program`, `Section` | Student class or program | `B.Tech CSE`, `Grade 12-A` |
| **Optional Metadata** | `Year`, `Semester`, `Batch`, `Academic_Year`, `Term` | Automatically merged into cohort tag | `Year 2`, `Sem 3` |
| **Subject Marks** | Any course title (e.g., `Python`, `DAA (4 Cr)`, `Physics`) | Numerical marks between 0 and 100 | `95.0`, `82.5` |

### Sample CSV Structure:
```csv
Student_ID,Name,Class,Year,Semester,Python (4),Data Mining (3),DAA (4),Web Programming (3)
Roll_1,John Doe,B.Tech CSE,2,3,92.0,85.0,88.0,91.0
Roll_2,Jane Smith,B.Tech CSE,2,3,78.0,65.0,38.0,72.0
```
*(Jane Smith will be marked as Failed/Remediation Needed because her DAA mark is 38.0 < 40.0)*

---

## Grading Scheme & Weighted GPA Formula

### Grade Boundaries
| Percentage Range | Grade | 10.0 Scale Points | 4.0 Scale Points | Standing |
|:---:|:---:|:---:|:---:|---|
| **90.0% – 100.0%** | `A+` | 10.0 | 4.0 | Outstanding / First Class with Distinction |
| **80.0% – 89.9%** | `A` | 9.0 | 3.7 | Commendable / First Class |
| **70.0% – 79.9%** | `B+` | 8.0 | 3.3 | Solid / Upper Second Class |
| **60.0% – 69.9%** | `B` | 7.0 | 3.0 | Satisfactory / Second Class |
| **50.0% – 59.9%** | `C` | 6.0 | 2.0 | Acceptable / Third Class |
| **40.0% – 49.9%** | `D` | 5.0 | 1.0 | Marginal Pass |
| **Below 40.0%** | `F` | 0.0 | 0.0 | Remediation Required |

### Institutional Weighted GPA Formula
$$\text{Weighted GPA} = \frac{\sum_{i=1}^{n} (\text{Grade Points}_i \times \text{Credit Hours}_i)}{\sum_{i=1}^{n} \text{Credit Hours}_i}$$

---

## Automated Test Suite

Evalia comes with a comprehensive unit and integration test suite:

```bash
python test_evalia.py
```

### Coverage:
- Column header alias detection and metadata filtering.
- Data validation rules (duplicate IDs, score bounds, non-numeric values).
- Exact mathematical calculation of credit-weighted GPA on 10.0 and 4.0 scales.
- Tie-aware competition ranking logic.
- Vector A4 single-page PDF transcript generation and styling constraints.
- Two-sheet formatted openpyxl Excel generation.
- Complete Flask REST API endpoints (`/api/upload`, `/api/update-credits`, `/api/switch-scale`, `/api/pdf/<id>`, `/api/export-excel`, `/api/download-all-pdfs`).

---

## Repository Structure

```
Evalia/
├── app.py                      # Flask REST controller & application routes
├── calculator.py               # Ingestion engine, validation, grading, weighted GPA
├── pdf_generator.py            # Vector A4 PDF transcript & ZIP batch generator
├── excel_exporter.py           # Two-sheet formatted openpyxl workbook generator
├── test_evalia.py              # Automated test suite
├── requirements.txt            # Python dependencies (Flask, Pandas, ReportLab, OpenPyXL, Gunicorn)
├── Procfile                    # Deployment entry point for Render / Railway / Heroku
├── Dockerfile                  # Containerized production deployment configuration
├── .dockerignore               # Docker build exclusions
├── .gitignore                  # Git tracking exclusions
├── README.md                   # Complete documentation & usage guide
├── design.md                   # Design system tokens and specifications
├── sample_data/
│   ├── students_marks.csv      # Standard 12-student K-12 sample dataset
│   └── btech_cse_data_science.csv # 128-student university B.Tech dataset
├── static/
│   ├── style.css               # Responsive design-system stylesheet
│   └── app.js                  # Client-side state manager & interactive UI controller
└── templates/
    └── index.html              # HTML5 dashboard markup
```

---

## License
Open source for educational and institutional evaluation use.
