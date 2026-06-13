"""Replay Generator — self-contained HTML report of the entire comparison execution."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_html_template() -> str:
    """Load the HTML replay template (inline)."""
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Browser Comparison Replay Report</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; line-height: 1.6; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; border-radius: 12px; margin-bottom: 30px; }
.header h1 { font-size: 28px; margin-bottom: 8px; }
.header .meta { opacity: 0.9; font-size: 14px; }
.section { background: white; border-radius: 10px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.section h2 { font-size: 20px; margin-bottom: 16px; color: #333; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; }
.badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-success { background: #d4edda; color: #155724; }
.badge-failure { background: #f8d7da; color: #721c24; }
.badge-warning { background: #fff3cd; color: #856404; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }
th { background: #f8f9fa; font-weight: 600; color: #555; }
tr:hover { background: #f8f9fa; }
.action-log { font-family: 'SF Mono', 'Cascadia Code', monospace; font-size: 13px; }
.action-log .step { color: #667eea; font-weight: 600; }
.action-log .action { color: #e83e8c; font-weight: 500; }
.action-log .success { color: #28a745; }
.action-log .failure { color: #dc3545; }
.action-log .target { color: #6c757d; }
.screenshot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-top: 12px; }
.screenshot-card { border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }
.screenshot-card img { width: 100%; height: auto; display: block; }
.screenshot-card .caption { padding: 8px 12px; font-size: 12px; color: #666; background: #fafafa; }
.timeline { position: relative; padding-left: 30px; }
.timeline-item { position: relative; padding-bottom: 20px; border-left: 2px solid #e0e0e0; padding-left: 20px; margin-left: 10px; }
.timeline-item::before { content: ''; position: absolute; left: -6px; top: 4px; width: 12px; height: 12px; border-radius: 50%; background: #667eea; }
.timeline-item .time { font-size: 12px; color: #999; }
.timeline-item .event { font-size: 14px; margin-top: 4px; }
.comparison-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.comparison-card h3 { font-size: 16px; margin-bottom: 8px; }
.comparison-card .meta { font-size: 13px; color: #666; }
.comparison-card .meta span { display: inline-block; margin-right: 16px; }
.check-list { list-style: none; }
.check-list li { padding: 8px 0; border-bottom: 1px solid #f0f0f0; display: flex; align-items: center; gap: 8px; }
.check-list .check-icon { font-size: 18px; }
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.metric-card { background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; }
.metric-card .value { font-size: 28px; font-weight: 700; color: #667eea; }
.metric-card .label { font-size: 12px; color: #666; margin-top: 4px; }
.path-visualization { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 12px 0; }
.path-node { background: #e8eaf6; padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 500; }
.path-node.selected { background: #667eea; color: white; }
.path-node.failed { background: #f8d7da; color: #721c24; }
.path-arrow { color: #999; font-size: 18px; }
.collapsible { cursor: pointer; user-select: none; }
.collapsible::after { content: ' [+]'; color: #667eea; font-size: 12px; }
.collapsible.active::after { content: ' [-]'; }
.collapsible-content { display: none; padding: 12px 0; }
.collapsible-content.active { display: block; }
@media (max-width: 768px) {
  .screenshot-grid { grid-template-columns: 1fr; }
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>%TITLE%</h1>
<div class="meta">Query: <strong>%QUERY%</strong> &middot; Status: <span class="badge badge-%STATUS_CLASS%">%STATUS%</span></div>
<div class="meta">Generated: %TIMESTAMP% &middot; Session: %SESSION_ID%</div>
</div>

<div class="section">
<h2>1. Original User Goal</h2>
<p style="font-size:16px;color:#555;">%QUERY%</p>
</div>

<div class="section">
<h2>2. Planner DAG Visualization</h2>
<div class="path-visualization">
  <span class="path-node selected">Planner</span>
  <span class="path-arrow">&rarr;</span>
  <span class="path-node %BROWSER_NODE_CLASS%">Browser</span>
  <span class="path-arrow">&rarr;</span>
  <span class="path-node %DISTILLER_NODE_CLASS%">Distiller</span>
  <span class="path-arrow">&rarr;</span>
  <span class="path-node %CRITIC_NODE_CLASS%">Critic</span>
  <span class="path-arrow">&rarr;</span>
  <span class="path-node %FORMATTER_NODE_CLASS%">Formatter</span>
</div>
<table>
<tr><th>Node</th><th>Duration</th><th>Status</th><th>Path</th></tr>
<tr><td>Planner</td><td>%PLANNER_DURATION%</td><td><span class="badge badge-success">succeeded</span></td><td>&mdash;</td></tr>
<tr><td>Browser Comparison</td><td>%BROWSER_DURATION%</td><td><span class="badge badge-%BROWSER_STATUS_CLASS%">%BROWSER_STATUS%</span></td><td>%BROWSER_PATH%</td></tr>
<tr><td>Distiller</td><td>%DISTILLER_DURATION%</td><td><span class="badge badge-%DISTILLER_STATUS_CLASS%">%DISTILLER_STATUS%</span></td><td>&mdash;</td></tr>
<tr><td>Critic</td><td>%CRITIC_DURATION%</td><td><span class="badge badge-%CRITIC_STATUS_CLASS%">%CRITIC_STATUS%</span></td><td>&mdash;</td></tr>
<tr><td>Formatter</td><td>%FORMATTER_DURATION%</td><td><span class="badge badge-success">succeeded</span></td><td>&mdash;</td></tr>
</table>
</div>

<div class="section">
<h2>3. Browser Path Chosen</h2>
<p><strong>Selected Path:</strong> %BROWSER_PATH%</p>
<p><strong>Rationale:</strong> %PATH_RATIONALE%</p>
<div class="path-visualization">
  <span class="path-node %EXTRACT_CLASS%">Extract</span>
  <span class="path-arrow">&rarr;</span>
  <span class="path-node %DETERMINISTIC_CLASS%">Deterministic</span>
  <span class="path-arrow">&rarr;</span>
  <span class="path-node %A11Y_CLASS%">A11y</span>
  <span class="path-arrow">&rarr;</span>
  <span class="path-node %VISION_CLASS%">Vision</span>
  <span class="path-arrow">&rarr;</span>
  <span class="path-node %BLOCKED_CLASS%">Blocked</span>
</div>
</div>

<div class="section">
<h2>4. Browser Actions Taken (%ACTION_COUNT%)</h2>
<table>
<tr><th>Step</th><th>Action</th><th>Target</th><th>URL</th><th>Status</th><th>Screenshot</th></tr>
%ACTIONS_TABLE%
</table>
</div>

<div class="section">
<h2>5. Screenshots &amp; Page States</h2>
<div class="screenshot-grid">
%SCREENSHOTS_GRID%
</div>
</div>

<div class="section">
<h2>6. Extracted Data</h2>
%EXTRACTED_DATA%
</div>

<div class="section">
<h2>7. Critic Evaluation</h2>
<p><strong>Status:</strong> <span class="badge badge-%CRITIC_STATUS_CLASS%">%CRITIC_STATUS%</span></p>
<p><strong>Checks:</strong> %CRITIC_PASSED%/%CRITIC_TOTAL% passed</p>
<ul class="check-list">
%CRITIC_CHECKS%
</ul>
%CRITIC_RECOVERY%
</div>

<div class="section">
<h2>8. Final Comparison Table</h2>
<table>
<tr><th>Rank</th><th>Name</th><th>Likes</th><th>Downloads</th><th>Rating</th><th>Price</th><th>Source</th></tr>
%COMPARISON_TABLE%
</table>
</div>

<div class="section">
<h2>9. Execution Timeline</h2>
<div class="timeline">
%TIMELINE%
</div>
</div>

<div class="section">
<h2>10. Metrics</h2>
<div class="metrics-grid">
  <div class="metric-card"><div class="value">%TOTAL_DURATION%</div><div class="label">Total Duration (ms)</div></div>
  <div class="metric-card"><div class="value">%ACTION_COUNT%</div><div class="label">Browser Actions</div></div>
  <div class="metric-card"><div class="value">%ITEM_COUNT%</div><div class="label">Items Extracted</div></div>
  <div class="metric-card"><div class="value">%CONFIDENCE%</div><div class="label">Confidence</div></div>
  <div class="metric-card"><div class="value">%RECOVERY_ATTEMPTS%</div><div class="label">Recovery Attempts</div></div>
  <div class="metric-card"><div class="value">%CRITIC_PASSED%/%CRITIC_TOTAL%</div><div class="label">Critic Pass Rate</div></div>
</div>
</div>

<div class="section">
<h2>11. Recovery Attempts</h2>
%RECOVERY_SECTION%
</div>

<div class="section">
<h2>12. Final Status</h2>
<p style="font-size:18px;">
<strong>Overall:</strong> <span class="badge badge-%STATUS_CLASS%">%STATUS%</span>
</p>
<p style="font-size:14px;color:#666;">%STATUS_MESSAGE%</p>
</div>

</div>
<script>
document.querySelectorAll('.collapsible').forEach(el => {
  el.addEventListener('click', function() {
    this.classList.toggle('active');
    this.nextElementSibling.classList.toggle('active');
  });
});
</script>
</body>
</html>"""


