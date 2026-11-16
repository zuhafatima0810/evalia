# Quickstart: Local Setup & Render Deployment

This guide gives you copy-pasteable instructions to run **Evalia** locally and deploy it live to **Render**.

---

## 1. How to Run Locally

### Prerequisites
- Python 3.10 or higher installed on your computer.

### Quick Commands (PowerShell / Terminal)

```bash
# 1. Navigate to the project root
cd E:\Evalia

# 2. Create and activate a virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On Mac / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests to confirm everything works
python test_evalia.py

# 5. Start the web application
python app.py
```

### Accessing the Web App
- On your computer: Open `http://127.0.0.1:5000`
- On your mobile phone (connected to same Wi-Fi):
  1. Run `ipconfig` (Windows) or `ifconfig` (macOS/Linux) to find your local IP address (e.g. `192.168.1.45`).
  2. Open `http://192.168.1.45:5000` on your mobile browser.

---

## 2. How to Push to GitHub

If you have not pushed to GitHub yet:

```bash
cd E:\Evalia
git init
git add .
git commit -m "Initial release of Evalia Academic Engine"
git branch -M main
git remote add origin https://github.com/zuhafatima0810/evalia.git
git push -u origin main
```

---

## 3. How to Deploy Live on Render (Free)

1. Go to **[render.com](https://render.com)** and sign in with **GitHub**.
2. Click the **New +** button in the top navigation bar → Select **Web Service**.
3. Choose **"Build and deploy from a Git repository"** and connect your `evalia` repository.
4. Fill in the settings:
   - **Name**: `evalia` *(or your preferred name, which becomes `https://evalia.onrender.com`)*
   - **Region**: Select the closest region to you (e.g., *Singapore*, *Frankfurt*, *Ohio*)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: **Free** ($0/month)
5. Click **Deploy Web Service**.
6. Wait 1–2 minutes until the status shows **"Live"**.
7. Click your live URL (e.g. `https://evalia.onrender.com`) to open your live application on the internet!

---

## 4. How to Use the Key Features

1. **Load Data**:
   - Click **"Load Sample Cohort"** for immediate sample data, OR
   - Drag and drop your own `.csv` file onto the dropzone.
2. **Configure Subject Credits**:
   - Click **"Course Credits"** in the control bar.
   - Adjust credits for each course (e.g., Core: 4.0, Elective: 3.0, Lab: 1.5).
   - Click **"Apply Credits & Recalculate"** to update weighted GPA across all students.
3. **Switch GPA Scale**:
   - Click **"10.0 Scale"** or **"4.0 Scale"** to recalculate GPAs instantly.
4. **Search and Filter**:
   - Type in the search box to filter by name, student ID, or class.
   - Click **"All"**, **"Passed"**, or **"Failed"** to filter by academic standing.
5. **Download Transcripts**:
   - Click the eye icon on any student row for a vector A4 PDF modal preview.
   - Click **"Download All PDF Reports (.ZIP)"** to export all transcripts in one zip archive.
   - Click **"Export Excel Report (.XLSX)"** for a 2-sheet analytical workbook.

