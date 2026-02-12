"""
Adaptive Learning Engine for Guardrails

Learns from violations and patterns to improve guardrail rules
and provide intelligent recommendations.
"""

import json
import pickle
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
import logging
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class ViolationPattern:
    """Represents a learned violation pattern."""
    pattern_id: str
    violation_type: str
    context_features: Dict[str, Any]
    frequency: int
    confidence: float
    suggested_fixes: List[str]
    created_at: datetime
    last_seen: datetime
    success_rate: float = 0.0


@dataclass
class ModuleCluster:
    """Represents a cluster of similar modules."""
    cluster_id: int
    module_names: List[str]
    common_traits: List[str]
    common_violations: List[str]
    personality_profile: Dict[str, Any]
    guardrail_rules: List[Dict[str, Any]]


class QCurveBand(Enum):
    """Q-curve risk bands for guardrail profiling."""
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"


@dataclass
class QCurveProfile:
    """Represents a Q-curve profile for a module."""
    module: str
    score: int
    band: QCurveBand
    leading_signals: Dict[str, Any]
    lagging_signals: Dict[str, Any]
    updated_at: datetime


class PatternExtractor:
    """Extracts patterns from violation data."""
    
    def __init__(self):
        self.context_features = [
            "module_path_depth",
            "has_tests",
            "is_config_module",
            "is_main_module",
            "import_count",
            "line_count",
        ]
        
    def extract_context(self, violation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context features from a violation."""
        module_name = violation_data.get("module", "")
        
        features = {
            "module_path_depth": module_name.count('.'),
            "has_tests": "test" in module_name.lower(),
            "is_config_module": any(x in module_name.lower() for x in ["config", "settings"]),
            "is_main_module": module_name.endswith("__main__") or module_name.endswith("main"),
            "import_count": violation_data.get("import_count", 0),
            "line_count": violation_data.get("line_count", 0),
        }
        
        return features
        
    def find_patterns(self, violations: List[Dict[str, Any]]) -> List[ViolationPattern]:
        """Find recurring patterns in violations."""
        patterns = []
        
        # Group by violation type
        by_type = defaultdict(list)
        for v in violations:
            by_type[v["type"]].append(v)
            
        # Find patterns within each type
        for vtype, type_violations in by_type.items():
            # Extract contexts
            contexts = [self.extract_context(v) for v in type_violations]
            
            # Cluster similar contexts
            if len(contexts) > 1:
                clusters = self._cluster_contexts(contexts)
                
                for cluster_id, cluster_violations in clusters.items():
                    pattern = self._create_pattern(
                        vtype,
                        cluster_violations,
                        cluster_id
                    )
                    patterns.append(pattern)
                    
        return patterns
        
    def _cluster_contexts(self, contexts: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """Cluster similar contexts using simple heuristics."""
        clusters = defaultdict(list)
        
        # Simple clustering based on key features
        for i, context in enumerate(contexts):
            # Create a simple hash for clustering
            key = (
                context["module_path_depth"] // 2,  # Group by depth ranges
                context["has_tests"],
                context["is_config_module"],
                min(context["import_count"] // 5, 5),  # Group by import count ranges
            )
            clusters[key].append(context)
            
        # Convert to numeric cluster IDs
        return {i: list(clusters.values())[i] for i in range(len(clusters))}
        
    def _create_pattern(self, vtype: str, violations: List[Dict[str, Any]], cluster_id: int) -> ViolationPattern:
        """Create a pattern from a cluster of violations."""
        # Calculate frequency and confidence
        frequency = len(violations)
        confidence = min(frequency / 10.0, 1.0)  # Normalize to 0-1
        
        # Extract common context
        contexts = [self.extract_context(v) for v in violations]
        common_context = {}
        
        for feature in self.context_features:
            values = [c.get(feature) for c in contexts]
            if all(isinstance(v, bool) for v in values):
                common_context[feature] = all(values)
            elif all(isinstance(v, (int, float)) for v in values):
                common_context[feature] = np.mean(values)
                
        # Suggest fixes based on violation type
        suggested_fixes = self._get_suggested_fixes(vtype, violations)
        
        return ViolationPattern(
            pattern_id=f"{vtype}_cluster_{cluster_id}",
            violation_type=vtype,
            context_features=common_context,
            frequency=frequency,
            confidence=confidence,
            suggested_fixes=suggested_fixes,
            created_at=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )
        
    def _get_suggested_fixes(self, vtype: str, violations: List[Dict[str, Any]]) -> List[str]:
        """Get suggested fixes for a violation type."""
        fixes = {
            "hardcoded_path": [
                "Use environment variables for paths",
                "Implement a path configuration system",
                "Use pathlib for cross-platform compatibility",
            ],
            "circular_import": [
                "Extract common code to separate module",
                "Use dependency injection",
                "Reorganize module structure",
            ],
            "missing_dependency": [
                "Update requirements.txt",
                "Add optional import with fallback",
                "Document optional dependencies",
            ],
            "side_effect": [
                "Move to function/class level",
                "Use lazy initialization",
                "Add __all__ to control exports",
            ],
        }
        
        return fixes.get(vtype, ["Review module structure"])


class RuleGenerator:
    """Generates guardrail rules from learned patterns."""
    
    def __init__(self):
        self.rule_templates = {
            "hardcoded_path": {
                "condition": "module.has_hardcoded_paths",
                "action": "validate_paths",
                "severity": "warning",
                "message": "Module {module} has hardcoded paths",
            },
            "circular_import": {
                "condition": "module.is_circular_prone",
                "action": "check_import_order",
                "severity": "error",
                "message": "Circular import detected in {module}",
            },
            "missing_dependency": {
                "condition": "module.has_conditional_imports",
                "action": "validate_dependencies",
                "severity": "warning",
                "message": "Module {module} has missing dependencies",
            },
        }
        
    def generate_rules(self, patterns: List[ViolationPattern]) -> List[Dict[str, Any]]:
        """Generate guardrail rules from patterns."""
        rules = []
        
        for pattern in patterns:
            if pattern.confidence > 0.5:  # Only generate rules for confident patterns
                rule = self._create_rule_from_pattern(pattern)
                rules.append(rule)
                
        return rules
        
    def _create_rule_from_pattern(self, pattern: ViolationPattern) -> Dict[str, Any]:
        """Create a rule from a pattern."""
        template = self.rule_templates.get(pattern.violation_type, {})
        
        rule = {
            "id": pattern.pattern_id,
            "type": pattern.violation_type,
            "condition": self._build_condition(pattern),
            "action": template.get("action", "log"),
            "severity": template.get("severity", "warning"),
            "message": template.get("message", "Violation detected"),
            "confidence": pattern.confidence,
            "suggested_fixes": pattern.suggested_fixes,
            "context": pattern.context_features,
        }
        
        return rule
        
    def _build_condition(self, pattern: ViolationPattern) -> str:
        """Build a condition expression for the rule."""
        conditions = []
        
        for feature, value in pattern.context_features.items():
            if isinstance(value, bool):
                conditions.append(f"module.{feature} == {value}")
            elif isinstance(value, (int, float)):
                conditions.append(f"module.{feature} >= {value}")
                
        return " and ".join(conditions) if conditions else "True"


class AdaptiveEngine:
    """Main adaptive learning engine."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("guardrail_learning_data")
        self.storage_path.mkdir(exist_ok=True)
        
        self.pattern_extractor = PatternExtractor()
        self.rule_generator = RuleGenerator()
        
        # Learning data
        self.violations: List[Dict[str, Any]] = []
        self.patterns: List[ViolationPattern] = []
        self.rules: List[Dict[str, Any]] = []
        self.clusters: List[ModuleCluster] = []
        
        # Performance tracking
        self.rule_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "applied": 0,
            "successful": 0,
            "false_positives": 0,
        })
        
        # Load existing data
        self._load_learning_data()
        
    def add_violation(self, violation_data: Dict[str, Any]) -> None:
        """Add a new violation to learn from."""
        self.violations.append({
            **violation_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Trigger learning periodically
        if len(self.violations) % 10 == 0:
            self.learn()
            
    def learn(self) -> None:
        """Learn from accumulated violations."""
        logger.info(f"Starting learning from {len(self.violations)} violations")
        
        # Extract patterns
        self.patterns = self.pattern_extractor.find_patterns(self.violations)
        logger.info(f"Extracted {len(self.patterns)} patterns")
        
        # Generate rules
        new_rules = self.rule_generator.generate_rules(self.patterns)
        
        # Merge with existing rules
        self._merge_rules(new_rules)
        logger.info(f"Generated {len(new_rules)} rules, total: {len(self.rules)}")
        
        # Cluster modules
        self._cluster_modules()
        
        # Save learning data
        self._save_learning_data()
        
    def get_recommendations(self, module_name: str, module_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations for a module based on learned patterns."""
        recommendations = []
        
        # Find similar modules
        similar_modules = self._find_similar_modules(module_name, module_data)
        
        # Get their violations and fixes
        for similar in similar_modules[:5]:  # Top 5 similar
            similar_violations = [
                v for v in self.violations
                if v.get("module") == similar["name"]
            ]
            
            for violation in similar_violations:
                recommendations.append({
                    "type": "prevention",
                    "based_on": similar["name"],
                    "similarity": similar["similarity"],
                    "violation": violation["type"],
                    "suggestion": f"Module {similar['name']} had this issue",
                    "fixes": self._get_fixes_for_violation(violation["type"]),
                })
                
        # Check against learned rules
        applicable_rules = [
            rule for rule in self.rules
            if self._rule_applies(rule, module_data)
        ]
        
        for rule in applicable_rules:
            recommendations.append({
                "type": "rule_based",
                "rule_id": rule["id"],
                "confidence": rule["confidence"],
                "suggestion": rule["message"].format(module=module_name),
                "fixes": rule["suggested_fixes"],
            })
            
        return recommendations

    def get_q_curve_profile(self, module_name: str, module_data: Dict[str, Any]) -> QCurveProfile:
        """Compute a Q-curve profile for a module."""
        leading_signals = self._extract_leading_signals(module_data)
        lagging_signals = self._extract_lagging_signals(module_name)

        score = self._calculate_q_curve_score(leading_signals, lagging_signals)
        band = self._resolve_q_curve_band(score)

        return QCurveProfile(
            module=module_name,
            score=score,
            band=band,
            leading_signals=leading_signals,
            lagging_signals=lagging_signals,
            updated_at=datetime.now(timezone.utc),
        )
        
    def update_rule_performance(self, rule_id: str, success: bool, false_positive: bool = False) -> None:
        """Update the performance metrics for a rule."""
        perf = self.rule_performance[rule_id]
        perf["applied"] += 1
        
        if success:
            perf["successful"] += 1
        if false_positive:
            perf["false_positives"] += 1
            
        # Recalculate success rate
        perf["success_rate"] = perf["successful"] / perf["applied"] if perf["applied"] > 0 else 0
        
        # Disable rules with high false positive rates
        if perf["false_positives"] / perf["applied"] > 0.3 and perf["applied"] > 10:
            logger.warning(f"Disabling rule {rule_id} due to high false positive rate")
            for rule in self.rules:
                if rule["id"] == rule_id:
                    rule["disabled"] = True
                    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning progress."""
        return {
            "violations_analyzed": len(self.violations),
            "patterns_discovered": len(self.patterns),
            "rules_generated": len(self.rules),
            "modules_clustered": len(self.clusters),
            "rule_performance": dict(self.rule_performance),
            "last_learning": max([p.created_at for p in self.patterns], default=None),
        }

    def _extract_leading_signals(self, module_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract leading signals from module data."""
        trait_flags = {
            "path_dependent": bool(module_data.get("is_path_dependent")),
            "runtime_fragile": bool(module_data.get("is_runtime_fragile")),
            "circular_prone": bool(module_data.get("is_circular_prone")),
            "import_heavy": bool(module_data.get("is_import_heavy")),
            "side_effects": bool(module_data.get("has_side_effects")),
            "stateful": bool(module_data.get("is_stateful")),
        }

        evidence_counts = {
            "hardcoded_paths": int(module_data.get("hardcoded_paths", 0)),
            "conditional_imports": int(module_data.get("conditional_imports", 0)),
            "import_count": int(module_data.get("import_count", 0)),
            "line_count": int(module_data.get("line_count", 0)),
        }

        return {
            "traits": trait_flags,
            "evidence": evidence_counts,
        }

    def _extract_lagging_signals(self, module_name: str) -> Dict[str, Any]:
        """Extract lagging signals from violation history."""
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(days=7)
        recent = []

        for violation in self.violations:
            if violation.get("module") != module_name:
                continue
            timestamp = violation.get("timestamp")
            if not timestamp:
                continue
            try:
                occurred_at = datetime.fromisoformat(timestamp)
                if occurred_at.tzinfo is None:
                    occurred_at = occurred_at.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if occurred_at >= lookback:
                recent.append(violation)

        severity_counts = Counter(v.get("severity", "warning") for v in recent)
        type_counts = Counter(v.get("type", "unknown") for v in recent)

        return {
            "recent_violations": len(recent),
            "severity_counts": dict(severity_counts),
            "type_counts": dict(type_counts),
        }

    def _calculate_q_curve_score(self, leading: Dict[str, Any], lagging: Dict[str, Any]) -> int:
        """Calculate a Q-curve score from leading and lagging signals."""
        trait_weights = {
            "path_dependent": 18,
            "runtime_fragile": 15,
            "circular_prone": 22,
            "import_heavy": 8,
            "side_effects": 6,
            "stateful": 6,
        }

        leading_score = 0
        for trait, weight in trait_weights.items():
            if leading["traits"].get(trait):
                leading_score += weight

        evidence = leading.get("evidence", {})
        leading_score += min(evidence.get("hardcoded_paths", 0) * 4, 12)
        leading_score += min(evidence.get("conditional_imports", 0) * 3, 9)
        leading_score += 3 if evidence.get("import_count", 0) > 15 else 0
        leading_score += 3 if evidence.get("line_count", 0) > 400 else 0

        lagging_score = 0
        recent_violations = lagging.get("recent_violations", 0)
        lagging_score += min(recent_violations * 5, 35)

        severity_counts = lagging.get("severity_counts", {})
        lagging_score += severity_counts.get("error", 0) * 6
        lagging_score += severity_counts.get("warning", 0) * 2

        score = int(min(100, leading_score * 0.6 + lagging_score * 0.4))
        return score

    def _resolve_q_curve_band(self, score: int) -> QCurveBand:
        """Resolve Q-curve band from score."""
        if score >= 60:
            return QCurveBand.H3
        if score >= 30:
            return QCurveBand.H2
        return QCurveBand.H1
        
    def _find_similar_modules(self, module_name: str, module_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find modules similar to the given module."""
        similar: Dict[str, float] = {}

        target_violation_types = set()
        if module_data.get("has_hardcoded_paths"):
            target_violation_types.add("hardcoded_path")
        if module_data.get("is_circular_prone"):
            target_violation_types.add("circular_import")
        if module_data.get("has_conditional_imports"):
            target_violation_types.add("missing_dependency")
        if module_data.get("has_side_effects"):
            target_violation_types.add("side_effect")
        
        # Simple similarity based on path structure
        target_parts = module_name.split('.')
        
        for violation in self.violations:
            other_module = violation.get("module", "")
            if other_module == module_name:
                continue
                
            other_parts = other_module.split('.')
            
            # Calculate similarity (Jaccard on path parts)
            target_set = set(target_parts)
            other_set = set(other_parts)
            
            intersection = len(target_set & other_set)
            union = len(target_set | other_set)
            
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.3:
                similar[other_module] = max(similar.get(other_module, 0.0), similarity)
                continue

            if target_violation_types and violation.get("type") in target_violation_types:
                similar[other_module] = max(similar.get(other_module, 0.0), 0.35)

        return [
            {"name": name, "similarity": score}
            for name, score in sorted(similar.items(), key=lambda item: item[1], reverse=True)
        ]
        
    def _cluster_modules(self) -> None:
        """Cluster modules based on their traits and violations."""
        # Extract module features
        module_features = {}
        
        for violation in self.violations:
            module = violation.get("module", "")
            if module not in module_features:
                module_features[module] = {
                    "violations": defaultdict(int),
                    "traits": set(),
                }
                
            module_features[module]["violations"][violation["type"]] += 1
            
        # Simple clustering based on violation patterns
        clusters = defaultdict(list)
        
        for module, features in module_features.items():
            # Create a signature based on violation types
            signature = tuple(sorted(features["violations"].keys()))
            clusters[signature].append(module)
            
        # Convert to ModuleCluster objects
        self.clusters = []
        for i, (signature, modules) in enumerate(clusters.items()):
            if len(modules) > 1:  # Only keep clusters with multiple modules
                cluster = ModuleCluster(
                    cluster_id=i,
                    module_names=modules,
                    common_traits=list(signature),
                    common_violations=list(signature),
                    personality_profile=self._infer_cluster_personality(modules),
                    guardrail_rules=self._get_cluster_rules(modules),
                )
                self.clusters.append(cluster)
                
    def _infer_cluster_personality(self, modules: List[str]) -> Dict[str, Any]:
        """Infer personality profile for a cluster of modules."""
        # Aggregate traits from modules in cluster
        traits = defaultdict(int)
        
        for module in modules:
            for violation in self.violations:
                if violation.get("module") == module:
                    traits[violation["type"]] += 1
                    
        # Determine dominant traits
        total = sum(traits.values())
        personality = {
            "dominant_violation": max(traits, key=traits.get) if traits else None,
            "violation_distribution": {k: v/total for k, v in traits.items()},
            "risk_level": "high" if total > len(modules) * 2 else "medium" if total > len(modules) else "low",
        }
        
        return personality
        
    def _get_cluster_rules(self, modules: List[str]) -> List[Dict[str, Any]]:
        """Get rules that apply to modules in a cluster."""
        cluster_rules = []
        
        for rule in self.rules:
            # Check if rule applies to any module in cluster
            for module in modules:
                if self._rule_applies_to_module(rule, module):
                    cluster_rules.append(rule)
                    break
                    
        return cluster_rules
        
    def _rule_applies(self, rule: Dict[str, Any], module_data: Dict[str, Any]) -> bool:
        """Check if a rule applies to module data."""
        # Simple rule application logic
        condition = rule.get("condition", "True")
        
        # For now, just check if module has relevant traits
        if "hardcoded_path" in rule["type"] and module_data.get("has_hardcoded_paths"):
            return True
        if "circular_import" in rule["type"] and module_data.get("is_circular_prone"):
            return True
        if "missing_dependency" in rule["type"] and module_data.get("has_conditional_imports"):
            return True
            
        return False
        
    def _rule_applies_to_module(self, rule: Dict[str, Any], module_name: str) -> bool:
        """Check if a rule applies to a specific module."""
        # Check violations for this module
        for violation in self.violations:
            if violation.get("module") == module_name:
                if rule["type"] == violation["type"]:
                    return True
        return False
        
    def _merge_rules(self, new_rules: List[Dict[str, Any]]) -> None:
        """Merge new rules with existing ones."""
        existing_ids = {r["id"] for r in self.rules}
        
        for rule in new_rules:
            if rule["id"] not in existing_ids:
                self.rules.append(rule)
            else:
                # Update existing rule
                for i, existing in enumerate(self.rules):
                    if existing["id"] == rule["id"]:
                        # Update confidence if higher
                        if rule["confidence"] > existing["confidence"]:
                            self.rules[i] = rule
                        break
                        
    def _get_fixes_for_violation(self, violation_type: str) -> List[str]:
        """Get fixes for a violation type."""
        fixes = {
            "hardcoded_path": ["Use environment variables", "Use pathlib.Path"],
            "circular_import": ["Extract common code", "Use dependency injection"],
            "missing_dependency": ["Update requirements", "Add optional imports"],
            "side_effect": ["Move to function", "Use lazy initialization"],
        }
        return fixes.get(violation_type, ["Review module"])
        
    def _save_learning_data(self) -> None:
        """Save learning data to disk."""
        data = {
            "violations": self.violations[-1000:],  # Keep last 1000
            "patterns": [asdict(p) for p in self.patterns],
            "rules": self.rules,
            "rule_performance": dict(self.rule_performance),
        }
        
        with open(self.storage_path / "learning_data.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
            
    def _load_learning_data(self) -> None:
        """Load learning data from disk."""
        data_file = self.storage_path / "learning_data.json"
        
        if data_file.exists():
            try:
                with open(data_file, "r") as f:
                    data = json.load(f)
                    
                self.violations = data.get("violations", [])
                
                # Reconstruct patterns
                self.patterns = []
                for p_data in data.get("patterns", []):
                    pattern = ViolationPattern(**p_data)
                    self.patterns.append(pattern)
                    
                self.rules = data.get("rules", [])
                self.rule_performance = defaultdict(lambda: {
                    "applied": 0,
                    "successful": 0,
                    "false_positives": 0,
                })
                self.rule_performance.update(data.get("rule_performance", {}))
                
                logger.info(f"Loaded learning data: {len(self.violations)} violations, {len(self.patterns)} patterns")
            except Exception as e:
                logger.error(f"Failed to load learning data: {e}")


# Global adaptive engine instance
_adaptive_engine: Optional[AdaptiveEngine] = None


def get_adaptive_engine() -> AdaptiveEngine:
    """Get the global adaptive engine instance."""
    global _adaptive_engine
    if _adaptive_engine is None:
        _adaptive_engine = AdaptiveEngine()
    return _adaptive_engine


def learn_from_violation(violation_data: Dict[str, Any]) -> None:
    """Convenience function to learn from a violation."""
    engine = get_adaptive_engine()
    engine.add_violation(violation_data)


def get_module_recommendations(module_name: str, module_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get recommendations for a module."""
    engine = get_adaptive_engine()
    return engine.get_recommendations(module_name, module_data)


def get_q_curve_profile(module_name: str, module_data: Dict[str, Any]) -> QCurveProfile:
    """Get Q-curve profile for a module."""
    engine = get_adaptive_engine()
    return engine.get_q_curve_profile(module_name, module_data)
