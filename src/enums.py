from enum import Enum


class Distance(Enum):
    NO_TRANSPORTATION = 1  #Set to default of 1 mile to allow walking and bus
    WITHIN_IOWA_CITY_CORALVILLE_NORTH_LIBERTY = 8
    UP_TO_15_MILES = 15
    UP_TO_30_MILES = 30
