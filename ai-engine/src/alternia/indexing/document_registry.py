import hashlib
import json
from pathlib import Path


class DocumentRegistry:
    """
    Registre persistant des documents indexés.

    Permet de déterminer si un document PDF
    a changé depuis sa dernière indexation.
    """

    def __init__(
        self,
        storage_path: str | Path,
    ):
        self.storage_path = Path(
            storage_path
        )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.documents: dict[str, dict] = {}

        self.load()

    # =========================================================
    # HASH
    # =========================================================

    @staticmethod
    def compute_hash(
        file_path: str | Path,
    ) -> str:

        path = Path(file_path)

        sha256 = hashlib.sha256()

        with path.open(
            "rb"
        ) as file:

            while True:

                block = file.read(
                    1024 * 1024
                )

                if not block:
                    break

                sha256.update(
                    block
                )

        return sha256.hexdigest()

    # =========================================================
    # EXISTENCE
    # =========================================================

    def is_up_to_date(
        self,
        file_path: str | Path,
    ) -> bool:

        path = Path(file_path)

        source = str(path)

        if source not in self.documents:
            return False

        current_hash = self.compute_hash(
            path
        )

        stored_hash = self.documents[
            source
        ].get("hash")

        return current_hash == stored_hash

    # =========================================================
    # ENREGISTREMENT
    # =========================================================

    def register(
        self,
        file_path: str | Path,
        chunk_count: int,
    ) -> None:

        path = Path(file_path)

        self.documents[str(path)] = {
            "hash": self.compute_hash(path),
            "chunk_count": chunk_count,
        }

        self.save()

    # =========================================================
    # PERSISTENCE
    # =========================================================

    def save(self) -> None:

        temporary_path = self.storage_path.with_suffix(
            self.storage_path.suffix + ".tmp"
        )

        temporary_path.write_text(
            json.dumps(
                self.documents,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(
            self.storage_path
        )

    def load(self) -> None:

        if not self.storage_path.exists():
            return

        content = self.storage_path.read_text(
            encoding="utf-8"
        )

        if not content.strip():
            return

        self.documents = json.loads(
            content
        )

    def remove(
        self,
        file_path: str | Path,
    ) -> None:

        self.documents.pop(
            str(Path(file_path)),
            None,
        )

        self.save()