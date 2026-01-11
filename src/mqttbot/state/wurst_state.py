from dataclasses import dataclass

from enum import Enum, auto



@dataclass
class WurstState:
    suspended: bool = False
