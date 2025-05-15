import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
import pandas as pd

def apply_flicker_filter(frame, intensity=2.0):
    if frame is None or intensity <= 0:
        return frame
    blurred = cv2.GaussianBlur(frame, (0, 0), intensity)
    return cv2.addWeighted(frame, 1.5, blurred, -0.5, 0)

def process_frame(prev_gray, gray, roi_top=0.1, roi_bottom=0.9):
    if prev_gray is None or gray is None:
        return 0
    height = gray.shape[0]
    roi = gray[int(roi_top * height):int(roi_bottom * height), :]
    prev_roi = prev_gray[int(roi_top * height):int(roi_bottom * height), :]
    if prev_roi.shape != roi.shape:
        roi = cv2.resize(roi, (prev_roi.shape[1], prev_roi.shape[0]))
    if len(prev_roi.shape) == 3 and len(roi.shape) == 3:
        prev_roi = cv2.cvtColor(prev_roi, cv2.COLOR_BGR2GRAY)
        roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(prev_roi, roi)
    return np.sum(diff) / diff.size

def is_dav_file(file_path):
    _, ext = os.path.splitext(file_path)
    return ext.lower() == ".dav"

def check_audio(video_file):
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=codec_type", "-of", "default=nw=1:nk=1", video_file
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return bool(result.stdout.strip())
    except Exception as e:
        print(f"Error checking audio: {e}")
        return False

def create_video_capture(video_file):
    if is_dav_file(video_file):
        return process_dav_file(video_file)
    else:
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            return None, None
        return cap, None

def process_dav_file(dav_file):
    try:
        from dav2mp4 import convert_dav_to_mp4
        temp_dir = tempfile.gettempdir()
        base_name = os.path.basename(dav_file)
        mp4_file = os.path.join(temp_dir, f"{os.path.splitext(base_name)[0]}_temp.mp4")
        convert_dav_to_mp4(dav_file, mp4_file)
        cap = cv2.VideoCapture(mp4_file)
        if not cap.isOpened():
            raise Exception(f"Failed to open converted file: {mp4_file}")
        return cap, mp4_file
    except ImportError:
        temp_dir = tempfile.gettempdir()
        base_name = os.path.basename(dav_file)
        mp4_file = os.path.join(temp_dir, f"{os.path.splitext(base_name)[0]}_temp.mp4")
        cmd = ["ffmpeg", "-i", dav_file, "-c:v", "copy", "-c:a", "copy", mp4_file, "-y"]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cap = cv2.VideoCapture(mp4_file)
        if not cap.isOpened():
            raise Exception(f"Failed to open converted file: {mp4_file}")
        return cap, mp4_file

def merge_motion_peaks(peaks, frame_tolerance=5, gap_threshold=5):
    if not peaks:
        return peaks
    peaks.sort(key=lambda x: x["start_frame"])
    merged = []
    current = peaks[0]
    for peak in peaks[1:]:
        time_gap = peak["start_time"] - current.get("end_time", current["max_time"])
        if (peak["start_frame"] <= current["end_frame"] + frame_tolerance) or (time_gap <= gap_threshold):
            if peak.get("end_frame", peak["max_frame"]) > current.get("end_frame", current["max_frame"]):
                current["end_frame"] = peak.get("end_frame", peak["max_frame"])
                current["end_time"] = peak.get("end_time", peak["max_time"])
                current["end_time_str"] = peak.get("end_time_str", peak["max_time_str"])
            if peak["max_score"] > current["max_score"]:
                current["max_score"] = peak["max_score"]
                current["max_frame"] = peak["max_frame"]
                current["max_time"] = peak["max_time"]
                current["max_time_str"] = peak["max_time_str"]
        else:
            merged.append(current)
            current = peak
    merged.append(current)
    return merged

def plot_flicker_trend(flicker_time_list, flicker_list, out_dir):
    if not flicker_time_list:
        return
    plt.figure()
    plt.plot(flicker_time_list, flicker_list, "o", label="Wartość migotania")
    coeffs = np.polyfit(flicker_time_list, flicker_list, 1)
    trend = np.poly1d(coeffs)
    x_trend = np.linspace(min(flicker_time_list), max(flicker_time_list), 100)
    plt.plot(x_trend, trend(x_trend), "r-", label="Trend")
    plt.xlabel("Czas (s)")
    plt.ylabel("Wartość migotania")
    plt.title("Wykres wykrytego migotania")
    plt.legend()
    filename = os.path.join(out_dir, "wykres_wykrytego_migotania.png")
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()

