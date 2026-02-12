"""
Wellness Studio - Report Generator
Creates user-friendly, thoughtful summary reports from wellness plans.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import asdict

from .config import path_config
from .medical_model import WellnessPlan, NaturalAlternative


class ReportGenerator:
    """
    Generates beautiful, user-friendly reports from wellness plans.
    Supports multiple output formats: Markdown, HTML, JSON.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or path_config.REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self, 
        wellness_plan: WellnessPlan, 
        patient_name: Optional[str] = None,
        format: str = 'markdown'
    ) -> Path:
        """
        Generate a report from a wellness plan.
        
        Args:
            wellness_plan: The generated wellness plan
            patient_name: Optional patient identifier
            format: Output format ('markdown', 'html', 'json')
            
        Returns:
            Path to the generated report file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        patient_id = patient_name or 'anonymous'
        
        if format.lower() == 'markdown':
            return self._generate_markdown(wellness_plan, patient_id, timestamp)
        elif format.lower() == 'html':
            return self._generate_html(wellness_plan, patient_id, timestamp)
        elif format.lower() == 'json':
            return self._generate_json(wellness_plan, patient_id, timestamp)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_markdown(
        self, 
        plan: WellnessPlan, 
        patient_id: str, 
        timestamp: str
    ) -> Path:
        """Generate a Markdown report."""
        filename = f"wellness_report_{patient_id}_{timestamp}.md"
        filepath = self.output_dir / filename
        
        content = f"""# 🌿 Your Personal Wellness Transformation Plan

**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

---

## 📝 Your Case Summary

{plan.case_summary}

---

## 🌱 Natural Alternatives & Complementary Approaches

"""
        
        if plan.natural_alternatives:
            # Group by category
            by_category = {}
            for alt in plan.natural_alternatives:
                cat = alt.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(alt)
            
            for category, alts in by_category.items():
                content += f"\n### {category.title()} Approaches\n\n"
                for alt in alts:
                    evidence_emoji = {"high": "🔬", "moderate": "📊", "preliminary": "🔍"}.get(
                        alt.evidence_level, "🔍"
                    )
                    content += f"""**{alt.original}** → *{alt.alternative}*
{evidence_emoji} Evidence Level: {alt.evidence_level.title()}

{alt.description}

"""
        else:
            content += "_No specific alternatives generated for this case._\n\n"
        
        content += f"""---

## 🧘 Mindfulness Practices

Incorporating mindfulness into your daily routine can significantly enhance your overall wellbeing:

"""
        for practice in plan.mindfulness_practices:
            content += f"- {practice}\n"
        
        content += f"""

---

## 🥗 Nutritional Suggestions

Food is medicine. Consider these dietary approaches:

"""
        for suggestion in plan.nutritional_suggestions:
            content += f"- {suggestion}\n"
        
        content += f"""

---

## 🌅 Lifestyle Modifications

Small changes in daily habits can have profound effects:

"""
        for mod in plan.lifestyle_modifications:
            content += f"- {mod}\n"
        
        content += f"""

---

## 🤝 The Combined Approach: Best of Both Worlds

{plan.combined_approach}

---

## 📋 Important Reminders

{plan.disclaimer}

---

## 🎯 Next Steps

1. **Review with your healthcare provider** before making any changes
2. **Start gradually** - pick one suggestion to implement this week
3. **Track your progress** - keep a simple journal of what works
4. **Be patient** - natural approaches often take time to show benefits
5. **Stay consistent** - small daily practices compound over time

---

*This plan was generated with care using AI-powered medical document analysis. It represents a bridge between conventional medicine and natural wellness approaches.*

