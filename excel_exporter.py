"""
Evalia - Consolidated Excel Summary Exporter
Generates a formatted, publication-grade multi-sheet Excel workbook (.xlsx) using openpyxl.
Adheres strictly to design.md standards with subtle styling, auto column widths,
frozen panes, and comprehensive class analytics.
"""

import io
from datetime import datetime
from typing import Dict, Any, List

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# Styling Tokens matching design.md
COLOR_INK_HEX = "0C0A09"
COLOR_PRIMARY_HEX = "292524"
COLOR_HEADER_BG = "292524"
COLOR_HEADER_TEXT = "FFFFFF"
COLOR_SUBTLE_BG = "F5F5F5"
COLOR_ZEBRA_BG = "FAFAFA"
COLOR_WHITE_BG = "FFFFFF"
COLOR_BORDER = "D6D3D1"
COLOR_PASS_BG = "EAF7EE"
COLOR_PASS_TEXT = "137333"
COLOR_FAIL_BG = "FDECEA"
COLOR_FAIL_TEXT = "C5221F"
COLOR_SECTION_HEADER_BG = "E7E5E4"

FONT_FAMILY = "Segoe UI"


def get_thin_border() -> Border:
    thin_side = Side(border_style="thin", color=COLOR_BORDER)
    return Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)


