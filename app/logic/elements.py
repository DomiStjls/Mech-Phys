class Block:
    def __init__(self, x: int, y: int, width: int = 60, height: int = 30):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def to_svg(self) -> str:
        return f'<rect x="{self.x}" y="{self.y}" width="{self.width}" height="{self.height}" fill="gray" stroke="black" stroke-width="2" />'


class Force:
    def __init__(self, x: int, y: int, dx: int = 40, dy: int = 0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy

    def to_svg(self) -> str:
        x2 = self.x + self.dx
        y2 = self.y + self.dy
        return f'<line x1="{self.x}" y1="{self.y}" x2="{x2}" y2="{y2}" stroke="red" stroke-width="2" marker-end="url(#arrow)" />'

    def move(self, dx: int = 0, dy: int = 0):
        self.x += dx
        self.y += dy