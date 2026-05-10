"""
Security Policy Enforcement for PromptOps
==========================================

Policy-based security enforcement for container scanning.
Enforces vulnerability thresholds and compliance rules.

Author: DevOps Engineer - Phase 6 Week 58-59
Date: 2026-05-10
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class PolicyAction(Enum):
    """Policy actions."""
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


class PolicyScope(Enum):
    """Policy scopes."""
    GLOBAL = "global"
    PROJECT = "project"
    ENVIRONMENT = "environment"


# ============================================================================
# Security Policy Engine
# ============================================================================

class SecurityPolicy:
    """
    Security policy enforcement engine.

    Features:
    - Vulnerability threshold enforcement
    - License compliance checking
    - SBOM validation
    - Custom policy rules
    - Risk-based decisions
    - Exemption management
    """

    def __init__(self):
        """Initialize Security Policy Engine."""
        self.policies = []
        self.exemptions = []
        self.default_policy = self._get_default_policy()

    def _get_default_policy(self) -> Dict[str, Any]:
        """Get default security policy."""
        return {
            "name": "default",
            "scope": PolicyScope.GLOBAL.value,
            "rules": {
                "max_critical": 0,
                "max_high": 5,
                "max_medium": 20,
                "max_low": 100,
                "block_unfixed_critical": True,
                "block_unfixed_high": True,
                "require_sbom": True,
                "allowed_licenses": [
                    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
                    "ISC", "MPL-2.0", "LGPL-2.1", "LGPL-3.0"
                ],
                "blocked_licenses": [
                    "GPL-3.0", "AGPL-3.0", "SSPL-1.0"
                ],
                "max_risk_score": 50.0
            },
            "actions": {
                "critical_violation": PolicyAction.BLOCK.value,
                "high_violation": PolicyAction.BLOCK.value,
                "medium_violation": PolicyAction.WARN.value,
                "low_violation": PolicyAction.ALLOW.value
            }
        }

    def add_policy(
        self,
        name: str,
        scope: str,
        rules: Dict[str, Any],
        actions: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Add security policy.

        Args:
            name: Policy name
            scope: Policy scope
            rules: Policy rules
            actions: Policy actions

        Returns:
            Created policy
        """
        policy = {
            "name": name,
            "scope": scope,
            "rules": rules,
            "actions": actions or self.default_policy["actions"],
            "created_at": datetime.utcnow().isoformat()
        }

        self.policies.append(policy)
        logger.info(f"Added policy: {name}")

        return policy

    def evaluate_scan_results(
        self,
        scan_results: Dict[str, Any],
        policy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate scan results against policy.

        Args:
            scan_results: Security scan results
            policy_name: Policy to evaluate against

        Returns:
            Policy evaluation result
        """
        logger.info("Evaluating scan results against policy")

        policy = self._get_policy(policy_name) or self.default_policy

        summary = scan_results.get("summary", {})
        violations = []
        warnings = []

        # Check vulnerability thresholds
        rules = policy["rules"]

        critical_count = summary.get("critical_count", 0)
        if critical_count > rules.get("max_critical", 0):
            violations.append({
                "rule": "max_critical",
                "severity": "CRITICAL",
                "current": critical_count,
                "allowed": rules["max_critical"],
                "message": f"Critical vulnerabilities ({critical_count}) exceed threshold ({rules['max_critical']})"
            })

        high_count = summary.get("high_count", 0)
        if high_count > rules.get("max_high", 5):
            violations.append({
                "rule": "max_high",
                "severity": "HIGH",
                "current": high_count,
                "allowed": rules["max_high"],
                "message": f"High vulnerabilities ({high_count}) exceed threshold ({rules['max_high']})"
            })

        medium_count = summary.get("medium_count", 0)
        if medium_count > rules.get("max_medium", 20):
            warnings.append({
                "rule": "max_medium",
                "severity": "MEDIUM",
                "current": medium_count,
                "allowed": rules["max_medium"],
                "message": f"Medium vulnerabilities ({medium_count}) exceed threshold ({rules['max_medium']})"
            })

        # Determine overall action
        action = self._determine_action(policy, violations, warnings)

        result = {
            "policy_name": policy["name"],
            "action": action,
            "compliant": action != PolicyAction.BLOCK.value,
            "violations": violations,
            "warnings": warnings,
            "summary": {
                "total_violations": len(violations),
                "total_warnings": len(warnings),
                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count
            },
            "evaluated_at": datetime.utcnow().isoformat()
        }

        return result

    def _get_policy(self, policy_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get policy by name."""
        if not policy_name:
            return None

        for policy in self.policies:
            if policy["name"] == policy_name:
                return policy

        return None

    def _determine_action(
        self,
        policy: Dict[str, Any],
        violations: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ) -> str:
        """Determine policy action based on violations."""
        if violations:
            # Check if any critical/high violations exist
            for violation in violations:
                if violation["severity"] in ["CRITICAL", "HIGH"]:
                    return policy["actions"].get("critical_violation", PolicyAction.BLOCK.value)

        if warnings:
            return policy["actions"].get("medium_violation", PolicyAction.WARN.value)

        return PolicyAction.ALLOW.value

    def evaluate_licenses(
        self,
        sbom_data: Dict[str, Any],
        policy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate SBOM licenses against policy.

        Args:
            sbom_data: SBOM data
            policy_name: Policy to evaluate against

        Returns:
            License evaluation result
        """
        logger.info("Evaluating licenses against policy")

        policy = self._get_policy(policy_name) or self.default_policy
        rules = policy["rules"]

        violations = []
        warnings = []

        # Extract licenses from SBOM
        licenses = self._extract_licenses(sbom_data)

        allowed = set(rules.get("allowed_licenses", []))
        blocked = set(rules.get("blocked_licenses", []))

        for license_id, count in licenses.items():
            if license_id in blocked:
                violations.append({
                    "license": license_id,
                    "count": count,
                    "message": f"Blocked license {license_id} found in {count} component(s)"
                })
            elif allowed and license_id not in allowed and license_id != "NOASSERTION":
                warnings.append({
                    "license": license_id,
                    "count": count,
                    "message": f"Non-approved license {license_id} found in {count} component(s)"
                })

        action = PolicyAction.BLOCK.value if violations else (PolicyAction.WARN.value if warnings else PolicyAction.ALLOW.value)

        return {
            "policy_name": policy["name"],
            "action": action,
            "compliant": action != PolicyAction.BLOCK.value,
            "violations": violations,
            "warnings": warnings,
            "total_licenses": len(licenses),
            "evaluated_at": datetime.utcnow().isoformat()
        }

    def _extract_licenses(self, sbom_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract licenses from SBOM."""
        licenses = {}

        # SPDX format
        if "spdxVersion" in sbom_data:
            for pkg in sbom_data.get("packages", []):
                lic = pkg.get("licenseConcluded", "NOASSERTION")
                licenses[lic] = licenses.get(lic, 0) + 1

        # CycloneDX format
        elif "bomFormat" in sbom_data:
            for comp in sbom_data.get("components", []):
                for lic_info in comp.get("licenses", []):
                    lic = lic_info.get("license", {}).get("id", "NOASSERTION")
                    licenses[lic] = licenses.get(lic, 0) + 1

        return licenses

    def add_exemption(
        self,
        vuln_id: str,
        reason: str,
        expiry_date: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add vulnerability exemption.

        Args:
            vuln_id: Vulnerability ID to exempt
            reason: Exemption reason
            expiry_date: Exemption expiry date
            approved_by: Approver name

        Returns:
            Exemption record
        """
        exemption = {
            "vuln_id": vuln_id,
            "reason": reason,
            "expiry_date": expiry_date,
            "approved_by": approved_by,
            "created_at": datetime.utcnow().isoformat()
        }

        self.exemptions.append(exemption)
        logger.info(f"Added exemption for {vuln_id}")

        return exemption

    def is_exempted(self, vuln_id: str) -> bool:
        """Check if vulnerability is exempted."""
        for exemption in self.exemptions:
            if exemption["vuln_id"] == vuln_id:
                # Check if exemption is still valid
                if exemption.get("expiry_date"):
                    expiry = datetime.fromisoformat(exemption["expiry_date"])
                    if datetime.utcnow() > expiry:
                        continue

                return True

        return False

    def generate_compliance_report(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate compliance report.

        Args:
            evaluations: List of policy evaluations

        Returns:
            Compliance report
        """
        total_scans = len(evaluations)
        compliant = sum(1 for e in evaluations if e.get("compliant", False))
        blocked = sum(1 for e in evaluations if e.get("action") == PolicyAction.BLOCK.value)

        return {
            "total_scans": total_scans,
            "compliant": compliant,
            "non_compliant": total_scans - compliant,
            "blocked": blocked,
            "compliance_rate": round((compliant / total_scans * 100), 2) if total_scans > 0 else 0,
            "generated_at": datetime.utcnow().isoformat()
        }


# ============================================================================
# Testing
# ============================================================================

def test_security_policy():
    """Test Security Policy Engine."""
    logger.info("Testing Security Policy Engine...")

    policy_engine = SecurityPolicy()

    # Test 1: Evaluate scan results
    print("\n=== Test 1: Evaluate Scan Results ===")
    scan_results = {
        "summary": {
            "total_vulnerabilities": 45,
            "critical_count": 2,
            "high_count": 8,
            "medium_count": 15,
            "low_count": 20
        }
    }

    evaluation = policy_engine.evaluate_scan_results(scan_results)
    print(f"Policy: {evaluation['policy_name']}")
    print(f"Action: {evaluation['action']}")
    print(f"Compliant: {evaluation['compliant']}")
    print(f"Violations: {len(evaluation['violations'])}")
    for violation in evaluation['violations']:
        print(f"  - {violation['message']}")

    # Test 2: Custom policy
    print("\n=== Test 2: Custom Strict Policy ===")
    policy_engine.add_policy(
        name="strict",
        scope="production",
        rules={
            "max_critical": 0,
            "max_high": 0,
            "max_medium": 5,
            "max_low": 20
        }
    )

    strict_eval = policy_engine.evaluate_scan_results(scan_results, policy_name="strict")
    print(f"Policy: {strict_eval['policy_name']}")
    print(f"Action: {strict_eval['action']}")
    print(f"Violations: {len(strict_eval['violations'])}")

    # Test 3: License evaluation
    print("\n=== Test 3: License Evaluation ===")
    sbom_data = {
        "spdxVersion": "SPDX-2.3",
        "packages": [
            {"licenseConcluded": "MIT"},
            {"licenseConcluded": "Apache-2.0"},
            {"licenseConcluded": "GPL-3.0"},  # Blocked
            {"licenseConcluded": "MIT"}
        ]
    }

    license_eval = policy_engine.evaluate_licenses(sbom_data)
    print(f"Action: {license_eval['action']}")
    print(f"Compliant: {license_eval['compliant']}")
    print(f"Violations: {len(license_eval['violations'])}")
    for violation in license_eval['violations']:
        print(f"  - {violation['message']}")

    # Test 4: Exemptions
    print("\n=== Test 4: Exemptions ===")
    exemption = policy_engine.add_exemption(
        vuln_id="CVE-2024-1234",
        reason="False positive - not exploitable in our configuration",
        approved_by="Security Team"
    )
    print(f"Exemption added: {exemption['vuln_id']}")
    print(f"Is exempted: {policy_engine.is_exempted('CVE-2024-1234')}")


if __name__ == "__main__":
    test_security_policy()
