import tkinter as tk
from tkinter import ttk
from gui.widgets import ScrolledText, Canvas, HistogramCanvas, SpectrogramCanvas

def setup_tab_enkripsi(gui_instance, parent):
    """Setup UI untuk tab Enkripsi & Penyisipan dengan layout Stack Vertikal (Responsive untuk layar kecil)."""
    
    # Konfigurasi grid parent agar 1 kolom meregang
    parent.grid_columnconfigure(0, weight=1)

    # --- Frame 1: Input Data dan Enkripsi ---
    frame_kontrol = ttk.LabelFrame(parent, text="Input Data dan Enkripsi", padding="10")
    frame_kontrol.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), padx=10, pady=10)
    frame_kontrol.grid_columnconfigure(1, weight=1) # Kolom input teks meregang

    # 1. Input Teks
    row_idx = 0
    ttk.Button(frame_kontrol, text="Pilih File Teks", 
              command=gui_instance.pilih_txt_button).grid(row=row_idx, column=0, sticky=tk.W, padx=5, pady=5)
    
    gui_instance.lokasi_txt_form = ttk.Entry(frame_kontrol)
    gui_instance.lokasi_txt_form.grid(row=row_idx, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
    row_idx += 1
    
    ttk.Label(frame_kontrol, text="Teks Pesan:").grid(row=row_idx, column=0, sticky=tk.W, padx=5)
    gui_instance.teks_pesan_form = ScrolledText(frame_kontrol, height=4)
    gui_instance.teks_pesan_form.grid(row=row_idx, column=1, padx=5, pady=2, sticky="nsew")
    row_idx += 1
    gui_instance.teks_pesan_form.bind("<KeyRelease>", gui_instance.update_jumlah_char)
    gui_instance.teks_pesan_form.bind("<<Paste>>", gui_instance.update_jumlah_char)
    gui_instance.teks_pesan_form.bind("<ButtonRelease-1>", gui_instance.update_jumlah_char)
    
    ttk.Label(frame_kontrol, text="Jumlah Karakter:").grid(row=row_idx, column=0, sticky=tk.W, padx=5)
    gui_instance.jumlah_char_form = ttk.Entry(frame_kontrol)
    gui_instance.jumlah_char_form.grid(row=row_idx, column=1, sticky=tk.W, padx=5, pady=2)
    row_idx += 1
    
    ttk.Button(frame_kontrol, text="Konversi ke ASCII", 
              command=gui_instance.konversi_ascii_button).grid(row=row_idx, column=0, sticky=tk.W, padx=5, pady=5)
    
    gui_instance.kode_ascii_form = ScrolledText(frame_kontrol, height=3)
    gui_instance.kode_ascii_form.grid(row=row_idx, column=1, padx=5, pady=2, sticky="nsew")
    row_idx += 1

    # Separator
    ttk.Separator(frame_kontrol, orient='horizontal').grid(row=row_idx, column=0, columnspan=2, sticky=(tk.E, tk.W), pady=10)
    row_idx += 1
    
    # 2. Enkripsi AES
    ttk.Label(frame_kontrol, text="Kunci AES (16 byte):").grid(row=row_idx, column=0, sticky=tk.W, padx=5)
    
    key_frame = ttk.Frame(frame_kontrol)
    key_frame.grid(row=row_idx, column=1, sticky=(tk.W, tk.E), padx=5)
    key_frame.columnconfigure(0, weight=1)
    
    gui_instance.kunci_aes_form = ttk.Entry(key_frame, show="*")
    gui_instance.kunci_aes_form.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
    gui_instance.kunci_aes_form.insert(0, "kunciAES128bit!!")
    
    # Tombol Show/Hide
    show_hide_btn_enkripsi = ttk.Button(key_frame, text="Show")
    show_hide_btn_enkripsi.grid(row=0, column=1, padx=(5, 0))
    # Binding command ke handler baru
    show_hide_btn_enkripsi.config(
        command=lambda: gui_instance.toggle_password_visibility(
            gui_instance.kunci_aes_form, 
            show_hide_btn_enkripsi
        )
    )

    ttk.Button(key_frame, text="Rand Key", 
            command=gui_instance.generate_random_key).grid(row=0, column=2, padx=(5, 0))
    ttk.Button(key_frame, text="Enkripsi", 
            command=gui_instance.enkripsi_pesan_button).grid(row=0, column=3, padx=(5, 0))
    row_idx += 1
    
    ttk.Label(frame_kontrol, text="Pesan Enkripsi (Hex):").grid(row=row_idx, column=0, sticky=tk.W, padx=5)
    gui_instance.pesan_terenkripsi_form = ScrolledText(frame_kontrol, height=3)
    gui_instance.pesan_terenkripsi_form.grid(row=row_idx, column=1, padx=5, pady=2, sticky="nsew")

    # --- Frame 2: Video Cover dan Pengaturan Stego ---
    frame_video = ttk.LabelFrame(parent, text="Video Cover dan Pengaturan Stego", padding="10")
    frame_video.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), padx=10, pady=10)
    frame_video.grid_columnconfigure(0, weight=1)
    frame_video.grid_columnconfigure(1, weight=1)

    ttk.Button(frame_video, text="Pilih Video Cover", 
              command=gui_instance.pilih_video_cover_button).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

    # Pengaturan Penyisipan (berada di baris yang sama dengan tombol Pilih Video)
    frame_sisip_settings = ttk.Frame(frame_video)
    frame_sisip_settings.grid(row=0, column=1, sticky=(tk.E), padx=5, pady=5)
    
    ttk.Label(frame_sisip_settings, text="Layer:").pack(side=tk.LEFT, padx=5)
    gui_instance.layer_dropdown = ttk.Combobox(frame_sisip_settings, values=["red", "green", "blue"], state="readonly", width=8)
    gui_instance.layer_dropdown.pack(side=tk.LEFT, padx=5)
    gui_instance.layer_dropdown.set("red")
    
    ttk.Label(frame_sisip_settings, text="Subband:").pack(side=tk.LEFT, padx=5)
    gui_instance.signal_dropdown = ttk.Combobox(frame_sisip_settings, values=["LL", "LH", "HL", "HH"], state="readonly", width=8)
    gui_instance.signal_dropdown.pack(side=tk.LEFT, padx=5)
    gui_instance.signal_dropdown.set("LH")

    # Baris Codec dan Tombol Sisipkan
    frame_sisip_control = ttk.Frame(frame_video)
    frame_sisip_control.grid(row=1, column=0, columnspan=2, sticky=(tk.E, tk.W), padx=5, pady=5)
    frame_sisip_control.columnconfigure(1, weight=1)

    ttk.Label(frame_sisip_control, text="Codec Output:").grid(row=0, column=0, sticky=tk.W, padx=5)
    codec_options = ["HuffYuv (HFYU)"]
    if gui_instance.ffmpeg_available:
         codec_options.insert(1, "H.264 Lossless")
         codec_options.insert(2, "WebM Lossless (VP9)")
         gui_instance.ffmpeg_info = "FFmpeg tersedia."
    else:
         gui_instance.ffmpeg_info = "FFmpeg TIDAK tersedia."
    
    gui_instance.codec_dropdown = ttk.Combobox(frame_sisip_control, values=codec_options, state="readonly")
    gui_instance.codec_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
    gui_instance.codec_dropdown.set(codec_options[0])

    ttk.Button(frame_sisip_control, text="Sisipkan Pesan", 
              command=gui_instance.sisip_pesan_button).grid(row=0, column=2, padx=10, pady=5)
    
    # --- Frame 3: Visualisasi dan Kualitas ---
    frame_visual_kualitas = ttk.LabelFrame(parent, text="Visualisasi dan Kualitas Steganografi", padding="10")
    frame_visual_kualitas.grid(row=2, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), padx=10, pady=10)
    frame_visual_kualitas.grid_columnconfigure(0, weight=1)
    frame_visual_kualitas.grid_rowconfigure(0, weight=1)

    # Display Visualisasi: Dibuat 2 kolom di dalam frame ini
    frame_display = ttk.Frame(frame_visual_kualitas)
    frame_display.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    frame_display.grid_columnconfigure(0, weight=1)
    frame_display.grid_columnconfigure(1, weight=1)
    frame_display.grid_rowconfigure(0, weight=1) # Agar canvas meregang vertikal

    # 3.1 Cover Image + Hist (Kolom Kiri)
    frame_cover_col = ttk.LabelFrame(frame_display, text="Frame Cover (Asli)", padding=5)
    frame_cover_col.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    frame_cover_col.grid_columnconfigure(0, weight=1)
    frame_cover_col.grid_rowconfigure(0, weight=1)

    gui_instance.canvas_cover = Canvas(frame_cover_col, width=300, height=300, bg="lightgrey")
    gui_instance.canvas_cover.grid(row=0, column=0, sticky="nsew")
    gui_instance.histogram_cover = HistogramCanvas(frame_cover_col, width=300, height=150)
    gui_instance.histogram_cover.grid(row=1, column=0, sticky="ew")

    # >>> TAMBAHAN: Spektogram Cover
    ttk.Label(frame_cover_col, text="Audio Cover Spectrogram").grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
    gui_instance.spectrogram_cover = SpectrogramCanvas(frame_cover_col, width=300, height=150, bg="white")
    gui_instance.spectrogram_cover.grid(row=4, column=0, sticky="ew")
    frame_cover_col.grid_rowconfigure(4, weight=0) # Spektogram tidak meregang vertikal

    # 3.2 Stego Image + Hist (Kolom Kanan)
    frame_stego_col = ttk.LabelFrame(frame_display, text="Frame Stego (Hasil)", padding=5)
    frame_stego_col.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    frame_stego_col.grid_columnconfigure(0, weight=1)
    frame_stego_col.grid_rowconfigure(0, weight=1)

    gui_instance.canvas_stego = Canvas(frame_stego_col, width=300, height=300, bg="lightgrey")
    gui_instance.canvas_stego.grid(row=0, column=0, sticky="nsew")
    gui_instance.histogram_stego = HistogramCanvas(frame_stego_col, width=300, height=150)
    gui_instance.histogram_stego.grid(row=1, column=0, sticky="ew")

    # >>> TAMBAHAN: Spektogram Stego
    ttk.Label(frame_stego_col, text="Audio Stego Spectrogram").grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
    gui_instance.spectrogram_stego = SpectrogramCanvas(frame_stego_col, width=300, height=150, bg="white")
    gui_instance.spectrogram_stego.grid(row=4, column=0, sticky="ew")
    frame_stego_col.grid_rowconfigure(4, weight=0) # Spektogram tidak meregang vertikal

    # 3.3 Kualitas Steganografi (di bawah visualisasi, rentang 4 kolom kecil)
    frame_kualitas = ttk.Frame(frame_visual_kualitas)
    frame_kualitas.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
    frame_kualitas.grid_columnconfigure(1, weight=1)
    frame_kualitas.grid_columnconfigure(3, weight=1) 

    ttk.Label(frame_kualitas, text="PSNR:").grid(row=0, column=0, sticky=tk.W, padx=5)
    gui_instance.psnr_form = ttk.Entry(frame_kualitas)
    gui_instance.psnr_form.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
    
    ttk.Label(frame_kualitas, text="Kategori:").grid(row=0, column=2, sticky=tk.W, padx=5)
    gui_instance.kategori_form = ttk.Entry(frame_kualitas)
    gui_instance.kategori_form.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5)
    
    ttk.Label(frame_kualitas, text="BER:").grid(row=1, column=0, sticky=tk.W, padx=5)
    gui_instance.ber_form = ttk.Entry(frame_kualitas)
    gui_instance.ber_form.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
    
    ttk.Label(frame_kualitas, text="CER:").grid(row=1, column=2, sticky=tk.W, padx=5)
    gui_instance.cer_form = ttk.Entry(frame_kualitas)
    gui_instance.cer_form.grid(row=1, column=3, sticky=(tk.W, tk.E), padx=5)