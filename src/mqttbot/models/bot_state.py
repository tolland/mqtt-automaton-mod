
# Blackboard: state container with event notifications
@dataclass
class BotState:
    position: tuple[float, float, float] = (0, 0, 0)
    health: int = 20
    inventory: dict[str, int] = None
    entities: dict[str, dict] = None
    players: dict[str, dict] = None

    def __post_init__(self):
        if self.inventory is None:
            self.inventory = {}
        if self.entities is None:
            self.entities = {}
        if self.players is None:
            self.players = {}
