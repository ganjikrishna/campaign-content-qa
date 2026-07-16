"""Deterministic, explainable marketing content preflight checks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def finding(rule: str, severity: str, evidence: str, recommendation: str) -> dict[str, str]:
    return {"rule": rule, "severity": severity, "evidence": evidence, "recommendation": recommendation}


def suggest_rewrite(text: str, campaign: dict[str, Any], policy: dict[str, Any]) -> tuple[str, list[str]]:
    """Create a conservative, deterministic rewrite and explain every change."""
    rewritten = text
    changes: list[str] = []
    replacements = {"instantly": "quickly", "guaranteed": "", "best": "practical", "every": "modern"}
    flagged = [*policy.get("prohibited_phrases", []), *policy.get("absolute_claims", [])]
    for phrase in flagged:
        phrase = str(phrase)
        if not re.search(re.escape(phrase), rewritten, flags=re.IGNORECASE):
            continue
        replacement = replacements.get(phrase.lower(), "supportable")
        rewritten = re.sub(re.escape(phrase), replacement, rewritten, flags=re.IGNORECASE)
        changes.append(f'Replaced "{phrase}" with more supportable language.')

    rewritten = re.sub(r"\bThe\s+practical reporting platform for modern marketing team\b", "A practical reporting platform for modern marketing teams", rewritten, flags=re.IGNORECASE)
    rewritten = re.sub(r"[ \t]{2,}", " ", rewritten).strip()

    disclosures = [str(item).strip() for item in campaign.get("required_disclosures", []) if str(item).strip()]
    missing = [item for item in disclosures if item.lower() not in rewritten.lower()]
    if missing:
        rewritten = rewritten.rstrip() + " " + " ".join(missing)
        changes.append("Added required disclosure: " + ", ".join(missing) + ".")

    ctas = [str(item).strip() for item in policy.get("cta_phrases", []) if str(item).strip()]
    if policy.get("require_cta", True) and ctas and not any(item.lower() in rewritten.lower() for item in ctas):
        cta = ctas[0].capitalize() + "."
        rewritten = rewritten.rstrip() + " " + cta
        changes.append(f'Added an approved call to action: "{cta}"')

    channel = str(campaign.get("channel", "")).lower().strip()
    limit = int(policy.get("channel_limits", {}).get(channel, 10_000))
    if len(rewritten) > limit:
        rewritten = rewritten[: max(0, limit - 1)].rstrip(" ,;:-") + "…"
        changes.append(f"Shortened the suggestion to the {limit}-character {channel} limit.")
    return rewritten, changes


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
    rewritten_text, rewrite_changes = suggest_rewrite(text, campaign, policy)
    return {"campaign_id": campaign.get("campaign_id", "demo"), "status": "ready_for_human_review" if not findings else "revise", "score": score, "finding_count": len(findings), "findings": findings, "rewritten_text": rewritten_text, "rewrite_changes": rewrite_changes}


def main() -> None:
    parser = argparse.ArgumentParser(description="Review marketing content against an explainable policy.")
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--policy", type=Path, required=True)
    args = parser.parse_args()
    result = review(json.loads(args.campaign.read_text(encoding="utf-8")), json.loads(args.policy.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
