import re
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer

CUSTOM_STOPWORDS = {
    'looking', 'seeking', 'looking for', 'work', 'job', 'description',
    'role', 'candidate', 'ideal', 'requirements', 'responsibilities',
    'ability', 'strong', 'proven', 'track', 'record', 'experience'
}


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())


def _is_stopword_phrase(kw: str) -> bool:
    return any(stop in kw for stop in CUSTOM_STOPWORDS)


def _split_into_segments(text: str) -> List[str]:
    raw_segments = re.split(r'[,;.\n]+|\band\b|\bor\b', text.lower())
    return [s.strip() for s in raw_segments if s.strip()]


def _extract_weighted_jd_keywords(job_description: str, top_n: int = 40) -> List[Tuple[str, float]]:
    segments = _split_into_segments(job_description)
    cleaned_segments = [clean_text(s) for s in segments if clean_text(s)]
    if not cleaned_segments:
        return []

    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(cleaned_segments)
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.sum(axis=0).A1  # aggregate importance across all segments

        pairs = [
            (kw, float(score)) for kw, score in zip(feature_names, scores)
            if not _is_stopword_phrase(kw)
        ]
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:top_n]
    except Exception:
        return []


def calculate_ats_score(cv_text: str, job_description: str, top_n: int = 40) -> float:
    clean_cv = clean_text(cv_text)
    if not clean_cv:
        return 0.0

    keywords = _extract_weighted_jd_keywords(job_description, top_n=top_n)
    if not keywords:
        return 0.0

    total_weight = sum(w for _, w in keywords)
    if total_weight == 0:
        return 0.0

    matched_weight = sum(w for kw, w in keywords if kw in clean_cv)
    return round(matched_weight / total_weight * 100, 1)


def get_missing_keywords(cv_text: str, job_description: str, top_n: int = 10) -> list:
    clean_cv = clean_text(cv_text)
    if not clean_cv:
        return []

    keywords = _extract_weighted_jd_keywords(job_description, top_n=1000) 
    missing = []
    for kw, _ in keywords:
        if kw not in clean_cv:
            missing.append(kw)
        if len(missing) >= top_n:
            break
    return missing