import numpy as np
from PIL import Image, ImageTk
from scipy.ndimage import convolve as nd_convolve

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def gaussian_kernel(size: int, sigma: float) -> np.ndarray:
    ax = np.arange(-(size // 2), size // 2 + 1, dtype=np.float64)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx ** 2 + yy ** 2) / (2.0 * sigma ** 2))
    kernel /= kernel.sum()
    return kernel


def normalize_to_uint8(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float64)
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-9:
        return np.zeros_like(arr, dtype=np.uint8)
    return ((arr - mn) / (mx - mn) * 255.0).astype(np.uint8)


def low_pass_filter(img: np.ndarray,
                              sigma: float = 2.0,
                              ksize: int = 9) -> np.ndarray:
    h, w, _ = img.shape
    kernel = gaussian_kernel(ksize, sigma)
    result = img.astype(np.float64).copy()

    for ch in (0, 1):
        result[:, :w // 2, ch] = nd_convolve(
            img[:, :w // 2, ch].astype(np.float64),
            kernel, mode='nearest'
        )

    for ch in (1, 2):
        result[:, w // 2:, ch] = nd_convolve(
            img[:, w // 2:, ch].astype(np.float64),
            kernel, mode='nearest'
        )

    return np.clip(result, 0, 255).astype(np.uint8)


def roberts_filter(img: np.ndarray) -> np.ndarray:
    gray = img.astype(np.float64).mean(axis=2)

    Kx = np.array([[1, 0],
                   [0, -1]], dtype=np.float64)
    Ky = np.array([[0, 1],
                   [-1, 0]], dtype=np.float64)

    gx = nd_convolve(gray, Kx, mode='nearest')
    gy = nd_convolve(gray, Ky, mode='nearest')

    return normalize_to_uint8(np.sqrt(gx * gx + gy * gy))


def prewitt_filter(img: np.ndarray) -> np.ndarray:
    gray = img.astype(np.float64).mean(axis=2)

    Kx = np.array([[-1, 0, 1],
                   [-1, 0, 1],
                   [-1, 0, 1]], dtype=np.float64)  # вертикальный
    Ky = np.array([[-1, -1, -1],
                   [0, 0, 0],
                   [1, 1, 1]], dtype=np.float64)   # горизонтальный

    gx = nd_convolve(gray, Kx, mode='nearest')
    gy = nd_convolve(gray, Ky, mode='nearest')

    return normalize_to_uint8(np.sqrt(gx * gx + gy * gy))


def hpf(img: np.ndarray) -> np.ndarray:
    r = roberts_filter(img).astype(np.int32)
    p = prewitt_filter(img).astype(np.int32)
    diff = np.abs(r - p)
    return np.clip(diff, 0, 255).astype(np.uint8)


class FilterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)

        self.original_img = None
        self.lpf_img = None
        self.hpf_img = None

        top = ttk.Frame(root, padding=5)
        top.pack(side=tk.TOP, fill=tk.X)

        g_file = ttk.Frame(top)
        g_file.pack(side=tk.LEFT, padx=(0, 30))
        ttk.Button(g_file, text="Открыть", width=14,
                   command=self.open_image).pack(side=tk.LEFT)

        g_lpf = ttk.Frame(top)
        g_lpf.pack(side=tk.LEFT, padx=(0, 30))
        ttk.Button(g_lpf, text="Обработать ФНЧ", width=16,
                   command=self.process_lpf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(g_lpf, text="Сохранить", width=12,
                   command=self.save_lpf).pack(side=tk.LEFT)

        g_hpf = ttk.Frame(top)
        g_hpf.pack(side=tk.LEFT)
        ttk.Button(g_hpf, text="Обработать ФВЧ", width=16,
                   command=self.process_hpf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(g_hpf, text="Сохранить", width=12,
                   command=self.save_hpf).pack(side=tk.LEFT)

        mid = ttk.Frame(root, padding=5)
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.lbl_orig = self._make_image_panel(mid, 0)
        self.lbl_lpf = self._make_image_panel(mid, 1)
        self.lbl_hpf = self._make_image_panel(mid, 2)

        for i in range(3):
            mid.columnconfigure(i, weight=1, minsize=200)
        mid.rowconfigure(0, weight=1)

        self.root.update_idletasks()

    def _make_image_panel(self, parent, col: int) -> tk.Label:
        frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        frame.grid(row=0, column=col, sticky="nsew", padx=2, pady=2)

        lbl = ttk.Label(frame, anchor=tk.CENTER)
        lbl.pack(fill=tk.BOTH, expand=True)
        return lbl

    # ---------- Открытие изображения ----------
    def open_image(self):
        path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
                       ("Все файлы", "*.*")]
        )
        if not path:
            return

        try:
            pil_img = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
            return

        self.original_img = np.array(pil_img)
        self.lpf_img = None
        self.hpf_img = None

        self._show_image(self.lbl_orig, pil_img)
        self._show_image(self.lbl_lpf, None)
        self._show_image(self.lbl_hpf, None)

    def _show_image(self, label: tk.Label, pil_img):
        if pil_img is None:
            label.config(image="", text="")
            label.image = None
            return

        self.root.update_idletasks()

        w = label.winfo_width()
        h = label.winfo_height()
        if w <= 1:
            w = 380
        if h <= 1:
            h = 550

        iw, ih = pil_img.size
        scale = min(w / iw, h / ih)
        new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
        resized = pil_img.resize(new_size, Image.LANCZOS)

        tk_img = ImageTk.PhotoImage(resized)
        label.config(image=tk_img, text="")
        label.image = tk_img 

    def process_lpf(self):
        if self.original_img is None:
            messagebox.showwarning("Внимание", "Сначала откройте изображение.")
            return

        self.lpf_img = low_pass_filter(self.original_img,
                                                 sigma=2.0, ksize=9)
        self._show_image(self.lbl_lpf, Image.fromarray(self.lpf_img))

    def process_hpf(self):
        if self.original_img is None:
            messagebox.showwarning("Внимание", "Сначала откройте изображение.")
            return

        self.hpf_img = hpf(self.original_img)
        self._show_image(self.lbl_hpf, Image.fromarray(self.hpf_img))

    def save_lpf(self):
        if self.lpf_img is None:
            messagebox.showwarning("Внимание", "Сначала обработайте ФНЧ.")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить результат ФНЧ",
            defaultextension=".png",
            initialfile="lpf.png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp"), ("PPM", "*.ppm")]
        )
        if not path:
            return
        try:
            Image.fromarray(self.lpf_img).save(path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def save_hpf(self):
        if self.hpf_img is None:
            messagebox.showwarning("Внимание", "Сначала обработайте ФВЧ.")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить результат ФВЧ",
            defaultextension=".png",
            initialfile="hpf.png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp"), ("PPM", "*.ppm")]
        )
        if not path:
            return
        try:
            Image.fromarray(self.hpf_img).save(path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")


def main():
    root = tk.Tk()
    FilterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()