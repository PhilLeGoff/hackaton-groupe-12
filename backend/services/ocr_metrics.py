from __future__ import annotations

from collections import Counter
import re


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def levenshtein_distance(reference: list[str], hypothesis: list[str]) -> int:
    if not reference:
        return len(hypothesis)
    if not hypothesis:
        return len(reference)

    previous_row = list(range(len(hypothesis) + 1))

    for ref_index, ref_item in enumerate(reference, start=1):
        current_row = [ref_index]

        for hyp_index, hyp_item in enumerate(hypothesis, start=1):
            insertion = current_row[hyp_index - 1] + 1
            deletion = previous_row[hyp_index] + 1
            substitution = previous_row[hyp_index - 1] + (ref_item != hyp_item)
            current_row.append(min(insertion, deletion, substitution))

        previous_row = current_row

    return previous_row[-1]


def character_error_rate(reference_text: str, hypothesis_text: str) -> float:
    reference = list(normalize_text(reference_text))
    hypothesis = list(normalize_text(hypothesis_text))

    if not reference:
        return 0.0 if not hypothesis else 1.0

    return levenshtein_distance(reference, hypothesis) / len(reference)


def word_error_rate(reference_text: str, hypothesis_text: str) -> float:
    reference = normalize_text(reference_text).split()
    hypothesis = normalize_text(hypothesis_text).split()

    if not reference:
        return 0.0 if not hypothesis else 1.0

    return levenshtein_distance(reference, hypothesis) / len(reference)


def field_accuracy(expected_fields: dict[str, str], predicted_fields: dict[str, str]) -> dict:
    normalized_expected = {
        key: normalize_field_value(value)
        for key, value in expected_fields.items()
        if value not in (None, "")
    }
    normalized_predicted = {
        key: normalize_field_value(value)
        for key, value in predicted_fields.items()
        if value not in (None, "")
    }

    field_results = {}
    matched = 0

    for key, expected_value in normalized_expected.items():
        predicted_value = normalized_predicted.get(key)
        is_match = predicted_value == expected_value
        field_results[key] = {
            "expected": expected_value,
            "predicted": predicted_value,
            "matched": is_match,
        }
        matched += int(is_match)

    total = len(normalized_expected)
    accuracy = matched / total if total else 0.0

    return {
        "matched_fields": matched,
        "total_fields": total,
        "accuracy": accuracy,
        "details": field_results,
    }


def normalize_field_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, int):
        return str(value)
    return re.sub(r"\s+", " ", str(value)).strip()


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def safe_counter(values: list[str]) -> dict[str, int]:
    return dict(Counter(values))
