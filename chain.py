import os
import json
import re
import requests
from typing import List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

from ats_evaluator import calculate_ats_score, get_missing_keywords

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

class ImprovedBullet(BaseModel):
    before: str = Field(
        default="",
        description="The original bullet point from the CV prior to keyword insertion"
    )
    after: str = Field(
        default="",
        description="The updated bullet point with newly integrated missing keywords/skills"
    )
    pattern_used: Optional[str] = Field(
        default="skill_and_keyword_integration",
        description="Category of improvement"
    )


class ATSResult(BaseModel):
    missing_keywords: List[str] = Field(
        default=[],
        description="Important keywords from the job description originally missing from the CV"
    )
    added_skills: List[str] = Field(
        default=[],
        description="Explicit skills, tools, or technologies added"
    )
    improved_bullet_points: List[ImprovedBullet] = Field(
        default=[],
        description="Key rewritten bullet points showing before/after transformations"
    )
    full_optimized_cv: str = Field(
        default="",
        description="The complete, polished, and fully optimized plain text CV"
    )
    elevator_pitch: str = Field(
        default="",
        description="A 30-second spoken elevator pitch tailored for this role"
    )
    likely_interview_questions: List[str] = Field(
        default=[],
        description="3-5 interview questions likely to be asked"
    )


output_parser = PydanticOutputParser(pydantic_object=ATSResult)

class NgrokKaggleLLM(BaseChatModel):
    ngrok_url: str
    api_key: str = "secret123"
    max_new_tokens: int = 4096  
    temperature: float = 0.2
    request_timeout: int = 480  

    @property
    def _llm_type(self) -> str:
        return "ngrok_kaggle_llm"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt_text = "\n".join([m.content for m in messages])

        endpoint = self.ngrok_url.rstrip("/") + "/generate"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt_text,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
        }

        response = requests.post(endpoint, json=payload, headers=headers, timeout=self.request_timeout)

        if response.status_code != 200:
            raise RuntimeError(
                f"Ngrok API Request failed with status {response.status_code}: {response.text}"
            )

        data = response.json()
        generated_text = data.get("response", "")

        if prompt_text and prompt_text in generated_text:
            generated_text = generated_text.split(prompt_text)[-1].strip()

        message = AIMessage(content=generated_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])


def build_llm(ngrok_url: Optional[str] = None, api_key: Optional[str] = None):
    url = ngrok_url or os.environ.get("NGROK_URL")
    key = api_key or os.environ.get("NGROK_API_KEY", "secret123")

    if not url:
        raise ValueError(
            "Missing NGROK_URL. Pass it into run_pipeline() or set NGROK_URL in your .env file."
        )

    return NgrokKaggleLLM(ngrok_url=url, api_key=key)


