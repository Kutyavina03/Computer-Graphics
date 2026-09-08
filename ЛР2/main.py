import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import math


class DrawFigure:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1100x650")

        self.source_image = None
        self.result_image = None
        self.photo_source = None
        self.photo_result = None

        self.create_widgets()

    def create_widgets(self):
        top = tk.Frame(self.root, bg="#e5e5e5", height=80)
        top.pack(fill=tk.X, padx=10, pady=5)
        top.pack_propagate(False)

        tk.Label(top, text="Ширина:").place(x=10, y=10)
        self.edit_w = tk.Entry(top, width=7)
        self.edit_w.insert(0, "600")
        self.edit_w.place(x=70, y=8)

        tk.Label(top, text="Высота:").place(x=140, y=10)
        self.edit_h = tk.Entry(top, width=7)
        self.edit_h.insert(0, "600")
        self.edit_h.place(x=200, y=8)

        tk.Button(top, text="Создать", width=11, command=self.create_new).place(x=270, y=6)
        tk.Button(top, text="Открыть", width=11, command=self.load_image).place(x=365, y=6)
        tk.Button(top, text="Перевести", width=11, command=self.insert_fragment).place(x=460, y=6)
        tk.Button(top, text="Координаты", width=11, command=self.draw_axes).place(x=555, y=6)
        tk.Button(top, text="x*cos(x)", width=11, command=self.draw_graph).place(x=650, y=6)
        tk.Button(top, text="Сохранить", width=11, command=self.save_image).place(x=745, y=6)

        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left = tk.LabelFrame(bottom, text="Новое изображение")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.canvas_result = tk.Canvas(left, bg="#d0d0d0")
        self.canvas_result.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        right = tk.LabelFrame(bottom, text="Исходное изображение")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.canvas_source = tk.Canvas(right, bg="#d0d0d0")
        self.canvas_source.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_new(self):
        try:
            w, h = int(self.edit_w.get()), int(self.edit_h.get())
            if w <= 0 or h <= 0:
                raise ValueError
            self.result_image = Image.new("RGB", (w, h), "white")
            self.show_result()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные размеры.")

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            self.source_image = Image.open(path).convert("RGB")
            self.show_source()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def insert_fragment(self):
        if self.result_image is None or self.source_image is None:
            messagebox.showerror("Ошибка", "Сначала создайте и откройте изображения.")
            return

        W, H = self.result_image.size
        SW, SH = self.source_image.size

        x1, y1 = W // 2, H // 2
        x2, y2 = (3 * W) // 4, (3 * H) // 4
        tw, th = x2 - x1, y2 - y1

        sx, sy = SW // 2, SH // 2
        start_x, start_y = sx - tw // 2, sy - th // 2

        for y in range(th):
            for x in range(tw):
                if x <= y:  # Треугольник
                    px, py = start_x + x, start_y + y
                    if 0 <= px < SW and 0 <= py < SH:
                        self.result_image.putpixel(
                            (x1 + x, y1 + y),
                            self.source_image.getpixel((px, py))
                        )

        self.show_result()

    def draw_axes(self):
        if self.result_image is None:
            messagebox.showerror("Ошибка", "Сначала создайте изображение.")
            return

        draw = ImageDraw.Draw(self.result_image)
        w, h = self.result_image.size

        draw.line((10, h - 10, 10, 10), fill="black", width=2)
        draw.line((5, 20, 10, 10, 15, 20), fill="black", width=2)
        draw.line((10, h // 2, w - 10, h // 2), fill="black", width=2)
        draw.line((w - 20, h // 2 - 5, w - 10, h // 2, w - 20, h // 2 + 5), fill="black", width=2)

        for i in range(0, w, 10):
            draw.line((i, h // 2 - 2, i, h // 2 + 2), fill="black")
        for i in range(0, h, 10):
            draw.line((8, i, 12, i), fill="black")

        draw.text((2, h // 2 + 3), "0", fill="black")
        draw.text((w - 20, h // 2 + 5), "x", fill="black")
        draw.text((18, 2), "y", fill="black")

        self.show_result()

    def draw_graph(self):
        if self.result_image is None:
            messagebox.showerror("Ошибка", "Сначала создайте изображение.")
            return

        draw = ImageDraw.Draw(self.result_image)
        w, h = self.result_image.size

        draw.text((w // 2, 10), "y = x*cos(x)", fill=(80, 80, 220))

        points = []
        scale_x, scale_y = 50, 20

        for px in range(10, w - 10):
            x = (px - w // 2) / scale_x
            y = x * math.cos(x)
            py = h // 2 - int(y * scale_y)
            if 0 <= py < h:
                points.append((px, py))

        if len(points) > 1:
            draw.line(points, fill=(80, 80, 220), width=2)

        self.show_result()

    def show_result(self):
        if self.result_image is None:
            return
        img = self.result_image.copy()
        scale = min(480 / img.width, 480 / img.height, 1)
        size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(size, Image.Resampling.LANCZOS)
        self.photo_result = ImageTk.PhotoImage(img)
        self.canvas_result.delete("all")
        self.canvas_result.create_image(size[0] // 2, size[1] // 2, image=self.photo_result)

    def show_source(self):
        if self.source_image is None:
            return
        img = self.source_image.copy()
        scale = min(480 / img.width, 480 / img.height, 1)
        size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(size, Image.Resampling.LANCZOS)
        self.photo_source = ImageTk.PhotoImage(img)
        self.canvas_source.delete("all")
        self.canvas_source.create_image(size[0] // 2, size[1] // 2, image=self.photo_source)

    def save_image(self):
        if self.result_image is None:
            messagebox.showerror("Ошибка", "Нет изображения для сохранения.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if path:
            self.result_image.save(path)
            messagebox.showinfo("Готово", "Изображение сохранено.")


root = tk.Tk()
app = DrawFigure(root)
root.mainloop()