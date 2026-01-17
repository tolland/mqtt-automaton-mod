from dataclasses import dataclass


@dataclass
class GameState:
    suspended: bool = False
