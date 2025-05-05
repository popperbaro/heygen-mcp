import json
import os
import tkinter as tk
from tkinter import messagebox

CONFIG_FILE = "heygen_config.json"
AVATAR_CACHE_FILE = "avatar_list_cache.json"

def save_config(config_data, log_callback):
    """Lưu dữ liệu cấu hình vào file JSON."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)
        log_callback(f"Đã lưu cấu hình vào {CONFIG_FILE}")
        # messagebox.showinfo("Thành công", "Đã lưu cấu hình thành công!") # Thông báo này nên ở lớp GUI
        return True
    except Exception as e:
        log_callback(f"Lỗi lưu cấu hình: {e}")
        messagebox.showerror("Lỗi", f"Không thể lưu cấu hình: {e}")
        return False

def load_config(log_callback):
    """Tải dữ liệu cấu hình từ file JSON."""
    default_config = {
        "api_keys": [""] * 5,
        "avatar_id": "Conrad_standing_house_front",
        "output_dir": os.getcwd(),
        "proxy": {"http": "", "https": ""},
        "window_geometry": "850x900+100+100" # widthxheight+x_offset+y_offset
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            log_callback(f"Đang tải cấu hình từ {CONFIG_FILE}...")
            loaded_config = default_config.copy()
            loaded_config.update(config)
            loaded_config["api_keys"] = loaded_config.get("api_keys", [""] * 5)[:5]
            while len(loaded_config["api_keys"]) < 5:
                loaded_config["api_keys"].append("")
            loaded_config["proxy"] = loaded_config.get("proxy", {"http": "", "https": ""})
            loaded_config["window_geometry"] = str(loaded_config.get("window_geometry", default_config["window_geometry"]))
            log_callback(f"Đã tải cấu hình thành công từ {CONFIG_FILE}")
            return loaded_config
        else:
            log_callback(f"Không tìm thấy file cấu hình ({CONFIG_FILE}). Sử dụng cài đặt mặc định.")
            return default_config
    except json.JSONDecodeError as e:
        log_callback(f"Lỗi đọc file cấu hình {CONFIG_FILE}: {e}. File có thể bị lỗi. Sử dụng cài đặt mặc định.")
        messagebox.showerror("Lỗi Cấu hình", f"Không thể đọc file cấu hình: {e}. Sử dụng cài đặt mặc định.")
        return default_config
    except Exception as e:
        log_callback(f"Lỗi không xác định khi tải cấu hình: {e}. Sử dụng cài đặt mặc định.")
        messagebox.showerror("Lỗi Cấu hình", f"Không thể tải cấu hình: {e}. Sử dụng cài đặt mặc định.")
        return default_config

# --- Avatar Cache Functions ---
def save_avatar_cache(id_list, log_callback):
    """Lưu danh sách avatar ID vào file cache."""
    try:
        with open(AVATAR_CACHE_FILE, "w") as f:
            json.dump(id_list, f, indent=2) # Lưu list trực tiếp
        log_callback(f"Đã lưu cache danh sách avatar vào {AVATAR_CACHE_FILE}")
        return True
    except Exception as e:
        log_callback(f"Lỗi lưu cache avatar: {e}")
        # Không cần messagebox ở đây
        return False

def load_avatar_cache(log_callback):
    """Tải danh sách avatar ID từ file cache."""
    if not os.path.exists(AVATAR_CACHE_FILE):
        log_callback(f"Không tìm thấy file cache avatar ({AVATAR_CACHE_FILE}).")
        return None # Trả về None nếu file không tồn tại

    try:
        with open(AVATAR_CACHE_FILE, "r") as f:
            id_list = json.load(f)
        if isinstance(id_list, list):
            log_callback(f"Đã tải thành công {len(id_list)} ID từ cache {AVATAR_CACHE_FILE}")
            return id_list
        else:
            log_callback(f"Lỗi: Dữ liệu trong cache avatar ({AVATAR_CACHE_FILE}) không phải là danh sách.")
            os.remove(AVATAR_CACHE_FILE) # Xóa file cache lỗi
            return None
    except json.JSONDecodeError as e:
        log_callback(f"Lỗi đọc file cache avatar ({AVATAR_CACHE_FILE}): {e}. File có thể bị lỗi.")
        os.remove(AVATAR_CACHE_FILE) # Xóa file cache lỗi
        return None
    except Exception as e:
        log_callback(f"Lỗi không xác định khi tải cache avatar: {e}")
        return None 