"""
Export utilities for generating PDF and Markdown reports.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from red_team_analyzer import AnalysisResult
from config import RED_TEAM_PERSPECTIVES

def export_to_pdf(
    strategy: str,
    analysis_results: Dict[str, AnalysisResult],
    synthesis: Optional[Dict[str, Any]] = None
) -> bytes:
    """Export analysis results to PDF format."""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1f77b4',
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#333333',
        spaceBefore=20,
        spaceAfter=10
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor='#666666',
        spaceBefore=15,
        spaceAfter=8
    )
    
    # Title
    story.append(Paragraph("Strategic Red Team Analysis Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    if synthesis and 'executive_summary' in synthesis:
        story.append(Paragraph(synthesis['executive_summary'], styles['Normal']))
    else:
        story.append(Paragraph("This report contains a comprehensive red team analysis of the submitted strategy from multiple analytical perspectives.", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Original Strategy
    story.append(Paragraph("Original Strategy", heading_style))
    story.append(Paragraph(strategy, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Analysis Results
    story.append(Paragraph("Detailed Analysis Results", heading_style))
    
    for perspective, result in analysis_results.items():
        perspective_info = RED_TEAM_PERSPECTIVES.get(perspective, {})
        perspective_name = perspective_info.get('name', perspective)
        
        # Perspective header
        story.append(Paragraph(f"{perspective_name} Analysis", subheading_style))
        story.append(Paragraph(f"Confidence Score: {result.confidence_score:.1%}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Analysis content
        story.append(Paragraph("Analysis:", styles['Heading4']))
        story.append(Paragraph(result.analysis, styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Key insights
        if result.key_insights:
            story.append(Paragraph("Key Insights:", styles['Heading4']))
            for insight in result.key_insights:
                story.append(Paragraph(f"• {insight}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Recommendations
        if result.recommendations:
            story.append(Paragraph("Recommendations:", styles['Heading4']))
            for rec in result.recommendations:
                story.append(Paragraph(f"→ {rec}", styles['Normal']))
            story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))
    
    # Synthesis Section
    if synthesis:
        story.append(PageBreak())
        story.append(Paragraph("Strategic Synthesis & Recommendations", heading_style))
        
        if 'critical_insights' in synthesis:
            story.append(Paragraph("Critical Insights:", subheading_style))
            for i, insight in enumerate(synthesis['critical_insights'], 1):
                story.append(Paragraph(f"{i}. {insight}", styles['Normal']))
            story.append(Spacer(1, 15))
        
        if 'priority_recommendations' in synthesis:
            story.append(Paragraph("Priority Recommendations:", subheading_style))
            for i, rec in enumerate(synthesis['priority_recommendations'], 1):
                story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
            story.append(Spacer(1, 15))
        
        if 'risk_mitigation' in synthesis:
            story.append(Paragraph("Risk Mitigation Strategies:", subheading_style))
            for risk in synthesis['risk_mitigation']:
                story.append(Paragraph(f"• {risk}", styles['Normal']))
            story.append(Spacer(1, 15))
        
        if 'implementation_roadmap' in synthesis:
            story.append(Paragraph("Implementation Roadmap:", subheading_style))
            for phase in synthesis['implementation_roadmap']:
                story.append(Paragraph(f"• {phase}", styles['Normal']))
            story.append(Spacer(1, 15))
    
    # Build PDF
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def export_to_markdown(
    strategy: str,
    analysis_results: Dict[str, AnalysisResult],
    synthesis: Optional[Dict[str, Any]] = None
) -> str:
    """Export analysis results to Markdown format."""
    
    md_content = []
    
    # Header
    md_content.append("# Strategic Red Team Analysis Report")
    md_content.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    md_content.append("")
    
    # Executive Summary
    md_content.append("## Executive Summary")
    if synthesis and 'executive_summary' in synthesis:
        md_content.append(synthesis['executive_summary'])
    else:
        md_content.append("This report contains a comprehensive red team analysis of the submitted strategy from multiple analytical perspectives.")
    md_content.append("")
    
    # Original Strategy
    md_content.append("## Original Strategy")
    md_content.append(f"> {strategy}")
    md_content.append("")
    
    # Analysis Results
    md_content.append("## Detailed Analysis Results")
    md_content.append("")
    
    for perspective, result in analysis_results.items():
        perspective_info = RED_TEAM_PERSPECTIVES.get(perspective, {})
        perspective_name = perspective_info.get('name', perspective)
        icon = perspective_info.get('icon', '•')
        
        md_content.append(f"### {icon} {perspective_name} Analysis")
        md_content.append(f"**Confidence Score:** {result.confidence_score:.1%}")
        md_content.append("")
        
        md_content.append("**Analysis:**")
        md_content.append(result.analysis)
        md_content.append("")
        
        if result.key_insights:
            md_content.append("**Key Insights:**")
            for insight in result.key_insights:
                md_content.append(f"- {insight}")
            md_content.append("")
        
        if result.recommendations:
            md_content.append("**Recommendations:**")
            for rec in result.recommendations:
                md_content.append(f"- {rec}")
            md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # Synthesis Section
    if synthesis:
        md_content.append("## Strategic Synthesis & Recommendations")
        md_content.append("")
        
        if 'critical_insights' in synthesis:
            md_content.append("### 🎯 Critical Insights")
            for i, insight in enumerate(synthesis['critical_insights'], 1):
                md_content.append(f"{i}. {insight}")
            md_content.append("")
        
        if 'priority_recommendations' in synthesis:
            md_content.append("### 📋 Priority Recommendations")
            for i, rec in enumerate(synthesis['priority_recommendations'], 1):
                md_content.append(f"{i}. {rec}")
            md_content.append("")
        
        if 'risk_mitigation' in synthesis:
            md_content.append("### ⚠️ Risk Mitigation Strategies")
            for risk in synthesis['risk_mitigation']:
                md_content.append(f"- {risk}")
            md_content.append("")
        
        if 'implementation_roadmap' in synthesis:
            md_content.append("### 🗺️ Implementation Roadmap")
            for phase in synthesis['implementation_roadmap']:
                md_content.append(f"- {phase}")
            md_content.append("")
        
        if 'success_metrics' in synthesis:
            md_content.append("### 📊 Success Metrics")
            for metric in synthesis['success_metrics']:
                md_content.append(f"- {metric}")
            md_content.append("")
        
        if 'confidence_assessment' in synthesis:
            confidence = synthesis['confidence_assessment']
            md_content.append(f"### 🎯 Overall Strategic Confidence: {confidence:.1%}")
            md_content.append("")
    
    # Footer
    md_content.append("---")
    md_content.append("*This report was generated by the Strategic Red Team Analyzer using Claude Opus 4.*")
    
    return "\n".join(md_content)

def create_summary_table(analysis_results: Dict[str, AnalysisResult]) -> str:
    """Create a markdown table summarizing analysis results."""
    
    table_lines = [
        "| Perspective | Confidence | Key Insights | Recommendations |",
        "|-------------|------------|--------------|-----------------|"
    ]
    
    for perspective, result in analysis_results.items():
        perspective_info = RED_TEAM_PERSPECTIVES.get(perspective, {})
        name = perspective_info.get('name', perspective)
        confidence = f"{result.confidence_score:.1%}"
        insights_count = len(result.key_insights)
        rec_count = len(result.recommendations)
        
        table_lines.append(f"| {name} | {confidence} | {insights_count} | {rec_count} |")
    
    return "\n".join(table_lines)