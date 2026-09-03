from typing import Protocol


class Committer(Protocol):
    """Commits the work performed by an application operation."""

    def commit(self) -> None:
        """Make the current application operation persistent."""
        ...