def create_excel_summary_workbook(
    data: Dict[str, Any],
    scale_type: str = "10.0",
    academic_session: str = "2025–2026"
) -> bytes:
    """
    Generate a 2-sheet formatted Excel workbook:
    - Sheet 1: Results Summary (student roster with subjects, totals, ranks, status)
    - Sheet 2: Class Analytics (executive metrics, grade distribution, subject performance)
    Returns bytes of the .xlsx file.
    """
    wb = openpyxl.Workbook()
    students: List[Dict[str, Any]] = data["students"]
    analytics: Dict[str, Any] = data["analytics"]
    subject_cols: List[str] = data["subject_columns"]

    thin_border = get_thin_border()

    # =========================================================================
    # SHEET 1: RESULTS SUMMARY
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Results Summary"
    ws1.views.sheetView[0].showGridLines = True

    active_credits = data.get("subject_credits", {})
    headers = ["Rank", "Student ID", "Student Name", "Class"]
    for sc in subject_cols:
        cr_val = active_credits.get(sc, 4.0)
        headers.append(f"{sc} ({cr_val:g} Cr)")
    gpa_header = f"Weighted GPA ({scale_type})"
    headers.extend(["Total Marks", "Max Marks", "Total Credits", "Percentage", gpa_header, "Grade", "Status", "Academic Remarks"])
    last_col_idx = len(headers)
    last_col_letter = get_column_letter(last_col_idx)

    # 1. Document Title Banner
    ws1.merge_cells(f"A1:{last_col_letter}1")
    title_cell = ws1["A1"]
    title_cell.value = "EVALIA — OFFICIAL ACADEMIC PERFORMANCE SUMMARY"
    title_cell.font = Font(name=FONT_FAMILY, size=14, bold=True, color=COLOR_HEADER_TEXT)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 34
    fill_primary = PatternFill(start_color=COLOR_PRIMARY_HEX, end_color=COLOR_PRIMARY_HEX, fill_type="solid")
    for c in range(1, last_col_idx + 1):
        ws1.cell(row=1, column=c).fill = fill_primary

    # 2. Metadata Sub-banner
    doc_date = datetime.now().strftime("%B %d, %Y")
    ws1.merge_cells(f"A2:{last_col_letter}2")
    sub_cell = ws1["A2"]
    sub_cell.value = (
        f"Session: {academic_session}  |  Grading Scale: {scale_type} Scale  |  "
        f"Enrolled Students: {analytics['total_students']}  |  "
        f"Pass Rate: {analytics['pass_rate']}%  |  Generated: {doc_date}"
    )
    sub_cell.font = Font(name=FONT_FAMILY, size=9.5, italic=True, color=COLOR_HEADER_TEXT)
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 20
    fill_sub = PatternFill(start_color="3F3B39", end_color="3F3B39", fill_type="solid")
    for c in range(1, last_col_idx + 1):
        ws1.cell(row=2, column=c).fill = fill_sub

    # 3. Table Headers (Row 4)
    ws1.row_dimensions[3].height = 10  # Spacing row

    ws1.row_dimensions[4].height = 26
    for col_idx, header_title in enumerate(headers, start=1):
        cell = ws1.cell(row=4, column=col_idx, value=header_title)
        cell.font = Font(name=FONT_FAMILY, size=10, bold=True, color=COLOR_HEADER_TEXT)
        cell.fill = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    # Freeze header rows so scrolling keeps table header visible
    ws1.freeze_panes = "A5"

    # 4. Data Rows
    current_row = 5
    for s_idx, student in enumerate(students):
        ws1.row_dimensions[current_row].height = 20
        row_bg = COLOR_WHITE_BG if s_idx % 2 == 0 else COLOR_ZEBRA_BG
        row_fill = PatternFill(start_color=row_bg, end_color=row_bg, fill_type="solid")

        gpa_val = student["gpa_10"] if scale_type == "10.0" else student["gpa_4"]
        is_pass = student["status"] == "Passed"

        # Map row values
        row_values = [
            student["rank"],
            student["student_id"],
            student["name"],
            student["class_name"]
        ]

        # Subject marks
        subj_map = {sub["subject"]: sub["marks_obtained"] for sub in student["subjects"]}
        for sc in subject_cols:
            row_values.append(subj_map.get(sc, 0.0))

        row_values.extend([
            student["total_marks"],
            student["max_marks"],
            student.get("total_credits", 0.0),
            student["percentage"] / 100.0,  # For percentage number format
            gpa_val,
            student["grade"],
            student["status"].upper(),
            student["remarks"]
        ])

        for col_idx, val in enumerate(row_values, start=1):
            cell = ws1.cell(row=current_row, column=col_idx, value=val)
            cell.font = Font(name=FONT_FAMILY, size=9.5)
            cell.fill = row_fill
            cell.border = thin_border

            # Number formatting and alignment
            col_name = headers[col_idx - 1]
            if col_name == "Rank":
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_name in ("Student ID", "Class", "Grade"):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_name == "Student Name":
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif any(col_name.startswith(f"{sc} (") for sc in subject_cols) or col_name in ("Total Marks", "Max Marks", "Total Credits"):
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "#,##0.0" if isinstance(val, float) else "#,##0"
            elif col_name == "Percentage":
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "0.00%"
            elif col_name == gpa_header:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = "0.00"
            elif col_name == "Status":
                cell.alignment = Alignment(horizontal="center", vertical="center")
                status_bg = COLOR_PASS_BG if is_pass else COLOR_FAIL_BG
                status_text = COLOR_PASS_TEXT if is_pass else COLOR_FAIL_TEXT
                cell.fill = PatternFill(start_color=status_bg, end_color=status_bg, fill_type="solid")
                cell.font = Font(name=FONT_FAMILY, size=9.5, bold=True, color=status_text)
            elif col_name == "Academic Remarks":
                cell.alignment = Alignment(horizontal="left", vertical="center")

        current_row += 1

    # Auto-adjust column widths for Sheet 1
    for col in ws1.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            # Skip merged banner row 1 and 2 in length calculation
            if cell.row in (1, 2, 3):
                continue
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        # Apply padding and bounds
        adjusted_width = max(max_len + 3, 11)
        if col_letter == "C":  # Student Name
            adjusted_width = max(adjusted_width, 22)
        elif col_letter == get_column_letter(len(headers)):  # Remarks
            adjusted_width = min(max(adjusted_width, 35), 65)
        ws1.column_dimensions[col_letter].width = adjusted_width

    # =========================================================================
    # SHEET 2: CLASS ANALYTICS
    # =========================================================================
    ws2 = wb.create_sheet(title="Class Analytics")
    ws2.views.sheetView[0].showGridLines = True

    # Title Banner (6 columns: A through F)
    ws2.merge_cells("A1:F1")
    a_title = ws2["A1"]
    a_title.value = "EVALIA — CLASS ACADEMIC ANALYTICS & INSIGHTS"
    a_title.font = Font(name=FONT_FAMILY, size=13, bold=True, color=COLOR_HEADER_TEXT)
    a_title.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 32
    fill_a_title = PatternFill(start_color=COLOR_PRIMARY_HEX, end_color=COLOR_PRIMARY_HEX, fill_type="solid")
    for c in range(1, 7):
        ws2.cell(row=1, column=c).fill = fill_a_title

    # Section 1: Executive KPI Metrics
    ws2.cell(row=3, column=1, value="1. EXECUTIVE COHORT METRICS").font = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_PRIMARY_HEX)

    kpi_headers = ["Performance Metric", "Cohort Value", "Benchmark Status"]
    for c_idx, h in enumerate(kpi_headers, start=1):
        cell = ws2.cell(row=4, column=c_idx, value=h)
        cell.font = Font(name=FONT_FAMILY, size=9.5, bold=True, color=COLOR_HEADER_TEXT)
        cell.fill = PatternFill(start_color=COLOR_PRIMARY_HEX, end_color=COLOR_PRIMARY_HEX, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws2.row_dimensions[4].height = 22

    active_avg_gpa = analytics["avg_gpa_10"] if scale_type == "10.0" else analytics["avg_gpa_4"]
    max_scale_gpa = "10.00" if scale_type == "10.0" else "4.00"

    kpis = [
        ("Total Students Enrolled", analytics["total_students"], "Official Cohort Roster"),
        ("Students Successfully Passed", analytics["passed_count"], f"{analytics['pass_rate']}% of cohort"),
        ("Students Requiring Remediation", analytics["failed_count"], f"{100.0 - analytics['pass_rate']:.2f}% of cohort"),
        ("Overall Cohort Pass Rate", f"{analytics['pass_rate']:.2f}%", "Institutional Target: >= 75%"),
        ("Total Curriculum Credits", f"{data.get('total_credits', 0.0):.1f}", "Cumulative Degree / Term Credits"),
        ("Class Mean Percentage", f"{analytics['class_average']:.2f}%", "Overall Average"),
        ("Highest Class Percentage", f"{analytics['highest_percentage']:.2f}%", f"Top Performer: {analytics['top_performer']}"),
        ("Lowest Class Percentage", f"{analytics['lowest_percentage']:.2f}%", "Minimum Recorded Score"),
        (f"Class Mean GPA ({scale_type})", f"{active_avg_gpa:.2f} / {max_scale_gpa}", "Cumulative GPA Average"),
    ]

    for idx, (metric, val, note) in enumerate(kpis, start=5):
        ws2.row_dimensions[idx].height = 19
        row_fill = PatternFill(start_color=COLOR_WHITE_BG if idx % 2 == 1 else COLOR_ZEBRA_BG, end_color=COLOR_WHITE_BG, fill_type="solid")

        c1 = ws2.cell(row=idx, column=1, value=metric)
        c2 = ws2.cell(row=idx, column=2, value=str(val))
        c3 = ws2.cell(row=idx, column=3, value=note)

        c1.alignment = Alignment(horizontal="left", vertical="center")
        c2.alignment = Alignment(horizontal="right", vertical="center")
        c3.alignment = Alignment(horizontal="left", vertical="center")

        for c in (c1, c2, c3):
            c.font = Font(name=FONT_FAMILY, size=9.5)
            c.fill = row_fill
            c.border = thin_border

    # Section 2: Grade Distribution Table
    sec2_start = len(kpis) + 7
    ws2.cell(row=sec2_start, column=1, value="2. GRADE BOUNDARY DISTRIBUTION").font = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_PRIMARY_HEX)

    dist_headers = ["Letter Grade", "Percentage Range", "Student Count", "Cohort Share (%)", f"Grade Point ({scale_type})"]
    for c_idx, h in enumerate(dist_headers, start=1):
        cell = ws2.cell(row=sec2_start + 1, column=c_idx, value=h)
        cell.font = Font(name=FONT_FAMILY, size=9.5, bold=True, color=COLOR_HEADER_TEXT)
        cell.fill = PatternFill(start_color=COLOR_PRIMARY_HEX, end_color=COLOR_PRIMARY_HEX, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws2.row_dimensions[sec2_start + 1].height = 22

    for d_idx, item in enumerate(analytics["grade_distribution"], start=sec2_start + 2):
        ws2.row_dimensions[d_idx].height = 19
        row_fill = PatternFill(start_color=COLOR_WHITE_BG if d_idx % 2 == 1 else COLOR_ZEBRA_BG, end_color=COLOR_WHITE_BG, fill_type="solid")
        gp = item["points_10"] if scale_type == "10.0" else item["points_4"]

        row_vals = [
            item["grade"],
            f"{int(item['min_score'])}% – {int(item['max_score'])}%",
            item["count"],
            f"{item['percentage']:.1f}%",
            f"{gp:.1f}"
        ]

        for c_idx, val in enumerate(row_vals, start=1):
            cell = ws2.cell(row=d_idx, column=c_idx, value=val)
            cell.font = Font(name=FONT_FAMILY, size=9.5)
            cell.fill = row_fill
            cell.border = thin_border
            if c_idx in (1, 2):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")

    # Section 3: Subject-wise Performance Analytics
    sec3_start = sec2_start + len(analytics["grade_distribution"]) + 3
    ws2.cell(row=sec3_start, column=1, value="3. SUBJECT-WISE CURRICULUM PERFORMANCE").font = Font(name=FONT_FAMILY, size=11, bold=True, color=COLOR_PRIMARY_HEX)

    subj_headers = ["Subject Course", "Credit Hours", "Cohort Mean", "Highest Mark", "Lowest Mark", "Course Pass Rate (%)"]
    for c_idx, h in enumerate(subj_headers, start=1):
        cell = ws2.cell(row=sec3_start + 1, column=c_idx, value=h)
        cell.font = Font(name=FONT_FAMILY, size=9.5, bold=True, color=COLOR_HEADER_TEXT)
        cell.fill = PatternFill(start_color=COLOR_PRIMARY_HEX, end_color=COLOR_PRIMARY_HEX, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws2.row_dimensions[sec3_start + 1].height = 22

    for s_idx, item in enumerate(analytics["subject_analytics"], start=sec3_start + 2):
        ws2.row_dimensions[s_idx].height = 19
        row_fill = PatternFill(start_color=COLOR_WHITE_BG if s_idx % 2 == 1 else COLOR_ZEBRA_BG, end_color=COLOR_WHITE_BG, fill_type="solid")

        row_vals = [
            item["subject"],
            f"{item.get('credits', 4.0):.1f}",
            f"{item['mean']:.1f}",
            f"{item['max']:.1f}",
            f"{item['min']:.1f}",
            f"{item['pass_rate']:.1f}%"
        ]

        for c_idx, val in enumerate(row_vals, start=1):
            cell = ws2.cell(row=s_idx, column=c_idx, value=val)
            cell.font = Font(name=FONT_FAMILY, size=9.5)
            cell.fill = row_fill
            cell.border = thin_border
            if c_idx == 1:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif c_idx == 2:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")

    # Auto-adjust column widths for Sheet 2
    for col in ws2.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row in (1, 2):
                continue
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws2.column_dimensions[col_letter].width = max(max_len + 4, 15)

    out_buffer = io.BytesIO()
    wb.save(out_buffer)
    out_buffer.seek(0)
    return out_buffer.getvalue()
