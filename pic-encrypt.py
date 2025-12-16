import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import os

# KONFIGURASI
TOTAL_ROUNDS = 3 
BASE_SEED = 67

# BAGIAN 1: FUNGSI INTI (ALJABAR LINEAR)
def generate_key_matrix(h, w, round_num):
    np.random.seed(BASE_SEED + round_num)
    
    # [Langkah 2a] Matriks Benih (A) ukuran 2x2
    # Kita pakai angka kecil (1-10) agar mirip simulasi manual
    A = np.random.randint(1, 10, (2, 2))
    
    # [Langkah 2b & 2c] Hitung Nilai Eigen (D) dan Vektor Eigen (V)
    # NumPy otomatis menghitung determinan karakteristik di balik layar
    D_vals, V = np.linalg.eig(A)
    
    # [Langkah 2d] Modifikasi (Pangkat 3) dan Rekonstruksi
    # D^3 (Memangkatkan nilai eigen)
    D_power = np.power(D_vals, 3) 
    
    # Matriks Diagonal D
    D_matrix = np.diag(D_power)
    
    # K = V * D^3 * V_inv
    K_block = V @ D_matrix @ np.linalg.inv(V)
    
    # Ambil bagian Real (buang imajiner) dan Modulo 256
    # astype(int) membulatkan angka desimal (misal 85.999 jadi 85)
    K_block = np.real(K_block).astype(int) % 256
    
    # [Langkah 2e] Perluasan Kunci (Tiling)
    # Membuat blok 2x2 secara berulang sampai memenuhi ukuran Citra (Gambar) h x w
    K_full = np.tile(K_block, (int(np.ceil(h/2)), int(np.ceil(w/2))))
    
    return K_full[:h, :w] # Potong sisa ukuran matriks K agar pas dengan ukuran Citra (Gambar) hx w

def get_permutation_indices(h, w, round_num):
    # Membuat Vektor Permutasi Baris & Kolom
    np.random.seed(BASE_SEED + round_num)
    perm_row = np.random.permutation(h)
    perm_col = np.random.permutation(w)
    return perm_row, perm_col

def visualize_permutation_spy_plot(size, seed_val, title_text, round_num):
    # Visualisasi Spy Plot dengan nama file dinamis per ronde.
    np.random.seed(seed_val)
    limit = min(size, 100) # Sampel 100x100
    perm = np.random.permutation(limit)
    
    P_matrix = np.zeros((limit, limit))
    for i in range(limit):
        P_matrix[i, perm[i]] = 1
        
    plt.figure(figsize=(5, 5))
    plt.spy(P_matrix, markersize=2, color='black')
    plt.title(f"{title_text} (Ronde {round_num+1})")
    plt.xlabel("Index Kolom Asal")
    plt.ylabel("Index Baris Tujuan")
    
    # NAMA FILE DINAMIS
    filename = f"Bukti_Permutasi_Ronde_{round_num+1}.png"
    plt.savefig(filename) 
    print(f">> Gambar '{filename}' telah disimpan!")
    
    plt.show()

# BAGIAN 2: PROSES ENKRIPSI
def encrypt_image():
    file_path = filedialog.askopenfilename(title="Pilih Gambar Asli")
    if not file_path: return
    
    img = Image.open(file_path).convert('L')
    I = np.array(img, dtype=int)
    h, w = I.shape
    
    print(f"Memproses Enkripsi {TOTAL_ROUNDS} Putaran...")
    E_current = I.copy()

    for r in range(TOTAL_ROUNDS):
        print(f"\n=== RONDE {r+1} ===")
        
        # 1. Ambil Kunci & Permutasi
        K_full = generate_key_matrix(h, w, r)
        perm_row, perm_col = get_permutation_indices(h, w, r)
        
        if r < 2:    
            print(f"[BUKTI MATEMATIS] Sampel Vektor Permutasi Baris: {perm_row[:10]} ...")
            print(f"[BUKTI MATEMATIS] Sampel Vektor Permutasi Kolom: {perm_col[:10]} ...")
            print(">> Sedang membuat Spy Plot Matriks Permutasi (Cek jendela popup)...")
            visualize_permutation_spy_plot(h, BASE_SEED + r, "Visualisasi Matriks Permutasi Baris (Prow)", r)
        
        # 2. Tahap Difusi (Penjumlahan Matriks)
        E_step1 = (E_current + K_full) % 256
        
        # 3. Tahap Permutasi (Global Permutation)
        E_step2 = E_step1[perm_row, :][:, perm_col]
        
        E_current = E_step2

    # Tampilkan & Simpan Hasil
    show_comparison(I, E_current, "Asli", f"Enkripsi ({TOTAL_ROUNDS} Rounds)", True)
    
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], title="Simpan Hasil")
    if save_path:
        Image.fromarray(E_current.astype(np.uint8)).save(save_path)
        print("File Terenkripsi Disimpan!")

