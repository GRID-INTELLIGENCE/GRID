"""
Automated Safety Protocol Generation Module
Generates safety protocols based on detected gaps
"""
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class SafetyProtocolGenerator:
    """Generates safety protocols based on detected gaps"""
    
    def __init__(self):
        self.protocol_templates = {
            "safety_framework": {
                "title": "AI Safety Framework Protocol",
                "sections": ["Mission", "Safety Principles", "Prohibited Applications", "Monitoring Parameters"]
            },
            "content_moderation": {
                "title": "Content Moderation Protocol",
                "sections": ["Content Filtering", "Moderation Thresholds", "Escalation Procedures"]
            },
            "risk_management": {
                "title": "Risk Management Protocol",
                "sections": ["Risk Assessment", "Mitigation Strategies", "Incident Response"]
            }
        }
    
    def generate_protocol(self, provider: str, gaps: List[str], safety_score: int) -> Dict[str, Any]:
        """Generate a safety protocol based on detected gaps"""
        protocol = {
            "protocol_id": f"PROTO-{provider}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "provider": provider,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "title": f"{provider} Safety Protocol",
            "safety_score": safety_score,
            "gaps_detected": gaps,
            "gap_count": len(gaps),
            "severity": self._calculate_severity(len(gaps)),
            "sections": []
        }
        
        # Generate sections based on gaps
        for gap in gaps:
            section = self._generate_section_for_gap(gap, provider)
            protocol["sections"].append(section)
        
        # Add recommendations
        protocol["recommendations"] = self._generate_recommendations(gaps, safety_score)
        
        return protocol
    
    def _calculate_severity(self, gap_count: int) -> str:
        """Calculate protocol severity based on gap count"""
        if gap_count >= 8:
            return "critical"
        elif gap_count >= 5:
            return "high"
        elif gap_count >= 3:
            return "medium"
        else:
            return "low"
    
    def _generate_section_for_gap(self, gap: str, provider: str) -> Dict[str, Any]:
        """Generate a protocol section for a specific gap"""
        section = {
            "gap": gap,
            "provider": provider,
            "section_title": f"Addressing: {gap}",
            "recommendations": []
        }
        
        # Add specific recommendations based on gap type
        if "safety" in gap.lower():
            section["recommendations"].extend([
                "Implement comprehensive safety framework",
                "Document safety evaluation methodology",
                "Establish safety metrics and thresholds"
            ])
        elif "evaluation" in gap.lower():
            section["recommendations"].extend([
                "Create evaluation hub with test cases",
                "Document evaluation protocols",
                "Implement regular safety audits"
            ])
        elif "policy" in gap.lower():
            section["recommendations"].extend([
                "Define clear safety policies",
                "Document policy enforcement procedures",
                "Create policy violation response procedures"
            ])
        elif "moderation" in gap.lower():
            section["recommendations"].extend([
                "Implement content moderation system",
                "Define moderation thresholds",
                "Create escalation procedures"
            ])
        elif "guardrail" in gap.lower():
            section["recommendations"].extend([
                "Implement guardrails for all content",
                "Document guardrail bypass procedures",
                "Create guardrail violation handling"
            ])
        else:
            section["recommendations"].append(f"Address {gap} through policy and procedure")
        
        return section
    
    def _generate_recommendations(self, gaps: List[str], safety_score: int) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        if safety_score < 60:
            recommendations.append("URGENT: Immediate safety framework overhaul required")
            recommendations.append("Implement all missing critical safety components")
        elif safety_score < 80:
            recommendations.append("HIGH PRIORITY: Address major safety gaps")
            recommendations.append("Implement missing safety components")
        else:
            recommendations.append("MAINTENANCE: Continue monitoring and improving safety")
        
        # Provider-specific recommendations
        if any("preparedness" in gap.lower() for gap in gaps):
            recommendations.append("Implement Preparedness Framework with red teaming")
        
        if any("constitutional" in gap.lower() for gap in gaps):
            recommendations.append("Implement Constitutional AI principles")
        
        if any("frontier" in gap.lower() for gap in gaps):
            recommendations.append("Implement Frontier Safety Framework")
        
        if any("risk" in gap.lower() for gap in gaps):
            recommendations.append("Implement comprehensive Risk Management Framework")
        
        return recommendations
    
    def export_protocol(self, protocol: Dict[str, Any], format: str = "json") -> str:
        """Export protocol in specified format"""
        if format == "json":
            return json.dumps(protocol, indent=2)
        elif format == "markdown":
            return self._export_as_markdown(protocol)
        else:
            return json.dumps(protocol, indent=2)
    
    def _export_as_markdown(self, protocol: Dict[str, Any]) -> str:
        """Export protocol as markdown"""
        md = f"# {protocol['title']}\n\n"
        md += f"**Provider:** {protocol['provider']}\n"
        md += f"**Safety Score:** {protocol['safety_score']}/100\n"
        md += f"**Severity:** {protocol['severity'].upper()}\n"
        md += f"**Gaps Detected:** {protocol['gap_count']}\n\n"
        
        md += "## Gaps Detected\n"
        for gap in protocol['gaps_detected']:
            md += f"- {gap}\n"
        
        md += "\n## Recommendations\n"
        for rec in protocol['recommendations']:
            md += f"- {rec}\n"
        
        md += "\n## Protocol Sections\n"
        for section in protocol['sections']:
            md += f"\n### {section['section_title']}\n"
            for rec in section['recommendations']:
                md += f"- {rec}\n"
        
        return md
