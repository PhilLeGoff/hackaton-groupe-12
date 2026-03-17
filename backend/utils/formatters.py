def parse_confidence(value: str) -> float:
    return float(value.replace("%", ""))