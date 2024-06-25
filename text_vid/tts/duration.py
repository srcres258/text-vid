import math


class Duration:
    def __init__(self, raw_duration: float):
        """
        Turn a float value of raw duration into a Duration object.
        :param raw_duration: The raw duration value.
        """

        self.raw_duration = raw_duration
        self.hours: int = int(math.floor(raw_duration / 10 ** 7 / 3600))
        self.minutes: int = int(math.floor((raw_duration / 10 ** 7 / 60) % 60))
        self.seconds: float = (raw_duration / 10 ** 7) % 60

    def seconds_in_total(self) -> float:
        """
        Return the total number of seconds in this duration.
        :return: The total number of seconds in this duration.
        """

        return self.raw_duration / 10 ** 7