def generate_spatial_analysis_image(accum, out_dir, base_name, timestamp, frame_size):
    norm = cv2.normalize(accum, None, 0, 1.0, cv2.NORM_MINMAX)
    height, width = norm.shape
    spatial_img = np.zeros((height, width, 3), dtype=np.uint8)
    violet_palette = [
        (230, 190, 250),
        (200, 150, 220),
        (170, 110, 190),
        (140, 70, 160),
        (110, 30, 130)
    ]
    blue_color = (255, 0, 0)
    cell_size = 10
    for y in range(0, height, cell_size):
        for x in range(0, width, cell_size):
            cell = norm[y:min(y+cell_size, height), x:min(x+cell_size, width)]
            avg = np.mean(cell)
            if avg < 0.1:
                color = blue_color
            else:
                idx = int(min(4, (avg - 0.1) / (0.9/5)))
                color = violet_palette[idx]
            cv2.rectangle(spatial_img, (x, y), (x+cell_size-1, y+cell_size-1), color, -1)
    legend_height = int(0.2 * height)
    final_img = np.full((height+legend_height, width, 3), 255, dtype=np.uint8)
    final_img[0:height, 0:width] = spatial_img
    legend_texts = [
        ("Brak ruchu", blue_color),
        ("Niski ruch", violet_palette[0]),
        ("Umiarkowany ruch", violet_palette[2]),
        ("Wysoki ruch", violet_palette[4])
    ]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    y0 = height + 10
    for i, (text, color) in enumerate(legend_texts):
        cv2.putText(final_img, text, (10, y0 + i*20), font, font_scale, color, thickness, cv2.LINE_AA)
    spatial_filename = os.path.join(out_dir, f"analiza_przestrzenna_{base_name}_{timestamp}.png")
    cv2.imwrite(spatial_filename, final_img)