# BAGIAN 3: PROSES DEKRIPSI
def decrypt_image():
    file_path = filedialog.askopenfilename(title="Pilih Gambar Terenkripsi")
    if not file_path: return
    
    img = Image.open(file_path).convert('L')
    E_current = np.array(img, dtype=int)
    h, w = E_current.shape
    
    print(f"Memproses Dekripsi {TOTAL_ROUNDS} Putaran...")

    # LOOPING MUNDUR (5 -> 4 -> ... -> 1)
    for r in range(TOTAL_ROUNDS - 1, -1, -1):
        # 1. Ambil Kunci SAMA dengan saat Enkripsi
        K_full = generate_key_matrix(h, w, r)
        perm_row, perm_col = get_permutation_indices(h, w, r)
        
        # 2. Invers Permutasi
        inv_perm_row = np.argsort(perm_row)
        inv_perm_col = np.argsort(perm_col)
        
        E_unshuffled = E_current[:, inv_perm_col][inv_perm_row, :]
        
        # 3. Invers Difusi
        E_step1 = (E_unshuffled - K_full) % 256
        
        E_current = E_step1 # AKAN MENGEMBALIKAN CITRA I

    show_comparison(img, E_current, "Terenkripsi", "Hasil Dekripsi", False)
    
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], title="Simpan Dekripsi")
    if save_path:
        Image.fromarray(E_current.astype(np.uint8)).save(save_path)
        print("File Dekripsi Disimpan!")

# UTILITY
def show_comparison(img1, img2, t1, t2, show_hist=False):
    if show_hist:
        plt.figure(figsize=(10, 8))
        
        # Gambar
        plt.subplot(2, 2, 1); plt.imshow(img1, cmap='gray', vmin=0, vmax=255); plt.title(t1); plt.axis('off')
        plt.subplot(2, 2, 2); plt.imshow(img2, cmap='gray', vmin=0, vmax=255); plt.title(t2); plt.axis('off')
        
        # Histogram
        plt.subplot(2, 2, 3); plt.hist(img1.ravel(), 256, [0, 256], color='black'); plt.title("Histogram Asli")
        plt.subplot(2, 2, 4); plt.hist(img2.ravel(), 256, [0, 256], color='red'); plt.title("Histogram Enkripsi (Uniform)")
        
    else:
        plt.figure(figsize=(10, 5))
        plt.subplot(1, 2, 1); plt.imshow(img1, cmap='gray', vmin=0, vmax=255); plt.title(t1); plt.axis('off')
        plt.subplot(1, 2, 2); plt.imshow(img2, cmap='gray', vmin=0, vmax=255); plt.title(t2); plt.axis('off')

    plt.tight_layout()
    plt.show()

def main_menu():
    root = tk.Tk(); root.withdraw()
    print("=== PROGRAM ENKRIPSI ALJABAR LINEAR LENGKAP ===")
    print("1. Enkripsi (Generate Bukti Spy Plot & Histogram)")
    print("2. Dekripsi (Kembalikan Gambar)")
    
    pilihan = input("Pilih (1/2): ")
    if pilihan == '1': encrypt_image()
    elif pilihan == '2': decrypt_image()
    else: print("Error.")

if __name__ == "__main__":
    main_menu()