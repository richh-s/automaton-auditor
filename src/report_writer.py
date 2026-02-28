"""
Forensic Report Writer: Generates a structured Markdown report from AuditReport.
Structure: Executive Summary -> Criterion Breakdown -> Remediation Plan
"""

import os
from src.state import AuditReport


def write_forensic_report(report: AuditReport, output_dir: str = "reports") -> str:
    """
    Writes a forensic audit report as a Markdown file.
    
    - Creates output_dir if missing
    - Writes UTF-8
    - All paths in output are relative (portable)
    
    Returns the path to the generated report.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "forensic_report.md")

    lines = []

    # --- Header ---
    lines.append("# Forensic Audit Report")
    lines.append("")
    lines.append(
        f"**Repo:** {report.repo_url} | "
        f"**Score:** {report.overall_score:.1f}/5.0 | "
        f"**Dimensions:** {len(report.criteria)}"
    )
    lines.append("")

    # --- Executive Summary ---
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")

    # --- Criterion Breakdown ---
    lines.append("## Criterion Breakdown")
    lines.append("")

    for criterion in report.criteria:
        lines.append(f"### {criterion.dimension_name} — Score: {criterion.final_score}/5")
        lines.append("")

        # Judge opinions table
        lines.append("| Judge | Score | Argument |")
        lines.append("|-------|-------|----------|")
        for op in criterion.judge_opinions:
            # Truncate argument for readability, escape pipes
            arg_text = op.argument[:150].replace("|", "\\|")
            lines.append(f"| {op.judge} | {op.score}/5 | {arg_text} |")
        lines.append("")

        # Dissent
        if criterion.dissent_summary:
            lines.append(f"**Dissent:** {criterion.dissent_summary}")
            lines.append("")

        # Evidence Citations (deduped, sorted, max 5)
        all_citations = []
        for op in criterion.judge_opinions:
            all_citations.extend(op.cited_evidence)
        # Deduplicate, sort, cap at 5
        unique_citations = sorted(set(all_citations))[:5]
        if unique_citations:
            lines.append("**Evidence Citations:**")
            for cite in unique_citations:
                lines.append(f"- `{cite}`")
            lines.append("")

        # Remediation
        if criterion.remediation:
            lines.append("**Remediation:**")
            lines.append(f"- {criterion.remediation}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # --- Remediation Plan ---
    lines.append("## Remediation Plan")
    lines.append("")
    lines.append(report.remediation_plan)
    lines.append("")

    # --- Write to file ---
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path
