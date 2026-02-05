import tkinter as tk
from tkinter import ttk
from gui.widgets import ScrolledText, Canvas, HistogramCanvas

def setup_tab_dekripsi(gui_instance, parent):
    """Setup UI untuk tab Dekripsi & Ekstraksi dengan layout Stack Vertikal (Responsive untuk layar kecil)."""
    
    # Konfigurasi grid parent agar 1 kolom meregang
    parent.grid_columnconfigure(0, weight=1)

    # --- Frame 1: Video Stego dan Ekstraksi ---
    frame_video_stego = ttk.LabelFrame(parent, text="Video Stego dan Ekstraksi", padding="10")
    frame_video_stego.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), padx=10, pady=10)
    frame_video_stego.grid_columnconfigure(0, weight=1) # Kolom display meregang
    frame_video_stego.grid_rowconfigure(1, weight=1) # Baris display meregang

    # Kontrol Video dan Ekstraksi
    frame_control = ttk.Frame(frame_video_stego)
    frame_control.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
    
    ttk.Button(frame_control, text="Pilih Video Stego", 
              command=gui_instance.pilih_video_stego_button).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_control, text="Ekstrak Pesan", 
              command=gui_instance.ekstrak_pesan_button).pack(side=tk.LEFT, padx=5)

    # Display Frame Stego + Histogram
    frame_stego_display = ttk.LabelFrame(frame_video_stego, text="Frame yang Diekstrak", padding=5)
    frame_stego_display.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    frame_stego_display.grid_columnconfigure(0, weight=1)
    frame_stego_display.grid_rowconfigure(0, weight=1)

    gui_instance.canvas_stego_dekripsi = Canvas(frame_stego_display, width=300, height=300, bg="lightgrey")
    gui_instance.canvas_stego_dekripsi.grid(row=0, column=0, sticky="nsew")
    gui_instance.histogram_stego_dekripsi = HistogramCanvas(frame_stego_display, width=300, height=150)
    gui_instance.histogram_stego_dekripsi.grid(row=1, column=0, sticky="ew")
    
    # --- Frame 2: Hasil Ekstraksi (Ciphertext) ---
    frame_ekstrak_hasil = ttk.LabelFrame(parent, text="Hasil Ekstraksi (Ciphertext)", padding="10")
    frame_ekstrak_hasil.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
    frame_ekstrak_hasil.grid_columnconfigure(0, weight=1)
    frame_ekstrak_hasil.grid_rowconfigure(1, weight=1)
    
    ttk.Label(frame_ekstrak_hasil, text="Pesan Terenkripsi (Hex):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
    gui_instance.pesan_terenkripsi_dekripsi_form = ScrolledText(frame_ekstrak_hasil, height=8)
    gui_instance.pesan_terenkripsi_dekripsi_form.grid(row=1, column=0, padx=5, pady=2, sticky="nsew")
    
    # --- Frame 3: Dekripsi AES-128 CTR dan Output Pesan ---
    frame_dekripsi = ttk.LabelFrame(parent, text="Dekripsi AES-128 CTR dan Hasil", padding="10")
    frame_dekripsi.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
    frame_dekripsi.grid_columnconfigure(1, weight=1) # Kolom input meregang
    frame_dekripsi.grid_rowconfigure(2, weight=1) # Baris output pesan meregang

    # Input Kunci
    ttk.Label(frame_dekripsi, text="Kunci AES (16 byte):").grid(row=0, column=0, sticky=tk.W, padx=5)
    key_frame_dek = ttk.Frame(frame_dekripsi)
    key_frame_dek.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
    key_frame_dek.columnconfigure(0, weight=1)

    # 1. Entry Kunci AES Dekripsi
    gui_instance.kunci_aes_dekripsi_form = ttk.Entry(key_frame_dek, show="*")
    gui_instance.kunci_aes_dekripsi_form.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
    gui_instance.kunci_aes_dekripsi_form.insert(0, "kunciAES128bit!!")

    # 2. Tombol Show/Hide 👁️
    show_hide_btn_dekripsi = ttk.Button(key_frame_dek, text="Show")
    # Tombol Show/Hide berada di kolom 1
    show_hide_btn_dekripsi.grid(row=0, column=1, padx=(5, 0)) 
    show_hide_btn_dekripsi.config(
        command=lambda: gui_instance.toggle_password_visibility(
            gui_instance.kunci_aes_dekripsi_form, 
            show_hide_btn_dekripsi
        )
    )

    # 3. Tombol Dekripsi Pesan harus dipindahkan ke kolom 2
    ttk.Button(key_frame_dek, text="Dekripsi Pesan", 
        command=gui_instance.dekripsi_pesan_button).grid(row=0, column=2, padx=(5, 0))
    ttk.Label(frame_dekripsi, text="Kode ASCII Dekripsi:").grid(row=1, column=0, sticky=tk.W, padx=5)
    gui_instance.kode_ascii_dekripsi_form = ScrolledText(frame_dekripsi, height=3)
    gui_instance.kode_ascii_dekripsi_form.grid(row=1, column=1, padx=5, pady=2, sticky="nsew")
    

    ttk.Label(frame_dekripsi, text="Jumlah Karakter:").grid(row=2, column=0, sticky=tk.W, padx=5)
    gui_instance.jumlah_char_dekripsi_form = ttk.Entry(frame_dekripsi, width=20)
    gui_instance.jumlah_char_dekripsi_form.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
    
    ttk.Label(frame_dekripsi, text="Teks Pesan Dekripsi:").grid(row=3, column=0, sticky=tk.W, padx=5)
    gui_instance.teks_pesan_dekripsi_form = ScrolledText(frame_dekripsi, height=6)
    gui_instance.teks_pesan_dekripsi_form.grid(row=3, column=1, padx=5, pady=2, sticky="nsew")