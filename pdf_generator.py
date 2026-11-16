"""
Evalia - Vector A4 PDF Report Card Generator
Generates formal, print-ready A4 academic transcripts adhering strictly to design.md.
Includes institutional branding, student metadata, ruled subject breakdown,
academic remarks, and formal signature lines.
"""

import io
import os
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, String, Group, Circle, Line


# Design System Colors from design.md
COLOR_INK = colors.HexColor("#0C0A09")           # Deep ink
COLOR_PRIMARY = colors.HexColor("#292524")       # Warm near-black
COLOR_BODY = colors.HexColor("#4E4E4E")          # Body text
COLOR_MUTED = colors.HexColor("#777169")         # Muted labels
COLOR_HAIRLINE = colors.HexColor("#E7E5E4")      # 1px border
COLOR_HAIRLINE_STRONG = colors.HexColor("#D6D3D1")
COLOR_CANVAS_SOFT = colors.HexColor("#FAFAFA")   # Soft alternating rows
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_SUCCESS = colors.HexColor("#16A34A")       # Pass badge
COLOR_SUCCESS_BG = colors.HexColor("#F0FDF4")
COLOR_ERROR = colors.HexColor("#DC2626")         # Fail badge
COLOR_ERROR_BG = colors.HexColor("#FEF2F2")
COLOR_BADGE_BG = colors.HexColor("#F0EFED")


def build_institutional_crest() -> Drawing:
    """
    Draw a clean, minimalist vector institutional seal for Evalia.
    Restrained geometric crest with circular framing and monogram.
    """
    d = Drawing(46, 46)
    # Outer circle
    d.add(Circle(23, 23, 22, fillColor=None, strokeColor=COLOR_PRIMARY, strokeWidth=1.2))
    # Inner circle
    d.add(Circle(23, 23, 19, fillColor=COLOR_PRIMARY, strokeColor=None))
    # Monogram 'E' in white
    d.add(String(16, 16, "E", fontName="Helvetica-Bold", fontSize=18, fillColor=COLOR_WHITE))
    return d


