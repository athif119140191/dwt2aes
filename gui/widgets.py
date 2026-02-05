import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
import os

class ScrolledText(tk.Frame):
    """Text widget dengan scrollbar"""
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.text = tk.Text(self, *args, **kwargs)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)
        
        self.text.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def get(self, index1, index2=None):
        if index2:
            return self.text.get(index1, index2)
        return self.text.get(index1)
    
    def insert(self, index, text):
        self.text.insert(index, text)
    
    def delete(self, index1, index2=None):
        if index2:
            self.text.delete(index1, index2)
        else:
            self.text.delete(index1)
    
    def bind(self, sequence, func):
        self.text.bind(sequence, func)

class Canvas(tk.Frame):
    """Canvas widget dasar tanpa scrollbar dan zoom"""
    def __init__(self, parent, width, height, *args, **kwargs):
        # 1. Inisialisasi Frame Induk
        tk.Frame.__init__(self, parent)
        
        # 2. Membuat Canvas
        self.canvas = tk.Canvas(self, width=width, height=height, *args, **kwargs)
        
        # 3. Tata Letak (Layout)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # 4. Konfigurasi Grid agar Canvas Meregang
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
                
    def create_image(self, x, y, image, **kwargs):
        """Create image di canvas"""
        return self.canvas.create_image(x, y, image=image, **kwargs)
    
    def delete(self, item):
        """Delete item dari canvas"""
        self.canvas.delete(item)
    
    # Properti image tetap dipertahankan untuk kompatibilitas
    @property
    def image(self):
        return self.canvas.image
    
    @image.setter
    def image(self, value):
        self.canvas.image = value

class HistogramCanvas(tk.Canvas):
    """Canvas khusus untuk menampilkan histogram"""
    def __init__(self, parent, width=300, height=200, *args, **kwargs):
        super().__init__(parent, width=width, height=height, *args, **kwargs)
        self.width = width
        self.height = height
        self.configure(bg='white')
    
    def draw_histogram(self, image, title="Histogram"):
        """Menggambar histogram dari gambar"""
        self.delete("all")
        
        # Konversi ke grayscale jika berwarna
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = image
        
        # Hitung histogram
        hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
        
        # Normalisasi histogram - pastikan nilai integer
        if hist.max() > 0:
            hist_normalized = (hist / hist.max() * (self.height - 50)).astype(int)
        else:
            hist_normalized = np.zeros(256, dtype=int)
        
        # Gambar sumbu
        self.create_line(30, 20, 30, self.height - 30, width=2)  # Sumbu Y
        self.create_line(30, self.height - 30, self.width - 10, self.height - 30, width=2)  # Sumbu X
        
        # Gambar batang histogram - pastikan koordinat integer
        bar_width = max(1, (self.width - 40) // 256)
        for i in range(256):
            x0 = 30 + i * bar_width
            y0 = self.height - 30
            x1 = x0 + bar_width
            y1 = y0 - int(hist_normalized[i])  # Pastikan integer
            
            if hist_normalized[i] > 0:
                self.create_rectangle(int(x0), int(y0), int(x1), int(y1), fill='blue', outline='')
        
        # Tambahkan judul dan label
        self.create_text(self.width//2, 10, text=title, font=("Arial", 10, "bold"))
        self.create_text(15, self.height//2, text="Frekuensi", angle=90, font=("Arial", 8))
        self.create_text(self.width//2, self.height - 10, text="Intensitas Pixel", font=("Arial", 8))
        
        # Tambahkan beberapa nilai pada sumbu X
        for i in range(0, 256, 64):
            x = 30 + i * bar_width
            self.create_text(x, self.height - 20, text=str(i), font=("Arial", 6))

class SpectrogramCanvas(tk.Canvas):
    """Canvas untuk menampilkan gambar spektogram"""
    def __init__(self, parent, width, height, *args, **kwargs):
        tk.Canvas.__init__(self, parent, width=width, height=height, *args, **kwargs)
        self.image_ref = None
        self.width = width
        self.height = height

    def display_spectrogram(self, image_path):
        self.delete("all")
        
        if not image_path or not os.path.exists(image_path):
            self.create_text(
                self.width // 2, 
                self.height // 2, 
                text="Spektogram Audio Tidak Tersedia", 
                fill="red",
                font=("Arial", 10, "bold")
            )
            self.image_ref = None
            return

        try:
            # Buka gambar spektogram PNG/JPEG yang dihasilkan Matplotlib/Librosa
            img = Image.open(image_path)
            
            # Ubah ukuran agar pas dengan canvas
            img_resized = img.resize((self.width, self.height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img_resized)
            
            # Tampilkan gambar di canvas
            self.create_image(0, 0, image=photo, anchor=tk.NW)
            
            # Simpan referensi agar tidak dihapus oleh garbage collector
            self.image_ref = photo 
            
        except Exception as e:
            self.create_text(
                self.width // 2, 
                self.height // 2, 
                text=f"Error Tampil Spektogram: {e}", 
                fill="red"
            )
            self.image_ref = None