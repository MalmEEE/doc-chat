class FakeProvider:
    """Returns a canned answer and records what it was asked. For tests only."""

    def __init__(self, answer: str = "NOT_FOUND"):
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def generate(self, system: str, prompt: str) -> str:
        self.calls.append((system, prompt))
        return self.answer