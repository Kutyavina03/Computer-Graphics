import tkinter as tk
from tkinter import messagebox, filedialog
import struct, math


class Rasterizer:
    def __init__(self, root):
        self.root = root
        self.root.geometry("600x600")

        self.W = 500
        self.H = 500
        self.gold = (218, 165, 32)
        self.gold_hex = "#DAA520"

        self.build_ui()
        self.build_canvas()

    def build_ui(self):
        main = tk.Frame(self.root)
        main.pack(pady=10)

        pf = tk.LabelFrame(main, text="Параметры золотого треугольника", padx=5, pady=5)
        pf.pack(fill=tk.X, padx=5, pady=5)
        row = tk.Frame(pf)
        row.pack(fill=tk.X, pady=2)

        tk.Label(row, text="Вершина A:").pack(side=tk.LEFT, padx=2)
        tk.Label(row, text="X1:").pack(side=tk.LEFT, padx=2)
        self.x1 = tk.Entry(row, width=5)
        self.x1.pack(side=tk.LEFT, padx=2)
        self.x1.insert(0, "400")

        tk.Label(row, text="Y1:").pack(side=tk.LEFT, padx=2)
        self.y1 = tk.Entry(row, width=5)
        self.y1.pack(side=tk.LEFT, padx=2)
        self.y1.insert(0, "100")

        tk.Label(row, text="Вершина B:").pack(side=tk.LEFT, padx=15)
        tk.Label(row, text="X2:").pack(side=tk.LEFT, padx=2)
        self.x2 = tk.Entry(row, width=5)
        self.x2.pack(side=tk.LEFT, padx=2)
        self.x2.insert(0, "300")

        tk.Label(row, text="Y2:").pack(side=tk.LEFT, padx=2)
        self.y2 = tk.Entry(row, width=5)
        self.y2.pack(side=tk.LEFT, padx=2)
        self.y2.insert(0, "300")

        af = tk.LabelFrame(main, text="Алгоритмы растеризации", padx=5, pady=5)
        af.pack(fill=tk.X, padx=5, pady=5)
        br = tk.Frame(af)
        br.pack(fill=tk.X)

        tk.Button(br, text="ЦДА", command=self.draw_dda, width=15).pack(side=tk.LEFT, padx=2)
        tk.Button(br, text="Брезенхем", command=self.draw_bresenham, width=15).pack(side=tk.LEFT, padx=2)
        tk.Button(br, text="Целочисленный", command=self.draw_int_bresenham, width=15).pack(side=tk.LEFT, padx=2)
        tk.Button(br, text="Встроенные", command=self.draw_builtin, width=15).pack(side=tk.LEFT, padx=2)

        cf = tk.LabelFrame(main, text="Управление", padx=5, pady=5)
        cf.pack(fill=tk.X, padx=5, pady=5)
        cb = tk.Frame(cf)
        cb.pack(fill=tk.X)

        tk.Button(cb, text="Сохранить BMP", command=self.save_bmp, width=15).pack(side=tk.LEFT, padx=2)
        tk.Button(cb, text="Сохранить PBM", command=self.save_pbm, width=15).pack(side=tk.LEFT, padx=2)
        tk.Button(cb, text="Очистить", command=self.clear, width=15).pack(side=tk.LEFT, padx=2)

    def build_canvas(self):
        self.canvas = tk.Canvas(self.root, bg="white", width=self.W, height=self.H,
                                relief=tk.SUNKEN, bd=2)
        self.canvas.pack(pady=10)
        self.pixels = self.new_pixels()

    def new_pixels(self):
        return [[(255, 255, 255) for _ in range(self.W)] for _ in range(self.H)]

    def clear(self):
        self.pixels = self.new_pixels()
        self.canvas.delete("all")

    # ЗОЛОТОЙ ТРЕУГОЛЬНИК
    def get_points(self):
        try:
            x1, y1 = float(self.x1.get()), float(self.y1.get())
            x2, y2 = float(self.x2.get()), float(self.y2.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректные координаты")
            return None

        dx, dy = x2 - x1, y2 - y1
        side = math.hypot(dx, dy)
        if side == 0:
            messagebox.showerror("Ошибка", "Точки A и B совпадают")
            return None

        phi = (1 + math.sqrt(5)) / 2
        base = side / phi
        ux, uy = dx / side, dy / side
        t = side - base * base / (2 * side)
        h = math.sqrt(side * side - t * t)
        px, py = -uy, ux
        x3 = x1 + t * ux + h * px
        y3 = y1 + t * uy + h * py

        return [(x1, y1), (x2, y2), (x3, y3), (x1, y1)]

    # АЛГОРИТМЫ
    def set_pixel(self, x, y):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.pixels[y][x] = self.gold

    def dda(self, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            self.set_pixel(round(x1), round(y1))
            return
        xi, yi = dx / steps, dy / steps
        for _ in range(int(steps) + 1):
            self.set_pixel(round(x1), round(y1))
            x1 += xi
            y1 += yi

    def bresenham(self, x1, y1, x2, y2):
        x1, y1, x2, y2 = map(lambda v: int(round(v)), (x1, y1, x2, y2))
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
        err = dx - dy
        while True:
            self.set_pixel(x1, y1)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def int_bresenham(self, x1, y1, x2, y2):
        x1, y1, x2, y2 = map(lambda v: int(round(v)), (x1, y1, x2, y2))
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
        if dx > dy:
            err = dx // 2
            for _ in range(dx + 1):
                self.set_pixel(x1, y1)
                err -= dy
                if err < 0:
                    y1 += sy
                    err += dx
                x1 += sx
        else:
            err = dy // 2
            for _ in range(dy + 1):
                self.set_pixel(x1, y1)
                err -= dx
                if err < 0:
                    x1 += sx
                    err += dy
                y1 += sy

    # ОТРИСОВКА
    def draw_with(self, algorithm):
        pts = self.get_points()
        if not pts:
            return
        self.clear()
        for i in range(3):
            algorithm(*pts[i], *pts[i + 1])
        self.refresh()

    def draw_dda(self):
        self.draw_with(self.dda)

    def draw_bresenham(self):
        self.draw_with(self.bresenham)

    def draw_int_bresenham(self):
        self.draw_with(self.int_bresenham)

    def draw_builtin(self):
        pts = self.get_points()
        if not pts:
            return
        self.clear()
        flat = [v for p in pts for v in p]
        self.canvas.create_polygon(flat, outline=self.gold_hex, fill="", width=1)
        for i in range(3):
            self.bresenham(*pts[i], *pts[i + 1])

    # ОТОБРАЖЕНИЕ
    def refresh(self):
        self.canvas.delete("all")
        header = f"P6\n{self.W} {self.H}\n255\n".encode()
        data = bytearray()
        for y in range(self.H):
            for x in range(self.W):
                data.extend(self.pixels[y][x])
        photo = tk.PhotoImage(data=header + data)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo

    # СОХРАНЕНИЕ BMP
    def save_bmp(self):
        fn = filedialog.asksaveasfilename(defaultextension=".bmp",
                                           filetypes=[("BMP", "*.bmp")])
        if not fn:
            return
        try:
            row = self.W * 3
            pad = (4 - row % 4) % 4
            size = self.H * (row + pad)
            with open(fn, "wb") as f:
                f.write(b"BM")
                f.write(struct.pack("<I", 54 + size))
                f.write(struct.pack("<I", 0))
                f.write(struct.pack("<I", 54))
                f.write(struct.pack("<I", 40))
                f.write(struct.pack("<i", self.W))
                f.write(struct.pack("<i", self.H))
                f.write(struct.pack("<H", 1))
                f.write(struct.pack("<H", 24))
                f.write(struct.pack("<I", 0))
                f.write(struct.pack("<I", size))
                f.write(struct.pack("<i", 0))
                f.write(struct.pack("<i", 0))
                f.write(struct.pack("<I", 0))
                f.write(struct.pack("<I", 0))
                for y in range(self.H - 1, -1, -1):
                    for x in range(self.W):
                        r, g, b = self.pixels[y][x]
                        f.write(struct.pack("BBB", b, g, r))
                    f.write(b"\x00" * pad)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # СОХРАНЕНИЕ PBM
    def save_pbm(self):
        fn = filedialog.asksaveasfilename(defaultextension=".pbm",
                                           filetypes=[("PBM", "*.pbm")])
        if not fn:
            return
        try:
            with open(fn, "w") as f:
                f.write("P1\n# Золотой треугольник\n")
                f.write(f"{self.W} {self.H}\n")
                for y in range(self.H):
                    row = ["0" if self.pixels[y][x] == (255, 255, 255) else "1"
                           for x in range(self.W)]
                    f.write(" ".join(row) + "\n")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


def main():
    root = tk.Tk()
    Rasterizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()