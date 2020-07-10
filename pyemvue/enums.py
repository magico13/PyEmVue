from enum import Enum

class Scale(Enum):
    SECOND = '1S'
    MINUTE = '1MIN'
    MINUTES_15 = '15MIN'
    HOUR = '1H'
    # These higher times are only valid for /usage/date calls
    DAY = '1D'
    WEEK = '1W'
    MONTH = '1MON'
    YEAR = '1Y'

class Unit(Enum):
    WATTS = 'WATTS'
    USD = 'USD'
    TREES = 'TREES'
    GAS = 'GALLONSGAS'
    DRIVEN = 'MILESDRIVEN'
    FLOWN = 'MILESFLOWN'


class TotalTimeFrame(Enum):
    ALL = 'ALLTODATE'
    MONTH = 'MONTHTODATE'

class TotalUnit(Enum):
    WATTHOURS = 'WATTHOURS'