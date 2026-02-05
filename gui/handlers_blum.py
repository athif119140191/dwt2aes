import cv2
import os
import subprocess
import traceback

def extract_frame_from_video(video_path, frame_index=None):
    """
    Mengekstrak frame berdasarkan indeks spesifik.
    Jika frame_index None, default ke frame 100 atau indeks tertentu yang Anda mau.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Tidak dapat membuka video: {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Jika tidak ditentukan, ambil frame di 90% durasi video (agar konsisten)
    if frame_index is None:
        target_frame = int(total_frames * 0.9)
    else:
        target_frame = frame_index

    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError("Gagal membaca frame target")
        
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