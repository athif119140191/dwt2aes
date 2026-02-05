import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np
import math
import traceback

def tampilkan_gambar(gambar, canvas_widget):
    """Menampilkan gambar di ScrolledCanvas"""
    try:
        # Konversi BGR ke RGB
        if len(gambar.shape) == 3:
            gambar_rgb = cv2.cvtColor(gambar, cv2.COLOR_BGR2RGB)
        else:
            gambar_rgb = gambar
        
        # Konversi ke format PhotoImage
        img_pil = Image.fromarray(gambar_rgb)
        
        # Resize gambar agar sesuai dengan canvas
        canvas_width = canvas_widget.canvas.winfo_width()
        canvas_height = canvas_widget.canvas.winfo_height()
        
        # Jika canvas belum di-render, gunakan ukuran default
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 300
            canvas_height = 300
        
        # Resize gambar
        img_pil.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        
        img_tk = ImageTk.PhotoImage(img_pil)
        
        # Simpan referensi untuk mencegah garbage collection
        canvas_widget.image = img_tk
        
        # Hapus konten lama dan tampilkan gambar baru
        canvas_widget.delete("all")
        
        # Create image di tengah canvas
        canvas_widget.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=img_tk)
        
    except Exception as e:
        print(f"Error dalam menampilkan gambar: {str(e)}")
        traceback.print_exc()

def calculate_psnr(original, compressed):
    """Menghitung PSNR antara gambar original dan compressed"""
    mse = np.mean((original - compressed) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
    return psnr

def hitung_cer(pesan_asli, pesan_dekripsi, cer_form_widget):
    """Hitung Character Error Rate (CER) dan update widget CER"""
    # ... (kode hitung_cer yang sudah ada) ...
    panjang_pesan_asli = len(pesan_asli)
    asli = np.frombuffer(pesan_asli.encode('utf-8'), dtype=np.uint8)
    dekripsi = np.frombuffer(pesan_dekripsi.encode('utf-8'), dtype=np.uint8)

    min_len = min(len(asli), len(dekripsi))
    char_error = np.count_nonzero(asli[:min_len] != dekripsi[:min_len])
    char_error += abs(len(asli) - len(dekripsi))
    cer = (char_error / max(len(asli), 1)) * 100
    
    cer_form_widget.delete(0, tk.END)
    cer_form_widget.insert(0, f"{cer:.2f}%")
    
    print(f"CER: {cer:.2f}% ({char_error} errors dari {panjang_pesan_asli} karakter)")


def hitung_ber(bit_pesan_asli_full, bit_pesan_ekstrak_ciphertext, ber_form_widget):
    """
    Hitung Bit Error Rate (BER) antara bit pesan asli dan bit pesan ekstrak.
    Header (Panjang Pesan 16 bit + Nonce 64 bit) diabaikan dari BER.
    """
    start_compare = 16 + 64 # Index mulai setelah Header (ciphertext)
    
    if len(bit_pesan_asli_full) <= start_compare:
        ber_form_widget.delete(0, tk.END)
        ber_form_widget.insert(0, "N/A")
        print("Peringatan: Bit pesan asli terlalu pendek untuk dihitung BER (Tidak ada ciphertext).")
        return

    # Ambil hanya bagian ciphertext dari bit pesan asli
    bit_asli_ciphertext = bit_pesan_asli_full[start_compare:]
    
    # Tentukan panjang minimum untuk perbandingan
    min_len = min(len(bit_asli_ciphertext), len(bit_pesan_ekstrak_ciphertext))
    
    bit_asli = bit_asli_ciphertext[:min_len]
    bit_ekstrak = bit_pesan_ekstrak_ciphertext[:min_len]
    
    if len(bit_asli) == 0:
        ber_form_widget.delete(0, tk.END)
        ber_form_widget.insert(0, "N/A")
        return

    try:
        # Konversi string '0'/'1' ke array integer [0, 1]
        bit_asli_arr = np.frombuffer(bit_asli.encode(), dtype=np.uint8) - ord('0')
        bit_ekstrak_arr = np.frombuffer(bit_ekstrak.encode(), dtype=np.uint8) - ord('0')
        
        # Hitung perbedaan bit
        bit_error = np.count_nonzero(bit_asli_arr != bit_ekstrak_arr)
        
        # Hitung BER
        ber = (bit_error / len(bit_asli_arr)) * 100
        
        ber_form_widget.delete(0, tk.END)
        ber_form_widget.insert(0, f"{ber:.2f}%")
        print(f"BER: {ber:.2f}% ({bit_error} errors dari {len(bit_asli_arr)} bit)")
        
    except Exception as e:
        print(f"Error saat menghitung BER: {e}")
        ber_form_widget.delete(0, tk.END)
        ber_form_widget.insert(0, "Error")