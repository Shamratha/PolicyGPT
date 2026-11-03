import logging
import json
import re
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
from app.config import settings
from app.models.profile import Profile
from app.models.scheme import Scheme, EligibilityRule
from app.schemas.scheme import EligibilityCheckResponse

logger = logging.getLogger(__name__)


def _split_items(text: Optional[str]) -> List[str]:
    """Turn 'A, B, C' or '1. Do x. 2. Do y.' into a clean list."""
    if not text:
        return []
    parts = re.split(r"(?:\s*\d+\.\s+)|[;,\n]", str(text))
    return [p.strip(" .") for p in parts if p and p.strip(" .")]

class EligibilityService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY or "sk-mock")

    def evaluate_rule(self, rule: EligibilityRule, profile: Profile) -> Tuple[bool, str]:
        """
        Evaluate a single eligibility rule against the user profile.
        Returns (is_passed, debug_message).
        If the profile field is missing/None, we return (True, "missing_info") to count as potentially eligible.
        """
        field = rule.field_name.lower()
        operator = rule.operator.strip()
        expected = rule.expected_value.strip()

        # Get field value from profile
        if not hasattr(profile, field):
            return True, f"Field '{field}' does not exist on profile."
        
        val = getattr(profile, field)
        if val is None:
            return True, "missing_info"

        try:
            if field == "age":
                user_age = int(val)
                exp_age = int(expected)
                if operator == ">=":
                    return user_age >= exp_age, f"Age {user_age} must be >= {exp_age}"
                elif operator == "<=":
                    return user_age <= exp_age, f"Age {user_age} must be <= {exp_age}"
                elif operator == "==":
                    return user_age == exp_age, f"Age {user_age} must be == {exp_age}"
            
            elif field == "income":
                user_income = float(val)
                exp_income = float(expected)
                if operator == "<=":
                    return user_income <= exp_income, f"Family income {user_income} must be <= {exp_income}"
                elif operator == ">=":
                    return user_income >= exp_income, f"Family income {user_income} must be >= {exp_income}"

            elif field == "gender" and operator == "==":
                # Case-insensitive string match
                return val.lower() == expected.lower(), f"Gender '{val}' must be '{expected}'"

            elif field == "state" and operator == "==":
                # Case-insensitive string match
                return val.lower() == expected.lower(), f"State '{val}' must be '{expected}'"

            elif field in ["student_status", "startup_status", "is_for_farmers", "is_for_women"]:
                # Boolean evaluation
                user_bool = bool(val)
                exp_bool = expected.lower() in ["true", "1", "yes"]
                return user_bool == exp_bool, f"Field '{field}' ({user_bool}) must be {exp_bool}"

            # Generic text fields (occupation, education, ...) and any "in" rule
            if isinstance(val, str):
                user_val = val.strip().lower()
                if operator == "in":
                    options = [o.strip().lower() for o in expected.split(",") if o.strip()]
                    return user_val in options, f"{field.replace('_', ' ').title()} '{val}' must be one of: {expected}"
                if operator == "==":
                    return user_val == expected.lower(), f"{field.replace('_', ' ').title()} '{val}' must be '{expected}'"
                if operator == "!=":
                    return user_val != expected.lower(), f"{field.replace('_', ' ').title()} '{val}' must not be '{expected}'"

            return True, "unknown_field_skipped"
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")
            return True, f"Error: {str(e)}"

    def check_eligibility(self, db: Session, profile: Optional[Profile], scheme: Scheme) -> EligibilityCheckResponse:
        """
        Runs deterministic hard-coded checks followed by LLM contextualization.
        """
        if profile is None:
            profile = Profile()  # blank profile -> every rule is "missing info"
        # Phase 1: Check rules
        rules = scheme.rules
        failed_reasons = []
        has_missing_info = False
        missing_fields: List[str] = []

        for rule in rules:
            passed, msg = self.evaluate_rule(rule, profile)
            if msg == "missing_info":
                has_missing_info = True
                missing_fields.append(str(rule.field_name).replace("_", " "))
            elif not passed:
                failed_reasons.append(msg)

        # If they failed any hard rules, they are definitively Not Eligible
        if failed_reasons:
            return EligibilityCheckResponse(
                scheme_id=str(scheme.id),
                scheme_title=str(scheme.title),
                status="Not Eligible",
                reason=f"Failed criteria: {', '.join(failed_reasons)}.",
                benefits=str(scheme.benefits) if scheme.benefits is not None else "",
                required_documents=[],
                application_steps=[],
                next_opportunities=[]
            )

        # Phase 2: LLM checks for complex terms (e.g. "engineering graduate interested in starting a business")
        # If the key is mock, return a standard result
        if settings.ai_offline:
            status = "Potentially Eligible" if (has_missing_info or not rules) else "Eligible"
            return EligibilityCheckResponse(
                scheme_id=str(scheme.id),
                scheme_title=str(scheme.title),
                status=status,
                reason=(
                    "You meet all the rule-based criteria we could check, but some profile details are missing - "
                    f"update {', '.join(missing_fields)} on your profile for a definitive result."
                    if has_missing_info else
                    "You meet all the rule-based eligibility criteria recorded for this scheme."
                ) if rules else "This scheme's eligibility can't be checked automatically. Read the criteria below and confirm on the official portal.",
                benefits=str(scheme.benefits) if scheme.benefits is not None else "",
                required_documents=_split_items(scheme.required_documents) or ["Aadhaar Card", "Income Certificate"],
                application_steps=_split_items(scheme.application_steps) or ["Visit the official portal", "Upload documents", "Submit the application"],
                next_opportunities=[]
            )

        system_prompt = (
            "You are the eligibility engine of PolicyGPT. Your job is to check if a citizen is eligible for a specific government scheme "
            "based on their profile and the scheme's guidelines.\n\n"
            "INSTRUCTIONS:\n"
            "1. Output a JSON object with exactly these four keys:\n"
            "   - 'status': 'Eligible' (if matches all criteria), 'Potentially Eligible' (if matches but some profile information is missing/empty, or matches partially), or 'Not Eligible' (if explicitly violates criteria).\n"
            "   - 'reason': a detailed explanation of why they are eligible, potentially eligible, or not eligible.\n"
            "   - 'required_documents': list of documents they need to apply for this scheme.\n"
            "   - 'application_steps': step-by-step instructions to apply.\n"
            "   - 'next_opportunities': list of 1-3 generic suggestions for this user.\n"
        )

        user_context = (
            f"Scheme Title: {scheme.title}\n"
            f"Scheme Description: {scheme.description}\n"
            f"Eligibility Guidelines: {scheme.eligibility_criteria}\n"
            f"Required Documents (Original): {scheme.required_documents}\n"
            f"Application Steps (Original): {scheme.application_steps}\n\n"
            f"User Profile:\n"
            f"- Age: {profile.age}\n"
            f"- Gender: {profile.gender}\n"
            f"- State: {profile.state}\n"
            f"- Education: {profile.education}\n"
            f"- Occupation: {profile.occupation}\n"
            f"- Income: {profile.income}\n"
            f"- Startup Status: {profile.startup_status}\n"
            f"- Student Status: {profile.student_status}\n"
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            result = json.loads(content.strip())
            
            # If our Python rule check detected missing info, elevate "Eligible" to "Potentially Eligible"
            status = result.get("status", "Potentially Eligible")
            if status == "Eligible" and has_missing_info:
                status = "Potentially Eligible"

            return EligibilityCheckResponse(
                scheme_id=str(scheme.id),
                scheme_title=str(scheme.title),
                status=status,
                reason=result.get("reason", "Checks complete."),
                benefits=str(scheme.benefits) if scheme.benefits is not None else "",
                required_documents=result.get("required_documents", []),
                application_steps=result.get("application_steps", []),
                next_opportunities=result.get("next_opportunities", [])
            )
        except Exception as e:
            logger.error(f"Failed to check eligibility via LLM: {e}")
            return EligibilityCheckResponse(
                scheme_id=str(scheme.id),
                scheme_title=str(scheme.title),
                status="Potentially Eligible",
                reason=f"Automated matching running. Detail: Basic checks passed. (Error: {str(e)})",
                benefits=str(scheme.benefits) if scheme.benefits is not None else "",
                required_documents=["Contact administrative representative"],
                application_steps=["Consult local service center"],
                next_opportunities=[]
            )

eligibility_service = EligibilityService()
