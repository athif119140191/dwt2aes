import numpy as np
import cv2
import pywt
import binascii
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES
from Crypto.Util import Counter
import os
import subprocess
import math
import tempfile

def aes_ctr_encrypt(plaintext, key, nonce):
    """Enkripsi AES-CTR secara paralel"""
    block_size = 16
    blocks = [plaintext[i:i + block_size] for i in range(0, len(plaintext), block_size)]

    def encrypt_block(index, block):
        ctr = Counter.new(64, prefix=nonce.to_bytes(8, 'big'), initial_value=index)
        cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
        return cipher.encrypt(block)

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda x: encrypt_block(x[0], x[1]), enumerate(blocks)))

    return b"".join(results)

def sisip_pesan_logic(cover_img, pesan_terenkripsi_hex, nonce, selected_layer, selected_signal,
                      cover_video_path, cover_frame_index, codec_dropdown_get, ffmpeg_available):
    """
    Melakukan penyisipan DWT dan pembuatan video stego.
    Mengembalikan stego_image, nilai PSNR/MOS, dan informasi video stego, serta path audio.
    """
    from gui.utils import calculate_psnr # Import lokal untuk menghindari circular dependency

    cipher_bytes = binascii.unhexlify(pesan_terenkripsi_hex)
    
    panjang_byte_pesan = len(cipher_bytes)
    panjang_bit_pesan = panjang_byte_pesan * 8

    # Siapkan header
    panjang_bit_pesan_bin = format(panjang_bit_pesan, '016b')
    nonce_bin = format(nonce, '064b')
    bit_pesan = ''.join(format(b, '08b') for b in cipher_bytes)
    
    bit_pesan_full = panjang_bit_pesan_bin + nonce_bin + bit_pesan
    total_bits = len(bit_pesan_full)
    
    # Ambil frame cover
    full_img = cover_img
    
    if selected_layer == 'red': layer_index = 2
    elif selected_layer == 'green': layer_index = 1
    else: layer_index = 0
        
    layer = full_img[:, :, layer_index]

    # Lakukan DWT
    coeffs = pywt.dwt2(layer, 'haar')
    LL, (LH, HL, HH) = coeffs

    if selected_signal == 'LL': used_signal = LL
    elif selected_signal == 'LH': used_signal = LH
    elif selected_signal == 'HL': used_signal = HL
    else: used_signal = HH
    
    signal_sebaris = used_signal.flatten()
    
    if total_bits > len(signal_sebaris):
        raise ValueError(f"Ukuran pesan melebihi kapasitas gambar. Diperlukan: {total_bits} bit, Kapasitas: {len(signal_sebaris)} bit")

    # Tentukan embedding strength
    mean_val = np.mean(np.abs(signal_sebaris))
    if selected_signal == 'LL': embedding_strength = mean_val * 0.5
    else: embedding_strength = mean_val * 2.0
    embedding_strength = max(embedding_strength, 10.0) # Minimum strength
    
    # Lakukan penyisipan bit
    new_signal_sebaris = np.copy(signal_sebaris)
    quant_level = int(10)

    for i in range(total_bits):
        bit = int(bit_pesan_full[i])
        current_val = signal_sebaris[i]
        
        current_quantized = round(current_val / quant_level) * quant_level
        
        if bit == 1:
            new_val = abs(current_quantized) + quant_level
        else:
            new_val = -abs(current_quantized) - quant_level
            
        new_signal_sebaris[i] = new_val

    # Gabungkan kembali subband yang sudah dimodifikasi
    new_used_signal = new_signal_sebaris.reshape(used_signal.shape)
    
    if selected_signal == 'LL': new_coeffs = (new_used_signal, (LH, HL, HH))
    elif selected_signal == 'LH': new_coeffs = (LL, (new_used_signal, HL, HH))
    elif selected_signal == 'HL': new_coeffs = (LL, (LH, new_used_signal, HH))
    else: new_coeffs = (LL, (LH, HL, new_used_signal))
        
    # Lakukan Inverse DWT
    new_layer = pywt.idwt2(new_coeffs, 'haar')
    new_layer = np.clip(new_layer, 0, 255).astype(np.uint8)

    # Gabungkan kembali layer
    stego_image = full_img.copy()
    stego_image[:, :, layer_index] = new_layer

    # Simpan frame stego sementara
    cv2.imwrite('stego_image.bmp', stego_image)

    # ==============================
    # SELECTIVE RE-ENCODE (SIZE SAFE)
    # ==============================

    cap = cv2.VideoCapture(cover_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    frame_time = cover_frame_index / fps
    frame_duration = 1.0 / fps

    workdir = tempfile.mkdtemp(prefix="stego_")

    audio_path = os.path.join(workdir, "audio.aac")
    part_A = os.path.join(workdir, "part_A.mp4")
    part_B = os.path.join(workdir, "part_B.mp4")
    part_C = os.path.join(workdir, "part_C.mp4")
    video_no_audio = os.path.join(workdir, "video_no_audio.mp4")
    concat_list = os.path.join(workdir, "concat_list.txt")

    final_mp4 = "stego_video_final.mp4"

    # 1. Extract audio (COPY)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", cover_video_path,
        "-vn", "-c:a", "copy",
        audio_path
    ], check=True)

    # 2. Part A — BEFORE FRAME (BITSTREAM COPY)
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", "0",
        "-to", str(frame_time),
        "-i", cover_video_path,
        "-c", "copy",
        "-an",
        part_A
    ], check=True)

    # 3. Part B — ONLY STEGO FRAME (CONTROLLED RE-ENCODE)
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "stego_image.bmp",
        "-t", str(frame_duration),
        "-r", str(fps),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-level", "4.0",
        "-x264-params",
        "qp=0:ref=1:no-dct-decimate=1:deadzone-inter=0:deadzone-intra=0",
        "-bf", "0",
        "-g", "1",
        "-keyint_min", "1",
        "-sc_threshold", "0",
        "-an",
        part_B
    ], check=True)

    # 4. Part C — AFTER FRAME (BITSTREAM COPY)
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", str(frame_time + frame_duration),
        "-i", cover_video_path,
        "-c", "copy",
        "-an",
        part_C
    ], check=True)

    # 5. Concat WITHOUT re-encode
    with open(concat_list, "w") as f:
        f.write(f"file '{part_A}'\n")
        f.write(f"file '{part_B}'\n")
        f.write(f"file '{part_C}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        video_no_audio
    ], check=True)

    # 6. Mux audio back (COPY)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_no_audio,
        "-i", audio_path,
        "-c", "copy",
        final_mp4
    ], check=True)

    # Hitung PSNR dan MOS
    nilai_psnr = calculate_psnr(full_img, stego_image)
    if nilai_psnr > 37: nilai_mos = 'Excellent'
    elif nilai_psnr > 31: nilai_mos = 'Good'
    elif nilai_psnr > 25: nilai_mos = 'Fair'
    elif nilai_psnr > 20: nilai_mos = 'Poor'
    else: nilai_mos = 'Bad'
        

    # KEMBALIKAN PATH AUDIO
    return (
        stego_image,
        nilai_psnr,
        nilai_mos,
        final_mp4,   # <— mp4 untuk user
        "Selective Re-Encode (Lossless Core)",
        new_signal_sebaris[:20],
        total_bits,
        embedding_strength,
        bit_pesan_full,
        audio_path,
        audio_path
    )