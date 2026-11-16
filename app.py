"""
Evalia - Production-Ready Flask Web Application
Automated student grade calculation, vector A4 PDF report card generation,
and consolidated Excel summary exports.
"""

import io
import os
import uuid
from typing import Dict, Any, Optional

import pandas as pd
from flask import (
    Flask, render_template, request, jsonify, send_file, make_response
)

import calculator
import pdf_generator
import excel_exporter

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "evalia-secret-key-2025")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

# In-memory store for active session/dataset
ACTIVE_DATASET: Dict[str, Any] = {}
ACTIVE_DF: Optional[pd.DataFrame] = None
ACTIVE_CREDITS: Dict[str, float] = {}
SAMPLE_FILE_PATH = os.path.join(os.path.dirname(__file__), "sample_data", "students_marks.csv")


def load_sample_if_needed() -> Dict[str, Any]:
    """Helper to ensure active dataset is populated with sample data if empty."""
    global ACTIVE_DATASET, ACTIVE_DF, ACTIVE_CREDITS
    if not ACTIVE_DATASET or "students" not in ACTIVE_DATASET:
        df = calculator.validate_and_parse_csv(SAMPLE_FILE_PATH)
        ACTIVE_DF = df.copy()
        ACTIVE_DATASET = calculator.calculate_grades_and_analytics(
            df, scale_type="10.0", subject_credits=ACTIVE_CREDITS or None
        )
        ACTIVE_CREDITS = ACTIVE_DATASET.get("subject_credits", {})
    return ACTIVE_DATASET


@app.route("/")
def index():
    """Render the dashboard interface."""
    return render_template("index.html")


@app.route("/download/sample-csv", methods=["GET"])
def download_sample_csv():
    """Download the official sample CSV file."""
    if not os.path.exists(SAMPLE_FILE_PATH):
        return jsonify({"success": False, "message": "Sample CSV file not found on server."}), 404
    return send_file(
        SAMPLE_FILE_PATH,
        mimetype="text/csv",
        as_attachment=True,
        download_name="evalia_sample_students_marks.csv"
    )


@app.route("/api/sample", methods=["GET"])
def api_sample_data():
    """Process and return the sample dataset with analytics."""
    global ACTIVE_DATASET, ACTIVE_DF, ACTIVE_CREDITS
    scale_type = request.args.get("scale", "10.0")
    if scale_type not in ("10.0", "4.0"):
        scale_type = "10.0"

    try:
        df = calculator.validate_and_parse_csv(SAMPLE_FILE_PATH)
        ACTIVE_DF = df.copy()
        data = calculator.calculate_grades_and_analytics(
            df, scale_type=scale_type, subject_credits=ACTIVE_CREDITS or None
        )
        ACTIVE_CREDITS = data.get("subject_credits", {})
        ACTIVE_DATASET = data
        return jsonify({
            "success": True,
            "scale_type": scale_type,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error loading sample data: {str(e)}"
        }), 500


@app.route("/api/clear", methods=["POST"])
def api_clear():
    """Clear active cohort dataset."""
    global ACTIVE_DATASET, ACTIVE_DF, ACTIVE_CREDITS
    ACTIVE_DATASET = {}
    ACTIVE_DF = None
    ACTIVE_CREDITS = {}
    return jsonify({"success": True, "message": "Dataset cleared."})


@app.route("/api/upload", methods=["POST"])
def api_upload_csv():
    """Handle CSV upload, validate structure, calculate grades and return results."""
    global ACTIVE_DATASET, ACTIVE_DF, ACTIVE_CREDITS

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "message": "No file part in upload request."
        }), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({
            "success": False,
            "message": "No file selected for upload."
        }), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({
            "success": False,
            "message": "Unsupported file format. Please upload a standard comma-separated (.csv) file."
        }), 400

    scale_type = request.form.get("scale", "10.0")
    if scale_type not in ("10.0", "4.0"):
        scale_type = "10.0"

    try:
        df = calculator.validate_and_parse_csv(file)
        ACTIVE_DF = df.copy()
        ACTIVE_CREDITS = {}  # reset on fresh file upload
        data = calculator.calculate_grades_and_analytics(df, scale_type=scale_type)
        ACTIVE_CREDITS = data.get("subject_credits", {})
        ACTIVE_DATASET = data
        return jsonify({
            "success": True,
            "scale_type": scale_type,
            "filename": file.filename,
            "data": data
        })
    except calculator.ValidationError as ve:
        return jsonify({
            "success": False,
            "message": ve.message,
            "errors": ve.errors
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Unexpected server error processing CSV: {str(e)}"
        }), 500
    finally:
        try:
            file.close()
        except Exception:
            pass


