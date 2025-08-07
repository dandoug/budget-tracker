"""PDF and other report generation."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO


class ReportGenerator:
    """Generates PDF reports from budget analysis."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )

    def generate_budget_report(
        self,
        variance_data: pd.DataFrame,
        summary_stats: Dict[str, float],
        report_period: str = None,
        output_path: Optional[Path] = None
    ) -> BytesIO:
        """Generate comprehensive budget report."""

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer if output_path is None else str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        story = []

        # Title
        title = f"Budget Analysis Report"
        if report_period:
            title += f" - {report_period}"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 12))

        # Generated date
        story.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%B %d, %Y')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))

        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['Heading2']))
        summary_text = self._create_summary_text(summary_stats)
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))

        # Budget vs Actual Table
        story.append(Paragraph("Budget vs Actual Analysis", self.styles['Heading2']))
        variance_table = self._create_variance_table(variance_data)
        story.append(variance_table)
        story.append(Spacer(1, 20))

        # Recommendations
        story.append(Paragraph("Recommendations", self.styles['Heading2']))
        recommendations = self._generate_recommendations(variance_data, summary_stats)
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['Normal']))

        doc.build(story)

        if output_path is None:
            buffer.seek(0)
            return buffer

        return None

    def _create_summary_text(self, summary_stats: Dict[str, float]) -> str:
        """Create executive summary text."""
        budgeted_net = summary_stats['budgeted_net']
        actual_net = summary_stats['actual_net']
        variance = actual_net - budgeted_net

        summary = f"""
        Total Budgeted Income: ${summary_stats['total_budgeted_income']:,.2f}<br/>
        Total Budgeted Expenses: ${summary_stats['total_budgeted_expenses']:,.2f}<br/>
        Budgeted Net: ${budgeted_net:,.2f}<br/><br/>

        Total Actual Income: ${summary_stats['total_actual_income']:,.2f}<br/>
        Total Actual Expenses: ${summary_stats['total_actual_expenses']:,.2f}<br/>
        Actual Net: ${actual_net:,.2f}<br/><br/>

        Net Variance: ${variance:,.2f} ({'Over' if variance < 0 else 'Under'} budget)
        """

        return summary

    def _create_variance_table(self, variance_data: pd.DataFrame) -> Table:
        """Create budget variance table."""
        data = [['Category', 'Budgeted', 'Actual', 'Variance', 'Variance %']]

        for _, row in variance_data.iterrows():
            data.append([
                row['category'],
                f"${row['budgeted']:,.2f}",
                f"${row['actual']:,.2f}",
                f"${row['variance']:,.2f}",
                f"{row['variance_percent']:.1f}%"
            ])

        table = Table(data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Right align numbers
        ]))

        return table

    def _generate_recommendations(self, variance_data: pd.DataFrame, summary_stats: Dict[str, float]) -> list:
        """Generate budget recommendations based on analysis."""
        recommendations = []

        # Check for overspending categories
        overspent = variance_data[variance_data['variance_percent'] > 10]
        if not overspent.empty:
            categories = ', '.join(overspent['category'].tolist())
            recommendations.append(f"Review spending in {categories} - significantly over budget")

        # Check for underspending
        underspent = variance_data[variance_data['variance_percent'] < -20]
        if not underspent.empty:
            categories = ', '.join(underspent['category'].tolist())
            recommendations.append(f"Consider reallocating budget from {categories} - consistently under budget")

        # Overall budget performance
        if summary_stats['actual_net'] < summary_stats['budgeted_net']:
            recommendations.append("Overall spending exceeds budget - consider expense reduction strategies")

        if not recommendations:
            recommendations.append("Budget performance is on track - continue current spending patterns")

        return recommendations

    def export_to_excel(self, data_dict: Dict[str, pd.DataFrame], output_path: Path) -> None:
        """Export multiple dataframes to Excel with multiple sheets."""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
