import os
import subprocess

def write_fragments_list(fragment_list, list_file_path):
    """
    Zapisuje plik listy fragmentów w formacie wymaganym przez ffmpeg:
      file 'pełna/ścieżka/do/fragmentu.mp4'
    Jeżeli fragment_list jest pusta, funkcja zwraca False.
    """
    if not fragment_list:
        print("Brak fragmentów do połączenia.")
        return False

    with open(list_file_path, "w", encoding="utf-8") as f:
        for frag in fragment_list:
            full_path = os.path.abspath(frag)  # uzyskujemy pełną ścieżkę
            line = f"file '{full_path}'\n"
            f.write(line)
    return True

def merge_fragments(fragment_list, out_dir):
    """
    Łączy fragmenty wideo przy użyciu ffmpeg.
    Jeśli fragment_list jest pusta, zwraca None.
    Jeśli zawiera tylko jeden fragment, zwraca ten fragment bez łączenia.
    W przeciwnym razie tworzy plik merged_filename i zwraca jego ścieżkę.
    """
    if not fragment_list:
        print("Brak fragmentów do łączenia – zwracam None.")
        return None

    if len(fragment_list) == 1:
        print("Tylko jeden fragment – łączenie nie jest potrzebne.")
        return fragment_list[0]

    list_file = os.path.join(out_dir, "fragments_list.txt")
    if not write_fragments_list(fragment_list, list_file):
        print("Nie udało się zapisać pliku listy fragmentów.")
        return None

    merged_filename = os.path.join(out_dir, "Wszystkie_polaczone_fragmenty.mp4")
    cmd_merge = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        merged_filename,
        "-y"
    ]
    try:
        print("Łączenie fragmentów przy użyciu ffmpeg...")
        subprocess.run(cmd_merge, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Fragmenty zostały połączone w: {merged_filename}")
        return merged_filename
    except subprocess.CalledProcessError as e:
        print("Błąd podczas łączenia fragmentów:", e.stderr.decode())
        return None

if __name__ == "__main__":
    # Przykładowa lista fragmentów; zmodyfikuj te ścieżki do plików, które masz na dysku
    fragment_list = [
        r"testowy000\fragment_testowy000_20250515_195701_1.mp4",
        r"testowy000\fragment_testowy000_20250515_195701_2.mp4",
        r"testowy000\fragment_testowy000_20250515_195701_3.mp4",
        r"testowy000\fragment_testowy000_20250515_195701_4.mp4",
        r"testowy000\fragment_testowy000_20250515_195701_5.mp4",
        r"testowy000\fragment_testowy000_20250515_195701_6.mp4",
        r"testowy000\fragment_testowy000_20250515_195701_7.mp4",
        r"testowy000\fragment_testowy000_20250515_195701_8.mp4",
        r"testowy000\fragment_testowy000_20250515_195701_9.mp4"
    ]
    
    # Przykłady użycia:
    output_dir = os.path.abspath("testowy000")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("Przypadek 1: Pusta lista fragmentów")
    merged = merge_fragments([], output_dir)
    print("Wynik:", merged)
    
    print("\nPrzypadek 2: Jeden fragment")
    merged = merge_fragments([fragment_list[0]], output_dir)
    print("Wynik:", merged)
    
    print("\nPrzypadek 3: Kilka fragmentów (jeśli pliki istnieją)")
    merged = merge_fragments(fragment_list, output_dir)
    print("Wynik:", merged)
