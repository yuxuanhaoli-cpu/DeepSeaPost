"""Rules and maps for Deep Sea Post. The model can run without a GUI."""

from dataclasses import dataclass
from typing import NamedTuple


class Dive(NamedTuple):
    name: str
    hint: str
    battery: int
    par: int
    chart: tuple[str, ...]


DIVES = (
    Dive("浅海试航", "规划路线，集齐 2 个邮包后返航。", 18, 15, (
        "###########",
        "#S...#...E#",
        "#.##.#.##.#",
        "#..P...#..#",
        "###.##.#.##",
        "#...#..P..#",
        "#.###.##..#",
        "#.........#",
        "###########",
    )),
)


@dataclass(frozen=True)
class State:
    position: tuple[int, int]
    battery: int
    packets: frozenset[tuple[int, int]]
    chargers: frozenset[tuple[int, int]]
    unlocked: bool = False
    turns: int = 0
    outcome: str = "playing"


class Game:
    def __init__(self, index=0):
        self.index = index
        self.dive = DIVES[index]
        self.chart = self.dive.chart
        self.start = next(iter(self.find("S")))
        self.exit = next(iter(self.find("E")))
        self.total_packets = len(self.find("P"))
        self.reset()

    def find(self, tile):
        return frozenset(
            (x, y) for y, row in enumerate(self.chart)
            for x, value in enumerate(row) if value == tile
        )

    def reset(self):
        self.state = State(self.start, self.dive.battery, self.find("P"), self.find("C"))
        self.history = []

    def move(self, dx, dy):
        if abs(dx) + abs(dy) != 1:
            raise ValueError("A move must go one tile in a cardinal direction.")
        state = self.state
        if state.outcome != "playing":
            return ""
        x, y = state.position
        point = x + dx, y + dy
        tile = self.chart[point[1]][point[0]]
        if tile == "#":
            return "前方是礁石。"
        if point == self.exit and state.packets:
            return "还有邮包没有收齐。"

        battery = state.battery - 1
        packets = state.packets - {point}
        outcome = "playing"
        message = "已回收邮包。" if point in state.packets else ""
        if point == self.exit and battery >= 0:
            outcome = "won"
            message = "邮包全部送达。"
        elif battery <= 0:
            outcome = "lost"
            message = "电量耗尽。"
        self.history.append(state)
        self.state = State(point, max(0, battery), packets, state.chargers,
                           state.unlocked, state.turns + 1, outcome)
        return message
