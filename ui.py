# ui.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from video_processing import analyze_video

class AnalizatorRuchuUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizator ruchu 2025, Autor: Paweł")
        self.root.geometry("1000x750")
        self.root.configure(bg="#E6E6FA")
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Ramka wyboru plików
        files_frame = ttk.LabelFrame(main_frame, text="Wybór plików", padding="10")
        files_frame.pack(fill=tk.X, pady=5)
        ttk.Label(files_frame, text="Pliki wideo:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.files_entry = ttk.Entry(files_frame, width=80)
        self.files_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(files_frame, text="Przeglądaj", command=self.browse_files).grid(row=0, column=2, padx=5, pady=5)
        
        # Ramka katalogu wyjściowego
        output_frame = ttk.LabelFrame(main_frame, text="Katalog wyjściowy", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        self.output_entry = ttk.Entry(output_frame, width=80)
        self.output_entry.grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(output_frame, text="Przeglądaj", command=self.browse_output).grid(row=0, column=1, padx=5, pady=5)
        
        # Ramka parametrów analizy
        params_frame = ttk.LabelFrame(main_frame, text="Parametry analizy", padding="10")
        params_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(params_frame, text="ROI - Górna krawędź (%):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.roi_top_entry = ttk.Spinbox(params_frame, from_=0, to=100)
        self.roi_top_entry.set(10)
        self.roi_top_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(params_frame, text="ROI - Dolna krawędź (%):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.roi_bottom_entry = ttk.Spinbox(params_frame, from_=0, to=100)
        self.roi_bottom_entry.set(90)
        self.roi_bottom_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(params_frame, text="Sekundy przed ruchem:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.sec_before_entry = ttk.Spinbox(params_frame, from_=0, to=60, increment=0.5)
        self.sec_before_entry.set(5)
        self.sec_before_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(params_frame, text="Sekundy po ruchu:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.sec_after_entry = ttk.Spinbox(params_frame, from_=0, to=60, increment=0.5)
        self.sec_after_entry.set(5)
        self.sec_after_entry.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(params_frame, text="Próg wykrywania ruchu:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.motion_thresh_entry = ttk.Spinbox(params_frame, from_=0.1, to=50, increment=0.5)
        self.motion_thresh_entry.set(20)
        self.motion_thresh_entry.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(params_frame, text="Intensywność filtru migotania:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.flicker_intensity_entry = ttk.Spinbox(params_frame, from_=0, to=10, increment=0.1)
        self.flicker_intensity_entry.set(2)
        self.flicker_intensity_entry.grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(params_frame, text="Łącz fragmenty, (przerwa < sekundy):").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.merge_gap_entry = ttk.Spinbox(params_frame, from_=0, to=60, increment=0.5)
        self.merge_gap_entry.set(5)
        self.merge_gap_entry.grid(row=6, column=1, padx=5, pady=5)
        
        # Nowe parametry: czas wyświetlania oraz skala wyświetlania wykrytego ruchu
        ttk.Label(params_frame, text="Czas wyświetlania ruchu (s):").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.motion_display_time_entry = ttk.Spinbox(params_frame, from_=0, to=10, increment=0.5)
        self.motion_display_time_entry.set(2)
        self.motion_display_time_entry.grid(row=7, column=1, padx=5, pady=5)
        
        ttk.Label(params_frame, text="Skala wyświetlania ruchu:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=5)
        self.motion_display_scale_entry = ttk.Spinbox(params_frame, from_=0.1, to=1.0, increment=0.1)
        self.motion_display_scale_entry.set(0.5)
        self.motion_display_scale_entry.grid(row=8, column=1, padx=5, pady=5)
        
        # Opcje dodatkowe
        options_frame = ttk.LabelFrame(main_frame, text="Opcje dodatkowe", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        self.show_motion_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Wyświetlaj wykryte ruchy", variable=self.show_motion_var).grid(row=0, column=0, padx=5, pady=5)
        self.merge_fragments_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Połącz fragmenty", variable=self.merge_fragments_var).grid(row=0, column=1, padx=5, pady=5)
        
        # Przyciski sterowania
        control_frame = ttk.Frame(main_frame, padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Rozpocznij analizę", command=self.start_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Zatrzymaj analizę", command=self.stop_analysis).pack(side=tk.LEFT, padx=5)
    
    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="Wybierz pliki wideo",
            filetypes=[("Pliki wideo", "*.mp4 *.avi *.mov *.dav"), ("Wszystkie pliki", "*.*")]
        )
        if files:
            self.files_entry.delete(0, tk.END)
            self.files_entry.insert(0, "; ".join(files))
            self.video_files = list(files)
    
    def browse_output(self):
        directory = filedialog.askdirectory(title="Wybierz katalog wyjściowy")
        if directory:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
    
    def start_analysis(self):
        try:
            output_dir = self.output_entry.get()
            video_files = self.video_files
            params = {
                "roi_top": float(self.roi_top_entry.get()),
                "roi_bottom": float(self.roi_bottom_entry.get()),
                "seconds_before": float(self.sec_before_entry.get()),
                "seconds_after": float(self.sec_after_entry.get()),
                "motion_threshold": float(self.motion_thresh_entry.get()),
                "flicker_filter_intensity": float(self.flicker_intensity_entry.get()),
                "merge_gap_threshold": float(self.merge_gap_entry.get()),
                "show_motion": self.show_motion_var.get(),
                "merge_fragments": self.merge_fragments_var.get(),
                "motion_display_time": float(self.motion_display_time_entry.get()),
                "motion_display_scale": float(self.motion_display_scale_entry.get())
            }
            results = []
            for video in video_files:
                res = analyze_video(video, output_dir, params)
                results.append(res)
            messagebox.showinfo("Sukces", "Analiza zakończona.")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))
    
    def stop_analysis(self):
        messagebox.showinfo("Info", "Funkcja zatrzymania analizy nie została zaimplementowana.")

def main():
    root = tk.Tk()
    app = AnalizatorRuchuUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
