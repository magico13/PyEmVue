from enum import Enum


class Scale(str, Enum):
    SECOND = "1S"
    MINUTE = "1MIN"
    MINUTES_15 = "15MIN"
    HOUR = "1H"
    DAY = "1D"
    WEEK = "1W"
    MONTH = "1MON"
    YEAR = "1Y"

    def __str__(self) -> str:
        return self.value


class Unit(str, Enum):
    KWH = "KilowattHours"
    USD = "Dollars"
    AMPHOURS = "AmpHours"
    TREES = "Trees"
    GAS = "GallonsOfGas"
    DRIVEN = "MilesDriven"
    CARBON = "Carbon"

    def __str__(self) -> str:
        return self.value
