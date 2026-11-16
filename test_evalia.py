"""
Evalia - Comprehensive Automated Test Suite
Verifies CSV ingestion, validation rules, GPA & ranking algorithms,
vector PDF generation, batch ZIP archiving, Excel exports, and Flask endpoints.
"""

import io
import re
import unittest
import openpyxl
import pypdfium2

import calculator
import pdf_generator
import excel_exporter
from app import app


class TestEvaliaEngine(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.sample_csv_path = "sample_data/students_marks.csv"

    def test_sample_csv_parsing(self):
        """Test parsing of the official sample CSV."""
        df = calculator.validate_and_parse_csv(self.sample_csv_path)
        self.assertEqual(len(df), 12)
        id_col, name_col, class_col, subjects = calculator.identify_columns(df)
        self.assertEqual(id_col, "Student_ID")
        self.assertEqual(name_col, "Name")
        self.assertEqual(class_col, "Class")
        self.assertEqual(len(subjects), 5)
        self.assertIn("Mathematics", subjects)
        self.assertIn("Physics", subjects)

    def test_validation_errors(self):
        """Test strict validation checks and error messages."""
        # 1. Missing required column
        with self.assertRaises(calculator.ValidationError) as ctx:
            calculator.validate_and_parse_csv("Student_ID,Name\n1,Alice")
        self.assertIn("Missing required metadata column", str(ctx.exception))

        # 2. Out of range marks (> 100)
        with self.assertRaises(calculator.ValidationError) as ctx:
            calculator.validate_and_parse_csv("Student_ID,Name,Class,Math\n1,Alice,12-A,105")
        self.assertTrue(any("between 0 and 100" in err for err in ctx.exception.errors))

        # 3. Out of range marks (< 0)
        with self.assertRaises(calculator.ValidationError) as ctx:
            calculator.validate_and_parse_csv("Student_ID,Name,Class,Math\n1,Alice,12-A,-5")
        self.assertTrue(any("between 0 and 100" in err for err in ctx.exception.errors))

        # 4. Non-numeric marks
        with self.assertRaises(calculator.ValidationError) as ctx:
            calculator.validate_and_parse_csv("Student_ID,Name,Class,Math\n1,Alice,12-A,invalid")
        self.assertTrue(any("Invalid non-numeric" in err for err in ctx.exception.errors))

        # 5. Duplicate student IDs
        with self.assertRaises(calculator.ValidationError) as ctx:
            calculator.validate_and_parse_csv("Student_ID,Name,Class,Math\n1,Alice,12-A,80\n1,Bob,12-A,90")
        self.assertTrue(any("Duplicate Student ID" in err for err in ctx.exception.errors))

    def test_gpa_calculations_and_rules(self):
        """Test GPA, pass/fail rules, ranking, and remarks."""
        df = calculator.validate_and_parse_csv(self.sample_csv_path)
        res_10 = calculator.calculate_grades_and_analytics(df, scale_type="10.0")

        students = res_10["students"]
        # Top performer test
        top_student = students[0]
        self.assertEqual(top_student["rank"], 1)
        self.assertEqual(top_student["name"], "Eleanor Vance")
        self.assertEqual(top_student["grade"], "A+")
        self.assertEqual(top_student["gpa_10"], 10.0)
        self.assertEqual(top_student["status"], "Passed")

        # Single subject failure rule test (Ethan Bennett: Physics is 32)
        ethan = next(s for s in students if s["student_id"] == "EVA-2025-010")
        self.assertEqual(ethan["status"], "Failed")
        self.assertIn("Physics", ethan["failed_subjects"])
        self.assertIn("Remediation required", ethan["remarks"])

        # Scale 4.0 test
        res_4 = calculator.calculate_grades_and_analytics(df, scale_type="4.0")
        top_student_4 = res_4["students"][0]
        self.assertEqual(top_student_4["gpa_4"], 4.0)
        self.assertGreater(res_4["analytics"]["avg_gpa_4"], 2.0)

    def test_pdf_generation(self):
        """Test single vector A4 PDF generation and batch ZIP archiving."""
        df = calculator.validate_and_parse_csv(self.sample_csv_path)
        res = calculator.calculate_grades_and_analytics(df, scale_type="10.0")

        # Single student PDF
        pdf_bytes = pdf_generator.create_student_report_card_pdf(res["students"][0], scale_type="10.0")
        self.assertGreater(len(pdf_bytes), 1000)
        # Verify it's a valid 1-page PDF
        pdf_doc = pypdfium2.PdfDocument(pdf_bytes)
        self.assertEqual(len(pdf_doc), 1)

        # Batch ZIP archive
        zip_bytes = pdf_generator.generate_batch_pdf_zip(res["students"], scale_type="10.0")
        self.assertGreater(len(zip_bytes), 10000)

    def test_excel_export(self):
        """Test openpyxl two-sheet Excel generation."""
        df = calculator.validate_and_parse_csv(self.sample_csv_path)
        res = calculator.calculate_grades_and_analytics(df, scale_type="10.0")

        excel_bytes = excel_exporter.create_excel_summary_workbook(res, scale_type="10.0")
        self.assertGreater(len(excel_bytes), 3000)

        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
        self.assertIn("Results Summary", wb.sheetnames)
        self.assertIn("Class Analytics", wb.sheetnames)

        ws1 = wb["Results Summary"]
        # Header row 4
        headers = [c.value for c in ws1[4]]
        self.assertIn("Rank", headers)
        self.assertIn("Student ID", headers)
        self.assertIn("Percentage", headers)
        self.assertIn("Total Credits", headers)
        self.assertIn("Weighted GPA (10.0)", headers)

        ws2 = wb["Class Analytics"]
        self.assertEqual(ws2["A4"].value, "Performance Metric")

    def test_credit_weighted_gpa_calculation(self):
        """Test calculation of credit-weighted GPA."""
        csv_data = (
            "Student_ID,Name,Class,Math,Physics\n"
            "S01,Alice,Grade 10,95,55\n"
        )
        df = calculator.validate_and_parse_csv(csv_data)

        # Alice:
        # Math: 95 -> A+ -> GP10=10.0, GP4=4.0
        # Physics: 55 -> C -> GP10=6.0, GP4=2.0
        #
        # If Math has 4 credits and Physics has 1 credit:
        # Weighted GP10 = (10.0*4 + 6.0*1) / (4+1) = 46.0 / 5 = 9.20
        # Weighted GP4  = (4.0*4 + 2.0*1) / (4+1)  = 18.0 / 5 = 3.60
        res = calculator.calculate_grades_and_analytics(
            df, scale_type="10.0", subject_credits={"Math": 4.0, "Physics": 1.0}
        )
        student = res["students"][0]
        self.assertEqual(student["total_credits"], 5.0)
        self.assertAlmostEqual(student["gpa_10"], 9.20, places=2)
        self.assertAlmostEqual(student["gpa_4"], 3.60, places=2)

    def test_flask_endpoints(self):
        """Test all web endpoints."""
        # 1. Dashboard page
        res = self.app.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Evalia", res.data)

        # 2. Download sample CSV
        res = self.app.get("/download/sample-csv")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Student_ID,Name,Class", res.data)
        res.close()

        # 3. Load sample cohort API
        res = self.app.get("/api/sample?scale=10.0")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["analytics"]["total_students"], 12)
        self.assertIn("subject_credits", data["data"])

        # 4. Upload CSV endpoint
        with open(self.sample_csv_path, "rb") as f:
            res = self.app.post(
                "/api/upload",
                data={"file": (io.BytesIO(f.read()), "test_upload.csv"), "scale": "10.0"},
                content_type="multipart/form-data"
            )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        # 5. Update Credits API
        res = self.app.post("/api/update-credits", json={
            "credits": {
                "Mathematics": 4.0,
                "Physics": 4.0,
                "Chemistry": 3.0,
                "English": 2.0,
                "Computer_Science": 4.0
            }
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["total_credits"], 17.0)

        # 6. Switch scale API
        res = self.app.post("/api/switch-scale", json={"scale": "4.0"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["scale_type"], "4.0")

        # 7. Single PDF endpoint
        res = self.app.get("/api/pdf/EVA-2025-001?scale=10.0")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("Content-Type"), "application/pdf")
        res.close()

        # 8. Batch PDF ZIP endpoint
        res = self.app.get("/api/download-all-pdfs?scale=10.0")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("Content-Type"), "application/zip")
        res.close()

        # 9. Excel export endpoint
        res = self.app.get("/api/export-excel?scale=10.0")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/vnd.openxmlformats", res.headers.get("Content-Type"))
        res.close()


if __name__ == "__main__":
    unittest.main()