PROMPT_TEMPLATE = """You are an expert Resume Writer and ATS Optimization Specialist.

JOB DESCRIPTION:
{job_description}

ORIGINAL CANDIDATE CV:
{cv_text}

MISSING HIGH-VALUE KEYWORDS TO INTEGRATE:
{missing_keywords}

TASK INSTRUCTIONS:
1. Rewrite the entire Candidate CV to maximize ATS relevance against the Job Description.
2. CRITICAL — MIRROR THE ORIGINAL STRUCTURE: use the EXACT SAME section headings, section order, and formatting style as the ORIGINAL CANDIDATE CV. If the original uses headings like "Profile", "Education", "Professional Experience", "Skills" (with its own subcategory names), "Projects", "Courses" — reuse those exact heading names and that exact order. Do NOT rename sections to a generic template (e.g. do not turn "Profile" into "Professional Summary", do not turn "Professional Experience" into "Work Experience"). Do NOT add sections the original doesn't have, and do NOT drop any section, subcategory, or project the original has.
3. CRITICAL — PRESERVE EVERY SECTION: your `full_optimized_cv` response MUST include EVERY section and every project/course/entry that exists in the ORIGINAL CANDIDATE CV, fully written out (not just headers with no content). DO NOT SUMMARIZE, SHORTEN, OR DROP ANY SECTION OR PROJECT FROM THE ORIGINAL CV.
4. Naturally weave the missing keywords into bullet points and skills sections where relevant.
5. MAXIMIZE KEYWORD ALIGNMENT THROUGH HONEST REPHRASING: many missing keywords are just different wording for something the candidate already truthfully has. Wherever accurate, rephrase the candidate's real, existing experience using the Job Description's own terminology instead of the candidate's original phrasing — e.g. if the JD says "proficiency" and the candidate wrote "strong skills", use "proficiency"; if the JD says "business stakeholders" and the candidate wrote "business teams" or "product managers", use "business stakeholders" where it's truthfully the same audience; if the JD says "production" and the candidate described deploying/shipping something, use "production". This is honest rewording of real experience, not fabrication — it must never introduce a new fact, tool, metric, or claim the candidate didn't make.
6. Keep original candidate metrics/dates intact, but strengthen action verbs.
7. List every explicit skill/tool/technology you added under "added_skills".
8. CRITICAL — DO NOT FABRICATE DATA: never invent percentages, dollar amounts, team sizes, or any other numeric metric that is not already present in the ORIGINAL CANDIDATE CV. Likewise, do not invent specific technical details the candidate never stated — e.g. don't claim they used a specific evaluation metric (like MSE, AUC, F1-score), a specific tool, or a specific technique unless it is explicitly present in the ORIGINAL CANDIDATE CV. It is acceptable to naturally mention a missing keyword as a skill/tool the candidate has exposure to, but do NOT fabricate a specific story, result, or methodology detail involving that keyword that the candidate never described. If a bullet point has no quantifiable result or technical specific to draw on, strengthen it with qualitative impact language (e.g. "streamlined", "reduced manual effort", "improved reliability") instead of making something up.
9. Return ONLY a valid JSON object matching the exact schema below. No markdown fences, no commentary before or after the JSON, no trailing commas. Do NOT write the resume as plain markdown text outside of JSON — the entire rewritten CV, including all its section headings, must live INSIDE the "full_optimized_cv" string value, with real line breaks encoded as \\n. Every field below, including "elevator_pitch" and "likely_interview_questions", must be a proper JSON key — never a bare markdown header like "**elevator_pitch**".

JSON SCHEMA:
{{
  "missing_keywords": ["list", "of", "missing", "keywords"],
  "added_skills": ["skill", "tool", "technology"],
  "full_optimized_cv": "The complete rewritten CV text, using the SAME section headings/order/structure as the ORIGINAL CANDIDATE CV above (not a generic template) — every original section, subsection, and project preserved and enhanced, with real newlines represented as \\n",
  "improved_bullet_points": [
    {{
      "before": "Original bullet point",
      "after": "Optimized bullet point with incorporated keyword",
      "pattern_used": "skill_and_keyword_integration"
    }}
  ],
  "elevator_pitch": "30-second interview summary...",
  "likely_interview_questions": ["Question 1?", "Question 2?"]
}}

REMINDER: your entire response must start with {{ and end with }} — a single JSON object, nothing before it and nothing after it.
"""

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["job_description", "cv_text", "missing_keywords"],
)


def extract_numbers(text: str) -> set:
    return set(re.findall(r"\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?%?|\$?\d+(?:\.\d+)?%?", text))


def find_unverified_numbers(rewritten_bullet: str, original_cv_text: str) -> list:
    cv_numbers = extract_numbers(original_cv_text)
    bullet_numbers = extract_numbers(rewritten_bullet)
    return sorted(n for n in bullet_numbers if n not in cv_numbers)


def sanitize_plain_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text.strip()



def _header_pattern(*words: str) -> str:
    body = r'[\s_]+'.join(words)
    return rf'^\s*\*{{0,2}}\s*{body}\s*\*{{0,2}}\s*:?\s*$'


METADATA_SECTION_MARKERS = [
    r'"improved_bullet_points"',
    _header_pattern("improved", "bullet", "points"),
    _header_pattern("bullet", "point", "transformations"),
    _header_pattern("bullet", "transformations"),
    r'"elevator_pitch"',
    _header_pattern("elevator", "pitch"),
    r'"likely_interview_questions"',
    _header_pattern("likely", "interview", "questions"),
    _header_pattern("interview", "questions"),
    r'"missing_keywords"',
    _header_pattern("missing", "keywords"),
    r'"added_skills"',
    _header_pattern("added", "skills"),
]


def strip_leaked_metadata_sections(cv_text: str) -> str:
    if not cv_text:
        return cv_text

    earliest_cut = None
    for pattern in METADATA_SECTION_MARKERS:
        m = re.search(pattern, cv_text, flags=re.IGNORECASE | re.MULTILINE)
        if m and (earliest_cut is None or m.start() < earliest_cut):
            earliest_cut = m.start()

    if earliest_cut is not None and earliest_cut > 30:
        return cv_text[:earliest_cut].strip()

    return cv_text