@app.route("/api/update-credits", methods=["POST"])
def api_update_credits():
    """Update subject credits and recalculate credit-weighted GPAs."""
    global ACTIVE_DATASET, ACTIVE_DF, ACTIVE_CREDITS
    req_json = request.get_json(silent=True) or {}
    new_credits = req_json.get("credits", {})

    if ACTIVE_DF is None or ACTIVE_DF.empty:
        load_sample_if_needed()

    scale_type = ACTIVE_DATASET.get("scale_type", "10.0")
    for subj_name, cred_val in new_credits.items():
        try:
            ACTIVE_CREDITS[subj_name] = max(0.5, float(cred_val))
        except (ValueError, TypeError):
            pass

    data = calculator.calculate_grades_and_analytics(
        ACTIVE_DF, scale_type=scale_type, subject_credits=ACTIVE_CREDITS
    )
    ACTIVE_DATASET = data
    return jsonify({
        "success": True,
        "scale_type": scale_type,
        "subject_credits": ACTIVE_CREDITS,
        "data": ACTIVE_DATASET
    })


@app.route("/api/switch-scale", methods=["POST"])
def api_switch_scale():
    """Switch active GPA scale (10.0 vs 4.0) and return recalculated analytics."""
    global ACTIVE_DATASET, ACTIVE_DF, ACTIVE_CREDITS
    req_json = request.get_json(silent=True) or {}
    scale_type = req_json.get("scale", "10.0")
    if scale_type not in ("10.0", "4.0"):
        scale_type = "10.0"

    if ACTIVE_DF is not None and not ACTIVE_DF.empty:
        ACTIVE_DATASET = calculator.calculate_grades_and_analytics(
            ACTIVE_DF, scale_type=scale_type, subject_credits=ACTIVE_CREDITS
        )
    else:
        load_sample_if_needed()
        ACTIVE_DATASET["scale_type"] = scale_type

    return jsonify({
        "success": True,
        "scale_type": scale_type,
        "data": ACTIVE_DATASET
    })


@app.route("/api/pdf/<student_id>", methods=["GET"])
def api_student_pdf(student_id: str):
    """Generate and return an individual vector A4 PDF report card."""
    load_sample_if_needed()
    scale_type = request.args.get("scale", ACTIVE_DATASET.get("scale_type", "10.0"))
    if scale_type not in ("10.0", "4.0"):
        scale_type = "10.0"

    # Find student
    student = next(
        (s for s in ACTIVE_DATASET.get("students", []) if s["student_id"] == student_id),
        None
    )

    if not student:
        return jsonify({
            "success": False,
            "message": f"Student with ID '{student_id}' not found in the current cohort."
        }), 404

    try:
        pdf_bytes = pdf_generator.create_student_report_card_pdf(
            student=student,
            scale_type=scale_type
        )

        clean_id = "".join(c if c.isalnum() else "_" for c in student["student_id"]).strip("_")
        clean_name = "".join(c if c.isalnum() else "_" for c in student["name"]).strip("_")
        download_name = f"Evalia_Report_Card_{clean_id}_{clean_name}.pdf"

        is_download = request.args.get("download") == "1"
        disposition = "attachment" if is_download else "inline"

        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"{disposition}; filename={download_name}"
        return response
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to generate report card PDF: {str(e)}"
        }), 500


@app.route("/api/download-all-pdfs", methods=["GET", "POST"])
def api_download_all_pdfs():
    """Bundle all student report cards into a single ZIP archive."""
    load_sample_if_needed()
    scale_type = request.args.get("scale") or (request.form.get("scale") if request.method == "POST" else None) or ACTIVE_DATASET.get("scale_type", "10.0")
    if scale_type not in ("10.0", "4.0"):
        scale_type = "10.0"

    students = ACTIVE_DATASET.get("students", [])
    if not students:
        return jsonify({"success": False, "message": "No student cohort data available to export."}), 400

    try:
        zip_bytes = pdf_generator.generate_batch_pdf_zip(students, scale_type=scale_type)
        return send_file(
            io.BytesIO(zip_bytes),
            mimetype="application/zip",
            as_attachment=True,
            download_name="Evalia_Report_Cards_All_Students.zip"
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to generate batch PDF archive: {str(e)}"
        }), 500


@app.route("/api/export-excel", methods=["GET", "POST"])
def api_export_excel():
    """Generate consolidated two-sheet Excel workbook summary."""
    load_sample_if_needed()
    scale_type = request.args.get("scale") or (request.form.get("scale") if request.method == "POST" else None) or ACTIVE_DATASET.get("scale_type", "10.0")
    if scale_type not in ("10.0", "4.0"):
        scale_type = "10.0"

    try:
        excel_bytes = excel_exporter.create_excel_summary_workbook(ACTIVE_DATASET, scale_type=scale_type)
        return send_file(
            io.BytesIO(excel_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="Evalia_Academic_Summary.xlsx"
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to export Excel workbook: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Resource not found."}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Internal server error."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
