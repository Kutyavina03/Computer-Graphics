import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np


SUPPORTED_EXTS = [
    '.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff',
    '.gif', '.webp', '.ppm', '.pgm', '.pbm', '.ico',
]

FILETYPES = [
    ('Все поддерживаемые', ' '.join(f'*{e}' for e in SUPPORTED_EXTS)),
    ('PNG', '*.png'),
    ('JPEG', '*.jpg *.jpeg'),
    ('BMP', '*.bmp'),
    ('TIFF', '*.tif *.tiff'),
    ('GIF', '*.gif'),
    ('WEBP', '*.webp'),
    ('PPM/PGM/PBM', '*.ppm *.pgm *.pbm'),
    ('Все файлы', '*.*'),
]


def read_image(path):
    img = Image.open(path)
    img = img.convert('RGBA')
    bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
    bg.alpha_composite(img)
    img = bg.convert('RGB')
    return np.array(img, dtype=np.uint8)


def save_image(path, arr):
    img = Image.fromarray(arr.astype(np.uint8), mode='RGB')
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        img.save(path, quality=95, subsampling=0)
    else:
        img.save(path)


def remove_blue_high_brightness(img):
    result = img.astype(np.float32).copy()
    r = result[:, :, 0]
    g = result[:, :, 1]
    b = result[:, :, 2]

    v = 0.2125 * r + 0.7154 * g + 0.0721 * b

    mask = v > 0.75 * 255.0

    result[:, :, 2] = np.where(mask, 0.0, b)

    return np.clip(result, 0, 255).astype(np.uint8)

def pin_light(base, top):
    c1 = base.astype(np.float32) / 255.0
    c2 = top.astype(np.float32) / 255.0

    res = np.where(c2 < 0.5, np.minimum(c1, c2), np.maximum(c1, c2))

    return np.clip(res * 255.0, 0, 255).astype(np.uint8)


def align_images(img1, img2):
    h = min(img1.shape[0], img2.shape[0])
    w = min(img1.shape[1], img2.shape[1])
    return img1[:h, :w], img2[:h, :w]


class App:
    def __init__(self, root):
        self.root = root

        self.img1 = None
        self.img2 = None
        self.processed = None
        self.blended = None

        self.name1 = None
        self.name2 = None

        self._build_ui()

    def _build_ui(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text='Загрузить изображение 1',
                  command=self.load_img1).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text='Загрузить изображение 2',
                  command=self.load_img2).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text='Обработать',
                  command=self.process).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text='Наложить',
                  command=self.blend).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text='Сохранить обработку',
                  command=self.save_processed).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text='Сохранить наложение',
                  command=self.save_blended).pack(side=tk.LEFT, padx=3)

        img_frame = tk.Frame(self.root)
        img_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.labels = {}
        titles = [
            ('img1', 'Изображение 1'),
            ('processed', 'Обработка'),
            ('img2', 'Изображение 2'),
            ('blended', 'Наложение'),
        ]
        for idx, (key, title) in enumerate(titles):
            f = tk.LabelFrame(img_frame, text=title, width=300, height=300)
            f.grid(row=idx // 2, column=idx % 2, padx=5, pady=5, sticky='nsew')
            f.grid_propagate(False)
            lbl = tk.Label(f)
            lbl.pack(fill=tk.BOTH, expand=True)
            self.labels[key] = lbl

        img_frame.rowconfigure(0, weight=1)
        img_frame.rowconfigure(1, weight=1)
        img_frame.columnconfigure(0, weight=1)
        img_frame.columnconfigure(1, weight=1)

        self.status = tk.Label(self.root, text='Готово', anchor='w',
                               relief=tk.SUNKEN)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _show(self, key, arr):
        h, w, _ = arr.shape
        max_size = 300
        scale = min(max_size / w, max_size / h, 1.0)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        pil = Image.fromarray(arr).resize((new_w, new_h), Image.NEAREST)
        tkimg = ImageTk.PhotoImage(pil)
        lbl = self.labels[key]
        lbl.configure(image=tkimg)
        lbl.image = tkimg  

    def _open_dialog(self, title):
        return filedialog.askopenfilename(
            title=title,
            filetypes=FILETYPES)

    def load_img1(self):
        path = self._open_dialog('Выберите первое изображение')
        if not path:
            return
        try:
            self.img1 = read_image(path)
            self.name1 = path
            self._show('img1', self.img1)
            self.status.config(
                text=f'Загружено 1: {os.path.basename(path)} '
                     f'({self.img1.shape[1]}x{self.img1.shape[0]})')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось открыть файл:\n{e}')

    def load_img2(self):
        path = self._open_dialog('Выберите второе изображение')
        if not path:
            return
        try:
            self.img2 = read_image(path)
            self.name2 = path
            self._show('img2', self.img2)
            self.status.config(
                text=f'Загружено 2: {os.path.basename(path)} '
                     f'({self.img2.shape[1]}x{self.img2.shape[0]})')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось открыть файл:\n{e}')

    def process(self):
        if self.img1 is None:
            messagebox.showwarning('Внимание',
                                   'Сначала загрузите изображение 1')
            return
        self.processed = remove_blue_high_brightness(self.img1)
        self._show('processed', self.processed)
        self.status.config(text='Обработка выполнена')

    def blend(self):
        if self.processed is None or self.img2 is None:
            messagebox.showwarning(
                'Внимание',
                'Нужны обработанное изображение 1 и изображение 2')
            return
        a, b = align_images(self.processed, self.img2)
        self.blended = pin_light(a, b)
        self._show('blended', self.blended)
        self.status.config(
            text=f'Наложение выполнено: {self.blended.shape[1]}x'
                 f'{self.blended.shape[0]}')

    def _save_dialog(self, default_name):
        return filedialog.asksaveasfilename(
            title='Сохранить изображение',
            initialfile=default_name,
            defaultextension='.png',
            filetypes=FILETYPES)

    def _default_name(self, original, suffix):
        if original is None:
            return f'result_{suffix}.png'
        base = os.path.splitext(os.path.basename(original))[0]
        return f'{base}_{suffix}.png'

    def save_processed(self):
        if self.processed is None:
            messagebox.showwarning('Внимание', 'Нет обработанного изображения')
            return
        path = self._save_dialog(self._default_name(self.name1, 'processed'))
        if not path:
            return
        try:
            save_image(path, self.processed)
            self.status.config(text=f'Сохранено: {path}')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось сохранить:\n{e}')

    def save_blended(self):
        if self.blended is None:
            messagebox.showwarning('Внимание', 'Нет наложенного изображения')
            return
        path = self._save_dialog(self._default_name(self.name1, 'blended'))
        if not path:
            return
        try:
            save_image(path, self.blended)
            self.status.config(text=f'Сохранено: {path}')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось сохранить:\n{e}')


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('720x780')
    app = App(root)
    root.mainloop()