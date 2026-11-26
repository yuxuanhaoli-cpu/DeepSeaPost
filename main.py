"""Tkinter interface for the original puzzle game Deep Sea Post."""

import tkinter as tk
from tkinter import font

from game import DIVES, Game


BG = "#071722"
PANEL = "#0D2330"
EDGE = "#20414C"
TEXT = "#E5F6F5"
MUTED = "#8EAFBA"
MINT = "#7CE8C7"
GOLD = "#F5C46F"
BLUE = "#78BDF8"
RED = "#FF9A96"
GRID_X, GRID_Y, TILE = 53, 198, 44
DIRECTIONS = {
    "Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1),
    "a": (-1, 0), "d": (1, 0), "w": (0, -1), "s": (0, 1),
}


class Window:
    def __init__(self, root):
        self.root = root
        root.title("深海邮差  /  Deep Sea Post")
        root.configure(bg=BG)
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=1000, height=664, bg=BG, highlightthickness=0)
        self.canvas.pack()
        families = set(font.families(root))
        self.typeface = next(
            (name for name in ("Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC")
             if name in families),
            "TkDefaultFont",
        )
        self.best = {}
        self.buttons = []
        self.fog = False
        self.load(0)
        root.bind("<KeyPress>", self.key)
        self.canvas.bind("<Button-1>", self.click)

    def load(self, index):
        self.game = Game(index)
        self.message = self.game.dive.hint
        self.draw()

    def key(self, event):
        key = event.keysym if event.keysym in DIRECTIONS else event.keysym.lower()
        if key in DIRECTIONS:
            self.move(*DIRECTIONS[key])
        elif key in ("z", "backspace"):
            self.undo()
        elif key == "r":
            self.load(self.game.index)
        elif key == "f":
            self.toggle_fog()
        elif key in ("1", "2", "3"):
            self.load(int(key) - 1)
        elif key == "return" and self.game.state.outcome == "won":
            self.advance()

    def move(self, dx, dy):
        if self.game.state.outcome != "playing":
            return
        before = self.game.state
        message = self.game.move(dx, dy)
        state = self.game.state
        if message or state != before:
            self.message = message or self.game.dive.hint
        if state.outcome == "won":
            best = self.best.get(self.game.index, state.turns)
            self.best[self.game.index] = min(best, state.turns)
        self.draw()

    def undo(self):
        if self.game.undo():
            self.message = "已撤销一步，电量与地图状态已恢复。"
            self.draw()

    def advance(self):
        self.load((self.game.index + 1) % len(DIVES))

    def toggle_fog(self):
        self.fog = not self.fog
        self.draw()

    def click(self, event):
        for (x1, y1, x2, y2), action in self.buttons:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                action()
                return

    def label(self, x, y, value, size=14, color=TEXT, bold=False, anchor="w", mono=False):
        family = "Consolas" if mono else self.typeface
        self.canvas.create_text(
            x, y, text=value, fill=color, anchor=anchor,
            font=(family, -size, "bold" if bold else "normal"),
        )

    def box(self, x1, y1, x2, y2, fill, edge=""):
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=edge)

    def button(self, bounds, caption, action, active=False):
        x1, y1, x2, y2 = bounds
        self.box(*bounds, "#163C41" if active else PANEL, MINT if active else EDGE)
        self.label((x1 + x2) / 2, (y1 + y2) / 2, caption,
                   14, MINT if active else TEXT, active, "center")
        self.buttons.append((bounds, action))

    def draw(self):
        self.canvas.delete("all")
        self.buttons.clear()
        state = self.game.state
        dive = self.game.dive
        self.label(36, 28, "D E E P   S E A   P O S T", 13, MINT, mono=True)
        self.label(34, 65, "深海邮差", 38, TEXT, True)
        self.label(36, 103, "收齐邮包，赶在电力耗尽前返航。", 15, MUTED)
        self.label(964, 37, f"航线 {self.game.index + 1:02} / {len(DIVES):02}", 15,
                   MINT, anchor="e")
        fog_caption = "F  迷雾：开" if self.fog else "F  迷雾：关"
        self.button((836, 65, 965, 103), fog_caption, self.toggle_fog, active=self.fog)
        self.canvas.create_line(35, 126, 965, 126, fill=EDGE)

        self.box(35, 149, 555, 607, PANEL, EDGE)
        self.label(53, 173, dive.name, 17, TEXT, True)
        chart_label = "视野：相邻四格" if self.fog else "航  行  图"
        self.label(538, 173, chart_label, 12, MUTED, anchor="e")
        for y, row in enumerate(dive.chart):
            for x, value in enumerate(row):
                self.tile(x, y, value)

        self.box(578, 149, 965, 607, PANEL, EDGE)
        self.label(598, 175, "任务状态", 17, TEXT, True)
        self.label(598, 215, "潜艇电量", 14, MUTED)
        battery_color = RED if state.battery <= 4 else MINT
        self.label(945, 215, f"{state.battery:02} / {dive.battery:02}", 17,
                   battery_color, True, "e", True)
        bar_width = 347 / dive.battery
        for segment in range(dive.battery):
            left = 598 + segment * bar_width
            self.box(left, 234, left + bar_width - 3, 244,
                     battery_color if segment < state.battery else "#23404A")

        self.label(598, 272, "已回收邮包", 14, MUTED)
        collected = self.game.total_packets - len(state.packets)
        self.label(945, 272, f"{collected} / {self.game.total_packets}", 17, GOLD,
                   True, "e", True)
        self.label(598, 302, "航行步数", 14, MUTED)
        self.label(945, 302, f"{state.turns:02} / {dive.par:02}", 17, TEXT,
                   True, "e", True)
        self.label(598, 328, "步数参照为当前航线的最短可行路线。", 12, MUTED)
        self.canvas.create_line(598, 349, 945, 349, fill=EDGE)

        self.label(598, 373, "图例", 15, TEXT, True)
        for x, y, icon, caption in (
            (609, 409, "P", "邮包"), (732, 409, "E", "返航口"), (851, 409, "C", "充电站"),
            (609, 446, "X", "洋流"), (732, 446, "K", "信标"), (851, 446, "D", "闸门"),
        ):
            self.symbol(x, y, icon, ready=True)
            self.label(x + 20, y, caption, 13, MUTED)

        self.notice()
        self.button((598, 552, 700, 586), "Z  撤销", self.undo)
        self.button((711, 552, 813, 586), "R  重来", lambda: self.load(self.game.index))
        if state.outcome == "won":
            caption = "下一航线 →" if self.game.index < len(DIVES) - 1 else "返回首关 →"
            self.button((824, 552, 945, 586), caption, self.advance, active=True)

        for i in range(len(DIVES)):
            x = 35 + i * 74
            suffix = " ✓" if i in self.best else ""
            self.button((x, 622, x + 63, 649), f"{i + 1:02}{suffix}",
                        lambda index=i: self.load(index), active=self.game.index == i)
        self.label(273, 636, "点击编号选关", 13, MUTED)
        self.label(965, 636, "方向键 / WASD  移动", 14, MUTED, anchor="e")

    def notice(self):
        state = self.game.state
        color = MINT
        heading = "航行提示"
        message = self.message
        if state.outcome == "won":
            heading = "投递成功"
            message = f"本关最佳 {self.best[self.game.index]} 步。本次已完成 {len(self.best)} / {len(DIVES)} 条航线。"
        elif state.outcome == "lost":
            heading = "电量耗尽"
            color = RED
            message = "按 Z 撤销一步，或按 R 重新规划路线。"
        self.box(598, 475, 945, 530, "#102D3A", EDGE)
        self.label(612, 491, heading, 13, color, True)
        self.label(612, 513, message, 13)

    def tile(self, x, y, value):
        state = self.game.state
        left, top = GRID_X + x * TILE, GRID_Y + y * TILE
        cx, cy = left + TILE / 2, top + TILE / 2
        point = (x, y)
        px, py = state.position
        if self.fog and abs(x - px) + abs(y - py) > 1:
            self.box(left, top, left + TILE - 1, top + TILE - 1, "#081923", "#102733")
            if point in state.packets:
                self.symbol(cx, cy, "P")
            elif point == self.game.exit:
                self.symbol(cx, cy, "E", ready=not state.packets)
            return

        if value == "#":
            self.box(left, top, left + TILE - 1, top + TILE - 1, "#173440", "#193844")
            self.canvas.create_line(left + 5, top + 16, left + 20, top + 5, fill="#224553")
            self.canvas.create_line(left + 24, top + 37, left + 37, top + 26, fill="#224553")
            return
        background = "#0A202D" if (x + y) % 2 else "#0B2532"
        if value == "X":
            background = "#102F48"
        self.box(left, top, left + TILE - 1, top + TILE - 1, background, "#14333F")
        if state.position == point:
            self.symbol(cx, cy, "sub")
        elif point in state.packets:
            self.symbol(cx, cy, "P")
        elif point in state.chargers:
            self.symbol(cx, cy, "C")
        elif value == "K" and not state.unlocked:
            self.symbol(cx, cy, "K")
        elif value in "EXD":
            ready = state.unlocked if value == "D" else not state.packets
            self.symbol(cx, cy, value, ready)
        else:
            self.canvas.create_oval(cx - 1, cy - 1, cx + 1, cy + 1, fill="#235063", outline="")

    def symbol(self, x, y, kind, ready=False):
        canvas = self.canvas
        if kind == "sub":
            canvas.create_oval(x - 18, y - 18, x + 18, y + 18, fill="#14525A", outline="")
            canvas.create_polygon(x - 12, y, x - 16, y - 6, x - 16, y + 6, fill=MINT)
            canvas.create_oval(x - 12, y - 8, x + 14, y + 8, fill=MINT, outline="")
            self.box(x - 3, y - 12, x + 3, y - 5, MINT)
            canvas.create_oval(x + 1, y - 4, x + 9, y + 4, fill="#10515A", outline="")
        elif kind == "P":
            self.box(x - 10, y - 7, x + 10, y + 7, "#4F3C30", GOLD)
            canvas.create_line(x - 10, y - 7, x, y + 1, x + 10, y - 7, fill=GOLD)
        elif kind == "E":
            color = MINT if ready else MUTED
            canvas.create_oval(x - 11, y - 11, x + 11, y + 11, outline=color, width=2)
            canvas.create_line(x - 4, y, x + 5, y, fill=color, arrow="last")
        elif kind == "C":
            self.box(x - 9, y - 9, x + 9, y + 9, "#164B46", MINT)
            canvas.create_polygon(x + 1, y - 7, x - 5, y + 1, x, y + 1,
                                  x - 1, y + 7, x + 5, y - 2, x + 1, y - 2, fill=MINT)
        elif kind == "X":
            for offset in (-4, 4):
                canvas.create_line(x - 11, y + offset, x - 4, y + offset - 3,
                                   x + 4, y + offset + 2, x + 11, y + offset - 2,
                                   fill=BLUE, width=2, smooth=True)
        elif kind == "K":
            canvas.create_polygon(x, y - 10, x + 8, y, x, y + 10, x - 8, y,
                                  fill=GOLD, outline="#FFDEA2")
        elif kind == "D":
            self.box(x - 9, y - 10, x + 9, y + 10, "#243D45", MUTED)
            for offset in (-4, 4):
                canvas.create_line(x + offset, y - 10, x + offset, y + 10,
                                   fill=MINT if ready else MUTED, width=2)


def main():
    root = tk.Tk()
    Window(root)
    root.mainloop()


if __name__ == "__main__":
    main()