🌿 **Your journey to natural wellness begins now.**
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _generate_html(
        self, 
        plan: WellnessPlan, 
        patient_id: str, 
        timestamp: str
    ) -> Path:
        """Generate an HTML report with styling."""
        filename = f"wellness_report_{patient_id}_{timestamp}.html"
        filepath = self.output_dir / filename
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Wellness Transformation Plan</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
        }}
        .container {{
            background: white;
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c5f2d;
            border-bottom: 3px solid #97bc62;
            padding-bottom: 15px;
            font-size: 2.5em;
        }}
        h2 {{
            color: #4a7c59;
            margin-top: 40px;
            font-size: 1.8em;
        }}
        h3 {{
            color: #6b8e6b;
            font-size: 1.3em;
        }}
        .summary {{
            background: #f0f7f0;
            padding: 25px;
            border-radius: 10px;
            border-left: 5px solid #97bc62;
            margin: 20px 0;
        }}
        .alternative {{
            background: #fafafa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid #4a7c59;
        }}
        .evidence {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .evidence-high {{ background: #d4edda; color: #155724; }}
        .evidence-moderate {{ background: #fff3cd; color: #856404; }}
        .evidence-preliminary {{ background: #f8d7da; color: #721c24; }}
        ul {{
            padding-left: 25px;
        }}
        li {{
            margin: 10px 0;
            position: relative;
        }}
        li::marker {{
            color: #4a7c59;
        }}
        .disclaimer {{
            background: #fff8e1;
            border: 2px solid #ffc107;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
            font-size: 0.95em;
        }}
        .next-steps {{
            background: #e3f2fd;
            padding: 25px;
            border-radius: 10px;
            margin-top: 30px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-style: italic;
        }}
        .emoji {{
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1><span class="emoji">🌿</span> Your Personal Wellness Transformation Plan</h1>
        <p style="color: #666;"><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        
        <h2><span class="emoji">📝</span> Your Case Summary</h2>
        <div class="summary">
            {plan.case_summary}
        </div>
        
        <h2><span class="emoji">🌱</span> Natural Alternatives & Complementary Approaches</h2>
"""
        
        if plan.natural_alternatives:
            by_category = {}
            for alt in plan.natural_alternatives:
                cat = alt.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(alt)
            
            for category, alts in by_category.items():
                html_content += f"<h3>{category.title()} Approaches</h3>"
                for alt in alts:
                    evidence_class = f"evidence-{alt.evidence_level}"
                    html_content += f"""
        <div class="alternative">
            <strong>{alt.original}</strong> → <em>{alt.alternative}</em><br>
            <span class="evidence {evidence_class}">Evidence: {alt.evidence_level.title()}</span>
            <p>{alt.description}</p>
        </div>
"""
        
        html_content += f"""
        <h2><span class="emoji">🧘</span> Mindfulness Practices</h2>
        <ul>
"""
        for practice in plan.mindfulness_practices:
            html_content += f"            <li>{practice}</li>\n"
        
        html_content += f"""        </ul>
        
        <h2><span class="emoji">🥗</span> Nutritional Suggestions</h2>
        <ul>
"""
        for suggestion in plan.nutritional_suggestions:
            html_content += f"            <li>{suggestion}</li>\n"
        
        html_content += f"""        </ul>
        
        <h2><span class="emoji">🌅</span> Lifestyle Modifications</h2>
        <ul>
"""
        for mod in plan.lifestyle_modifications:
            html_content += f"            <li>{mod}</li>\n"
        
        html_content += f"""        </ul>
        
        <h2><span class="emoji">🤝</span> The Combined Approach</h2>
        <p>{plan.combined_approach}</p>
        
        <div class="disclaimer">
            <strong>⚠️ Important Disclaimer</strong><br>
            {plan.disclaimer}
        </div>
        
        <div class="next-steps">
            <h3><span class="emoji">🎯</span> Next Steps</h3>
            <ol>
                <li><strong>Review with your healthcare provider</strong> before making any changes</li>
                <li><strong>Start gradually</strong> - pick one suggestion to implement this week</li>
                <li><strong>Track your progress</strong> - keep a simple journal of what works</li>
                <li><strong>Be patient</strong> - natural approaches often take time to show benefits</li>
                <li><strong>Stay consistent</strong> - small daily practices compound over time</li>
            </ol>
        </div>
        
        <div class="footer">
            <p><span class="emoji">🌿</span> Your journey to natural wellness begins now.</p>
            <p style="font-size: 0.9em; color: #999;">
                This plan was generated with care using AI-powered medical document analysis.
            </p>
        </div>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_json(
        self, 
        plan: WellnessPlan, 
        patient_id: str, 
        timestamp: str
    ) -> Path:
        """Generate a JSON report."""
        filename = f"wellness_report_{patient_id}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'patient_id': patient_id,
                'version': '1.0'
            },
            'wellness_plan': plan.to_dict()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        return filepath
