"""
Evalia - Automated Student Grade Calculation Engine
Handles CSV ingestion, data validation, grade-boundary evaluation,
GPA calculations (10.0 and 4.0 scales), tie-aware ranking, and class analytics.
"""

import io
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd


class ValidationError(Exception):
    """Custom exception raised when CSV validation fails with plain-text explanation."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or [message]


# Grade boundaries and points mapping
GRADE_BOUNDARIES = [
    {"grade": "A+", "min": 90.0, "max": 100.0, "points_10": 10.0, "points_4": 4.0, "description": "Outstanding"},
    {"grade": "A",  "min": 80.0, "max": 89.999, "points_10": 9.0,  "points_4": 3.7, "description": "Excellent"},
    {"grade": "B+", "min": 70.0, "max": 79.999, "points_10": 8.0,  "points_4": 3.3, "description": "Very Good"},
    {"grade": "B",  "min": 60.0, "max": 69.999, "points_10": 7.0,  "points_4": 3.0, "description": "Good"},
    {"grade": "C",  "min": 50.0, "max": 59.999, "points_10": 6.0,  "points_4": 2.0, "description": "Satisfactory"},
    {"grade": "D",  "min": 40.0, "max": 49.999, "points_10": 5.0,  "points_4": 1.0, "description": "Marginal Pass"},
    {"grade": "F",  "min": 0.0,  "max": 39.999, "points_10": 0.0,  "points_4": 0.0, "description": "Failing"},
]

PASSING_THRESHOLD = 40.0


def score_to_grade_info(score: float) -> Dict[str, Any]:
    """
    Map a numeric score (0 to 100) to its corresponding letter grade,
    10.0 GPA points, and 4.0 GPA points.
    """
    score_clamped = max(0.0, min(100.0, float(score)))
    for boundary in GRADE_BOUNDARIES:
        if boundary["min"] <= score_clamped <= boundary["max"]:
            return {
                "grade": boundary["grade"],
                "points_10": boundary["points_10"],
                "points_4": boundary["points_4"],
                "description": boundary["description"]
            }
    # Fallback for boundary edge cases
    if score_clamped < 40.0:
        return {"grade": "F", "points_10": 0.0, "points_4": 0.0, "description": "Failing"}
    return {"grade": "A+", "points_10": 10.0, "points_4": 4.0, "description": "Outstanding"}


def normalize_column_name(col: str) -> str:
    """Normalize a header string for case-insensitive matching."""
    return str(col).strip().lower().replace(" ", "_").replace("-", "_")


# Known institutional metadata column names to exclude from academic course subjects
NON_SUBJECT_HEADER_ALIASES = {
    # Student Identifiers
    "student_id", "studentid", "student_no", "roll_no", "rollno", "id", 
    "admission_no", "reg_no", "registration_no", "enrollment_no", "enroll_no", 
    "usn", "seat_no", "uid", "hall_ticket_no", "ht_no",
    # Student Personal Info
    "name", "student_name", "full_name", "candidate_name", "first_name", "last_name",
    "gender", "sex", "dob", "date_of_birth", "email", "phone", "mobile", "contact", "contact_no",
    # Class / Cohort / Section / Academic Level
    "class", "grade", "section", "standard", "class_section", "class_grade", 
    "cohort", "batch", "division", "group",
    "year", "academic_year", "ay", "study_year", "current_year",
    "semester", "sem", "term", "trimester", "session", "academic_session",
    # Academic Program / Department / Institution
    "branch", "department", "dept", "stream", "program", "programme", 
    "course_name", "degree", "major", "specialization",
    "school", "college", "institution", "university", "campus", "faculty",
    # Index / Administrative
    "s_no", "sr_no", "sno", "sl_no", "serial_no", "index",
    # Pre-calculated summary or text columns if present
    "status", "result", "remarks", "remark", "grade_point", "cgpa", "sgpa", 
    "total", "total_marks", "percentage", "rank", "attendance"
}

META_KEYWORDS = {
    "sem", "semester", "year", "batch", "term", "section", "class", 
    "dept", "branch", "ay", "session", "trimester", "roll", "reg", "admission"
}


def is_metadata_column(col_name: str) -> bool:
    """Check if a column is non-subject metadata (e.g. Year, Semester, Section)."""
    norm = normalize_column_name(col_name)
    if norm in NON_SUBJECT_HEADER_ALIASES:
        return True
    parts = norm.split("_")
    if any(p in META_KEYWORDS for p in parts):
        return True
    return False


def identify_columns(df: pd.DataFrame) -> Tuple[str, str, str, List[str]]:
    """
    Detect metadata columns (Student_ID, Name, Class) and subject columns dynamically.
    Automatically filters out institutional metadata like Year, Semester, Section, etc.
    Returns: (id_col, name_col, class_col, subject_cols)
    """
    id_aliases = {
        "student_id", "studentid", "student_no", "roll_no", "rollno", "roll_number", "rollnumber", "roll_num",
        "id", "admission_no", "reg_no", "registration_no", "enrollment_no", "usn"
    }
    name_aliases = {"name", "student_name", "full_name", "candidate_name"}
    class_aliases = {
        "class", "grade", "grade_level", "cohort", "stream", "standard", "class_section", "class_grade",
        "branch", "department", "dept", "program", "programme", "degree", "course_name"
    }

    id_col = None
    name_col = None
    class_col = None

    for col in df.columns:
        norm = normalize_column_name(col)
        if not id_col and norm in id_aliases:
            id_col = col
        elif not name_col and norm in name_aliases:
            name_col = col
        elif not class_col and norm in class_aliases:
            class_col = col

    missing = []
    if not id_col:
        missing.append("Student_ID (or Roll_No / ID)")
    if not name_col:
        missing.append("Name (or Student_Name)")
    if not class_col:
        missing.append("Class (or Grade / Branch / Program)")

    if missing:
        raise ValidationError(
            f"Missing required metadata column(s): {', '.join(missing)}. "
            f"Detected columns were: {list(df.columns)}"
        )

    # Detect subject columns: exclude ID, Name, Class, and any other metadata columns (Year, Semester, etc.)
    base_meta = {id_col, name_col, class_col}
    subject_cols = [
        col for col in df.columns 
        if col not in base_meta and not is_metadata_column(col)
    ]

    if not subject_cols:
        raise ValidationError(
            "No academic subject columns detected. The CSV must contain at least one subject column "
            "with numerical marks (e.g. Mathematics, English, Physics)."
        )

    return id_col, name_col, class_col, subject_cols


def validate_and_parse_csv(file_stream_or_path: Any) -> pd.DataFrame:
    """
    Parse CSV content, perform strict schema and range validation, and return cleaned DataFrame.
    Supports file paths, raw CSV strings, bytes, and file-like objects (e.g. Flask FileStorage).
    """
    import os
    try:
        if isinstance(file_stream_or_path, str):
            if os.path.exists(file_stream_or_path):
                with open(file_stream_or_path, "r", encoding="utf-8") as f:
                    df = pd.read_csv(f, skipinitialspace=True)
            else:
                # String buffer of CSV content
                df = pd.read_csv(io.StringIO(file_stream_or_path), skipinitialspace=True)
        elif isinstance(file_stream_or_path, bytes):
            df = pd.read_csv(io.BytesIO(file_stream_or_path), skipinitialspace=True)
        elif hasattr(file_stream_or_path, "read"):
            # File-like object from web request
            content = file_stream_or_path.read()
            if isinstance(content, str):
                df = pd.read_csv(io.StringIO(content), skipinitialspace=True)
            else:
                df = pd.read_csv(io.BytesIO(content), skipinitialspace=True)
        else:
            df = pd.read_csv(file_stream_or_path, skipinitialspace=True)
    except Exception as e:
        raise ValidationError(f"Failed to parse CSV file: {str(e)}")

    if df.empty:
        raise ValidationError("The uploaded CSV file is empty. Please provide student records.")

    # Remove completely empty rows
    df = df.dropna(how="all").reset_index(drop=True)
    if df.empty:
        raise ValidationError("The uploaded CSV file contains only empty rows.")

    id_col, name_col, class_col, subject_cols = identify_columns(df)

    errors = []

    # Check for duplicate Student IDs
    id_series = df[id_col].astype(str).str.strip()
    duplicates = id_series[id_series.duplicated()].unique()
    if len(duplicates) > 0:
        dup_str = ", ".join(str(d) for d in duplicates[:5])
        errors.append(f"Duplicate Student ID entries found: {dup_str}")

    # Validate each row and subject score
    for row_idx, row in df.iterrows():
        student_identifier = str(row[id_col]).strip() if pd.notna(row[id_col]) else f"Row {row_idx + 1}"
        student_name = str(row[name_col]).strip() if pd.notna(row[name_col]) else "Unknown"

        if pd.isna(row[id_col]) or not str(row[id_col]).strip():
            errors.append(f"Row {row_idx + 1}: Student ID is empty.")

        if pd.isna(row[name_col]) or not str(row[name_col]).strip():
            errors.append(f"Row {row_idx + 1} ({student_identifier}): Student Name is empty.")

        for subject in subject_cols:
            val = row[subject]
            if pd.isna(val) or str(val).strip() == "":
                errors.append(
                    f"Row {row_idx + 1} ({student_name}, ID: {student_identifier}): "
                    f"Missing score for '{subject}'."
                )
                continue

            try:
                score = float(val)
            except (ValueError, TypeError):
                errors.append(
                    f"Row {row_idx + 1} ({student_name}, ID: {student_identifier}): "
                    f"Invalid non-numeric score '{val}' in subject '{subject}'."
                )
                continue

            if score < 0.0 or score > 100.0:
                errors.append(
                    f"Row {row_idx + 1} ({student_name}, ID: {student_identifier}): "
                    f"Score for '{subject}' must be between 0 and 100, found {score}."
                )

    if errors:
        raise ValidationError(
            f"CSV validation encountered {len(errors)} error(s).",
            errors=errors
        )

    return df


def generate_academic_remark(overall_pct: float, is_passed: bool, failed_subjects: List[str]) -> str:
    """
    Generate dignified, institutional academic remarks based on performance.
    """
    if not is_passed:
        if len(failed_subjects) == 1:
            return (
                f"Remediation required. Unsatisfactory performance in {failed_subjects[0]}. "
                "Institutional minimum competency threshold not achieved."
            )
        elif len(failed_subjects) == 2:
            return (
                f"Academic review required. Deficiencies noted in {failed_subjects[0]} and {failed_subjects[1]}. "
                "Subject-level re-examination mandated."
            )
        else:
            return (
                f"Academic intervention mandated. Critical deficiencies across {len(failed_subjects)} subjects. "
                "Comprehensive remedial program required."
            )

    # Passed cases
    if overall_pct >= 90.0:
        return "Distinguished academic standing. Demonstrates exceptional mastery of core competencies and institutional honors."
    elif overall_pct >= 80.0:
        return "Commendable academic achievement. Exhibits strong analytical proficiency and consistent excellence."
    elif overall_pct >= 70.0:
        return "Solid academic standing. Successfully fulfilled curricular objectives with notable subject consistency."
    elif overall_pct >= 60.0:
        return "Satisfactory academic performance. Meets institutional progression standards; targeted reinforcement recommended."
    elif overall_pct >= 50.0:
        return "Acceptable completion of academic term. Progression approved; strategic review advised in lower-scoring subjects."
    else:
        return "Marginal pass achieved. Meets minimum qualifying criteria; focused academic advisory recommended for subsequent terms."


def parse_subject_and_credit(header: str) -> Tuple[str, Optional[float]]:
    """Extract clean subject name and optional credit from headers like 'Python (4)' or 'DAA (4 Credits)'."""
    import re
    header_clean = header.strip()
    match = re.search(r"^(.*?)\s*[\(\[]\s*(\d+(?:\.\d+)?)\s*(?:cr|credits|credit|pts|points)?\s*[\)\]]$", header_clean, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        try:
            credit = float(match.group(2))
            return name, credit
        except ValueError:
            pass
    return header_clean, None


def calculate_grades_and_analytics(
    df: pd.DataFrame,
    scale_type: str = "10.0",
    subject_credits: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Compute comprehensive student results, credit-weighted GPAs, tie-aware ranks,
    per-subject breakdown, and class-level analytics.
    """
    id_col, name_col, class_col, subject_cols = identify_columns(df)

    # Detect extra metadata columns (Year, Semester, Section, etc.)
    extra_meta_cols = [
        c for c in df.columns 
        if c not in subject_cols and c not in {id_col, name_col, class_col}
    ]

    # Resolve course credit weights: use provided subject_credits, or header parsed credits, or default to 4.0
    active_credits: Dict[str, float] = {}
    for subj in subject_cols:
        if subject_credits and subj in subject_credits:
            try:
                active_credits[subj] = float(subject_credits[subj])
            except (ValueError, TypeError):
                active_credits[subj] = 4.0
        else:
            _, parsed_cr = parse_subject_and_credit(subj)
            active_credits[subj] = parsed_cr if parsed_cr is not None else 4.0

    total_curriculum_credits = sum(active_credits.values())

    students = []
    num_subjects = len(subject_cols)
    total_possible_marks = num_subjects * 100.0

    for _, row in df.iterrows():
        s_id = str(row[id_col]).strip()
        s_name = str(row[name_col]).strip()
        raw_class = str(row[class_col]).strip()

        extra_meta = {}
        for mc in extra_meta_cols:
            val = row[mc]
            if pd.notna(val) and str(val).strip():
                extra_meta[mc] = str(val).strip()

        meta_tags = []
        y_val = next((extra_meta[k] for k in extra_meta if normalize_column_name(k) in {"year", "academic_year", "study_year"}), None)
        sem_val = next((extra_meta[k] for k in extra_meta if normalize_column_name(k) in {"semester", "sem", "term", "trimester", "term_semester", "semester_term", "academic_term"}), None)
        sec_val = next((extra_meta[k] for k in extra_meta if normalize_column_name(k) in {"section", "sec"}), None)

        if y_val and f"year {y_val}" not in raw_class.lower() and f"y{y_val}" not in raw_class.lower():
            meta_tags.append(f"Year {y_val}")
        if sem_val and f"sem {sem_val}" not in raw_class.lower() and f"semester {sem_val}" not in raw_class.lower():
            meta_tags.append(f"Sem {sem_val}")
        if sec_val and f"sec {sec_val}" not in raw_class.lower() and f"section {sec_val}" not in raw_class.lower():
            meta_tags.append(f"Sec {sec_val}")

        display_class = f"{raw_class} ({', '.join(meta_tags)})" if meta_tags else raw_class

        subjects_data = []
        total_obtained = 0.0
        failed_subjects = []
        total_credit_points_10 = 0.0
        total_credit_points_4 = 0.0
        total_student_credits = 0.0

        for subj in subject_cols:
            score = float(row[subj])
            total_obtained += score
            grade_info = score_to_grade_info(score)
            subj_credit = active_credits.get(subj, 4.0)
            total_student_credits += subj_credit

            is_subj_pass = score >= PASSING_THRESHOLD
            if not is_subj_pass:
                failed_subjects.append(subj)

            cred_pts_10 = round(grade_info["points_10"] * subj_credit, 2)
            cred_pts_4 = round(grade_info["points_4"] * subj_credit, 2)

            subjects_data.append({
                "subject": subj,
                "credits": subj_credit,
                "max_marks": 100,
                "marks_obtained": score,
                "percentage": round(score, 2),
                "grade": grade_info["grade"],
                "points_10": grade_info["points_10"],
                "points_4": grade_info["points_4"],
                "credit_points_10": cred_pts_10,
                "credit_points_4": cred_pts_4,
                "status": "Passed" if is_subj_pass else "Failed"
            })

            total_credit_points_10 += cred_pts_10
            total_credit_points_4 += cred_pts_4

        overall_pct = round((total_obtained / total_possible_marks) * 100.0, 2)
        overall_grade_info = score_to_grade_info(overall_pct)

        # Pass/fail condition: failing any single subject means failed
        is_passed = len(failed_subjects) == 0
        status_text = "Passed" if is_passed else "Failed"

        # Credit-weighted GPA calculations: sum(Grade_Points * Credits) / sum(Credits)
        gpa_10 = round(total_credit_points_10 / total_student_credits, 2) if total_student_credits > 0 else 0.0
        gpa_4 = round(total_credit_points_4 / total_student_credits, 2) if total_student_credits > 0 else 0.0

        remark = generate_academic_remark(overall_pct, is_passed, failed_subjects)

        students.append({
            "student_id": s_id,
            "name": s_name,
            "class_name": display_class,
            "raw_class": raw_class,
            "extra_metadata": extra_meta,
            "subjects": subjects_data,
            "total_credits": round(total_student_credits, 1),
            "total_marks": round(total_obtained, 2),
            "max_marks": int(total_possible_marks),
            "percentage": overall_pct,
            "grade": overall_grade_info["grade"],
            "grade_description": overall_grade_info["description"],
            "gpa_10": gpa_10,
            "gpa_4": gpa_4,
            "status": status_text,
            "failed_subjects": failed_subjects,
            "remarks": remark,
        })

    # Tie-aware ranking: Sort by percentage descending (competition ranking: 1, 2, 2, 4...)
    # In standard competition ranking, equal scores get the same rank, and subsequent ranks skip.
    students.sort(key=lambda s: s["percentage"], reverse=True)

    current_rank = 1
    for i, student in enumerate(students):
        if i > 0 and student["percentage"] < students[i - 1]["percentage"]:
            current_rank = i + 1
        student["rank"] = current_rank

    # Calculate Class Analytics
    total_students = len(students)
    passed_count = sum(1 for s in students if s["status"] == "Passed")
    failed_count = total_students - passed_count
    pass_rate = round((passed_count / total_students) * 100.0, 2) if total_students > 0 else 0.0

    percentages = [s["percentage"] for s in students]
    class_average = round(sum(percentages) / total_students, 2) if total_students > 0 else 0.0
    highest_percentage = max(percentages) if percentages else 0.0
    lowest_percentage = min(percentages) if percentages else 0.0

    top_performers = [s for s in students if s["rank"] == 1]
    top_performer_label = top_performers[0]["name"] if top_performers else "None"

    # Grade distribution counts
    distribution = {b["grade"]: 0 for b in GRADE_BOUNDARIES}
    for s in students:
        distribution[s["grade"]] = distribution.get(s["grade"], 0) + 1

    grade_distribution_list = []
    for b in GRADE_BOUNDARIES:
        g = b["grade"]
        cnt = distribution.get(g, 0)
        pct = round((cnt / total_students) * 100.0, 1) if total_students > 0 else 0.0
        grade_distribution_list.append({
            "grade": g,
            "count": cnt,
            "percentage": pct,
            "min_score": b["min"],
            "max_score": b["max"],
            "points_10": b["points_10"],
            "points_4": b["points_4"],
        })

    # Subject-wise analytics
    subject_analytics = []
    for subj in subject_cols:
        subj_scores = [
            next(sub["marks_obtained"] for sub in s["subjects"] if sub["subject"] == subj)
            for s in students
        ]
        subj_passed = sum(1 for sc in subj_scores if sc >= PASSING_THRESHOLD)
        subj_pass_rate = round((subj_passed / total_students) * 100.0, 2) if total_students > 0 else 0.0

        subject_analytics.append({
            "subject": subj,
            "credits": active_credits.get(subj, 4.0),
            "mean": round(sum(subj_scores) / total_students, 2) if total_students > 0 else 0.0,
            "max": round(max(subj_scores), 2) if subj_scores else 0.0,
            "min": round(min(subj_scores), 2) if subj_scores else 0.0,
            "pass_rate": subj_pass_rate,
        })

    avg_gpa_10 = round(sum(s["gpa_10"] for s in students) / total_students, 2) if total_students > 0 else 0.0
    avg_gpa_4 = round(sum(s["gpa_4"] for s in students) / total_students, 2) if total_students > 0 else 0.0

    return {
        "scale_type": scale_type,
        "subject_columns": subject_cols,
        "subject_credits": active_credits,
        "total_credits": round(total_curriculum_credits, 1),
        "extra_metadata_columns": extra_meta_cols,
        "students": students,
        "analytics": {
            "total_students": total_students,
            "total_credits": round(total_curriculum_credits, 1),
            "passed_count": passed_count,
            "failed_count": failed_count,
            "pass_rate": pass_rate,
            "class_average": class_average,
            "highest_percentage": highest_percentage,
            "lowest_percentage": lowest_percentage,
            "top_performer": top_performer_label,
            "avg_gpa_10": avg_gpa_10,
            "avg_gpa_4": avg_gpa_4,
            "grade_distribution": grade_distribution_list,
            "subject_analytics": subject_analytics
        }
    }