def _try_repair_truncated_json(clean_str: str) -> Optional[dict]:
    candidate = clean_str.rstrip()

    candidate = re.sub(r",\s*$", "", candidate)

    quote_count = len(re.findall(r'(?<!\\)"', candidate))
    if quote_count % 2 == 1:
        candidate += '"'

    open_braces = candidate.count("{") - candidate.count("}")
    open_brackets = candidate.count("[") - candidate.count("]")

    candidate += "]" * max(open_brackets, 0)
    candidate += "}" * max(open_braces, 0)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def parse_llm_json(raw_text: str) -> tuple:
    clean_str = raw_text.strip()

    clean_str = re.sub(r"^```(?:json)?", "", clean_str, flags=re.IGNORECASE).strip()
    clean_str = re.sub(r"```$", "", clean_str).strip()

    first_brace = clean_str.find("{")
    last_brace = clean_str.rfind("}")

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        clean_str = clean_str[first_brace:last_brace + 1].strip()
    elif first_brace != -1:
        clean_str = clean_str[first_brace:].strip()

    try:
        result = json.loads(clean_str)
        if isinstance(result, dict) and "full_optimized_cv" in result:
            return result, "direct_json"
    except json.JSONDecodeError:
        pass

    repaired = _try_repair_truncated_json(clean_str)
    if repaired is not None and isinstance(repaired, dict) and "full_optimized_cv" in repaired:
        return repaired, "repaired_json"

    extracted = {
        "missing_keywords": [],
        "added_skills": [],
        "improved_bullet_points": [],
        "full_optimized_cv": "",
        "elevator_pitch": "",
        "likely_interview_questions": []
    }

    cv_match = re.search(r'"full_optimized_cv"\s*:\s*"([\s\S]*?)"\s*,\s*"', raw_text)
    if not cv_match:
        cv_match = re.search(r'"full_optimized_cv"\s*:\s*"([\s\S]*)$', raw_text)
    if cv_match:
        extracted["full_optimized_cv"] = cv_match.group(1)

    pitch_match = re.search(r'"elevator_pitch"\s*:\s*"([^"]+)"', raw_text)
    if pitch_match:
        extracted["elevator_pitch"] = pitch_match.group(1)

    for field in ("missing_keywords", "added_skills"):
        arr_match = re.search(rf'"{field}"\s*:\s*\[([\s\S]*?)\]', raw_text)
        if arr_match:
            items = re.findall(r'"([^"]*)"', arr_match.group(1))
            extracted[field] = items

    if extracted["full_optimized_cv"] and len(extracted["full_optimized_cv"].strip()) >= 30:
        return extracted, "regex_fallback"

    earliest_cut = None
    for pattern in METADATA_SECTION_MARKERS:
        m = re.search(pattern, raw_text, flags=re.IGNORECASE | re.MULTILINE)
        if m and (earliest_cut is None or m.start() < earliest_cut):
            earliest_cut = m.start()

    if earliest_cut and earliest_cut > 30:
        salvaged_cv = raw_text[:earliest_cut].strip()
        salvaged_cv = re.sub(r"^```(?:json|markdown)?\s*", "", salvaged_cv, flags=re.IGNORECASE)
        if len(salvaged_cv.strip()) >= 30:
            extracted["full_optimized_cv"] = salvaged_cv.strip()
            trailing = raw_text[earliest_cut:]
            pitch_match = re.search(
                r'(?:"elevator_pitch"\s*:\s*"([^"]+)"|\*\*elevator_pitch\*\*\s*\n+([^\n*]+)|^elevator_pitch\s*\n+([^\n]+))',
                trailing, flags=re.IGNORECASE | re.MULTILINE,
            )
            if pitch_match:
                extracted["elevator_pitch"] = next(g for g in pitch_match.groups() if g)

            questions_match = re.search(r'\[([\s\S]*?)\]', trailing[trailing.lower().find("interview_questions"):]) \
                if "interview_questions" in trailing.lower() else None
            if questions_match:
                extracted["likely_interview_questions"] = re.findall(r'"([^"]*)"', questions_match.group(1))

            return extracted, "raw_document_salvage"

    return extracted, "regex_fallback"


