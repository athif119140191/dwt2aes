import tkinter as tk
from gui.gui_main import EncryptGUI

def main():
    """Fungsi utama untuk menjalankan aplikasi GUI."""
    root = tk.Tk()
    app = EncryptGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()