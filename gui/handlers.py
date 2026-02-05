import cv2
import os
import subprocess
import traceback

def extract_frame_from_video(video_path, seconds_from_end=5):
    """Mengekstrak frame dari video pada detik ke-X dari akhir"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Tidak dapat membuka video: {video_path}")
    
    # === VALIDASI RESOLUSI VIDEO (maksimal 1080p) ===
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    MAX_WIDTH = 1920
    MAX_HEIGHT = 1920

    if width > MAX_WIDTH or height > MAX_HEIGHT:
        cap.release()
        raise ValueError(
            f"Resolusi video melebihi batas!\n"
            f"Resolusi video: {width} x {height}\n"
            f"Maksimal diperbolehkan: {MAX_WIDTH} x {MAX_HEIGHT} (1080p)"
        )
    
    # Dapatkan total frame dan FPS
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if total_frames == 0:
        # Jika tidak bisa dapat frame count, estimasi berdasarkan durasi
        duration = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if duration > 0:
            total_frames = int(duration * fps)
        else:
            # Fallback: asumsikan video punya cukup frame
            total_frames = int(seconds_from_end * fps * 2)
    
    print(f"Video info - Total frames: {total_frames}, FPS: {fps}")

    # === VALIDASI DURASI VIDEO ===
    if fps <= 0:
        raise ValueError("FPS video tidak valid")

    durasi = total_frames / fps

    MIN_DURASI = 6          # 6 detik
    MAX_DURASI = 180.99        # 3 menit

    if durasi < MIN_DURASI or durasi > MAX_DURASI:
        raise ValueError(
            f"Durasi video harus antara {MIN_DURASI} detik sampai {MAX_DURASI} detik.\n"
            f"Durasi video saat ini: {durasi:.2f} detik"
        )
    
    # Hitung frame target (5 detik dari akhir)
    target_frame = max(0, total_frames - int(seconds_from_end * fps))
    
    # Set posisi frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    
    # Baca frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        # Fallback: coba baca frame pertama
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise ValueError("Gagal membaca frame dari video")
    
    return frame, target_frame, total_frames, fps

def replace_frame_in_video(original_video_path, new_frame, frame_index, output_path):
    """Mengganti frame tertentu dalam video dengan frame baru"""
    cap = cv2.VideoCapture(original_video_path)
    
    if not cap.isOpened():
        raise ValueError("Tidak dapat membuka video asli")
    
    # Dapatkan properti video
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup video writer
    # Menggunakan MP4V sebagai fallback codec jika FFmpeg tidak digunakan di sisip_pesan_logic
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Ganti frame jika ini adalah frame target
        if frame_count == frame_index:
            # Pastikan ukuran frame baru sesuai
            if new_frame.shape != frame.shape:
                new_frame = cv2.resize(new_frame, (width, height))
            out.write(new_frame)
        else:
            out.write(frame)
        
        frame_count += 1
    
    cap.release()
    out.release()
    
    return output_path