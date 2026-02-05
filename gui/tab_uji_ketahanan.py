import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os

def get_ext(path):
    return os.path.splitext(path)[1]

def setup_tab_uji_ketahanan(gui_instance, parent):
    """
    Tab Uji Ketahanan (Robustness Testing)
    - Pemotongan video (awal, tengah, akhir)
    - Kompresi lossy
    """

    parent.grid_columnconfigure(0, weight=1)

    # ==============================
    # FRAME 1: PILIH VIDEO STEGO
    # ==============================
    frame_input = ttk.LabelFrame(parent, text="Input Video Stego", padding=10)
    frame_input.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

    frame_input.grid_columnconfigure(1, weight=1)

    ttk.Label(frame_input, text="Video Stego:").grid(row=0, column=0, sticky="w")

    gui_instance.uji_video_path_var = tk.StringVar()
    ttk.Entry(frame_input, textvariable=gui_instance.uji_video_path_var)\
        .grid(row=0, column=1, sticky="ew", padx=5)

    def pilih_video_uji():
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.webm *.mkv")]
        )
        if path:
            gui_instance.uji_video_path_var.set(path)

    ttk.Button(frame_input, text="Browse", command=pilih_video_uji)\
        .grid(row=0, column=2, padx=5)

    # ==============================
    # FRAME 2: UJI PEMOTONGAN VIDEO
    # ==============================
    frame_cut = ttk.LabelFrame(parent, text="Uji Pemotongan Video", padding=10)
    frame_cut.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

    ttk.Label(frame_cut, text="Jenis Pemotongan:").grid(row=0, column=0, sticky="w")

    gui_instance.cut_mode_var = tk.StringVar(value="awal")
    ttk.Combobox(
        frame_cut,
        textvariable=gui_instance.cut_mode_var,
        state="readonly",
        values=["awal", "tengah", "akhir"]
    ).grid(row=0, column=1, sticky="w", padx=5)

    ttk.Label(frame_cut, text="Durasi dipotong (detik):").grid(row=1, column=0, sticky="w")
    gui_instance.cut_duration_var = tk.IntVar(value=10)
    ttk.Entry(frame_cut, textvariable=gui_instance.cut_duration_var, width=10)\
        .grid(row=1, column=1, sticky="w", padx=5)

    def jalankan_uji_potong():
        video = gui_instance.uji_video_path_var.get()
        if not video:
            messagebox.showerror("Error", "Pilih video stego terlebih dahulu")
            return

        mode = gui_instance.cut_mode_var.get()
        durasi = gui_instance.cut_duration_var.get()

        output = f"stego_cut_{mode}.avi"

        try:
            ext = get_ext(video)
            output = f"stego_video_cut_{mode}{ext}"

            if mode == "awal":
                cmd = ["ffmpeg", "-y", "-i", video, "-ss", str(durasi),
                    "-map", "0", "-c", "copy", output]
                subprocess.run(cmd, check=True)

            elif mode == "akhir":
                probe = subprocess.check_output([
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video
                ])
                total_dur = float(probe.strip())
                end_time = max(0, total_dur - durasi)

                cmd = ["ffmpeg", "-y", "-i", video,
                    "-map", "0", "-c", "copy",
                    "-to", str(end_time), output]
                subprocess.run(cmd, check=True)

            else:  # === TENGAH (LOSSLESS CONCAT) ===
                probe = subprocess.check_output([
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video
                ])
                durasi_input = float(probe.strip())

                durasi_potong = gui_instance.cut_duration_var.get()
                durasi_tepi = max(0, (durasi_input - durasi_potong) / 2)

                ext = get_ext(video)
                tmp_awal = f"tmp_awal{ext}"
                tmp_akhir = f"tmp_akhir{ext}"
                concat_list = "concat_list.txt"

                # potong awal
                subprocess.run([
                    "ffmpeg", "-y", "-i", video,
                    "-t", str(durasi_tepi),
                    "-map", "0", "-c", "copy",
                    tmp_awal
                ], check=True)

                # potong akhir
                start_akhir = durasi_tepi + durasi_potong
                subprocess.run([
                    "ffmpeg", "-y", "-ss", str(start_akhir),
                    "-i", video,
                    "-map", "0", "-c", "copy",
                    tmp_akhir
                ], check=True)

                # concat
                with open(concat_list, "w") as f:
                    f.write(f"file '{tmp_awal}'\n")
                    f.write(f"file '{tmp_akhir}'\n")

                subprocess.run([
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", concat_list,
                    "-c", "copy",
                    output
                ], check=True)

                # cleanup
                for f in (tmp_awal, tmp_akhir, concat_list):
                    if os.path.exists(f):
                        os.remove(f)

            # subprocess.run(cmd, check=True)
            messagebox.showinfo("Sukses", f"Video hasil uji tersimpan:\n{output}")

        except Exception as e:
            messagebox.showerror("Error", f"Gagal uji pemotongan:\n{e}")

    ttk.Button(frame_cut, text="Jalankan Uji Pemotongan", command=jalankan_uji_potong)\
        .grid(row=2, column=0, columnspan=3, pady=5)

    # ==============================
    # FRAME 3: UJI KOMPRESI LOSSY
    # ==============================
    frame_compress = ttk.LabelFrame(parent, text="Uji Kompresi Lossy", padding=10)
    frame_compress.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

    ttk.Label(frame_compress, text="Codec:").grid(row=0, column=0, sticky="w")

    gui_instance.compress_codec_var = tk.StringVar(value="H.264")
    ttk.Combobox(
        frame_compress,
        textvariable=gui_instance.compress_codec_var,
        state="readonly",
        values=["H.264", "VP9"]
    ).grid(row=0, column=1, sticky="w", padx=5)

    ttk.Label(frame_compress, text="CRF:").grid(row=1, column=0, sticky="w")
    gui_instance.compress_crf_var = tk.IntVar(value=23)
    ttk.Entry(frame_compress, textvariable=gui_instance.compress_crf_var, width=10)\
        .grid(row=1, column=1, sticky="w", padx=5)

    def jalankan_uji_kompresi():
        video = gui_instance.uji_video_path_var.get()
        if not video:
            messagebox.showerror("Error", "Pilih video stego terlebih dahulu")
            return

        codec = gui_instance.compress_codec_var.get()
        crf = gui_instance.compress_crf_var.get()

        if codec == "H.264":
            output = f"stego_video_h264{crf}.mp4"
            cmd = ["ffmpeg", "-y", "-i", video, "-c:v", "libx264", "-crf", str(crf), output]

        else:  # VP9
            output = f"stego_video_vp9{crf}.webm"
            cmd = [
                "ffmpeg", "-y", "-i", video,
                "-c:v", "libvpx-vp9", "-crf", str(crf), "-b:v", "0", output
            ]

        try:
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Sukses", f"Video hasil kompresi:\n{output}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal kompresi:\n{e}")

    ttk.Button(frame_compress, text="Jalankan Uji Kompresi", command=jalankan_uji_kompresi)\
        .grid(row=2, column=0, columnspan=3, pady=5)
