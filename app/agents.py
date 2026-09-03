from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .config import Settings
from .models import ClaimAudit, QueryRequest
from .retrieval import Hit, HybridRetriever

DOMAIN_TERMS = {
    "education": ["student", "scholarship", "college", "education", "school", "fee"],
    "agriculture": ["farmer", "farm", "crop", "land", "agriculture", "kisan"],
    "msme": ["business", "startup", "enterprise", "msme", "udyam", "turnover"],
    "finance": ["loan", "interest", "credit", "bank", "finance", "subsidy"],
    "health": ["health", "hospital", "insurance", "treatment", "medical"],
    "disaster": ["flood", "relief", "disaster", "drought", "emergency", "cyclone"],
}


@dataclass
class RoutedQuery:
    domain: str
    intent: str


class DomainRouterAgent:
    def route(self, query: str) -> RoutedQuery:
        q = query.lower(); scores = {d: sum(t in q for t in terms) for d, terms in DOMAIN_TERMS.items()}
        domain = max(scores, key=scores.get) if max(scores.values()) else "general"
        if any(w in q for w in ("eligible", "qualify", "can i")): intent = "eligibility"
        elif any(w in q for w in ("apply", "application", "documents", "deadline")): intent = "application_guidance"
        elif any(w in q for w in ("compare", "overlap", "gap", "impact", "analys")): intent = "policy_analysis"
        else: intent = "explanation"
        return RoutedQuery(domain, intent)


class PolicyDiscoveryAgent:
    def discover(self, hits: list[Hit]) -> list[Hit]:
        return sorted(hits, key=lambda h: (-h.score, h.document.effective_date or ""))


class GenerationAgent:
    def generate(self, request: QueryRequest, route: RoutedQuery, hits: list[Hit]) -> tuple[str, list[dict[str, Any]]]:
        if not hits: return ("I could not find a matching policy record in the current corpus. Try a scheme name, domain, or beneficiary description.", [])
        lead = hits[0].document
        lines = [f"Based on **{lead.title}** from {lead.agency}, here is a corpus-grounded answer:", "", lead.text.split("Eligibility:", 1)[0].strip()]
        if route.intent == "eligibility": lines.append("\n**Eligibility check:** compare your profile with the conditions in the cited record. A missing field is unknown, not an automatic rejection.")
        elif route.intent == "application_guidance": lines.append("\n**How to proceed:** use the official source, confirm the current notice and deadline, and prepare the documents listed by the issuing agency.")
        elif route.intent == "policy_analysis": lines.append(f"\n**Analyst view:** {len(hits)} related records were retrieved for comparison. Review effective dates and agencies before treating differences as conflicts.")
        else: lines.append("\nThis explanation is simplified for readability. The cited source remains authoritative.")
        citations = [{"source_id": h.document.id, "title": h.document.title, "url": h.document.source_url, "excerpt": h.excerpt, "relevance": h.score} for h in hits]
        return "\n".join(lines), citations


class ValidationAgent:
    def validate(self, answer: str, citations: list[dict[str, Any]], hits: list[Hit]) -> tuple[float, float, list[ClaimAudit], list[str]]:
        claims = [c.strip() for c in re.split(r"[.!?]\s+", answer) if len(c.strip()) > 20]; audits=[]
        for claim in claims:
            words=set(re.findall(r"\w+", claim.lower())); overlap=max((len(words & set(re.findall(r"\w+", h.document.text.lower()))) for h in hits), default=0)
            audits.append(ClaimAudit(claim=claim, status="supported" if overlap >= 3 else "partially_supported", evidence_source_ids=[h.document.id for h in hits[:2]], note="Lexical evidence overlap; review the cited passage."))
        coverage=sum(a.status == "supported" for a in audits)/max(len(audits),1); confidence=round(min(.98,.55+.3*coverage+.15*min(len(citations),3)/3),3); risk=round(1-confidence,3)
        warnings=["This is decision support, not legal advice; verify current rules with the issuing agency."]
        if not citations: warnings.insert(0,"No matching source was found in the corpus.")
        return confidence,risk,audits,warnings


class FinalReportAgent:
    def format_markdown(self, request: QueryRequest, route: RoutedQuery, answer: str, citations: list[dict[str, Any]], audits: list[ClaimAudit]) -> str:
        lines=["# PolicyGPT Query Report","",f"- **Role:** {request.role}",f"- **Domain:** {route.domain}",f"- **Intent:** {route.intent}","","## Answer","",answer,"","## Sources",""]
        lines += [f"- **{c['title']}** ([source]({c['url']})): {c['excerpt']}" for c in citations]
        lines += ["","## Claim audit",""]+[f"- `{a.status}` — {a.claim} ({', '.join(a.evidence_source_ids) or 'none'})" for a in audits]
        return "\n".join(lines)+"\n"


class PolicyGPTOrchestrator:
    def __init__(self, retriever: HybridRetriever, settings: Settings):
        self.retriever=retriever; self.settings=settings; self.router=DomainRouterAgent(); self.discovery=PolicyDiscoveryAgent(); self.generator=GenerationAgent(); self.validator=ValidationAgent(); self.reporter=FinalReportAgent()

    def run(self, request: QueryRequest) -> dict[str, Any]:
        route=self.router.route(request.query); hits=self.discovery.discover(self.retriever.search(request.query, route.domain if route.domain != "general" else None, request.top_k)); answer,citations=self.generator.generate(request,route,hits); confidence,risk,audits,warnings=self.validator.validate(answer,citations,hits)
        if confidence < self.settings.confidence_threshold or risk > self.settings.hallucination_threshold:
            broader=self.retriever.search(request.query,None,request.top_k); hits=self.discovery.discover(broader); answer,citations=self.generator.generate(request,route,hits); confidence,risk,audits,warnings=self.validator.validate(answer,citations,hits)
        return {"answer":answer,"domain":route.domain,"intent":route.intent,"confidence":confidence,"hallucination_risk":risk,"citations":citations,"claim_audit":[a.model_dump() for a in audits],"eligibility":self._eligibility(request,hits),"warnings":warnings}

    def _eligibility(self, request: QueryRequest, hits: list[Hit]) -> list[dict[str, Any]]:
        if not request.profile or not hits: return []
        profile=request.profile.model_dump(exclude_none=True); results=[]
        for h in hits[:3]:
            checks=[]; text=h.document.text.lower()
            for criterion in ("income","landholding_acres"):
                if criterion.replace("_acres", "") in text or criterion in text: checks.append({"criterion":criterion,"status":"review_required","provided":profile.get(criterion)})
            results.append({"scheme":h.document.title,"status":"likely_match" if checks else "needs_manual_review","checks":checks})
        return results