def generate_krawedz_screenshots(cap, out_dir, base_name, timestamp, roi_top_percent, roi_bottom_percent):
    krawedz_dir = os.path.join(out_dir, "Krawedz")
    if not os.path.exists(krawedz_dir):
        os.makedirs(krawedz_dir)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = [0, total_frames-1, total_frames//4, total_frames//2, (3*total_frames)//4]
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            height = frame.shape[0]
            roi_top = int((roi_top_percent/100)*height)
            roi_bottom = int((roi_bottom_percent/100)*height)
            cv2.line(frame, (0, roi_top), (frame.shape[1], roi_top), (0,0,255), 2)
            cv2.line(frame, (0, roi_bottom), (frame.shape[1], roi_bottom), (0,0,255), 2)
            screenshot_filename = os.path.join(krawedz_dir, f"screenshot_{base_name}_{timestamp}_{idx}.png")
            cv2.imwrite(screenshot_filename, frame)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

def extract_fragments(motion_peaks, fps, frame_size, base_name, timestamp, out_dir, video_source, video_duration):
    if not motion_peaks:
        return []
    all_fragments = []
    for i, peak in enumerate(motion_peaks, 1):
        start_time = peak["start_time"]
        end_time = peak["end_time"]
        cmd = ["ffmpeg", "-i", video_source]
        if start_time > 0:
            cmd += ["-ss", str(start_time)]
        if end_time < video_duration:
            cmd += ["-to", str(end_time)]
        fragment_filename = os.path.join(out_dir, f"fragment_{base_name}_{timestamp}_{i}.mp4")
        cmd += ["-c:v", "copy", "-c:a", "copy", fragment_filename, "-y"]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            all_fragments.append(fragment_filename)
        except subprocess.CalledProcessError as e:
            print(f"Error extracting fragment {i}: {e.stderr.decode()}")
    return all_fragments

def merge_fragments(fragment_list, out_dir):
    merged_filename = os.path.join(out_dir, "Wszystkie_polaczone_fragmenty.mp4")
    list_file = os.path.join(out_dir, "fragments_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for frag in fragment_list:
            full_path = os.path.abspath(frag)
            f.write(f"file '{full_path}'\n")
    cmd_merge = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        merged_filename,
        "-y"
    ]
    subprocess.run(cmd_merge, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return merged_filename

def analyze_video(video_file, output_dir, params):
    cap, temp_file = create_video_capture(video_file)
    if cap is None:
        raise Exception(f"Nie udało się otworzyć pliku: {video_file}")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    video_duration = frame_count / fps
    frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    out_dir = os.path.join(output_dir, base_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    output_filename = os.path.join(out_dir, f"analiza_ruchu_{base_name}_{timestamp}.csv")
    peak_filename = os.path.join(out_dir, f"szczytowe_momenty_{base_name}_{timestamp}.txt")
    plot_filename = os.path.join(out_dir, f"wykres_ruchu_{base_name}_{timestamp}.png")
    
    spatial_accum = np.zeros(frame_size[::-1], dtype=np.float32)
    flicker_list, flicker_time_list, motion_list = [], [], []
    frame_indices, motion_scores, time_points, motion_peaks = [], [], [], []
    frame_idx = 0
    threshold = params["motion_threshold"]
    seconds_before = params["seconds_before"]
    seconds_after = params["seconds_after"]
    current_peak = None
    
    ret, frame = cap.read()
    if not ret or frame is None:
        cap.release()
        raise Exception(f"Nie udało się odczytać pierwszej klatki z {video_file}")
    frame = apply_flicker_filter(frame, params["flicker_filter_intensity"])
    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        time_sec = frame_idx / fps
        time_str = str(timedelta(seconds=int(time_sec)))
        filtered_frame = apply_flicker_filter(frame, params["flicker_filter_intensity"])
        gray = cv2.cvtColor(filtered_frame, cv2.COLOR_BGR2GRAY)
        spatial_accum += cv2.absdiff(prev_gray, gray).astype(np.float32)
        motion_score = process_frame(prev_gray, gray, roi_top=params["roi_top"]/100, roi_bottom=params["roi_bottom"]/100)
        frame_indices.append(frame_idx)
        time_points.append(timedelta(seconds=int(time_sec)))
        motion_scores.append(motion_score)
        
        if motion_score <= threshold:
            flicker_list.append(motion_score)
            flicker_time_list.append(time_sec)
        else:
            motion_list.append(motion_score)
        
        if motion_score > threshold:
            if current_peak is None:
                start_time_sec = 0 if time_sec <= seconds_before else time_sec - seconds_before
                start_frame = 0 if time_sec <= seconds_before else frame_idx - int(seconds_before * fps)
                current_peak = {"start_frame": start_frame,
                                "start_time": start_time_sec,
                                "start_time_str": str(timedelta(seconds=int(start_time_sec))),
                                "max_score": motion_score,
                                "max_frame": frame_idx,
                                "max_time": time_sec,
                                "max_time_str": str(timedelta(seconds=int(time_sec)))}
                if params["show_motion"]:
                    scale = params.get("motion_display_scale", 0.5)
                    display_time_ms = int(params.get("motion_display_time", 2) * 1000)
                    small_frame = cv2.resize(frame, None, fx=scale, fy=scale)
                    cv2.imshow("Wykryty ruch", small_frame)
                    cv2.waitKey(display_time_ms)
                    cv2.destroyWindow("Wykryty ruch")
            elif motion_score > current_peak["max_score"]:
                current_peak["max_score"] = motion_score
                current_peak["max_frame"] = frame_idx
                current_peak["max_time"] = time_sec
                current_peak["max_time_str"] = str(timedelta(seconds=int(time_sec)))
        elif current_peak is not None and motion_score <= threshold:
            end_time_sec = time_sec + seconds_after
            if end_time_sec > video_duration:
                end_time_sec = video_duration
            current_peak["end_frame"] = frame_idx + int(seconds_after * fps)
            current_peak["end_time"] = end_time_sec
            current_peak["end_time_str"] = str(timedelta(seconds=int(end_time_sec)))
            motion_peaks.append(current_peak)
            current_peak = None
        prev_gray = gray
    if current_peak is not None:
        end_time_sec = time_sec + seconds_after
        if end_time_sec > video_duration:
            end_time_sec = video_duration
        current_peak["end_frame"] = frame_idx + int(seconds_after * fps)
        current_peak["end_time"] = end_time_sec
        current_peak["end_time_str"] = str(timedelta(seconds=int(end_time_sec)))
        motion_peaks.append(current_peak)
    cap.release()
    
    merged_peaks = merge_motion_peaks(motion_peaks, frame_tolerance=5, gap_threshold=params["merge_gap_threshold"])
    
    with open(peak_filename, "w", encoding="utf-8") as f:
        if not merged_peaks:
            f.write("Nie wykryto znaczącego ruchu.\n")
        else:
            for i, peak in enumerate(merged_peaks, 1):
                f.write(f"Fragment {i}:\n")
                f.write(f"  Początek: {peak['start_time_str']} (klatka {peak['start_frame']})\n")
                f.write(f"  Koniec: {peak['end_time_str']} (klatka {peak['end_frame']})\n")
                f.write(f"  Szczyt: {peak['max_time_str']} (klatka {peak['max_frame']}, wynik: {peak['max_score']:.4f})\n\n")
    
    plot_flicker_trend(flicker_time_list, flicker_list, out_dir)
    generate_spatial_analysis_image(spatial_accum, out_dir, base_name, timestamp, frame_size)
    cap0, _ = create_video_capture(video_file)
    generate_krawedz_screenshots(cap0, out_dir, base_name, timestamp, params["roi_top"], params["roi_bottom"])
    fragments = extract_fragments(merged_peaks, fps, frame_size, base_name, timestamp, out_dir, video_file, video_duration)
    merged_file = None
    if params["merge_fragments"] and fragments:
        merged_file = merge_fragments(fragments, out_dir)
    
    return {
        "output_csv": output_filename,
        "peaks_txt": peak_filename,
        "motion_plot": plot_filename,
        "merged_file": merged_file
    }