def create_student_report_card_pdf(
    student: Dict[str, Any],
    scale_type: str = "10.0",
    academic_session: str = "2025–2026",
    output_target: Optional[Any] = None
) -> bytes:
    """
    Generate an individual vector A4 academic transcript for a single student.
    Returns bytes if output_target is None, otherwise writes to output_target.
    """
    buffer = io.BytesIO() if output_target is None else output_target

    # Page setup: Standard A4 (595.27 x 841.89 points) with 36pt (0.5 inch) margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=38,
        rightMargin=38,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_inst_title = ParagraphStyle(
        "InstTitle",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=COLOR_PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=1
    )
    style_inst_sub = ParagraphStyle(
        "InstSub",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=COLOR_MUTED,
        alignment=TA_LEFT
    )
    style_doc_title = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=COLOR_PRIMARY,
        alignment=TA_RIGHT
    )
    style_doc_meta = ParagraphStyle(
        "DocMeta",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=COLOR_MUTED,
        alignment=TA_RIGHT
    )
    style_meta_label = ParagraphStyle(
        "MetaLabel",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=COLOR_MUTED
    )
    style_meta_val = ParagraphStyle(
        "MetaVal",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=COLOR_PRIMARY
    )
    style_th = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_WHITE,
        alignment=TA_CENTER
    )
    style_th_left = ParagraphStyle(
        "TableHeaderLeft",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_WHITE,
        alignment=TA_LEFT
    )
    style_td = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=COLOR_INK,
        alignment=TA_CENTER
    )
    style_td_left = ParagraphStyle(
        "TableCellLeft",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=COLOR_INK,
        alignment=TA_LEFT
    )
    style_td_bold = ParagraphStyle(
        "TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_INK,
        alignment=TA_CENTER
    )
    style_remarks_head = ParagraphStyle(
        "RemarksHead",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_PRIMARY
    )
    style_remarks_body = ParagraphStyle(
        "RemarksBody",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=COLOR_BODY,
        alignment=TA_LEFT
    )
    style_footnote = ParagraphStyle(
        "Footnote",
        fontName="Helvetica",
        fontSize=6.5,
        leading=8.5,
        textColor=COLOR_MUTED,
        alignment=TA_CENTER
    )

    story = []

    # 1. Header Bar: Institutional Crest + Title + Document Verification Details
    crest = build_institutional_crest()
    header_text = [
        Paragraph("EVALIA ACADEMIC ASSESSMENT SYSTEM", style_inst_title),
        Paragraph("Institutional Board of Secondary and Senior Secondary Examinations", style_inst_sub),
        Paragraph(f"Academic Evaluation Record • Session {academic_session}", style_inst_sub)
    ]

    doc_date = datetime.now().strftime("%B %d, %Y")
    transcript_id = f"EVA-TR-{student['student_id'].replace('-', '')}"
    doc_meta_text = [
        Paragraph("OFFICIAL ACADEMIC TRANSCRIPT", style_doc_title),
        Paragraph(f"Transcript ID: {transcript_id}", style_doc_meta),
        Paragraph(f"Issuance Date: {doc_date}", style_doc_meta),
        Paragraph("Status: Certified Official Copy", style_doc_meta)
    ]

    header_table = Table(
        [
            [crest, header_text, doc_meta_text]
        ],
        colWidths=[52, 290, 177]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # Decorative Hairline
    story.append(HRFlowable(
        width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=8
    ))

    # 2. Student Profile & Academic Standing (Structured Box)
    gpa_val = student["gpa_10"] if scale_type == "10.0" else student["gpa_4"]
    gpa_max = "10.00" if scale_type == "10.0" else "4.00"
    tot_credits = student.get("total_credits", sum(s.get("credits", 4.0) for s in student["subjects"]))

    is_passed = student["status"] == "Passed"
    status_color = COLOR_SUCCESS if is_passed else COLOR_ERROR

    metadata_data = [
        [
            Paragraph("STUDENT NAME", style_meta_label),
            Paragraph(student["name"].upper(), style_meta_val),
            Paragraph("CLASS & SECTION", style_meta_label),
            Paragraph(student["class_name"], style_meta_val)
        ],
        [
            Paragraph("STUDENT ID", style_meta_label),
            Paragraph(student["student_id"], style_meta_val),
            Paragraph("EXAMINATION TERM", style_meta_label),
            Paragraph(f"Annual Final ({academic_session})", style_meta_val)
        ],
        [
            Paragraph("OVERALL PERCENTAGE", style_meta_label),
            Paragraph(f"{student['percentage']:.2f}%", style_meta_val),
            Paragraph(f"WEIGHTED GPA ({scale_type})", style_meta_label),
            Paragraph(f"{gpa_val:.2f} / {gpa_max}  ({tot_credits:.0f} Total Credits)", style_meta_val)
        ],
        [
            Paragraph("COHORT CLASS RANK", style_meta_label),
            Paragraph(f"Rank #{student['rank']}", style_meta_val),
            Paragraph("EXAMINATION RESULT", style_meta_label),
            Paragraph(
                f"<font color='{status_color.hexval()}'><b>{student['status'].upper()}</b></font>",
                style_meta_val
            )
        ]
    ]

    meta_table = Table(
        metadata_data,
        colWidths=[120, 140, 125, 134]
    )
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_CANVAS_SOFT),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_HAIRLINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_HAIRLINE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. Subject-wise Marks Table with Credits
    gpa_col_header = "Grade Pt"
    table_rows = [
        [
            Paragraph("Subject Course", style_th_left),
            Paragraph("Credits", style_th),
            Paragraph("Max Marks", style_th),
            Paragraph("Marks Obtained", style_th),
            Paragraph("Percentage", style_th),
            Paragraph("Letter Grade", style_th),
            Paragraph(gpa_col_header, style_th),
            Paragraph("Credit Pts", style_th),
            Paragraph("Status", style_th),
        ]
    ]

    for subj in student["subjects"]:
        pts = subj["points_10"] if scale_type == "10.0" else subj["points_4"]
        cred = subj.get("credits", 4.0)
        cred_pts = subj.get("credit_points_10", round(pts * cred, 2)) if scale_type == "10.0" else subj.get("credit_points_4", round(pts * cred, 2))
        subj_pass = subj["status"] == "Passed"
        subj_status_color = COLOR_SUCCESS if subj_pass else COLOR_ERROR

        table_rows.append([
            Paragraph(subj["subject"], style_td_left),
            Paragraph(f"{cred:.1f}", style_td),
            Paragraph(str(subj["max_marks"]), style_td),
            Paragraph(f"{subj['marks_obtained']:.1f}", style_td_bold),
            Paragraph(f"{subj['percentage']:.1f}%", style_td),
            Paragraph(subj["grade"], style_td_bold),
            Paragraph(f"{pts:.1f}", style_td),
            Paragraph(f"{cred_pts:.1f}", style_td_bold),
            Paragraph(
                f"<font color='{subj_status_color.hexval()}'><b>{subj['status'].upper()}</b></font>",
                style_td
            )
        ])

    # Totals Row
    tot_cred_pts = sum(
        (s.get("credit_points_10", s["points_10"] * s.get("credits", 4.0)) if scale_type == "10.0" 
         else s.get("credit_points_4", s["points_4"] * s.get("credits", 4.0)))
        for s in student["subjects"]
    )
    table_rows.append([
        Paragraph("<b>CUMULATIVE TOTALS</b>", style_td_left),
        Paragraph(f"<b>{tot_credits:.1f}</b>", style_td_bold),
        Paragraph(f"<b>{student['max_marks']}</b>", style_td),
        Paragraph(f"<b>{student['total_marks']:.1f}</b>", style_td_bold),
        Paragraph(f"<b>{student['percentage']:.2f}%</b>", style_td_bold),
        Paragraph(f"<b>{student['grade']}</b>", style_td_bold),
        Paragraph(f"<b>{gpa_val:.2f}</b>", style_td_bold),
        Paragraph(f"<b>{tot_cred_pts:.1f}</b>", style_td_bold),
        Paragraph(
            f"<font color='{status_color.hexval()}'><b>{student['status'].upper()}</b></font>",
            style_td
        )
    ])

    marks_table = Table(
        table_rows,
        colWidths=[135, 44, 50, 62, 50, 44, 48, 46, 40]
    )

    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_HAIRLINE),
        ('BACKGROUND', (0, -1), (-1, -1), COLOR_CANVAS_SOFT),
        ('LINEABOVE', (0, -1), (-1, -1), 1, COLOR_PRIMARY),
    ]

    # Alternating row background for readability
    for r_idx in range(1, len(table_rows) - 1):
        bg = COLOR_WHITE if r_idx % 2 == 1 else COLOR_CANVAS_SOFT
        t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))

    marks_table.setStyle(TableStyle(t_style))
    story.append(marks_table)
    story.append(Spacer(1, 10))

    # 4. Grading Scheme & Academic Summary Cards (2-Column Layout)
    # Left: Grade Scale Legend
    scheme_text = (
        "<b>Institutional Grade Boundary Key:</b><br/>"
        "A+ (90–100%): Outstanding | A (80–89%): Excellent | B+ (70–79%): Very Good<br/>"
        "B (60–69%): Good | C (50–59%): Satisfactory | D (40–49%): Marginal Pass | F (&lt;40%): Failing<br/>"
        "<i>*Criterion: Min 40% per subject. Weighted GPA (SGPA) = &Sigma;(Grade Pts &times; Credits) / &Sigma;(Credits).</i>"
    )
    style_legend = ParagraphStyle(
        "LegendStyle",
        fontName="Helvetica",
        fontSize=6.8,
        leading=9.2,
        textColor=COLOR_BODY
    )

    summary_left_p = Paragraph(scheme_text, style_legend)

    # Right: Institutional Academic Remarks
    remarks_content = [
        Paragraph("<b>Institutional Evaluation & Remarks:</b>", style_remarks_head),
        Spacer(1, 2),
        Paragraph(student["remarks"], style_remarks_body)
    ]

    analytics_table = Table(
        [
            [summary_left_p, remarks_content]
        ],
        colWidths=[245, 274]
    )
    analytics_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_HAIRLINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_HAIRLINE),
        ('BACKGROUND', (0, 0), (0, 0), COLOR_CANVAS_SOFT),
        ('BACKGROUND', (1, 0), (1, 0), COLOR_WHITE),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(analytics_table)
    story.append(Spacer(1, 14))

    # 5. Formal Authentication & Signature Block
    sig_line_data = [
        [
            Paragraph("_______________________________<br/><b>Class Teacher</b><br/><font size='6.5' color='#777169'>Faculty Signature</font>", style_td),
            Paragraph("_______________________________<br/><b>Controller of Examinations</b><br/><font size='6.5' color='#777169'>Academic Evaluation Wing</font>", style_td),
            Paragraph("_______________________________<br/><b>Principal / Head of Institution</b><br/><font size='6.5' color='#777169'>Institutional Seal & Signature</font>", style_td)
        ]
    ]
    sig_table = Table(
        sig_line_data,
        colWidths=[173, 173, 173]
    )
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(KeepTogether(sig_table))
    story.append(Spacer(1, 10))

    # 6. Security & Legal Notice Footer
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=COLOR_HAIRLINE_STRONG, spaceBefore=0, spaceAfter=4
    ))
    footer_text = (
        "CONFIDENTIAL & OFFICIAL: This academic transcript is generated by Evalia Assessment Systems. "
        "Any unauthorized alteration, erasure, or duplication renders this document null and void. "
        f"Verified electronic copy issued on {doc_date}."
    )
    story.append(Paragraph(footer_text, style_footnote))

    # Build the PDF document
    doc.build(story)

    if output_target is None:
        buffer.seek(0)
        return buffer.getvalue()
    return b""


def generate_batch_pdf_zip(
    students: List[Dict[str, Any]],
    scale_type: str = "10.0",
    academic_session: str = "2025–2026"
) -> bytes:
    """
    Generate report card PDFs for all students and bundle them into a single in-memory ZIP archive.
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for student in students:
            pdf_bytes = create_student_report_card_pdf(
                student=student,
                scale_type=scale_type,
                academic_session=academic_session
            )
            # Clean filename: Evalia_Report_Card_STU001_John_Doe.pdf
            clean_name = "".join(c if c.isalnum() else "_" for c in student["name"]).strip("_")
            clean_id = "".join(c if c.isalnum() else "_" for c in student["student_id"]).strip("_")
            filename = f"Evalia_Report_Card_{clean_id}_{clean_name}.pdf"

            zip_file.writestr(filename, pdf_bytes)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()
