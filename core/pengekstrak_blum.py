import numpy as np
import pywt
import binascii
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES
from Crypto.Util import Counter
import os

def aes_ctr_decrypt(ciphertext, key, nonce):
    """Dekripsi AES-CTR secara paralel"""
    block_size = 16
    blocks = [ciphertext[i:i + block_size] for i in range(0, len(ciphertext), block_size)]

    def decrypt_block(index, block):
        ctr = Counter.new(64, prefix=nonce.to_bytes(8, 'big'), initial_value=index)
        cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
        return cipher.decrypt(block)

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda x: decrypt_block(x[0], x[1]), enumerate(blocks)))

    return b"".join(results)

def ekstrak_pesan_logic(stego_img, selected_layer, selected_signal, embedding_strength_used=None, panjang_bit_pesan_actual=None):
    """
    Melakukan ekstraksi bit pesan dari frame stego DWT.
    Mengembalikan data pesan terenkripsi yang diekstrak.
    """
    
    if selected_layer == 'red': used_layer = stego_img[:, :, 2]
    elif selected_layer == 'green': used_layer = stego_img[:, :, 1]
    else: used_layer = stego_img[:, :, 0]
    
    coeffs = pywt.dwt2(used_layer.astype(np.float64), 'haar')
    LL, (LH, HL, HH) = coeffs
    
    if selected_signal == 'LL': used_signal = LL
    elif selected_signal == 'LH': used_signal = LH
    elif selected_signal == 'HL': used_signal = HL
    else: used_signal = HH
    
    signal_sebaris = used_signal.flatten()
    
    # Tentukan threshold
    # if embedding_strength_used is not None:
    #     threshold = embedding_strength_used * 0.5
    # else:
    #     mean_val = np.mean(np.abs(signal_sebaris))
    #     threshold = mean_val * 0.3
    mean_val = np.mean(np.abs(signal_sebaris))
    threshold = mean_val * 0.3
    
    print(f"Threshold untuk ekstraksi: {threshold:.2f}")

    # 1. Ekstrak panjang bit pesan (16 bit pertama)
    panjang_bit_pesan_bit = ""
    for i in range(16):
        val = signal_sebaris[i]
        if val > threshold: panjang_bit_pesan_bit += '1'
        elif val < -threshold: panjang_bit_pesan_bit += '0' 
        else: panjang_bit_pesan_bit += '0'
    
    try:
        panjang_bit_pesan = int(panjang_bit_pesan_bit, 2)
    except ValueError:
        panjang_bit_pesan = 1416 # Fallback
        
    if panjang_bit_pesan == 0 or panjang_bit_pesan > 100000:
        if panjang_bit_pesan_actual is not None:
            panjang_bit_pesan = panjang_bit_pesan_actual
        else:
            panjang_bit_pesan = 1416 # Default fallback
    
    # 2. Ekstrak nonce (64 bit berikutnya)
    nonce_bit = ""
    for i in range(16, 16 + 64):
        if signal_sebaris[i] < -threshold: nonce_bit += '0'
        elif signal_sebaris[i] > threshold: nonce_bit += '1'
        else: nonce_bit += '0'
    
    nonce_bytes = bytearray()
    for i in range(0, 64, 8):
        byte_val = int(nonce_bit[i:i+8], 2)
        nonce_bytes.append(byte_val)
    
    nonce = int.from_bytes(nonce_bytes, byteorder='big')
    
    # 3. Ekstrak bit pesan (ciphertext)
    start_index = 16 + 64
    bit_pesan_ekstrak = ""
    
    for i in range(panjang_bit_pesan):
        idx = start_index + i
        if idx >= len(signal_sebaris): break
            
        if signal_sebaris[idx] < -threshold: bit_pesan_ekstrak += '0'
        elif signal_sebaris[idx] > threshold: bit_pesan_ekstrak += '1'
        else: bit_pesan_ekstrak += '0'
    
    # Konversi bit pesan ke bytes
    pesan_ekstraksi_bytes = bytearray()
    for i in range(0, len(bit_pesan_ekstrak), 8):
        if i + 8 <= len(bit_pesan_ekstrak):
            byte_val = int(bit_pesan_ekstrak[i:i+8], 2)
            pesan_ekstraksi_bytes.append(byte_val)
    
    cipher_hex = binascii.hexlify(pesan_ekstraksi_bytes).decode('utf-8')
    total_bit_ekstrak = len(bit_pesan_ekstrak)
    
    return (cipher_hex, nonce, bit_pesan_ekstrak, total_bit_ekstrak, pesan_ekstraksi_bytes, 
            signal_sebaris[:20], threshold)