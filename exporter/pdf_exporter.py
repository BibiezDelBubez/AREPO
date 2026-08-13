"""
PDF Exporter Module for AREPO.
Generates professional vector PDFs (ReportLab) for Crosswords, Rebus, and Verse games.
"""

import os
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


class PDFExporter:
    """Generates high-resolution vector PDF documents using ReportLab."""

    @staticmethod
    def export_crossword_pdf(
        output_filepath: str,
        title: str,
        grid_matrix: List[List[str]],
        clues_across: List[str],
        clues_down: List[str],
        include_solution: bool = True
    ) -> bool:
        """Generate 2-page PDF: Page 1 = Empty Grid & Clues; Page 2 = Solution Grid."""
        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#2C3E50"),
            alignment=1
        )
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#017E84")
        )
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=12
        )

        story = []

        # Page 1 Title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 15))

        # Blank Crossword Grid
        rows = len(grid_matrix)
        cols = len(grid_matrix[0]) if rows > 0 else 0

        cell_size = min(380 / max(1, cols), 380 / max(1, rows))
        
        blank_table_data = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                val = grid_matrix[r][c]
                row_data.append("" if val != '#' else "")
            blank_table_data.append(row_data)

        # Style grid cells
        t_style = [
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#2C3E50")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        for r in range(rows):
            for c in range(cols):
                if grid_matrix[r][c] == '#':
                    t_style.append(('BACKGROUND', (c, r), (c, r), colors.HexColor("#2C3E50")))

        blank_table = Table(blank_table_data, colWidths=[cell_size]*cols, rowHeights=[cell_size]*rows)
        blank_table.setStyle(TableStyle(t_style))

        story.append(blank_table)
        story.append(Spacer(1, 20))

        # Clues Section
        story.append(Paragraph("ORIZZONTALI", heading_style))
        for clue in clues_across:
            story.append(Paragraph(f"• {clue}", body_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("VERTICALI", heading_style))
        for clue in clues_down:
            story.append(Paragraph(f"• {clue}", body_style))

        # Page 2: Solution Page
        if include_solution:
            story.append(PageBreak())
            story.append(Paragraph(f"{title} - SOLUZIONE", title_style))
            story.append(Spacer(1, 15))

            sol_table_data = []
            for r in range(rows):
                row_data = []
                for c in range(cols):
                    val = grid_matrix[r][c]
                    row_data.append(val if val != '#' else "")
                sol_table_data.append(row_data)

            sol_table = Table(sol_table_data, colWidths=[cell_size]*cols, rowHeights=[cell_size]*rows)
            sol_table.setStyle(TableStyle(t_style))
            story.append(sol_table)

        doc.build(story)
        return True
