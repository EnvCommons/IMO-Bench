"""Mathematical answer verification utilities."""
from math_verify import parse, verify


def verify_math_answer(answer_one: str, answer_two: str) -> bool:
    """Verify if two math answers are equivalent."""
    parsed_one = parse_answer(answer_one)
    parsed_two = parse_answer(answer_two)
    # Fall back to normalized string comparison when math_verify can't parse
    if not parsed_one or not parsed_two:
        return answer_one.strip().lower() == answer_two.strip().lower()
    return verify(parsed_one, parsed_two)


def parse_answer(answer: str) -> list:
    """Parse math answer with LaTeX handling."""
    parsed = parse(answer)
    # Handle potential LaTeX by wrapping in $ for a proper LaTeX environment
    if not parsed:
        parsed = parse(f"$ {answer} $")
    return parsed
