from pathlib import Path


CLASS_MAP = {
    "10eme": "10eme",
    "11eme": "11eme",
    "12eme": "12eme",
}


SUBJECT_MAP = {
    "mathematiques": "mathematiques",
    "math": "mathematiques",
    "physique": "physique",
    "chimie": "chimie",
    "francais": "francais",
    "anglais": "anglais",
    "histoire": "histoire",
    "geographie": "geographie",
    "sciences": "sciences",
}


def infer_class(path: str | Path) -> str | None:

    name = str(path).lower()

    for key, value in CLASS_MAP.items():

        if key in name:
            return value

    return None


def infer_subject(path: str | Path) -> str | None:

    name = str(path).lower()

    for key, value in SUBJECT_MAP.items():

        if key in name:
            return value

    return None
