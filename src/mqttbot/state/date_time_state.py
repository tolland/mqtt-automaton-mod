from dataclasses import dataclass

from enum import Enum, auto



@dataclass
class DateTimeState:
    suspended: bool = False