class ReplayGenerator:
    """Generates self-contained HTML replay reports from comparison execution data."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or f"replay_{uuid.uuid4().hex[:8]}"

    def generate(
        self,
        query: str,
        browser_report: dict[str, Any],
        distiller_output: dict[str, Any],
        critic_output: dict[str, Any],
        planner_duration: float = 0.0,
        browser_duration: float = 0.0,
        distiller_duration: float = 0.0,
        critic_duration: float = 0.0,
        formatter_duration: float = 0.0,
        total_duration: float = 0.0,
        output_path: str | None = None,
    ) -> tuple[str, str]:
        """Generate the replay report. Returns (html_content, filepath)."""
        actions = browser_report.get("actions", [])
        screenshots = browser_report.get("screenshots", [])
        selected_path = browser_report.get("selected_path", "unknown")
        path_results = browser_report.get("path_results", {})

        items = distiller_output.get("items", [])
        critic_status = critic_output.get("status", "PASSED")
        critic_passed = critic_output.get("passed_count", 0)
        critic_total = critic_output.get("total_checks", 6)

        status = critic_status
        status_class = "success" if status == "PASSED" else "failure"

        status_messages = {
            "PASSED": "All checks passed. The comparison was successful with valid evidence.",
            "FAILED": "Some checks failed. The comparison may be incomplete or missing evidence.",
        }

        # Build actions table
        actions_rows = ""
        for a in actions:
            step = a.get("step", "")
            action = a.get("action", "")
            target = a.get("target", "")
            url = a.get("url", "")
            act_status = a.get("status", "success")
            status_badge = f'<span class="badge badge-{"success" if act_status == "success" else "failure"}">{act_status}</span>'
            actions_rows += f"<tr><td>{step}</td><td><span class='action-log'><span class='action'>{action}</span></span></td><td>{target[:60]}</td><td style='font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;'>{url[:80]}</td><td>{status_badge}</td><td>%SCREENSHOT_REF_{step}%</td></tr>"

        # Placeholder replacement for screenshot refs
        for a in actions:
            step = a.get("step", "")
            actions_rows = actions_rows.replace(f"%SCREENSHOT_REF_{step}%", f"Step {step}")

        # Screenshots grid
        screenshots_grid = ""
        for s in screenshots:
            rel_path = s.get("relative_path", "")
            label = s.get("label", "")
            kind = s.get("kind", "")
            url = s.get("url", "")
            title = s.get("title", "")
            if rel_path:
                img_src = f"../{rel_path}"
                screenshots_grid += f'<div class="screenshot-card"><img src="{img_src}" alt="{label}" loading="lazy"><div class="caption"><strong>{label}</strong> ({kind})<br>{url[:60]}</div></div>'
            else:
                screenshots_grid += f'<div class="screenshot-card" style="padding:40px;text-align:center;color:#999;"><div class="caption">{label} ({kind}) - screenshot not available</div></div>'

        if not screenshots_grid:
            screenshots_grid = '<p style="color:#999;">No screenshots captured.</p>'

        # Extracted data
        extracted_html = ""
        if items:
            for i, item in enumerate(items[:5]):
                name = item.get("name", "Unknown")
                source = item.get("source_url", "")
                likes = item.get("likes", "N/A")
                downloads = item.get("downloads", "N/A")
                rating = item.get("rating", "N/A")
                price = item.get("price", "N/A")
                desc = item.get("description", "")[:150]
                extracted_html += f'<div class="comparison-card"><h3>{i+1}. {name}</h3><div class="meta"><span>&#10084; {likes}</span><span>&#8595; {downloads}</span><span>&#9733; {rating}</span><span>&#36; {price}</span></div><p style="font-size:13px;color:#555;">{desc}</p><p style="font-size:12px;"><a href="{source}" target="_blank">{source[:80]}</a></p></div>'
        else:
            extracted_html = '<p style="color:#999;">No items extracted.</p>'

        # Critic checks
        checks_html = ""
        checks = critic_output.get("checks", {})
        for cname, cdata in checks.items():
            passed = cdata.get("passed", False)
            icon = "&#9989;" if passed else "&#10060;"
            detail = cdata.get("detail", "")
            checks_html += f'<li><span class="check-icon">{icon}</span> <strong>{cdata.get("name", cname)}</strong>: {detail}</li>'

        recovery_html = ""
        recovery_action = critic_output.get("recovery_action")
        if recovery_action:
            recovery_html = f'<div class="badge badge-warning" style="margin-top:8px;">Suggested Recovery: {recovery_action}</div>'

        # Comparison table
        table_rows = ""
        for i, item in enumerate(items[:10]):
            rank = i + 1
            name = item.get("name", "Unknown")
            likes = item.get("likes", "N/A")
            downloads = item.get("downloads", "N/A")
            rating = item.get("rating", "N/A")
            price = item.get("price", "N/A")
            source = item.get("source_url", "")
            source_link = f'<a href="{source}" target="_blank" style="font-size:12px;">link</a>' if source else "N/A"
            table_rows += f"<tr><td>{rank}</td><td>{name[:60]}</td><td>{likes}</td><td>{downloads}</td><td>{rating}</td><td>{price}</td><td>{source_link}</td></tr>"

        if not table_rows:
            table_rows = '<tr><td colspan="7" style="text-align:center;color:#999;">No comparison data available.</td></tr>'

        # Timeline
        timeline_html = ""
        for a in actions:
            action = a.get("action", "")
            target = a.get("target", "")
            timestamp = a.get("timestamp", "")
            act_status = a.get("status", "success")
            timeline_html += f'<div class="timeline-item"><div class="time">{timestamp[-8:]}</div><div class="event"><strong>{action}</strong> {target[:60]} <span class="badge badge-{"success" if act_status == "success" else "failure"}">{act_status}</span></div></div>'

        # Path node classes
        paths = ["extract", "deterministic", "a11y", "vision", "blocked"]
        path_classes = {}
        for p in paths:
            if p == selected_path:
                path_classes[p] = "selected"
            elif p in path_results and not path_results[p].get("success", False):
                path_classes[p] = "failed"
            else:
                path_classes[p] = ""

        # Path rationale
        path_rationales = {
            "extract": "Content directly available via HTTP fetch (cheapest path).",
            "deterministic": "Structured selectors exist (CSS/XPath). Browser interaction required.",
            "a11y": "DOM is complex. Using Accessibility Tree extraction.",
            "vision": "Selectors failed. Using screenshot + vision analysis.",
            "blocked": "Page is blocked by anti-bot measures.",
        }

        # Recovery section
        recovery_attempts = browser_report.get("path_results", {}).get("deterministic", {}).get("recovery_attempts", 0)
        if recovery_attempts > 0:
            recovery_section = f'<p>System recovered from {recovery_attempts} failure(s) during execution.</p>'
        else:
            recovery_section = '<p style="color:#999;">No recovery attempts were needed.</p>'

        # Build template replacements
        replacements = {
            "%TITLE%": f"Browser Comparison Replay Report — {query[:60]}",
            "%QUERY%": query,
            "%STATUS%": status,
            "%STATUS_CLASS%": status_class.lower(),
            "%TIMESTAMP%": datetime.now(timezone.utc).isoformat(),
            "%SESSION_ID%": self.session_id,
            "%BROWSER_PATH%": selected_path.upper() if selected_path else "N/A",
            "%PATH_RATIONALE%": path_rationales.get(selected_path, "Automatic path selection."),
            "%EXTRACT_CLASS%": f"path-node {path_classes.get('extract', '')}",
            "%DETERMINISTIC_CLASS%": f"path-node {path_classes.get('deterministic', '')}",
            "%A11Y_CLASS%": f"path-node {path_classes.get('a11y', '')}",
            "%VISION_CLASS%": f"path-node {path_classes.get('vision', '')}",
            "%BLOCKED_CLASS%": f"path-node {path_classes.get('blocked', '')}",
            "%BROWSER_NODE_CLASS%": "selected" if selected_path else "",
            "%DISTILLER_NODE_CLASS%": "selected" if items else "",
            "%CRITIC_NODE_CLASS%": "selected" if critic_status == "PASSED" else "failed",
            "%FORMATTER_NODE_CLASS%": "selected",
            "%PLANNER_DURATION%": f"{planner_duration:.0f} ms",
            "%BROWSER_DURATION%": f"{browser_duration:.0f} ms",
            "%DISTILLER_DURATION%": f"{distiller_duration:.0f} ms",
            "%CRITIC_DURATION%": f"{critic_duration:.0f} ms",
            "%FORMATTER_DURATION%": f"{formatter_duration:.0f} ms",
            "%BROWSER_STATUS%": "succeeded" if selected_path else "failed",
            "%BROWSER_STATUS_CLASS%": "success" if selected_path else "failure",
            "%DISTILLER_STATUS%": "succeeded" if items else "failed",
            "%DISTILLER_STATUS_CLASS%": "success" if items else "failure",
            "%CRITIC_STATUS%": critic_status,
            "%CRITIC_STATUS_CLASS%": "success" if critic_status == "PASSED" else "failure",
            "%CRITIC_PASSED%": str(critic_passed),
            "%CRITIC_TOTAL%": str(critic_total),
            "%TOTAL_DURATION%": f"{total_duration:.0f}",
            "%ACTION_COUNT%": str(len(actions)),
            "%ITEM_COUNT%": str(len(items)),
            "%CONFIDENCE%": f'{distiller_output.get("confidence", 0):.2f}',
            "%RECOVERY_ATTEMPTS%": str(recovery_attempts),
            "%ACTIONS_TABLE%": actions_rows,
            "%SCREENSHOTS_GRID%": screenshots_grid,
            "%EXTRACTED_DATA%": extracted_html,
            "%CRITIC_CHECKS%": checks_html,
            "%CRITIC_RECOVERY%": recovery_html,
            "%COMPARISON_TABLE%": table_rows,
            "%TIMELINE%": timeline_html,
            "%RECOVERY_SECTION%": recovery_section,
            "%STATUS_MESSAGE%": status_messages.get(status, "Execution completed."),
        }

        html = _load_html_template()
        for placeholder, value in replacements.items():
            html = html.replace(placeholder, str(value))

        # Write to file
        if output_path:
            report_path = Path(output_path)
        else:
            report_dir = Path(__file__).resolve().parents[1] / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"replay_{self.session_id}.html"

        report_path.write_text(html, encoding="utf-8")
        logger.info("Replay report generated: %s", report_path)

        return html, str(report_path)


def generate_replay_report(
    query: str,
    browser_report: dict[str, Any],
    distiller_output: dict[str, Any],
    critic_output: dict[str, Any],
    **kwargs: Any,
) -> tuple[str, str]:
    """Generate and return the replay report."""
    gen = ReplayGenerator(session_id=browser_report.get("session_id"))
    return gen.generate(
        query=query,
        browser_report=browser_report,
        distiller_output=distiller_output,
        critic_output=critic_output,
        **kwargs,
    )
