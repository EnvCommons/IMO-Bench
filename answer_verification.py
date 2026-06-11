"""Mathematical answer verification utilities."""
from math_verify import parse, verify


def verify_math_answer(answer_one: str, answer_two: str) -> bool:
    """Verify if two math answers are equivalent."""
    parsed_one = parse_answer(answer_one)
    parsed_two = parse_answer(answer_two)
    # Fall back to normalized string comparison when math_verify can't parse
    if not parsed_one or not parsed_two:
        return answer_one.strip().lower() == answer_two.strip().lower()
    try:
        return verify(parsed_one, parsed_two)
    except Exception:
        # A malformed/adversarial answer can make verify() raise; treat that as
        # "not equivalent under symbolic comparison" and fall back to strings.
        return answer_one.strip().lower() == answer_two.strip().lower()


def parse_answer(answer: str) -> list:
    """Parse math answer with LaTeX handling. Returns [] if the input can't be parsed."""
    try:
        parsed = parse(answer)
        # Handle potential LaTeX by wrapping in $ for a proper LaTeX environment
        if not parsed:
            parsed = parse(f"$ {answer} $")
        return parsed
    except Exception:
        return []
