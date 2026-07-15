"""Deterministic, explainable marketing content preflight checks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def finding(rule: str, severity: str, evidence: str, recommendation: str) -> dict[str, str]:
    return {"rule": rule, "severity": severity, "evidence": evidence, "recommendation": recommendation}


def review(campaign: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    text = str(campaign.get("text", "")).strip()
    channel = str(campaign.get("channel", "")).lower().strip()
    if not text or channel not in {"email", "social", "landing_page", "ad"}:
        raise ValueError("text is required and channel must be email, social, landing_page, or ad")
    findings: list[dict[str, str]] = []
    lower = text.lower()

    for phrase in policy.get("prohibited_phrases", []):
        if str(phrase).lower() in lower:
            findings.append(finding("brand.prohibited_phrase", "high", str(phrase), "Replace with specific, supportable language."))

    for claim in policy.get("absolute_claims", []):
        if re.search(rf"\b{re.escape(str(claim).lower())}\b", lower):
            findings.append(finding("claims.absolute", "high", str(claim), "Qualify the claim or add approved substantiation."))

    limit = int(policy.get("channel_limits", {}).get(channel, 10_000))
    if len(text) > limit:
        findings.append(finding("channel.length", "medium", f"{len(text)} characters; limit is {limit}", "Shorten the copy for this channel."))

    if policy.get("require_cta", True) and not any(cta.lower() in lower for cta in policy.get("cta_phrases", [])):
        findings.append(finding("content.missing_cta", "medium", "No approved call to action detected", "Add one clear, approved next step."))

    for disclosure in campaign.get("required_disclosures", []):
        if str(disclosure).lower() not in lower:
            findings.append(finding("compliance.missing_disclosure", "high", str(disclosure), "Add the required disclosure before approval."))

    penalty = sum(20 if x["severity"] == "high" else 10 for x in findings)
    score = max(0, 100 - penalty)
    return {"campaign_id": campaign.get("campaign_id", "demo"), "status": "ready_for_human_review" if not findings else "revise", "score": score, "finding_count": len(findings), "findings": findings}


def main() -> None:
    parser = argparse.ArgumentParser(description="Review marketing content against an explainable policy.")
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--policy", type=Path, required=True)
    args = parser.parse_args()
    result = review(json.loads(args.campaign.read_text(encoding="utf-8")), json.loads(args.policy.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

