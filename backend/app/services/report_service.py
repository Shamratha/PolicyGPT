import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReportService:
    def generate_pdf_report(self, stats: Dict[str, Any]) -> bytes:
        """
        Compiles research aggregates and yields a PDF report byte stream.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Custom elegant typography styles
        title_style = ParagraphStyle(
            name="ReportTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1e3a8a"), # Deep Navy
            spaceAfter=10
        )
        
        subtitle_style = ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#4b5563"), # Slate Gray
            spaceAfter=20
        )
        
        section_style = ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f172a"), # Dark Charcoal
            spaceBefore=15,
            spaceAfter=8,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            name="ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )
        
        table_cell_style = ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12
        )
        
        table_header_style = ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.white
        )

        story = []

        # 1. Header block
        story.append(Paragraph("PolicyGPT: Public Policy Access Report", title_style))
        story.append(Paragraph(f"Compiled on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Scope: System Research Surveys", subtitle_style))
        story.append(Spacer(1, 10))

        # 2. Executive Summary Metrics Box
        story.append(Paragraph("Executive Summary", section_style))
        story.append(Paragraph(
            "This report analyzes public scheme accessibility, citizen awareness levels, and structural application "
            "bottlenecks compiled from user feedback surveys. These insights help administrators target outreach, "
            "simplify document requirements, and identify marginalized demographics requiring active intervention.",
            body_style
        ))
        story.append(Spacer(1, 12))

        # Core Metrics Cards Table
        summary_data = [
            [
                Paragraph("<b>Total Submissions</b>", table_cell_style),
                Paragraph("<b>Awareness Rate</b>", table_cell_style),
                Paragraph("<b>Application Rate</b>", table_cell_style),
                Paragraph("<b>Avg Difficulty</b>", table_cell_style)
            ],
            [
                Paragraph(str(stats["total_submissions"]), table_cell_style),
                Paragraph(f"{stats['awareness_rate']}%", table_cell_style),
                Paragraph(f"{stats['application_rate']}%", table_cell_style),
                Paragraph(f"{stats['average_difficulty']}/5.0", table_cell_style)
            ]
        ]
        
        t_summary = Table(summary_data, colWidths=[130, 130, 130, 130])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_summary)
        story.append(Spacer(1, 20))

        # 3. Application Bottlenecks
        story.append(Paragraph("Key Application Bottlenecks", section_style))
        story.append(Paragraph(
            "Below is the distribution of core roadblocks faced by citizens when attempting to apply for government opportunities. "
            "A high concentration of 'Complex documentation' indicates a clear need to integrate eligibility checks with online document wallets (e.g. DigiLocker).",
            body_style
        ))
        story.append(Spacer(1, 8))

        if stats["bottlenecks"]:
            bottleneck_rows = [[Paragraph("<b>roadblock / bottleneck reason</b>", table_header_style), Paragraph("<b>count</b>", table_header_style)]]
            for reason, count in stats["bottlenecks"].items():
                bottleneck_rows.append([
                    Paragraph(reason, table_cell_style),
                    Paragraph(str(count), table_cell_style)
                ])
            
            t_bottlenecks = Table(bottleneck_rows, colWidths=[400, 120])
            t_bottlenecks.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t_bottlenecks)
        else:
            story.append(Paragraph("<i>No bottleneck events tracked yet.</i>", body_style))
        story.append(Spacer(1, 20))

        # 4. State-wise Policy Awareness
        story.append(Paragraph("State-wise Policy Awareness Distribution", section_style))
        story.append(Paragraph(
            "Regional distribution of scheme visibility helps ministries identify states with lower information penetration. "
            "Promotional outreach and localized translations should target states under 50% awareness.",
            body_style
        ))
        story.append(Spacer(1, 8))

        if stats["state_awareness"]:
            state_rows = [[
                Paragraph("<b>State</b>", table_header_style), 
                Paragraph("<b>Submissions</b>", table_header_style),
                Paragraph("<b>Awareness Rate</b>", table_header_style)
            ]]
            for item in stats["state_awareness"]:
                state_rows.append([
                    Paragraph(item["state"], table_cell_style),
                    Paragraph(str(item["submissions_count"]), table_cell_style),
                    Paragraph(f"{item['awareness_rate']}%", table_cell_style)
                ])
            
            t_states = Table(state_rows, colWidths=[200, 160, 160])
            t_states.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t_states)
        else:
            story.append(Paragraph("<i>No regional stats captured yet.</i>", body_style))
        story.append(Spacer(1, 20))

        # 5. Underserved Demographics
        story.append(Paragraph("Underserved Demographic Indicators", section_style))
        story.append(Paragraph(
            "This table highlights the application approval success rate across demographic segments. "
            "Segments displaying low success rates represent underserved groups that face potential systemic bias or "
            "insufficient guidance during the filing process.",
            body_style
        ))
        story.append(Spacer(1, 8))

        if stats["underserved_demographics"]:
            demo_rows = [[
                Paragraph("<b>Demographic Segment (Gender - Occupation)</b>", table_header_style), 
                Paragraph("<b>Survey Volume</b>", table_header_style),
                Paragraph("<b>Approval / Success Rate</b>", table_header_style)
            ]]
            for item in stats["underserved_demographics"]:
                demo_rows.append([
                    Paragraph(item["demographic"], table_cell_style),
                    Paragraph(str(item["volume"]), table_cell_style),
                    Paragraph(f"{item['match_rate']}%", table_cell_style)
                ])
            
            t_demos = Table(demo_rows, colWidths=[240, 140, 140])
            t_demos.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t_demos)
        else:
            story.append(Paragraph("<i>No demographic matches computed yet.</i>", body_style))

        # Build Document
        try:
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
        except Exception as e:
            logger.error(f"Failed to generate report PDF: {e}")
            raise e

report_service = ReportService()
