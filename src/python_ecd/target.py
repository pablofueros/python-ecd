from dataclasses import dataclass
from pathlib import Path
from typing import Literal

type ChallengeCategory = Literal["event", "story"]


@dataclass(frozen=True)
class ChallengeTarget:
    category: ChallengeCategory
    edition: int
    quest: int

    @property
    def api_event(self) -> int:
        """Return the event identifier expected by everybody-codes-data."""
        return self.edition

    @property
    def relative_dir(self) -> Path:
        """Return the quest directory relative to the workspace root."""
        collection = "events" if self.category == "event" else "stories"
        return Path(collection) / str(self.edition) / f"quest_{self.quest:02d}"

    @property
    def label(self) -> str:
        """Return a human-readable challenge label."""
        category = "Event" if self.category == "event" else "Story"
        return f"{category} {self.edition} Quest {self.quest}"