def run_pipeline(
    cv_text: str,
    job_description: str,
    llm=None,
    ngrok_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict:
    original_score = calculate_ats_score(cv_text, job_description)
    missing_keywords = get_missing_keywords(cv_text, job_description)

    missing_str = ", ".join(missing_keywords) if missing_keywords else "None missing (Focus on polishing tone and clarity)"

    formatted_prompt = prompt.format(
        job_description=job_description,
        cv_text=cv_text,
        missing_keywords=missing_str,
    )

    active_llm = llm or build_llm(ngrok_url=ngrok_url, api_key=api_key)

    raw_response = active_llm.invoke(formatted_prompt)
    raw_text = raw_response.content if hasattr(raw_response, "content") else str(raw_response)

# --- Attempt 1: the real PydanticOutputParser ---------------------------
    parsed = None
    parse_strategy = None
    try:
        parsed = output_parser.parse(raw_text)
        parse_strategy = "pydantic_parser"
    except Exception as parse_error:
        try:
            fix_prompt = (
                "You previously produced output that was supposed to be a single "
                "JSON object matching this schema:\n\n"
                f"{output_parser.get_format_instructions()}\n\n"
                f"It failed to parse with this error:\n{parse_error}\n\n"
                f"Here is the broken output:\n{raw_text}\n\n"
                "Return ONLY the corrected, complete, valid JSON object with the "
                "SAME content — do not shorten or omit any field, do not add "
                "commentary or markdown fences, just fix the JSON structure."
            )
            fix_response = active_llm.invoke(fix_prompt)
            fix_text = fix_response.content if hasattr(fix_response, "content") else str(fix_response)
            parsed = output_parser.parse(fix_text)
            raw_text = fix_text
            parse_strategy = "pydantic_parser_retry"
        except Exception:
            parsed = None

    if parsed is None:
        parsed_dict, parse_strategy = parse_llm_json(raw_text)

        try:
            parsed = ATSResult(**parsed_dict)
        except Exception:
            safe_bullets = []
            for b in (parsed_dict.get("improved_bullet_points") or []):
                if isinstance(b, dict):
                    safe_bullets.append({
                        "before": str(b.get("before", "")),
                        "after": str(b.get("after", "")),
                        "pattern_used": b.get("pattern_used") or "skill_and_keyword_integration",
                    })

            raw_missing = parsed_dict.get("missing_keywords")
            raw_added = parsed_dict.get("added_skills")
            raw_questions = parsed_dict.get("likely_interview_questions")

            parsed = ATSResult(
                missing_keywords=raw_missing if isinstance(raw_missing, list) else missing_keywords,
                added_skills=raw_added if isinstance(raw_added, list) else [],
                improved_bullet_points=safe_bullets,
                full_optimized_cv=str(parsed_dict.get("full_optimized_cv", "")),
                elevator_pitch=str(parsed_dict.get("elevator_pitch", "")),
                likely_interview_questions=raw_questions if isinstance(raw_questions, list) else [],
            )

    full_cv_text = sanitize_plain_text(parsed.full_optimized_cv)

    full_cv_text = strip_leaked_metadata_sections(full_cv_text)

    used_original_cv_fallback = False
    if not full_cv_text or len(full_cv_text.strip()) < 30 or full_cv_text.startswith("{"):
        full_cv_text = cv_text.strip()
        used_original_cv_fallback = True



    new_score = calculate_ats_score(full_cv_text, job_description)
    remaining_missing_keywords = get_missing_keywords(full_cv_text, job_description)

    improved_bullets_with_audit = []
    all_unverified_numbers = set()
    for bullet in parsed.improved_bullet_points:
        bullet_dict = bullet.model_dump()
        unverified = find_unverified_numbers(bullet.after, cv_text)
        bullet_dict["unverified_numbers"] = unverified
        all_unverified_numbers.update(unverified)
        improved_bullets_with_audit.append(bullet_dict)

    all_unverified_numbers.update(find_unverified_numbers(full_cv_text, cv_text))

    return {
        "original_score": original_score,
        "new_score": new_score,
        "full_optimized_cv": full_cv_text,
        "added_skills": parsed.added_skills,
        "missing_keywords_before_rewrite": missing_keywords,
        "missing_keywords_still_remaining": remaining_missing_keywords,
        "hallucination_warning": sorted(all_unverified_numbers) or None,
        "optimization_status": {
            "parse_strategy": parse_strategy,
            "used_original_cv_fallback": used_original_cv_fallback,
            "raw_llm_response_length_chars": len(raw_text),
            "raw_llm_response_preview": (raw_text[:500] + "...") if used_original_cv_fallback else None,
        },
        "improved_bullet_points": improved_bullets_with_audit,
        "elevator_pitch": parsed.elevator_pitch or "High-performing professional bringing strong domain alignment and technical expertise to this role.",
        "likely_interview_questions": parsed.likely_interview_questions or [
            "Can you walk us through your most relevant project experience?",
            "How do your technical skills align with the requirements for this role?",
            "What is a challenging problem you solved using your core skills?"
        ],
    }