import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class SimpleEditor:
    def __init__(self, root):
        self.root = root
        self.root.geometry("600x500")
        
        self.image = None
        self.photo = None
        self.img_path = None
        
        self.create_widgets()
    
    def create_widgets(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.btn_load = tk.Button(btn_frame, text="Загрузить", command=self.load_image, width=12)
        self.btn_load.pack(side=tk.LEFT, padx=5)
        
        self.btn_process = tk.Button(btn_frame, text="Обработать", command=self.process_image, width=12, state=tk.DISABLED)
        self.btn_process.pack(side=tk.LEFT, padx=5)
        
        self.btn_save_png = tk.Button(btn_frame, text="Сохранить PNG", command=lambda: self.save_image("png"), width=12, state=tk.DISABLED)
        self.btn_save_png.pack(side=tk.LEFT, padx=5)
        
        self.btn_save_pbm = tk.Button(btn_frame, text="Сохранить PBM", command=lambda: self.save_image("pbm"), width=12, state=tk.DISABLED)
        self.btn_save_pbm.pack(side=tk.LEFT, padx=5)
        
        self.canvas = tk.Canvas(self.root, bg="lightgray")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def load_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        
        self.img_path = path
        self.image = Image.open(path)
        if self.image.mode != 'RGB':
            self.image = self.image.convert('RGB')
        
        self.show_image()
        self.btn_process.config(state=tk.NORMAL)
    
    def show_image(self):
        w, h = self.image.size
        max_w, max_h = 550, 400
        scale = min(max_w/w, max_h/h, 1.0)
        new_w, new_h = int(w*scale), int(h*scale)
        
        img_resized = self.image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(img_resized)
        
        self.canvas.delete("all")
        self.canvas.config(width=new_w, height=new_h)
        self.canvas.create_image(new_w//2, new_h//2, anchor=tk.CENTER, image=self.photo)
    
    def process_image(self):
        w, h = self.image.size
        pix = self.image.load()
        
        pix[0, 0] = (64, 127, 127)          # верхний левый угол
        pix[w//2, h//2] = (127, 64, 127)    # центр изображения
        pix[w-1, h//2] = (127, 64, 64)      # центр правого столбца
        
        self.show_image()
        self.btn_save_png.config(state=tk.NORMAL)
        self.btn_save_pbm.config(state=tk.NORMAL)
        messagebox.showinfo("Готово", "Точки поставлены!")
    
    def save_image(self, fmt):
        if fmt == "png":
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if path:
                self.image.save(path)
                messagebox.showinfo("Успех", f"Сохранено PNG: {path}")
        else:  # pbm
            path = filedialog.asksaveasfilename(defaultextension=".pbm", filetypes=[("PBM files", "*.pbm")])
            if path:
                w, h = self.image.size
                
                # Создаем черное изображение
                pbm_img = Image.new('1', (w, h), 0)
                pix = pbm_img.load()
                
                # Ставим белые точки
                pix[0, 0] = 1
                pix[w//2, h//2] = 1
                pix[w-1, h//2] = 1
                
                pbm_img.save(path, format='PPM', bitmap_format='pbm')
                messagebox.showinfo("Успех", f"Сохранено PBM: {path}")

root = tk.Tk()
app = SimpleEditor(root)
root.mainloop()