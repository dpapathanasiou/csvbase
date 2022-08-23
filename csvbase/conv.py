import re
from datetime import date
from typing import Iterable, Optional, Pattern

from . import exc

WHITESPACE_REGEX = re.compile(r"^ *$")


def sniff_and_allow_blanks(regex: Pattern, values: Iterable[str]) -> bool:
    """This function takes a regex and looks at the values, return if:
    - at least one value matches the regex
    - the others are blanks

    and false otherwise."""
    non_match = False
    one_match = False
    for value in values:
        if regex.match(value):
            one_match = True
        elif WHITESPACE_REGEX.match(value):
            continue
        else:
            non_match = True
            break
    return (non_match is False) and one_match


class DateConverter:
    DATE_REGEX = re.compile(r"^ ?\d{4}-\d{2}-\d{2} ?$")
    DATE_FORMAT = "%Y-%m-%d"

    def sniff(self, values: Iterable[str]) -> bool:
        return sniff_and_allow_blanks(self.DATE_REGEX, values)

    def convert(self, value: str) -> Optional[date]:
        stripped = value.strip()
        if stripped == "":
            return None

        try:
            return date.fromisoformat(stripped)
        except ValueError:
            raise exc.UnconvertableValueException()


class IntegerConverter:
    INTEGER_REGEX = re.compile(r"^ ?-?(\d|,| )+$")

    def sniff(self, values: Iterable[str]) -> bool:
        return sniff_and_allow_blanks(self.INTEGER_REGEX, values)

    def convert(self, value: str) -> Optional[int]:
        stripped = value.strip()
        if stripped == "":
            return None
        match = self.INTEGER_REGEX.match(value)
        if not match:
            raise exc.UnconvertableValueException()
        return int(match.group().replace(",", ""))


class FloatConverter:
    FLOAT_REGEX = re.compile(r"^ ?-?(\d|,|\.| )+$")

    def sniff(self, values: Iterable[str]) -> bool:
        return sniff_and_allow_blanks(self.FLOAT_REGEX, values)

    def convert(self, value: str) -> Optional[float]:
        stripped = value.strip()
        if stripped == "":
            return None
        match = self.FLOAT_REGEX.match(value)
        if not match:
            raise exc.UnconvertableValueException()
        return float(match.group().replace(",", ""))


class BooleanConverter:
    BOOLEAN_REGEX = re.compile(r"^ ?(TRUE|FALSE|T|F|YES|NO|Y|N) ?$", re.I)
    TRUE_REGEX = re.compile(r"^(TRUE|T|YES|Y)$", re.I)
    FALSE_REGEX = re.compile(r"^(FALSE|F|NO|N)$", re.I)

    def sniff(self, values: Iterable[str]) -> bool:
        return sniff_and_allow_blanks(self.BOOLEAN_REGEX, values)

    def convert(self, value: str) -> Optional[float]:
        stripped = value.strip()
        if stripped == "":
            return None

        false_match = self.FALSE_REGEX.match(stripped)
        if false_match:
            return False

        true_match = self.TRUE_REGEX.match(stripped)
        if true_match:
            return True

        raise exc.UnconvertableValueException()
