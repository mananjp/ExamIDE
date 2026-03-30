"""
PDF Report Generator for Online Exam IDE
Uses ReportLab to generate exam reports with student scores and violations.
"""

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_exam_report(room_data: dict, scores_data: list, questions: list) -> bytes:
    """
    Generate a PDF exam report.

    Args:
        room_data: Room details (name, teacher, duration, start/end, etc.)
        scores_data: List of dicts per student:
            {
                "student_id": str,
                "student_name": str,
                "red_flags": int,
                "questions": [
                    {"question_id": str, "score": float, "max_score": float, "status": str}
                ],
                "total_score": float,
                "max_total": float
            }
        questions: List of question dicts with question_text and question_id

    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
        title=f"Exam Report - {room_data.get('room_name', 'Unknown')}",
        author=room_data.get("teacher_name", "Teacher")
    )

    styles = getSampleStyleSheet()
    elements = []

    # ============================
    # Custom styles
    # ============================
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold"
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=4,
        textColor=colors.HexColor("#555555"),
        fontName="Helvetica"
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor("#16213e"),
        fontName="Helvetica-Bold"
    )
    small_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor("#888888"),
    )

    # ============================
    # HEADER
    # ============================
    elements.append(Paragraph(f"📋 Exam Report", title_style))
    elements.append(Paragraph(
        f"<b>{room_data.get('room_name', 'Untitled Exam')}</b>",
        subtitle_style
    ))
    elements.append(Spacer(1, 4))

    # Exam info table
    start_time = room_data.get("start_time", "N/A")
    end_time = room_data.get("end_time", "N/A")
    if start_time and start_time != "N/A":
        try:
            start_time = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M")
        except:
            pass
    if end_time and end_time != "N/A":
        try:
            end_time = datetime.fromisoformat(end_time).strftime("%Y-%m-%d %H:%M")
        except:
            pass

    info_data = [
        ["Teacher", room_data.get("teacher_name", "N/A"),
         "Room Code", room_data.get("room_code", "N/A"),
         "Language", room_data.get("language", "N/A")],
        ["Duration", f"{room_data.get('duration_minutes', 'N/A')} min",
         "Start Time", str(start_time),
         "End Time", str(end_time)],
        ["Total Students", str(len(room_data.get("students", []))),
         "Total Questions", str(len(questions)),
         "Status", room_data.get("status", "N/A").upper()],
    ]

    info_table = Table(info_data, colWidths=[80, 140, 80, 140, 80, 140])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME', (4, 0), (4, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#333333")),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor("#333333")),
        ('TEXTCOLOR', (4, 0), (4, -1), colors.HexColor("#333333")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#f0f0f0")),
        ('BACKGROUND', (4, 0), (4, -1), colors.HexColor("#f0f0f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#16213e")))
    elements.append(Spacer(1, 8))

    # ============================
    # SCORES TABLE
    # ============================
    elements.append(Paragraph("📊 Student Scores & Violations", heading_style))
    elements.append(Spacer(1, 4))

    # Build header row
    q_headers = []
    for i, q in enumerate(questions):
        q_text = q.get("question_text", f"Q{i+1}")
        # Truncate long question text
        if len(q_text) > 25:
            q_text = q_text[:22] + "..."
        q_headers.append(f"Q{i+1}")

    header_row = ["#", "Student Name"] + q_headers + ["Total Score", "Percentage", "Violations", "Grade"]

    # Build data rows
    table_data = [header_row]
    
    for idx, student in enumerate(scores_data):
        row = [
            str(idx + 1),
            student.get("student_name", "Unknown"),
        ]

        # Per-question scores
        for q_score in student.get("questions", []):
            score = q_score.get("score", 0)
            max_s = q_score.get("max_score", 100)
            status = q_score.get("status", "not_attempted")
            
            if status == "accepted":
                cell = f"{score:.0f}/{max_s:.0f} ✓"
            elif status == "attempted":
                cell = f"{score:.0f}/{max_s:.0f}"
            else:
                cell = "—"
            row.append(cell)

        # Total score
        total = student.get("total_score", 0)
        max_total = student.get("max_total", 0)
        percentage = (total / max_total * 100) if max_total > 0 else 0

        row.append(f"{total:.0f}/{max_total:.0f}")
        row.append(f"{percentage:.1f}%")

        # Violations
        red_flags = student.get("red_flags", 0)
        flag_text = f"🚩 {red_flags}" if red_flags > 0 else "✅ 0"
        row.append(flag_text)

        # Grade
        if percentage >= 90:
            grade = "A+"
        elif percentage >= 80:
            grade = "A"
        elif percentage >= 70:
            grade = "B"
        elif percentage >= 60:
            grade = "C"
        elif percentage >= 50:
            grade = "D"
        else:
            grade = "F"
        
        # Flag if violations exist
        if red_flags >= 5:
            grade += " ⚠"
        
        row.append(grade)
        table_data.append(row)

    # Calculate column widths dynamically
    num_questions = len(questions)
    q_col_width = max(40, min(60, (500 - 200) // max(num_questions, 1)))
    col_widths = [25, 120] + [q_col_width] * num_questions + [70, 60, 60, 45]

    scores_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Style the table
    table_style_cmds = [
        # Header
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]

    # Alternating row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style_cmds.append(
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f8f9fa"))
            )

    # Highlight violation cells
    for i in range(1, len(table_data)):
        student = scores_data[i - 1]
        red_flags = student.get("red_flags", 0)
        violations_col = len(header_row) - 2  # violations column index
        if red_flags > 0:
            table_style_cmds.append(
                ('TEXTCOLOR', (violations_col, i), (violations_col, i), colors.red)
            )
        if red_flags >= 5:
            table_style_cmds.append(
                ('BACKGROUND', (violations_col, i), (violations_col, i), colors.HexColor("#ffe0e0"))
            )

    scores_table.setStyle(TableStyle(table_style_cmds))
    elements.append(scores_table)
    elements.append(Spacer(1, 12))

    # ============================
    # SUMMARY STATISTICS
    # ============================
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("📈 Summary Statistics", heading_style))

    if scores_data:
        all_percentages = []
        for s in scores_data:
            mt = s.get("max_total", 0)
            ts = s.get("total_score", 0)
            pct = (ts / mt * 100) if mt > 0 else 0
            all_percentages.append(pct)

        avg_score = sum(all_percentages) / len(all_percentages)
        max_score = max(all_percentages)
        min_score = min(all_percentages)
        passed = sum(1 for p in all_percentages if p >= 50)
        failed = len(all_percentages) - passed
        total_violations = sum(s.get("red_flags", 0) for s in scores_data)
        students_with_violations = sum(1 for s in scores_data if s.get("red_flags", 0) > 0)

        summary_data = [
            ["Metric", "Value"],
            ["Average Score", f"{avg_score:.1f}%"],
            ["Highest Score", f"{max_score:.1f}%"],
            ["Lowest Score", f"{min_score:.1f}%"],
            ["Passed (≥50%)", f"{passed}/{len(scores_data)}"],
            ["Failed (<50%)", f"{failed}/{len(scores_data)}"],
            ["Total Violations", str(total_violations)],
            ["Students with Violations", f"{students_with_violations}/{len(scores_data)}"],
        ]

        summary_table = Table(summary_data, colWidths=[180, 120])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
    else:
        elements.append(Paragraph("No student data available.", styles['Normal']))

    # ============================
    # QUESTION DETAILS
    # ============================
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    elements.append(Paragraph("📝 Questions", heading_style))

    for i, q in enumerate(questions):
        q_text = q.get("question_text", "N/A")
        tc_count = len(q.get("test_cases", []))
        elements.append(Paragraph(
            f"<b>Q{i+1}:</b> {q_text} <i>({tc_count} test cases)</i>",
            styles['Normal']
        ))
        elements.append(Spacer(1, 3))

    # ============================
    # VIOLATION DETAILS
    # ============================
    flagged_students = [s for s in scores_data if s.get("red_flags", 0) > 0]
    if flagged_students:
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        elements.append(Paragraph("🚩 Violation Report", heading_style))
        elements.append(Paragraph(
            "The following students had security violations during the exam:",
            styles['Normal']
        ))
        elements.append(Spacer(1, 4))

        violation_data = [["#", "Student Name", "Violations", "Severity", "Recommendation"]]
        for idx, s in enumerate(flagged_students):
            flags = s.get("red_flags", 0)
            if flags >= 10:
                severity = "CRITICAL"
                recommendation = "Disqualify / Manual Review"
            elif flags >= 5:
                severity = "HIGH"
                recommendation = "Flag for Review"
            elif flags >= 3:
                severity = "MEDIUM"
                recommendation = "Warning Issued"
            else:
                severity = "LOW"
                recommendation = "Monitor"
            
            violation_data.append([
                str(idx + 1),
                s.get("student_name", "Unknown"),
                str(flags),
                severity,
                recommendation
            ])

        viol_table = Table(violation_data, colWidths=[25, 150, 70, 80, 160])
        viol_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8b0000")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        # Color severity cells
        for i in range(1, len(violation_data)):
            severity = violation_data[i][3]
            if severity == "CRITICAL":
                viol_table.setStyle(TableStyle([
                    ('BACKGROUND', (3, i), (3, i), colors.HexColor("#ffcccc")),
                    ('TEXTCOLOR', (3, i), (3, i), colors.red),
                ]))
            elif severity == "HIGH":
                viol_table.setStyle(TableStyle([
                    ('BACKGROUND', (3, i), (3, i), colors.HexColor("#ffe0cc")),
                    ('TEXTCOLOR', (3, i), (3, i), colors.HexColor("#cc6600")),
                ]))

        elements.append(viol_table)

    # ============================
    # FOOTER
    # ============================
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Online Exam IDE | Confidential",
        small_style
    ))

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
