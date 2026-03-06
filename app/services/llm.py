from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class DraftInputs:
    user_email: str
    campaign_name: str
    target_company: Optional[str]
    target_role: Optional[str]
    resume_text: Optional[str]
    job_description_text: Optional[str]
    contact_name: str
    contact_company: Optional[str]
    contact_title: Optional[str]
    style: str
    ask: Optional[str]


class LLMClient:
    def draft_outreach(
        self,
        user_email: str,
        campaign_name: str,
        target_company: Optional[str],
        target_role: Optional[str],
        resume_text: Optional[str],
        job_description_text: Optional[str],
        contact_name: str,
        contact_company: Optional[str],
        contact_title: Optional[str],
        style: str,
        ask: Optional[str],
    ) -> str:
        raise NotImplementedError

    def prepare_info_interview(
        self,
        campaign_name: str,
        target_company: Optional[str],
        target_role: Optional[str],
        resume_text: Optional[str],
        job_description_text: Optional[str],
        contact_name: str,
        contact_company: Optional[str],
        contact_title: Optional[str],
        meeting_length_minutes: int,
        goal: Optional[str],
    ) -> str:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    def draft_outreach(
        self,
        user_email: str,
        campaign_name: str,
        target_company: Optional[str],
        target_role: Optional[str],
        resume_text: Optional[str],
        job_description_text: Optional[str],
        contact_name: str,
        contact_company: Optional[str],
        contact_title: Optional[str],
        style: str,
        ask: Optional[str],
    ) -> str:
        company = contact_company or target_company or "your company"
        role = target_role or "a role"
        ask_line = ask or "Would you be open to a 15-minute chat next week?"
        return (
            f"Subject: Quick question about {company}\n\n"
            f"Hi {contact_name},\n\n"
            f"I'm reaching out as part of my {campaign_name} search. I'm targeting {role} roles "
            f"and would love to learn how you approached your path at {company}.\n\n"
            f"{ask_line}\n\n"
            f"Thanks,\n"
            f"{user_email}"
        )

    def prepare_info_interview(
        self,
        campaign_name: str,
        target_company: Optional[str],
        target_role: Optional[str],
        resume_text: Optional[str],
        job_description_text: Optional[str],
        contact_name: str,
        contact_company: Optional[str],
        contact_title: Optional[str],
        meeting_length_minutes: int,
        goal: Optional[str],
    ) -> str:
        company = contact_company or target_company or "the company"
        role = target_role or "the role"
        goal_line = goal or "Learn about their path and get advice on next steps."
        title = f"{contact_title} at {company}" if contact_title else company

        return (
            "# Informational Interview Prep\n\n"
            f"**Campaign:** {campaign_name}\n\n"
            f"**Contact:** {contact_name} ({title})\n\n"
            f"**Time:** {meeting_length_minutes} minutes\n\n"
            f"**Goal:** {goal_line}\n\n"
            "## Your 30-second intro\n"
            "- 1 line: who you are (SWE + MBA)\n"
            f"- 1 line: what you're targeting ({role})\n"
            f"- 1 line: why you're reaching out (their experience at {company})\n\n"
            "## Agenda\n"
            "1. Quick intros (2 min)\n"
            "2. Their story + role (8 min)\n"
            "3. Advice + recruiting process (8 min)\n"
            "4. Close + next steps (2 min)\n\n"
            "## Questions (pick 6–8)\n"
            f"1. What has been the most impactful project you worked on at {company}?\n"
            "2. How is your team structured, and how do decisions get made?\n"
            f"3. What skills or signals matter most for {role} hiring there?\n"
            "4. What does a strong first 90 days look like?\n"
            f"5. What's underrated about working at {company}?\n"
            "6. If you were in my shoes, what would you focus on over the next 4 weeks?\n"
            "7. Are there 1–2 people you'd suggest I speak with next?\n\n"
            "## Close\n"
            "- Thank them\n"
            "- Ask about best next steps\n"
            "- Ask for 1–2 intros (only if the convo went well)\n"
        )


class OpenAIChatCompletionsClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    def draft_outreach(
        self,
        user_email: str,
        campaign_name: str,
        target_company: Optional[str],
        target_role: Optional[str],
        resume_text: Optional[str],
        job_description_text: Optional[str],
        contact_name: str,
        contact_company: Optional[str],
        contact_title: Optional[str],
        style: str,
        ask: Optional[str],
    ) -> str:
        system = (
            "You are an expert MBA/SWE networking copilot. "
            "Write concise outreach emails that sound human and specific."
        )
        user_prompt = (
            f"User email: {user_email}\n"
            f"Campaign: {campaign_name}\n"
            f"Target company: {target_company}\n"
            f"Target role: {target_role}\n"
            f"Contact name: {contact_name}\n"
            f"Contact company: {contact_company}\n"
            f"Contact title: {contact_title}\n"
            f"Style: {style}\n"
            f"Ask: {ask}\n\n"
            "Resume (may be empty):\n"
            f"{resume_text or ''}\n\n"
            "Job description (may be empty):\n"
            f"{job_description_text or ''}\n\n"
            "Return ONLY the email text, including a Subject line."
        )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.6,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        with httpx.Client(timeout=30) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def prepare_info_interview(
        self,
        campaign_name: str,
        target_company: Optional[str],
        target_role: Optional[str],
        resume_text: Optional[str],
        job_description_text: Optional[str],
        contact_name: str,
        contact_company: Optional[str],
        contact_title: Optional[str],
        meeting_length_minutes: int,
        goal: Optional[str],
    ) -> str:
        system = (
            "You are an expert MBA/SWE networking copilot. "
            "Generate actionable informational interview prep in concise markdown."
        )
        user_prompt = (
            f"Campaign: {campaign_name}\n"
            f"Target company: {target_company}\n"
            f"Target role: {target_role}\n"
            f"Contact name: {contact_name}\n"
            f"Contact company: {contact_company}\n"
            f"Contact title: {contact_title}\n"
            f"Meeting length minutes: {meeting_length_minutes}\n"
            f"Goal: {goal}\n\n"
            "Resume (may be empty):\n"
            f"{resume_text or ''}\n\n"
            "Job description (may be empty):\n"
            f"{job_description_text or ''}\n\n"
            "Return markdown with: 30-sec intro, agenda, 10 tailored questions, and a closing script."
        )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        with httpx.Client(timeout=30) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


def get_llm_client(settings) -> LLMClient:
    provider = (settings.llm_provider or "mock").lower()
    if provider == "openai":
        if not settings.openai_api_key:
            return MockLLMClient()
        return OpenAIChatCompletionsClient(api_key=settings.openai_api_key, model=settings.openai_model)
    return MockLLMClient()
