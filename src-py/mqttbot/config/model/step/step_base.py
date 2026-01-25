from __future__ import annotations

from mqttbot.config.model.metadata import WithMetadata


class StepBase(WithMetadata):
    """Base for all step types."""

    type: str

    def to_dict(self) -> dict:
        """Return a dictionary representation of the step."""
        return self.model_dump()

    # def __rich_repr__(self):
    #     for name, value in self.__dict__.items():
    #         if name != "type":  # Skip the discriminator to save space
    #             yield name, value
