"""Rules and maps for Deep Sea Post. The model can run without a GUI."""

from collections import deque
from dataclasses import dataclass, replace
from math import ceil
from random import choice
from time import monotonic
from typing import NamedTuple


class Dive(NamedTuple):
    name: str
    hint: str
    battery: int
    par: int
    chart: tuple[str, ...]


DIVES = (
    Dive("浅海试航", "规划路线，集齐 2 个邮包后返航。", 18, 16, (
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
    Dive("断电峡谷", "蓝色洋流格消耗 3 格电。电站只能使用一次。", 13, 22, (
        "###########",
        "#S.P#..P.E#",
        "#.#.#.##..#",
        "#.#...##..#",
        "#.###X###.#",
        "#..XC....P#",
        "##.##.##..#",
        "#.........#",
        "###########",
    )),
    Dive("深渊灯塔", "收起金色信标来打开闸门。留意最后的电量。", 14, 26, (
        "###########",
        "#S..#P.D.E#",
        "#.#.#.##..#",
        "#K#.#.##..#",
        "#.#...#####",
        "#P##X...P.#",
        "#.X..##...#",
        "#.......C.#",
        "###########",
    )),
)

ENDLESS_SECONDS = 60
ENDLESS_DIVE = Dive("迷雾无尽", "跟着邮包标记探索。回收后会立即充满电。", 15, 0, (
    "###########",
    "#S..#.....#",
    "#.#.#.##..#",
    "#.#.......#",
    "#...###.#.#",
    "###.....#.#",
    "#...#.#...#",
    "#.........#",
    "###########",
))


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
    def __init__(self, index=0, *, dive=None):
        self.index = index
        self.dive = DIVES[index] if dive is None else dive
        self.chart = self.dive.chart
        self.start = next(iter(self.find("S")))
        self.exit = next(iter(self.find("E")), None)
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
        if tile == "D" and not state.unlocked:
            return "闸门关闭。先找到金色信标。"
        if point == self.exit and state.packets:
            return "还有邮包没有收齐。"

        battery = state.battery - (3 if tile == "X" else 1)
        packets = state.packets
        chargers = state.chargers
        unlocked = state.unlocked
        outcome = "playing"
        message = "洋流消耗了 3 格电。" if tile == "X" else ""
        if battery >= 0:
            if point in packets:
                packets = packets - {point}
                message = "已回收邮包。"
            if point in chargers:
                chargers = chargers - {point}
                battery = self.dive.battery
                message = "电量已充满。"
            if tile == "K" and not unlocked:
                unlocked = True
                message = "信标已回收，闸门打开。"

        if point == self.exit and battery >= 0:
            outcome = "won"
            message = "邮包全部送达。"
        elif battery <= 0:
            outcome = "lost"
            message = "电量耗尽。"
        self.history.append(state)
        self.state = State(point, max(0, battery), packets, chargers,
                           unlocked, state.turns + 1, outcome)
        return message

    def undo(self):
        if not self.history:
            return False
        self.state = self.history.pop()
        return True


class EndlessGame(Game):
    """Timed score challenge with one reachable packet on the chart at a time."""

    def __init__(self, clock=monotonic):
        self.clock = clock
        super().__init__(dive=ENDLESS_DIVE)

    def reset(self):
        super().reset()
        self.score = 0
        self.state = replace(self.state, packets=self.spawn(self.start))
        self.finished_seconds = None
        self.deadline = self.clock() + ENDLESS_SECONDS

    @property
    def seconds_left(self):
        if self.finished_seconds is not None:
            return self.finished_seconds
        return max(0, ceil(self.deadline - self.clock()))

    def expire(self):
        if self.state.outcome == "playing" and self.seconds_left == 0:
            self.state = replace(self.state, outcome="timeout")

    def spawn(self, start):
        # Every step on this chart costs one unit, so BFS gives the energy cost.
        queue = deque([(start, 0)])
        seen = {start}
        candidates = []
        while queue:
            (x, y), distance = queue.popleft()
            if distance >= 5:
                candidates.append((x, y))
            if distance == 10:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                point = nx, ny
                if point not in seen and self.chart[ny][nx] != "#":
                    seen.add(point)
                    queue.append((point, distance + 1))
        return frozenset({choice(candidates)})

    def move(self, dx, dy):
        self.expire()
        before = self.state
        message = super().move(dx, dy)
        self.history.clear()
        if self.state.packets == before.packets:
            if self.state.outcome == "lost":
                self.finished_seconds = self.seconds_left
            return message

        self.score += 1
        self.state = replace(self.state, battery=self.dive.battery, outcome="playing",
                             packets=self.spawn(self.state.position))
        return "邮包已回收，电量充满，新邮包已出现。"
