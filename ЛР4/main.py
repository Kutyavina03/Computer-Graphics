import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageDraw
import math


class LensRasterizer:
    def __init__(self, root):
        self.root = root
        self.root.geometry("900x750")

        self.image = None
        self.scale = 1

        # верхняя панель управления
        top = ttk.Frame(root, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        # параметры первой окружности
        p1 = ttk.LabelFrame(top, text="Окружность 1", padding=5)
        p1.pack(side=tk.LEFT, padx=(0, 10))
        for label, attr, default in [("X1:", "x1_entry", "-80"), ("Y1:", "y1_entry", "0"), ("R1:", "r1_entry", "200")]:
            ttk.Label(p1, text=label).pack(side=tk.LEFT, padx=(0, 3))
            e = ttk.Entry(p1, width=6)
            e.insert(0, default)
            e.pack(side=tk.LEFT, padx=(0, 8))
            setattr(self, attr, e)

        # параметры второй окружности
        p2 = ttk.LabelFrame(top, text="Окружность 2", padding=5)
        p2.pack(side=tk.LEFT, padx=(0, 10))
        for label, attr, default in [("X2:", "x2_entry", "80"), ("Y2:", "y2_entry", "0"), ("R2:", "r2_entry", "200")]:
            ttk.Label(p2, text=label).pack(side=tk.LEFT, padx=(0, 3))
            e = ttk.Entry(p2, width=6)
            e.insert(0, default)
            e.pack(side=tk.LEFT, padx=(0, 8))
            setattr(self, attr, e)

        # метка с информацией о текущем методе и параметрах
        self.info = ttk.Label(top, text="Введите параметры и выберите метод")
        self.info.pack(side=tk.LEFT, padx=(10, 0))

        # кнопки выбора метода растеризации
        m = ttk.Frame(root, padding=(10, 0))
        m.pack(fill=tk.X, pady=(0, 5))
        for text, method in [
            ("Уравнение окружности", "equation"),
            ("Параметрическое уравнение", "parametric"),
            ("Алгоритм Брезенхема", "bresenham"),
            ("Встроенные средства", "builtin"),
        ]:
            ttk.Button(m, text=text, command=lambda x=method: self.draw_lens(x)).pack(side=tk.LEFT, padx=3)

        # кнопки сохранения и очистки
        s = ttk.Frame(root, padding=(10, 0))
        s.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(s, text="Сохранить BMP", command=self.save_bmp).pack(side=tk.LEFT, padx=3)
        ttk.Button(s, text="Сохранить PBM", command=self.save_pbm).pack(side=tk.LEFT, padx=3)
        ttk.Button(s, text="Очистить", command=self.clear).pack(side=tk.LEFT, padx=3)

        # разделитель между панелью и холстом
        ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # контейнер для холста фиксированного размера
        canvas_frame = ttk.Frame(root)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # холст фиксированного размера 800x600 с рамкой
        self.canvas = tk.Canvas(
            canvas_frame,
            width=800,
            height=600,
            bg="white",
            highlightthickness=1,
            highlightbackground="#888"
        )
        self.canvas.pack(pady=20)
        self.canvas.bind("<Configure>", lambda e: self.display_image() if self.image else None)

    # чтение и проверка параметров из полей ввода
    def get_parameters(self):
        try:
            x1 = float(self.x1_entry.get())
            y1 = float(self.y1_entry.get())
            r1 = float(self.r1_entry.get())
            x2 = float(self.x2_entry.get())
            y2 = float(self.y2_entry.get())
            r2 = float(self.r2_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числа.")
            return None

        if r1 <= 0 or r2 <= 0:
            messagebox.showerror("Ошибка", "Радиусы должны быть положительными.")
            return None

        d = math.hypot(x2 - x1, y2 - y1)

        if d == 0:
            messagebox.showerror("Ошибка", "Центры окружностей не должны совпадать.")
            return None

        if d > r1 + r2:
            messagebox.showerror("Ошибка", "Окружности не пересекаются.")
            return None
        if d < abs(r1 - r2):
            messagebox.showerror("Ошибка", "Одна окружность внутри другой — линза не образуется.")
            return None

        return x1, y1, r1, x2, y2, r2

    # вычисление точек пересечения двух окружностей
    def lens_geometry(self):
        params = self.get_parameters()
        if params is None:
            return None

        x1, y1, r1, x2, y2, r2 = params

        d = math.hypot(x2 - x1, y2 - y1)

        a = (r1 ** 2 - r2 ** 2 + d ** 2) / (2 * d)
        h_sq = r1 ** 2 - a ** 2
        if h_sq < 0:
            h_sq = 0
        h = math.sqrt(h_sq)

        ux = (x2 - x1) / d
        uy = (y2 - y1) / d

        mx = x1 + a * ux
        my = y1 + a * uy

        px = -uy
        py = ux

        p1 = (mx + h * px, my + h * py)
        p2 = (mx - h * px, my - h * py)

        return {"r1": r1, "r2": r2,
                "c1": (x1, y1), "c2": (x2, y2),
                "p1": p1, "p2": p2, "d": d}

    # создание изображения с нужными мировыми границами
    def prepare_image(self, geom):
        margin = 50
        x1, y1 = geom["c1"]
        x2, y2 = geom["c2"]
        r1, r2 = geom["r1"], geom["r2"]

        self.world_min_x = min(x1 - r1, x2 - r2) - margin
        self.world_max_x = max(x1 + r1, x2 + r2) + margin
        self.world_min_y = min(y1 - r1, y2 - r2) - margin
        self.world_max_y = max(y1 + r1, y2 + r2) + margin

        w = int(self.world_max_x - self.world_min_x)
        h = int(self.world_max_y - self.world_min_y)
        self.image = Image.new("RGB", (w, h), "white")

    # перевод мировых координат в пиксельные (с переворотом Y)
    def world_to_image(self, x, y):
        return int(round(x - self.world_min_x)), int(round(self.world_max_y - y))

    # угол точки относительно центра в диапазоне [0, 2pi)
    def angle(self, x, y, cx, cy):
        a = math.atan2(y - cy, x - cx)
        return a + 2 * math.pi if a < 0 else a

    # оставляем только точки чей угол попадает в диапазон дуги
    def filter_arc(self, points, cx, cy, start, end):
        out = []
        for x, y in points:
            a = self.angle(x, y, cx, cy)
            while a < start:
                a += 2 * math.pi
            if start <= a <= end:
                out.append((x, y))
        return out

    # сортировка точек дуги по углу
    def sort_arc_points(self, points, cx, cy, start):
        return [p for _, p in sorted(
            ((self.angle(p[0], p[1], cx, cy), p) for p in points),
            key=lambda t: t[0]
        )]

    # алгоритм Брезенхема для полной окружности
    def circle_bresenham(self, cx, cy, r):
        points, x, y, delta = [], 0, int(round(r)), 2 - 2 * int(round(r))
        while x <= y:
            points += [(cx + x, cy + y), (cx + y, cy + x), (cx - x, cy + y), (cx - y, cy + x),
                       (cx - x, cy - y), (cx - y, cy - x), (cx + x, cy - y), (cx + y, cy - x)]
            if delta < 0:
                d1 = 2 * (delta + y) - 1
                if d1 <= 0:
                    x += 1; delta += 2 * x + 1
                else:
                    x += 1; y -= 1; delta += 2 * (x - y)
            elif delta > 0:
                d2 = 2 * (delta - x) - 1
                if d2 > 0:
                    y -= 1; delta -= 2 * y + 1
                else:
                    x += 1; y -= 1; delta += 2 * (x - y)
            else:
                x += 1; y -= 1; delta += 2 * (x - y)
        return points

    # углы дуги n-й окружности, обращённой внутрь линзы
    def get_arc_angles(self, geom, n):
        cx, cy = geom["c1"] if n == 1 else geom["c2"]
        r = geom["r1"] if n == 1 else geom["r2"]
        p1, p2 = (geom["p1"], geom["p2"]) if n == 1 else (geom["p2"], geom["p1"])
        a1, a2 = self.angle(*p1, cx, cy), self.angle(*p2, cx, cy)
        if a2 < a1:
            a2 += 2 * math.pi

        if a2 - a1 > math.pi:
            a1, a2 = a2, a1 + 2 * math.pi

        return a1, a2

    # получение точек дуги выбранным методом
    def get_arc(self, method, cx, cy, r, start, end):
        if method in ("equation", "parametric"):
            step = 1.0 / max(r, 1)
            n = int((end - start) / step) + 1
            return [(cx + r * math.cos(start + i * step),
                     cy + r * math.sin(start + i * step)) for i in range(n)]
        # алгоритм Брезенхема
        if method == "bresenham":
            pts = self.circle_bresenham(int(round(cx)), int(round(cy)), int(round(r)))
            pts = self.filter_arc(pts, cx, cy, start, end)
            return self.sort_arc_points(pts, cx, cy, start)
        return []

    # основная функция отрисовки линзы выбранным методом
    def draw_lens(self, method):
        geom = self.lens_geometry()
        if geom is None:
            return
        self.prepare_image(geom)
        draw = ImageDraw.Draw(self.image)

        r1, r2 = geom["r1"], geom["r2"]
        c1, c2 = geom["c1"], geom["c2"]
        s1, e1 = self.get_arc_angles(geom, 1)
        s2, e2 = self.get_arc_angles(geom, 2)

        # встроенные средства PIL
        if method == "builtin":
            for (cx, cy), r, s, e in [(c1, r1, s1, e1), (c2, r2, s2, e2)]:
                bbox = (int(cx - r - self.world_min_x), int(self.world_max_y - cy - r),
                        int(cx + r - self.world_min_x), int(self.world_max_y - cy + r))
                draw.arc(bbox, start=-math.degrees(e), end=-math.degrees(s), fill="black", width=2)
        else:
            # рисуем обе дуги выбранным методом
            self.draw_arc(draw, self.get_arc(method, *c1, r1, s1, e1))
            self.draw_arc(draw, self.get_arc(method, *c2, r2, s2, e2))

        # замыкающая хорда между точками пересечения
        draw.line([self.world_to_image(*geom["p1"]), self.world_to_image(*geom["p2"])],
                  fill="black", width=2)

        self.display_image()
        name = {"equation": "Уравнение", "parametric": "Параметрическое",
                "bresenham": "Брезенхем", "builtin": "Встроенные"}.get(method, method)
        self.info.config(text=f"Метод: {name} | R1={r1:.0f} R2={r2:.0f} D={geom['d']:.0f}")

    # рисование дуги как цельной линии
    def draw_arc(self, draw, points):
        if len(points) >= 2:
            draw.line([self.world_to_image(x, y) for x, y in points],
                      fill="black", width=2, joint="curve")

    # масштабирование и вывод изображения на холст
    def display_image(self):
        if self.image is None:
            return
        self.root.update_idletasks()
        cw, ch = max(self.canvas.winfo_width(), 1), max(self.canvas.winfo_height(), 1)
        iw, ih = self.image.size
        self.scale = min(cw / iw, ch / ih, 1.0)
        nw, nh = max(1, int(iw * self.scale)), max(1, int(ih * self.scale))
        self.photo = __import__("PIL.ImageTk").ImageTk.PhotoImage(
            self.image.resize((nw, nh), Image.Resampling.NEAREST))
        self.canvas.delete("all")
        self.canvas.create_image((cw - nw) // 2, (ch - nh) // 2, anchor="nw", image=self.photo)

    # очистка холста
    def clear(self):
        self.image = None
        self.canvas.delete("all")
        self.info.config(text="Введите параметры и выберите метод")

    # сохранение текущего изображения в BMP
    def save_bmp(self):
        if self.image is None:
            messagebox.showwarning("Нет изображения", "Сначала постройте линзу.")
            return
        fn = filedialog.asksaveasfilename(defaultextension=".bmp", filetypes=[("BMP", "*.bmp")])
        if fn:
            self.image.save(fn, "BMP")
            messagebox.showinfo("Сохранение", "BMP сохранён.")

    # сохранение текущего изображения в PBM 
    def save_pbm(self):
        if self.image is None:
            messagebox.showwarning("Нет изображения", "Сначала постройте линзу.")
            return
        fn = filedialog.asksaveasfilename(defaultextension=".pbm", filetypes=[("PBM", "*.pbm")])
        if not fn:
            return
        gray = self.image.convert("L")
        w, h = gray.size
        px = gray.load()
        with open(fn, "wb") as f:
            f.write(b"P4\n" + f"{w} {h}\n".encode())
            for y in range(h):
                byte, bits = 0, 0
                for x in range(w):
                    byte = (byte << 1) | (1 if px[x, y] < 128 else 0)
                    bits += 1
                    if bits == 8:
                        f.write(bytes([byte])); byte = bits = 0
                if bits:
                    f.write(bytes([byte << (8 - bits)]))
        messagebox.showinfo("Сохранение", "PBM сохранён.")


if __name__ == "__main__":
    root = tk.Tk()
    LensRasterizer(root)
    root.mainloop()