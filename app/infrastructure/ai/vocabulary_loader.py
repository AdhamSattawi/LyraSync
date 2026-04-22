from pathlib import Path

VOCABULARY_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "resources" / "vocabularies"
)


def load_profession_vocabulary(profession: str) -> list[str]:
    """
    Loads the static vocabulary for a given profession from the .txt files.
    Always merges with general.txt (shared business terms).
    Returns an empty list if no vocabulary file exists for the profession.
    """
    terms: list[str] = []

    # Always load general/shared terms
    general_file = VOCABULARY_DIR / "general.txt"
    if general_file.exists():
        terms.extend(_parse_vocab_file(general_file))

    # Load profession-specific terms
    profession_file = VOCABULARY_DIR / f"{profession}.txt"
    if profession_file.exists():
        terms.extend(_parse_vocab_file(profession_file))

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        lower = term.lower()
        if lower not in seen:
            seen.add(lower)
            unique.append(term)

    return unique


def _parse_vocab_file(path: Path) -> list[str]:
    """Reads a comma-separated vocabulary file and returns a clean list of terms."""
    content = path.read_text(encoding="utf-8")
    return [term.strip() for term in content.split(",") if term.strip()]
