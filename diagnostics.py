# diagnostics.py

def run_import_test():
    print("Test importów:")
    try:
        import cv2, numpy, matplotlib, pandas, tkinter
        print("  OK – wszystkie moduły zaimportowane.")
    except Exception as e:
        print("  Błąd importu:", e)

def run_tkinter_test():
    import tkinter as tk
    print("Test Tkinter:")
    try:
        root = tk.Tk()
        root.title("Test Tkinter")
        label = tk.Label(root, text="Tkinter działa poprawnie!")
        label.pack(padx=20, pady=20)
        root.after(2000, root.destroy)
        root.mainloop()
        print("  OK – Tkinter działa.")
    except Exception as e:
        print("  Błąd Tkinter:", e)

def run_diagnostic_tests():
    run_import_test()
    run_tkinter_test()
    print("Testy diagnostyczne zakończone.\n")
