import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import secrets
import re
import binascii
import os
import traceback
import cv2
import numpy as np

import librosa
import librosa.display
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image
import io

# Import modul lokal
from gui.widgets import ScrolledText, Canvas, HistogramCanvas
from gui.tab_enkripsi import setup_tab_enkripsi
from gui.tab_dekripsi import setup_tab_dekripsi
from gui.tab_uji_ketahanan import setup_tab_uji_ketahanan
from gui.handlers import extract_frame_from_video
from gui.utils import tampilkan_gambar, hitung_cer, hitung_ber
from core.penyisipan import aes_ctr_encrypt, sisip_pesan_logic
from core.pengekstrak import aes_ctr_decrypt, ekstrak_pesan_logic

class EncryptGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Steganografi dengan AES dan DWT")
        self.root.state('zoomed')
                
        style = ttk.Style()
        try:
             style.theme_use('clam') 
        except tk.TclError:
             try:
                 style.theme_use('alt') 
             except tk.TclError:
                 pass 
        
        # Variabel untuk menyimpan data (State Variables)
        self.pesan = ""
        self.cover_image = None
        self.stego_image = None
        self.aes_key = None
        self.nonce = None
        self.cover_video_path = None
        self.stego_video_path = None
        self.cover_frame_index = None
        self.cover_total_frames = None
        self.panjang_bit_pesan_actual = None
        self.nonce_actual = None
        self.embedding_strength_used = None
        self.bit_pesan = "" # Digunakan untuk BER
        
        # CHECK FFmpeg
        self.ffmpeg_available = self._check_ffmpeg_availability()
        
        # Global Binding: Scroll bekerja di seluruh jendela, seperti di web
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Atur root agar meregang penuh
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Buat main frame dengan scrollbar
        self.setup_scrollable_main_frame()

        self.output_video_path = None
        self.ffmpeg_available = self._check_ffmpeg_availability()
        
        # Inisialisasi widget (akan diisi di setup_tab_enkripsi)
        self.spectrogram_cover = None
        self.spectrogram_stego = None
        self.setup_gui()

    def _check_ffmpeg_availability(self):
        """Check if ffmpeg is installed and accessible."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, PermissionError, OSError):
            return False
        except Exception as e:
            print(f"Error during FFmpeg check: {e}")
            return False

    def is_printable_ascii(self, text):
        """
        Printable ASCII: HEX 20 - 7E
        """
        for ch in text:
            code = ord(ch)
            if code < 0x20 or code > 0x7E:
                return False, ch, code
        return True, None, None
    
    def update_jumlah_char(self, event=None):
        teks = self.teks_pesan_form.get("1.0", "end-1c")
        jumlah = len(teks)
        
        # Update entry jumlah karakter
        self.jumlah_char_form.delete(0, "end")
        self.jumlah_char_form.insert(0, str(jumlah))

    def setup_scrollable_main_frame(self):
        """Setup main frame dengan scrollbar vertikal dan layout fluid menggunakan GRID."""
        
        self.main_container = ttk.Frame(self.root)
        # Gunakan grid, bukan pack
        self.main_container.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        # Konfigurasi main_container untuk meregang
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(self.main_container)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Binding untuk memperbarui scroll region saat konten berubah
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Buat window di canvas
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # KUNCI RESPONSIVENESS HORIZONTAL: 
        # Memaksa lebar scrollable_frame sama dengan lebar canvas.
        def _on_canvas_resize(event):
            self.canvas.itemconfig(self.window_id, width=event.width)
            
        self.canvas.bind('<Configure>', _on_canvas_resize)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Layout Canvas dan Scrollbar menggunakan GRID
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Pastikan frame internal (tempat tab_control berada) meregang
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
    def _on_mousewheel(self, event):
        """Handler mouse wheel yang dipanggil dari root window."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def setup_gui(self):
        # Frame utama menggunakan scrollable_frame
        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        # Pastikan main_frame mengisi lebar penuh di scrollable_frame
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)) 
        
        # Tambahkan weight pada main_frame agar tab_control meregang
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Tab Control
        tab_control = ttk.Notebook(main_frame)
        
        # Tab Enkripsi
        tab_enkripsi = ttk.Frame(tab_control)
        tab_control.add(tab_enkripsi, text='Enkripsi & Penyisipan')
        
        # Tab Dekripsi
        tab_dekripsi = ttk.Frame(tab_control)
        tab_control.add(tab_dekripsi, text='Dekripsi & Ekstraksi')

        # Tab Uji Ketahanan
        tab_uji = ttk.Frame(tab_control)
        tab_control.add(tab_uji, text='Uji Ketahanan')
        
        # Tab control mengisi penuh main_frame
        tab_control.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Panggil fungsi setup UI dari modul lain
        setup_tab_enkripsi(self, tab_enkripsi)
        setup_tab_dekripsi(self, tab_dekripsi)
        setup_tab_uji_ketahanan(self, tab_uji)
        
    def clear_fields(self):
        """Membersihkan semua field input/output yang terkait."""
        fields = [
            self.kode_ascii_form, self.pesan_terenkripsi_form, 
            self.psnr_form, self.kategori_form, 
            self.ber_form, self.cer_form, self.pesan_terenkripsi_dekripsi_form, 
            self.kode_ascii_dekripsi_form, self.teks_pesan_dekripsi_form, 
            self.jumlah_char_dekripsi_form
        ]
        
        for field in fields:
            if hasattr(field, 'delete'):
                if isinstance(field, ScrolledText):
                    field.delete(1.0, tk.END)
                else:
                    field.delete(0, tk.END)

    # --- ENCRYPTION HANDLERS ---
    
    def generate_random_key(self):
        """Generate random AES key"""
        random_key = secrets.token_bytes(16)
        key_hex = binascii.hexlify(random_key).decode('utf-8')
        self.kunci_aes_form.delete(0, tk.END)
        self.kunci_aes_form.insert(0, key_hex)
        messagebox.showinfo("Info", "Random key telah di-generate!")

    def pilih_txt_button(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not file_path:
            messagebox.showerror("Error", "File teks tidak dipilih")
        else:
            self.lokasi_txt_form.delete(0, tk.END)
            self.lokasi_txt_form.insert(0, file_path)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                pesan = file.read()
                MAX_CHAR = 500

                if len(pesan) > MAX_CHAR:
                    messagebox.showerror(
                        "Error",
                        f"Panjang teks melebihi batas!\n"
                        f"Maksimal {MAX_CHAR} karakter.\n"
                        f"Teks saat ini: {len(pesan)} karakter"
                    )
                    return
                
                valid, ch, code = self.is_printable_ascii(pesan)
                if not valid:
                    messagebox.showerror(
                        "Error",
                        f"Teks mengandung karakter NON-printable ASCII!\n\n"
                        f"Karakter: {repr(ch)}\n"
                        f"Kode ASCII: {code}\n\n"
                        f"Hanya diperbolehkan ASCII 0x20–0x7E."
                    )
                    return
            
            pesan = re.sub(r'\s+', ' ', pesan) # Hapus spasi berlebih
            
            self.teks_pesan_form.delete(1.0, tk.END)
            self.teks_pesan_form.insert(1.0, pesan)
            self.jumlah_char_form.delete(0, tk.END)
            self.jumlah_char_form.insert(0, str(len(pesan)))
            
            self.clear_fields()
    
    def konversi_ascii_button(self):
        pesan = self.teks_pesan_form.get(1.0, tk.END).strip()
        if not pesan:
            messagebox.showerror("Error", "Silahkan pilih file teks terlebih dahulu")
        else:
            ascii_pesan = [ord(char) for char in pesan]
            self.kode_ascii_form.delete(1.0, tk.END)
            self.kode_ascii_form.insert(1.0, ' '.join(map(str, ascii_pesan)))
            print(f"Pesan dalam ascii: {ascii_pesan}")
    
    def enkripsi_pesan_button(self):
        pesan = self.teks_pesan_form.get(1.0, tk.END).strip()
        MAX_CHAR = 500

        if len(pesan) > MAX_CHAR:
            messagebox.showerror(
                "Error",
                f"Panjang teks melebihi batas maksimal {MAX_CHAR} karakter.\n"
                f"Jumlah karakter saat ini: {len(pesan)}"
            )
            return
        
        valid, ch, code = self.is_printable_ascii(pesan)
        if not valid:
            messagebox.showerror(
                "Error",
                f"Teks mengandung karakter NON-printable ASCII!\n\n"
                f"Karakter: {repr(ch)}\n"
                f"Kode ASCII: {code}\n\n"
                f"Gunakan hanya karakter ASCII printable (0x20–0x7E)."
            )
            return

        if not pesan:
            messagebox.showerror("Error", "Silahkan pilih file teks terlebih dahulu")
            return
        
        kunci_str = self.kunci_aes_form.get().strip()
        if not kunci_str:
            messagebox.showerror("Error", "Silahkan masukkan kunci AES terlebih dahulu")
            return
        MAX_KEY_LEN = 16

        if len(kunci_str) > MAX_KEY_LEN:
            messagebox.showerror(
                "Error",
                f"Kunci AES terlalu panjang!\n"
                f"Maksimal {MAX_KEY_LEN} karakter.\n"
                f"Panjang saat ini: {len(kunci_str)}"
            )
            return

        if len(kunci_str) == 0:
            messagebox.showerror("Error", "Kunci AES tidak boleh kosong")
            return
        
        nonce = secrets.randbits(64)
        
        try:
            kunci = kunci_str.encode('utf-8')
            if len(kunci) < 16: kunci = kunci + b'\0' * (16 - len(kunci))
            elif len(kunci) > 16: kunci = kunci[:16]
            
            self.aes_key = kunci
            self.nonce = nonce
            
            cipher = aes_ctr_encrypt(pesan.encode('utf-8'), kunci, nonce)
            cipher_hex = binascii.hexlify(cipher).decode('utf-8')
            
            # self.kode_ascii_pesan_terenkripsi_form.delete(1.0, tk.END)
            # self.kode_ascii_pesan_terenkripsi_form.insert(1.0, ' '.join(str(b) for b in cipher))
            self.pesan_terenkripsi_form.delete(1.0, tk.END)
            self.pesan_terenkripsi_form.insert(1.0, cipher_hex)
            
            with open('teks_enkripsi.bin', 'wb') as fid:
                fid.write(nonce.to_bytes(8, byteorder='big') + cipher)
            
            messagebox.showinfo("Info", f"Enkripsi berhasil!\nNonce {nonce} telah digenerate otomatis dan akan disimpan ke dalam gambar.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengenkripsi: {str(e)}")
            traceback.print_exc()

    def pilih_video_cover_button(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.webm")])
        if not file_path:
            messagebox.showerror("Error", "File video cover tidak dipilih")
        else:
            try:
                frame, frame_index, total_frames, fps = extract_frame_from_video(file_path, 5)
                
                self.cover_image = frame
                self.cover_video_path = file_path
                self.cover_frame_index = frame_index
                self.cover_total_frames = total_frames
                
                cv2.imwrite('cover_image.bmp', self.cover_image)
                tampilkan_gambar(self.cover_image, self.canvas_cover)
                self.histogram_cover.draw_histogram(self.cover_image, "Histogram Cover Frame")
                
                print(f"Lokasi file video cover: {file_path}")
                print(f"Frame yang dipilih: {frame_index}/{total_frames} (5 detik dari akhir)")
                
                self.psnr_form.delete(0, tk.END)
                self.kategori_form.delete(0, tk.END)
                self.ber_form.delete(0, tk.END)
                self.cer_form.delete(0, tk.END)
                self.pesan_terenkripsi_dekripsi_form.delete(1.0, tk.END)
                self.kode_ascii_dekripsi_form.delete(1.0, tk.END)
                self.teks_pesan_dekripsi_form.delete(1.0, tk.END)
                self.jumlah_char_dekripsi_form.delete(0, tk.END)
                
            except Exception as e:
                messagebox.showerror("Error", f"Gagal memproses video: {str(e)}")
    
    def generate_spectrogram(self, audio_file_path):
        """Menghasilkan gambar spektogram (PNG) menggunakan Librosa dan Matplotlib."""        
        temp_png_path = None
        try:
            # 1. Baca Audio
            y, sr = librosa.load(audio_file_path)
            
            # 2. Hitung STFT dan ubah ke dB
            S = librosa.stft(y)
            S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
            
            # 3. Plot menggunakan Matplotlib
            fig, ax = plt.subplots(figsize=(6, 3)) # Ukuran kecil, akan di-resize
            librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz', ax=ax)
            ax.set_title('Spektogram Audio', fontsize=10)
            ax.set_ylim(0, sr / 2)
            ax.set_xlabel("Waktu (s)", fontsize=8)
            ax.set_ylabel("Frekuensi (Hz)", fontsize=8)
            plt.tight_layout()
            
            # 4. Simpan ke file sementara
            temp_png_path = os.path.join(os.path.dirname(audio_file_path), f"spectro_{os.path.basename(audio_file_path).split('.')[0]}.png")
            fig.savefig(temp_png_path, bbox_inches='tight', pad_inches=0.1)
            plt.close(fig) # Tutup plot agar tidak menumpuk di memori
            
            return temp_png_path 
            
        except Exception as e:
            print(f"Gagal generate spektogram untuk {audio_file_path}: {e}")
            traceback.print_exc()
            if temp_png_path and os.path.exists(temp_png_path):
                 os.remove(temp_png_path)
            return None

    def sisip_pesan_button(self):
        pesan_terenkripsi_hex = self.pesan_terenkripsi_form.get(1.0, tk.END).strip()
        if not pesan_terenkripsi_hex:
            messagebox.showerror("Error", "Silahkan enkripsi pesan terlebih dahulu")
            return
        if self.cover_image is None or self.cover_video_path is None:
            messagebox.showerror("Error", "Silahkan pilih video cover terlebih dahulu")
            return

        try:
            results = sisip_pesan_logic(
                cover_img=self.cover_image,
                pesan_terenkripsi_hex=pesan_terenkripsi_hex,
                nonce=self.nonce,
                selected_layer=self.layer_dropdown.get(),
                selected_signal=self.signal_dropdown.get(),
                cover_video_path=self.cover_video_path,
                cover_frame_index=self.cover_frame_index,
                codec_dropdown_get=self.codec_dropdown.get(),
                ffmpeg_available=self.ffmpeg_available
            )

            (stego_image, nilai_psnr, nilai_kategori, output_video_path, 
             selected_fourcc_info, new_signal_sebaris_20, total_bits, embedding_strength_used, bit_pesan_full,
             audio_cover_path, audio_stego_path) = results
            
            # Simpan state untuk ekstraksi
            self.stego_image = stego_image
            self.stego_video_path = output_video_path
            self.panjang_bit_pesan_actual = total_bits - 80
            self.nonce_actual = self.nonce
            self.embedding_strength_used = embedding_strength_used
            self.bit_pesan = bit_pesan_full # Ganti 'bit_pesan' dengan 'bit_pesan_full'

            # --- State Variabel Baru ---
            self.audio_cover_path = audio_cover_path # Menyimpan path audio cover
            self.audio_stego_path = audio_stego_path # Menyimpan path stego video/audio
            
            # Update UI
            self.psnr_form.delete(0, tk.END)
            self.psnr_form.insert(0, f"{nilai_psnr:.2f}")
            self.kategori_form.delete(0, tk.END)
            self.kategori_form.insert(0, nilai_kategori)
            
            tampilkan_gambar(stego_image, self.canvas_stego)
            self.histogram_stego.draw_histogram(stego_image, "Histogram Stego Image")

            temp_spectro_cover_path = None
            temp_spectro_stego_path = None
            
            if audio_cover_path:
                temp_spectro_cover_path = self.generate_spectrogram(audio_cover_path)
                self.spectrogram_cover.display_spectrogram(temp_spectro_cover_path)
            else:
                self.spectrogram_cover.display_spectrogram(None) # Tampilkan pesan "Tidak Tersedia"
            
            # Karena audio stego dan cover identik (lossless copy), gunakan file yang sama
            if audio_stego_path:
                 temp_spectro_stego_path = self.generate_spectrogram(audio_stego_path)
                 self.spectrogram_stego.display_spectrogram(temp_spectro_stego_path)
            else:
                 self.spectrogram_stego.display_spectrogram(None) # Tampilkan pesan "Tidak Tersedia"
            
            # Hapus file audio dan spektogram sementara setelah digunakan
            if audio_cover_path and os.path.exists(audio_cover_path): 
                os.remove(audio_cover_path)
            # Karena audio_stego_path sama dengan audio_cover_path, cukup hapus sekali.
            
            if temp_spectro_cover_path and os.path.exists(temp_spectro_cover_path): 
                os.remove(temp_spectro_cover_path)
            if temp_spectro_stego_path and os.path.exists(temp_spectro_stego_path): 
                os.remove(temp_spectro_stego_path)
            
            messagebox.showinfo("Success", 
                f"Penyisipan berhasil!\nPSNR: {nilai_psnr:.2f}\nVideo stego: {output_video_path} (Codec: {selected_fourcc_info})")
            
            print("Setelah embedding - 20 nilai pertama:")
            print(new_signal_sebaris_20)

        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyisipkan pesan: {str(e)}")
            traceback.print_exc()

    def toggle_password_visibility(self, entry_widget, button_widget):
        """
        Mengubah properti 'show' pada Entry widget (tombol Show/Hide).
        Digunakan untuk tab enkripsi dan dekripsi.
        """
        if entry_widget.cget('show') == '*':
            # Saat ini tersembunyi, tampilkan
            entry_widget.config(show='')
            button_widget.config(text="Hide")
        else:
            # Saat ini terlihat, sembunyikan
            entry_widget.config(show='*')
            button_widget.config(text="Show")

    # --- DECRYPTION HANDLERS ---
    
    def pilih_video_stego_button(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.webm *.avi *.mkv")])
        if not file_path:
            messagebox.showerror("Error", "File video stego tidak dipilih")
        else:
            try:
                frame, frame_index, total_frames, fps = extract_frame_from_video(file_path, 5)
                
                self.stego_image = frame
                self.stego_video_path = file_path
                
                cv2.imwrite('stego_image.bmp', self.stego_image)
                
                tampilkan_gambar(self.stego_image, self.canvas_stego_dekripsi)
                self.histogram_stego_dekripsi.draw_histogram(self.stego_image, "Histogram Stego Frame")
                
                print(f"Lokasi file video stego: {file_path}")
                print(f"Frame yang dipilih: {frame_index}/{total_frames} (5 detik dari akhir)")
                
            except Exception as e:
                messagebox.showerror("Error", f"Gagal memproses video: {str(e)}")

    def ekstrak_pesan_button(self):
        if self.stego_image is None:
            messagebox.showerror("Error", "Silahkan pilih video stego terlebih dahulu")
            return
        
        try:
            # Panggil core logic
            results = ekstrak_pesan_logic(
                stego_img=self.stego_image,
                selected_layer=self.layer_dropdown.get(),
                selected_signal=self.signal_dropdown.get(),
                embedding_strength_used=self.embedding_strength_used,
                panjang_bit_pesan_actual=self.panjang_bit_pesan_actual
            )
            
            (cipher_hex, nonce, bit_pesan_ekstrak, total_bit_ekstrak, pesan_ekstraksi_bytes, 
             signal_sebaris_20, threshold) = results
            
            # Simpan file ekstraksi untuk dekripsi
            nonce_bytes = nonce.to_bytes(8, byteorder='big')
            with open('teks_ekstraksi.bin', 'wb') as fid:
                fid.write(nonce_bytes + pesan_ekstraksi_bytes)
                
            # Update UI
            self.pesan_terenkripsi_dekripsi_form.delete(1.0, tk.END)
            self.pesan_terenkripsi_dekripsi_form.insert(1.0, cipher_hex)
            
            print(f"Ekstraksi berhasil! Panjang ciphertext: {len(pesan_ekstraksi_bytes)} bytes")
            print(f"Nonce {nonce} telah diekstrak dari gambar")
            
            # Hitung BER (gui/utils.py)
            if hasattr(self, 'bit_pesan') and self.bit_pesan:
                hitung_ber(self.bit_pesan, bit_pesan_ekstrak, self.ber_form)

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengekstrak pesan: {str(e)}")
            traceback.print_exc()

    def dekripsi_pesan_button(self):
        kunci_str = self.kunci_aes_dekripsi_form.get().strip()
        if not kunci_str:
            messagebox.showerror("Error", "Silahkan masukkan kunci AES terlebih dahulu")
            return
        
        try:
            kunci = kunci_str.encode('utf-8')
            if len(kunci) < 16: kunci = kunci + b'\0' * (16 - len(kunci))
            elif len(kunci) > 16: kunci = kunci[:16]
            
            with open('teks_ekstraksi.bin', 'rb') as fid:
                data_bytes = fid.read()
            
            nonce_bytes_from_file = data_bytes[:8]
            ciphertext_bytes = data_bytes[8:]
            nonce_from_file = int.from_bytes(nonce_bytes_from_file, byteorder='big')
            
            plaintext_bytes = aes_ctr_decrypt(ciphertext_bytes, kunci, nonce_from_file)
            pesan_dekripsi = plaintext_bytes.decode('utf-8')
            
            ascii_codes = [str(b) for b in plaintext_bytes]
            self.kode_ascii_dekripsi_form.delete(1.0, tk.END)
            self.kode_ascii_dekripsi_form.insert(1.0, ' '.join(ascii_codes))
            
            self.teks_pesan_dekripsi_form.delete(1.0, tk.END)
            self.teks_pesan_dekripsi_form.insert(1.0, pesan_dekripsi)
            
            self.jumlah_char_dekripsi_form.delete(0, tk.END)
            self.jumlah_char_dekripsi_form.insert(0, str(len(pesan_dekripsi)))
            
            print(f"Dekripsi berhasil! Menggunakan nonce dari gambar: {nonce_from_file}")
            
            pesan_asli = self.teks_pesan_form.get(1.0, tk.END).strip()
            if pesan_asli:
                hitung_cer(pesan_asli, pesan_dekripsi, self.cer_form)
            
            messagebox.showinfo("Success", "Dekripsi berhasil! Nonce diambil otomatis dari gambar.")
            
        except FileNotFoundError:
            messagebox.showerror("Error", "Silahkan ekstrak pesan dari gambar terlebih dahulu")
        except UnicodeDecodeError:
            messagebox.showerror("Error Decode", "Gagal decode UTF-8. Pastikan kunci AES sama dengan saat enkripsi.")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mendekripsi: {str(e)}")
            traceback.print_exc()