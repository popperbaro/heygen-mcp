import sys
import os
import time
import json
import requests
import traceback
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, StringVar
from typing import Dict, Any, List, Optional, Tuple
import pickle
import re

# Các đường dẫn lưu cấu hình
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".heygen_avatar_creator")
API_KEY_FILE = os.path.join(CONFIG_DIR, "api_key.txt")
AVATARS_CACHE_FILE = os.path.join(CONFIG_DIR, "avatars_cache.pkl")
WINDOW_CONFIG_FILE = os.path.join(CONFIG_DIR, "window_config.json")
SELECTED_AVATAR_FILE = os.path.join(CONFIG_DIR, "selected_avatar.txt")
PROXY_CONFIG_FILE = os.path.join(CONFIG_DIR, "proxy_config.json")
DOWNLOAD_DIR_FILE = os.path.join(CONFIG_DIR, "download_dir.txt")
INPUT_DIR_FILE = os.path.join(CONFIG_DIR, "input_dir.txt")

# Đường dẫn mặc định cho thư mục đầu vào
DEFAULT_INPUT_DIR = "G:\\Work\\MMO\\MP3"

# Đảm bảo thư mục cấu hình tồn tại
os.makedirs(CONFIG_DIR, exist_ok=True)

class HeyGenClient:
    """
    Client để tương tác với HeyGen API để tạo video avatar
    """
    
    BASE_URL = "https://api.heygen.com"
    API_KEY = "MDViZWM5N2ZhMTdmNDQzOTk0M2MwNjIzM2Q5ODYwZWMtMTc0NTYwNDEzMw=="
    
    def __init__(self, api_key: Optional[str] = None, proxy_settings: Optional[Dict[str, str]] = None):
        """
        Khởi tạo client với API key và cài đặt proxy
        
        Args:
            api_key: API key của HeyGen, sẽ sử dụng API key mặc định nếu không được cung cấp
            proxy_settings: Cài đặt proxy (địa chỉ, port, username, password)
        """
        self.api_key = api_key or self.API_KEY
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
        
        # Thiết lập proxy
        self.proxy_settings = proxy_settings
        self.proxies = self._setup_proxies(proxy_settings) if proxy_settings else None
    
    def _setup_proxies(self, proxy_settings: Dict[str, str]) -> Dict[str, str]:
        """
        Thiết lập proxy cho requests
        
        Args:
            proxy_settings: Dict chứa thông tin proxy (host, port, username, password)
            
        Returns:
            Dict cấu hình proxies cho thư viện requests
        """
        if not proxy_settings or not proxy_settings.get("host") or not proxy_settings.get("port"):
            return None
            
        host = proxy_settings.get("host")
        port = proxy_settings.get("port")
        username = proxy_settings.get("username")
        password = proxy_settings.get("password")
        
        # Tạo URL proxy
        if username and password:
            proxy_url = f"http://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"http://{host}:{port}"
            
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    
    def update_proxy_settings(self, proxy_settings: Optional[Dict[str, str]]) -> None:
        """
        Cập nhật cài đặt proxy
        
        Args:
            proxy_settings: Dict chứa thông tin proxy (host, port, username, password)
        """
        self.proxy_settings = proxy_settings
        self.proxies = self._setup_proxies(proxy_settings) if proxy_settings else None
        
    def test_connection(self) -> Tuple[bool, str]:
        """
        Kiểm tra kết nối thông qua proxy
        
        Returns:
            Tuple gồm (success, message) - success là bool, message là thông báo lỗi/thành công
        """
        try:
            url = f"{self.BASE_URL}/v2/avatars"
            response = requests.get(
                url, 
                headers=self.headers, 
                proxies=self.proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Kết nối thành công"
            else:
                return False, f"Lỗi kết nối: HTTP {response.status_code}"
        except requests.exceptions.ProxyError as e:
            return False, f"Lỗi proxy: {str(e)}"
        except requests.exceptions.ConnectTimeout:
            return False, f"Kết nối tới proxy bị timeout"
        except requests.exceptions.ConnectionError as e:
            return False, f"Lỗi kết nối: {str(e)}"
        except Exception as e:
            return False, f"Lỗi không xác định: {str(e)}"
    
    def get_all_avatars(self) -> Dict[str, Any]:
        """
        Lấy danh sách tất cả avatars có sẵn
        
        Returns:
            Dict chứa thông tin về tất cả avatars
        """
        url = f"{self.BASE_URL}/v2/avatars"
        try:
            response = requests.get(url, headers=self.headers, proxies=self.proxies)
            
            # Kiểm tra mã trạng thái cụ thể
            if response.status_code == 401:
                print(f"Lỗi xác thực API (401 Unauthorized). Kiểm tra lại API key của bạn.")
                return {"error": "Lỗi xác thực API (401 Unauthorized). Kiểm tra lại API key của bạn."}
            elif response.status_code == 403:
                print(f"Lỗi quyền truy cập API (403 Forbidden). API key không có quyền truy cập endpoint này.")
                return {"error": "Lỗi quyền truy cập API (403 Forbidden). API key không có quyền truy cập endpoint này."}
            
            # Sử dụng raise_for_status để xử lý các lỗi HTTP khác
            response.raise_for_status()
            
            # In ra response.text để debug
            print(f"API Response: {response.text[:200]}...") # Chỉ hiển thị 200 ký tự đầu tiên
            
            # Kiểm tra nếu response trống
            if not response.text:
                print("API trả về response trống")
                return {"error": "API trả về response trống"}
            
            # Phân tích JSON
            json_data = response.json()
            
            # Kiểm tra cấu trúc dữ liệu trả về để tránh lỗi "None"
            if "data" in json_data and "avatars" in json_data["data"]:
                print(f"Tìm thấy {len(json_data['data']['avatars'])} avatars")
                return json_data
            else:
                print(f"Không tìm thấy danh sách avatars trong phản hồi: {json_data}")
                return {"error": "Không tìm thấy danh sách avatars trong phản hồi"}
                
        except requests.exceptions.HTTPError as e:
            print(f"Lỗi HTTP khi lấy danh sách avatars: {e}")
            print(f"Response text: {getattr(e.response, 'text', 'N/A')}")
            return {"error": f"Lỗi HTTP: {str(e)}"}
        except requests.exceptions.ProxyError as e:
            print(f"Lỗi proxy khi lấy danh sách avatars: {e}")
            return {"error": f"Lỗi proxy: {str(e)}"}
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối khi lấy danh sách avatars: {e}")
            return {"error": f"Lỗi kết nối: {str(e)}"}
        except json.JSONDecodeError as e:
            print(f"Lỗi phân tích JSON: {e}")
            print(f"Response text: {response.text[:200]}...") # Chỉ hiển thị 200 ký tự đầu tiên
            return {"error": f"Lỗi phân tích JSON: {str(e)}"}
        except Exception as e:
            print(f"Lỗi không xác định khi lấy danh sách avatars: {e}")
            return {"error": str(e)}
    
    def upload_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Upload file âm thanh lên HeyGen để tạo audio asset
        
        Args:
            file_path: Đường dẫn đến file âm thanh cần upload
            
        Returns:
            Dict chứa thông tin về asset được tạo
        """
        url = f"{self.BASE_URL}/v1/upload"
        
        try:
            # Chuẩn bị multipart form data
            files = {
                'file': (os.path.basename(file_path), open(file_path, 'rb'), 'audio/mpeg')
            }
            
            headers = {
                "x-api-key": self.api_key
            }
            
            response = requests.post(url, files=files, headers=headers, proxies=self.proxies)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Lỗi khi upload file âm thanh: {e}")
            return {"error": str(e)}
    
    def create_avatar_video(self, 
                           avatar_id: str, 
                           audio_url: Optional[str] = None,
                           audio_asset_id: Optional[str] = None,
                           avatar_style: str = "normal",
                           background_color: str = "#f6f6fc",
                           width: int = 1280,
                           height: int = 720,
                           caption: bool = False) -> Dict[str, Any]:
        """
        Tạo video avatar với file âm thanh tùy chỉnh
        
        Args:
            avatar_id: ID của avatar muốn sử dụng
            audio_url: URL của file âm thanh (tùy chọn)
            audio_asset_id: ID của asset âm thanh đã tải lên (tùy chọn)
            avatar_style: Kiểu của avatar (mặc định: "normal")
            background_color: Màu nền dạng hex (mặc định: "#f6f6fc")
            width: Chiều rộng video (mặc định: 1280)
            height: Chiều cao video (mặc định: 720)
            caption: Bật/tắt phụ đề (mặc định: False)
            
        Returns:
            Dict chứa thông tin về video được tạo
        """
        if not audio_url and not audio_asset_id:
            raise ValueError("Phải cung cấp audio_url hoặc audio_asset_id")
        
        url = f"{self.BASE_URL}/v2/video/generate"
        
        # Cấu hình voice settings
        voice_settings = {
            "type": "audio"
        }
        
        if audio_url:
            voice_settings["audio_url"] = audio_url
        if audio_asset_id:
            voice_settings["audio_asset_id"] = audio_asset_id
        
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": avatar_style
                    },
                    "voice": voice_settings,
                    "background": {
                        "type": "color",
                        "value": background_color
                    }
                }
            ],
            "dimension": {
                "width": width,
                "height": height
            },
            "caption": caption
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, proxies=self.proxies)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Lỗi khi tạo video: {e}")
            return {"error": str(e)}
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái của video
        
        Args:
            video_id: ID của video cần kiểm tra
            
        Returns:
            Dict chứa thông tin về trạng thái video
        """
        url = f"{self.BASE_URL}/v1/video_status.get?video_id={video_id}"
        try:
            response = requests.get(url, headers=self.headers, proxies=self.proxies)
            response.raise_for_status()
            # Xử lý lỗi JSON decode
            try:
                return response.json()
            except json.JSONDecodeError:
                # Trả về dict mặc định nếu không phân tích được JSON
                print(f"Lỗi decode JSON. Response text: {response.text}")
                return {"error": "JSONDecodeError", "status_code": response.status_code, "text": response.text}
        except Exception as e:
            print(f"Lỗi khi kiểm tra trạng thái video: {e}")
            return {"error": str(e)}
    
    def get_all_videos(self, limit=100) -> Dict[str, Any]:
        """
        Lấy danh sách tất cả video của người dùng
        
        Args:
            limit: Số lượng video tối đa muốn lấy, mặc định là 100
            
        Returns:
            Dict chứa thông tin về tất cả video
        """
        url = f"{self.BASE_URL}/v1/video.list"
        if limit is not None:
            url += f"?limit={limit}"
            
        try:
            response = requests.get(url, headers=self.headers, proxies=self.proxies)
            response.raise_for_status()
            
            # Xử lý lỗi JSON decode
            try:
                return response.json()
            except json.JSONDecodeError:
                print(f"Lỗi decode JSON. Response text: {response.text}")
                return {"error": "JSONDecodeError", "status_code": response.status_code, "text": response.text}
        except Exception as e:
            print(f"Lỗi khi lấy danh sách video: {e}")
            return {"error": str(e)}
    
    def get_remaining_quota(self) -> Dict[str, Any]:
        """
        Lấy thông tin về số token còn lại của người dùng
        
        Returns:
            Dict chứa thông tin về quota còn lại
        """
        url = f"{self.BASE_URL}/v2/user/remaining_quota"
        try:
            response = requests.get(url, headers=self.headers, proxies=self.proxies)
            
            # Kiểm tra mã trạng thái cụ thể
            if response.status_code == 401:
                print(f"Lỗi xác thực API (401 Unauthorized). Kiểm tra lại API key của bạn.")
                return {"error": "Lỗi xác thực API (401 Unauthorized)."}
            elif response.status_code == 403:
                print(f"Lỗi quyền truy cập API (403 Forbidden).")
                return {"error": "Lỗi quyền truy cập API (403 Forbidden)."}
            
            # Sử dụng raise_for_status để xử lý các lỗi HTTP khác
            response.raise_for_status()
            
            # Phân tích JSON
            json_data = response.json()
            print(f"Phản hồi quota: {json.dumps(json_data)}")
            
            return json_data
                
        except requests.exceptions.HTTPError as e:
            print(f"Lỗi HTTP khi lấy thông tin quota: {e}")
            return {"error": f"Lỗi HTTP: {str(e)}"}
        except requests.exceptions.ProxyError as e:
            print(f"Lỗi proxy khi lấy thông tin quota: {e}")
            return {"error": f"Lỗi proxy: {str(e)}"}
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối khi lấy thông tin quota: {e}")
            return {"error": f"Lỗi kết nối: {str(e)}"}
        except json.JSONDecodeError as e:
            print(f"Lỗi phân tích JSON: {e}")
            return {"error": f"Lỗi phân tích JSON: {str(e)}"}
        except Exception as e:
            print(f"Lỗi không xác định khi lấy thông tin quota: {e}")
            return {"error": str(e)}


class HeyGenVideoCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HeyGen Avatar Video Creator")
        
        # Khởi tạo kích thước cửa sổ mặc định
        self.root.geometry("800x950")
        self.root.minsize(800, 600)
        
        # Đọc cấu hình cửa sổ từ lần chạy trước (nếu có)
        self.load_window_config()
        
        # Đọc cấu hình proxy từ file
        self.proxy_settings = self.load_proxy_config()
        
        # Đọc API key từ file (nếu có) và ưu tiên sử dụng
        api_key = self.load_api_key()
        
        # Nếu người dùng đã lưu API key, cũng cập nhật API_KEY mặc định của class HeyGenClient
        if api_key == "MDViZWM5N2ZhMTdmNDQzOTk0M2MwNjIzM2Q5ODYwZWMtMTc0NTYwNDEzMw==":
            HeyGenClient.API_KEY = api_key
        
        # Khởi tạo client với API key từ file và proxy
        self.client = HeyGenClient(api_key, self.proxy_settings)
        self.avatars = []
        
        # Khởi tạo ID avatar được chọn
        self.selected_avatar_id = self.load_selected_avatar()
        self.audio_file_path = None
        self.audio_asset_id = None
        
        # Danh sách các file audio được chọn
        self.audio_file_paths = []
        self.audio_assets = []  # Lưu danh sách các audio asset id đã upload
        self.current_upload_index = 0  # Chỉ số file đang upload
        
        # Khởi tạo thư mục tải về mặc định
        self.download_dir = self.load_download_dir()
        
        # Khởi tạo thư mục đầu vào mặc định
        self.input_dir = self.load_input_dir()
        
        # Biến để theo dõi các video đang được tạo
        self.processing_videos = {}
        
        # Biến cho chức năng tìm kiếm
        self.search_var = StringVar()
        self.search_var.trace_add("write", self.filter_avatars)
        
        # Biến lưu trữ thời gian còn lại
        self.remaining_time_format = None
        
        # Tạo giao diện
        self.create_ui()
        
        # Test proxy khi khởi động
        if self.proxy_settings:
            self.root.after(100, self.test_proxy_connection)
        
        # Đọc cache avatars nếu có
        self.load_avatars_cache()
        
        # Đăng ký sự kiện khi đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_proxy_config(self):
        """Đọc cấu hình proxy từ file nếu có"""
        try:
            if os.path.exists(PROXY_CONFIG_FILE):
                with open(PROXY_CONFIG_FILE, 'r') as f:
                    proxy_config = json.load(f)
                    print(f"Đã tải cấu hình proxy")
                    return proxy_config
        except Exception as e:
            print(f"Lỗi khi đọc cấu hình proxy: {e}")
        return None
    
    def save_proxy_config(self, proxy_settings):
        """Lưu cấu hình proxy vào file"""
        try:
            with open(PROXY_CONFIG_FILE, 'w') as f:
                json.dump(proxy_settings, f)
            print(f"Đã lưu cấu hình proxy")
        except Exception as e:
            print(f"Lỗi khi lưu cấu hình proxy: {e}")
    
    def test_proxy_connection(self, show_success=False):
        """
        Kiểm tra kết nối proxy với API
        
        Args:
            show_success: Có hiển thị thông báo thành công hay không
        """
        if not self.proxy_settings:
            return
            
        self.update_status("Đang kiểm tra kết nối proxy...")
        self.root.update()
        
        # Thử kết nối 3 lần
        success = False
        error_message = ""
        
        for attempt in range(3):
            success, message = self.client.test_connection()
            if success:
                self.update_status(f"Đã kết nối proxy thành công")
                if show_success:
                    messagebox.showinfo("Thành công", "Kết nối proxy thành công!")
                break
            else:
                error_message = message
                self.update_status(f"Thử kết nối proxy lần {attempt+1}/3: Thất bại - {message}")
                time.sleep(1)  # Đợi 1 giây trước khi thử lại
                
        if not success:
            self.update_status(f"Kết nối proxy thất bại sau 3 lần thử: {error_message}")
            if show_success:  # Chỉ hiển thị lỗi nếu người dùng test thủ công
                messagebox.showerror("Lỗi", f"Kết nối proxy thất bại: {error_message}")
    
    def update_proxy_settings(self):
        """Cập nhật cài đặt proxy từ giao diện người dùng"""
        # Lấy giá trị từ form
        host = self.proxy_host_var.get().strip()
        port = self.proxy_port_var.get().strip()
        username = self.proxy_username_var.get().strip()
        password = self.proxy_password_var.get().strip()
        
        # Kiểm tra giá trị bắt buộc
        if not host or not port:
            messagebox.showerror("Lỗi", "Host và Port không được để trống")
            return False
        
        try:
            # Chuyển port sang số nguyên
            port = int(port)
            if port <= 0 or port > 65535:
                raise ValueError("Port phải từ 1-65535")
        except ValueError as e:
            messagebox.showerror("Lỗi", f"Port không hợp lệ: {str(e)}")
            return False
            
        # Tạo dict cấu hình proxy
        proxy_settings = {
            "host": host,
            "port": port
        }
        
        # Thêm username và password nếu có
        if username:
            proxy_settings["username"] = username
        if password:
            proxy_settings["password"] = password
            
        # Cập nhật cài đặt proxy
        self.proxy_settings = proxy_settings
        self.client.update_proxy_settings(proxy_settings)
        
        # Lưu cấu hình vào file
        self.save_proxy_config(proxy_settings)
        
        self.update_status(f"Đã cập nhật cấu hình proxy: {host}:{port}")
        return True
    
    def on_closing(self):
        """Xử lý sự kiện khi đóng cửa sổ"""
        # Lưu cấu hình cửa sổ
        self.save_window_config()
        
        # Lưu API key hiện tại
        api_key = self.api_key_var.get().strip()
        if api_key:
            self.save_api_key(api_key)
        
        # Lưu avatar đã chọn
        if self.selected_avatar_id:
            self.save_selected_avatar(self.selected_avatar_id)
            
        # Lưu thư mục tải về mặc định
        if self.download_dir:
            self.save_download_dir(self.download_dir)
            
        # Lưu thư mục đầu vào mặc định
        if self.input_dir:
            self.save_input_dir(self.input_dir)
            
        self.root.destroy()
    
    def create_ui(self):
        # Tạo frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tạo notebook (tab control)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab tạo video
        create_tab = ttk.Frame(notebook)
        notebook.add(create_tab, text="Tạo Video")
        
        # Tab quản lý video
        manage_tab = ttk.Frame(notebook)
        notebook.add(manage_tab, text="Quản Lý Video")
        
        # Tab cấu hình proxy
        proxy_tab = ttk.Frame(notebook)
        notebook.add(proxy_tab, text="Cấu hình Proxy")
        
        # Nội dung Tab tạo video
        self.create_tab_content(create_tab)
        
        # Nội dung Tab quản lý video
        self.create_manage_tab_content(manage_tab)
        
        # Nội dung Tab cấu hình proxy
        self.create_proxy_tab_content(proxy_tab)
        
    def create_proxy_tab_content(self, parent_frame):
        """Tạo nội dung tab cấu hình proxy"""
        # Frame chính
        proxy_frame = ttk.LabelFrame(parent_frame, text="Cài đặt Proxy", padding="10")
        proxy_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Host
        host_frame = ttk.Frame(proxy_frame)
        host_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(host_frame, text="Host:").pack(side=tk.LEFT, padx=5)
        self.proxy_host_var = tk.StringVar(value=self.proxy_settings.get("host", "") if self.proxy_settings else "")
        ttk.Entry(host_frame, textvariable=self.proxy_host_var, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Port
        port_frame = ttk.Frame(proxy_frame)
        port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        self.proxy_port_var = tk.StringVar(value=str(self.proxy_settings.get("port", "")) if self.proxy_settings else "")
        ttk.Entry(port_frame, textvariable=self.proxy_port_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Username
        username_frame = ttk.Frame(proxy_frame)
        username_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(username_frame, text="Username:").pack(side=tk.LEFT, padx=5)
        self.proxy_username_var = tk.StringVar(value=self.proxy_settings.get("username", "") if self.proxy_settings else "")
        ttk.Entry(username_frame, textvariable=self.proxy_username_var, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Password
        password_frame = ttk.Frame(proxy_frame)
        password_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(password_frame, text="Password:").pack(side=tk.LEFT, padx=5)
        self.proxy_password_var = tk.StringVar(value=self.proxy_settings.get("password", "") if self.proxy_settings else "")
        ttk.Entry(password_frame, textvariable=self.proxy_password_var, width=30, show="*").pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Buttons
        buttons_frame = ttk.Frame(proxy_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Cập nhật", command=self.update_proxy).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Kiểm tra kết nối", command=self.test_proxy).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Xóa proxy", command=self.clear_proxy).pack(side=tk.LEFT, padx=5)
        
        # Trạng thái
        status_frame = ttk.LabelFrame(parent_frame, text="Trạng thái", padding="5")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        proxy_status_var = tk.StringVar(value="Proxy đang " + ("được bật" if self.proxy_settings else "tắt"))
        ttk.Label(status_frame, textvariable=proxy_status_var).pack(anchor=tk.W, padx=5, pady=5)
    
    def update_proxy(self):
        """Cập nhật proxy từ form nhập liệu"""
        if self.update_proxy_settings():
            # Kiểm tra kết nối với proxy mới
            self.test_proxy_connection(show_success=True)
    
    def test_proxy(self):
        """Test kết nối proxy từ giao diện người dùng"""
        # Cập nhật proxy settings trước khi test
        if self.update_proxy_settings():
            self.test_proxy_connection(show_success=True)
    
    def clear_proxy(self):
        """Xóa cấu hình proxy"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa cấu hình proxy không?"):
            self.proxy_settings = None
            self.client.update_proxy_settings(None)
            
            # Xóa file cấu hình nếu tồn tại
            if os.path.exists(PROXY_CONFIG_FILE):
                try:
                    os.remove(PROXY_CONFIG_FILE)
                except Exception as e:
                    print(f"Lỗi khi xóa file cấu hình proxy: {e}")
            
            # Reset các trường form
            self.proxy_host_var.set("")
            self.proxy_port_var.set("")
            self.proxy_username_var.set("")
            self.proxy_password_var.set("")
            
            self.update_status("Đã xóa cấu hình proxy")
    
    def load_api_key(self):
        """Đọc API key từ file nếu có"""
        try:
            if os.path.exists(API_KEY_FILE):
                with open(API_KEY_FILE, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        return api_key
        except Exception as e:
            print(f"Lỗi khi đọc API key: {e}")
        return None
    
    def save_api_key(self, api_key):
        """Lưu API key vào file"""
        try:
            with open(API_KEY_FILE, 'w') as f:
                f.write(api_key)
            print(f"Đã lưu API key")
        except Exception as e:
            print(f"Lỗi khi lưu API key: {e}")
    
    def load_avatars_cache(self):
        """Đọc danh sách avatars từ cache nếu có"""
        try:
            if os.path.exists(AVATARS_CACHE_FILE):
                with open(AVATARS_CACHE_FILE, 'rb') as f:
                    self.avatars = pickle.load(f)
                    if self.avatars:
                        self.update_status(f"Đã tải {len(self.avatars)} avatars từ cache")
                        self.populate_avatars_tree(self.avatars)
        except Exception as e:
            print(f"Lỗi khi đọc cache avatars: {e}")
    
    def save_avatars_cache(self):
        """Lưu danh sách avatars vào cache"""
        try:
            if self.avatars:
                with open(AVATARS_CACHE_FILE, 'wb') as f:
                    pickle.dump(self.avatars, f)
                print(f"Đã lưu {len(self.avatars)} avatars vào cache")
        except Exception as e:
            print(f"Lỗi khi lưu cache avatars: {e}")
    
    def load_window_config(self):
        """Đọc cấu hình cửa sổ từ file nếu có"""
        try:
            if os.path.exists(WINDOW_CONFIG_FILE):
                with open(WINDOW_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    if 'geometry' in config:
                        self.root.geometry(config['geometry'])
                    print(f"Đã tải cấu hình cửa sổ: {config['geometry']}")
        except Exception as e:
            print(f"Lỗi khi đọc cấu hình cửa sổ: {e}")
    
    def save_window_config(self):
        """Lưu cấu hình cửa sổ vào file"""
        try:
            config = {
                'geometry': self.root.geometry()
            }
            with open(WINDOW_CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            print(f"Đã lưu cấu hình cửa sổ: {config['geometry']}")
        except Exception as e:
            print(f"Lỗi khi lưu cấu hình cửa sổ: {e}")
    
    def load_selected_avatar(self):
        """Đọc avatar đã chọn từ lần trước, nếu không có thì dùng mặc định"""
        try:
            if os.path.exists(SELECTED_AVATAR_FILE):
                with open(SELECTED_AVATAR_FILE, 'r') as f:
                    avatar_id = f.read().strip()
                    if avatar_id:
                        print(f"Đã tải avatar đã chọn: {avatar_id}")
                        return avatar_id
        except Exception as e:
            print(f"Lỗi khi đọc avatar đã chọn: {e}")
        
        # Trả về avatar mặc định
        return "Conrad_standing_house_front"
    
    def save_selected_avatar(self, avatar_id):
        """Lưu avatar đã chọn vào file"""
        try:
            with open(SELECTED_AVATAR_FILE, 'w') as f:
                f.write(avatar_id)
            print(f"Đã lưu avatar đã chọn: {avatar_id}")
        except Exception as e:
            print(f"Lỗi khi lưu avatar đã chọn: {e}")
            
    def load_download_dir(self):
        """Đọc thư mục tải về mặc định từ file nếu có"""
        try:
            if os.path.exists(DOWNLOAD_DIR_FILE):
                with open(DOWNLOAD_DIR_FILE, 'r') as f:
                    download_dir = f.read().strip()
                    if download_dir and os.path.exists(download_dir) and os.path.isdir(download_dir):
                        print(f"Đã tải thư mục tải về mặc định: {download_dir}")
                        return download_dir
        except Exception as e:
            print(f"Lỗi khi đọc thư mục tải về mặc định: {e}")
        
        # Nếu không có hoặc không hợp lệ, trả về thư mục Downloads hoặc Documents
        default_dirs = [
            os.path.join(os.path.expanduser("~"), "Downloads"),
            os.path.join(os.path.expanduser("~"), "Documents"),
            os.path.expanduser("~")
        ]
        
        for dir_path in default_dirs:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                return dir_path
                
        return None
    
    def save_download_dir(self, download_dir):
        """Lưu thư mục tải về mặc định vào file"""
        try:
            with open(DOWNLOAD_DIR_FILE, 'w') as f:
                f.write(download_dir)
            print(f"Đã lưu thư mục tải về mặc định: {download_dir}")
        except Exception as e:
            print(f"Lỗi khi lưu thư mục tải về mặc định: {e}")
    
    def load_input_dir(self):
        """Đọc thư mục đầu vào mặc định từ file nếu có"""
        try:
            if os.path.exists(INPUT_DIR_FILE):
                with open(INPUT_DIR_FILE, 'r') as f:
                    input_dir = f.read().strip()
                    if input_dir and os.path.exists(input_dir) and os.path.isdir(input_dir):
                        print(f"Đã tải thư mục đầu vào mặc định: {input_dir}")
                        return input_dir
        except Exception as e:
            print(f"Lỗi khi đọc thư mục đầu vào mặc định: {e}")
        
        # Nếu không có hoặc không hợp lệ, trả về thư mục mặc định
        if os.path.exists(DEFAULT_INPUT_DIR) and os.path.isdir(DEFAULT_INPUT_DIR):
            return DEFAULT_INPUT_DIR
                
        # Nếu thư mục mặc định không tồn tại, trả về thư mục Documents
        default_dirs = [
            os.path.join(os.path.expanduser("~"), "Documents"),
            os.path.expanduser("~")
        ]
        
        for dir_path in default_dirs:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                return dir_path
                
        return None
    
    def save_input_dir(self, input_dir):
        """Lưu thư mục đầu vào mặc định vào file"""
        try:
            with open(INPUT_DIR_FILE, 'w') as f:
                f.write(input_dir)
            print(f"Đã lưu thư mục đầu vào mặc định: {input_dir}")
        except Exception as e:
            print(f"Lỗi khi lưu thư mục đầu vào mặc định: {e}")
    
    def create_tab_content(self, parent_frame):
        # API Key
        api_frame = ttk.LabelFrame(parent_frame, text="API Key", padding="5")
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Sử dụng API key từ client.api_key thay vì client.API_KEY
        self.api_key_var = tk.StringVar(value=self.client.api_key)
        ttk.Label(api_frame, text="API Key:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(api_frame, textvariable=self.api_key_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        api_buttons_frame = ttk.Frame(api_frame)
        api_buttons_frame.pack(side=tk.LEFT)
        
        ttk.Button(api_buttons_frame, text="Cập nhật", command=self.update_api_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(api_buttons_frame, text="Kiểm tra", command=self.verify_api_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(api_buttons_frame, text="Kiểm tra token", command=self.check_remaining_quota).pack(side=tk.LEFT, padx=5)
        
        # Frame cho danh sách avatars
        avatars_frame = ttk.LabelFrame(parent_frame, text="Danh sách Avatars", padding="5")
        avatars_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Thêm frame tìm kiếm avatar
        search_frame = ttk.Frame(avatars_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Tìm kiếm:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="Xóa", command=self.clear_search).pack(side=tk.LEFT, padx=5)
        
        buttons_frame = ttk.Frame(avatars_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Nút tải danh sách avatars
        ttk.Button(buttons_frame, text="Tải danh sách avatars", command=self.load_avatars).pack(side=tk.LEFT, padx=5)
        
        # Tạo Treeview để hiển thị avatars
        columns = ("id", "name", "gender", "premium")
        self.avatars_tree = ttk.Treeview(avatars_frame, columns=columns, show="headings", selectmode="browse")
        
        # Định nghĩa các tiêu đề cột
        self.avatars_tree.heading("id", text="Avatar ID")
        self.avatars_tree.heading("name", text="Tên")
        self.avatars_tree.heading("gender", text="Giới tính")
        self.avatars_tree.heading("premium", text="Premium")
        
        # Định nghĩa độ rộng cột
        self.avatars_tree.column("id", width=150)
        self.avatars_tree.column("name", width=200)
        self.avatars_tree.column("gender", width=80)
        self.avatars_tree.column("premium", width=80)
        
        # Thêm scrollbar
        scrollbar = ttk.Scrollbar(avatars_frame, orient=tk.VERTICAL, command=self.avatars_tree.yview)
        self.avatars_tree.configure(yscroll=scrollbar.set)
        
        self.avatars_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Xử lý sự kiện khi chọn avatar
        self.avatars_tree.bind("<<TreeviewSelect>>", self.on_avatar_selected)
        
        # Frame cho cài đặt video
        video_settings_frame = ttk.LabelFrame(parent_frame, text="Cài đặt Video", padding="5")
        video_settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Frame cho audio file
        audio_frame = ttk.Frame(video_settings_frame)
        audio_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(audio_frame, text="File âm thanh:").pack(side=tk.LEFT, padx=5)
        self.audio_file_var = tk.StringVar()
        ttk.Entry(audio_frame, textvariable=self.audio_file_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        buttons_panel = ttk.Frame(audio_frame)
        buttons_panel.pack(side=tk.LEFT)
        
        ttk.Button(buttons_panel, text="Chọn file", command=self.select_audio_file).pack(side=tk.LEFT, padx=5)
        self.upload_btn = ttk.Button(buttons_panel, text="Upload file", command=self.upload_audio, state="disabled")
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        
        # Thêm thông tin về audio asset
        audio_asset_frame = ttk.Frame(video_settings_frame)
        audio_asset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(audio_asset_frame, text="Audio Asset ID:").pack(side=tk.LEFT, padx=5)
        self.audio_asset_var = tk.StringVar()
        ttk.Entry(audio_asset_frame, textvariable=self.audio_asset_var, state="readonly").pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Frame cho background color
        bg_frame = ttk.Frame(video_settings_frame)
        bg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(bg_frame, text="Màu nền:").pack(side=tk.LEFT, padx=5)
        self.bg_color_var = tk.StringVar(value="#008000")
        ttk.Entry(bg_frame, textvariable=self.bg_color_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Frame cho kích thước video
        dim_frame = ttk.Frame(video_settings_frame)
        dim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(dim_frame, text="Chiều rộng:").pack(side=tk.LEFT, padx=5)
        self.width_var = tk.StringVar(value="1280")
        ttk.Entry(dim_frame, textvariable=self.width_var, width=6).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(dim_frame, text="Chiều cao:").pack(side=tk.LEFT, padx=5)
        self.height_var = tk.StringVar(value="720")
        ttk.Entry(dim_frame, textvariable=self.height_var, width=6).pack(side=tk.LEFT, padx=5)
        
        # Frame cho thư mục tải về
        download_frame = ttk.Frame(video_settings_frame)
        download_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(download_frame, text="Thư mục tải về:").pack(side=tk.LEFT, padx=5)
        self.download_dir_var = tk.StringVar(value=self.download_dir if self.download_dir else "")
        ttk.Entry(download_frame, textvariable=self.download_dir_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(download_frame, text="Chọn thư mục", command=self.select_download_dir).pack(side=tk.LEFT, padx=5)
        
        # Tự động tải về checkbox
        self.auto_download_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(download_frame, text="Tự động tải về", variable=self.auto_download_var).pack(side=tk.LEFT, padx=5)
        
        # Tạo video button
        buttons_frame = ttk.Frame(parent_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.create_btn = ttk.Button(buttons_frame, text="Tạo Video", command=self.create_video, state="disabled")
        self.create_btn.pack(side=tk.RIGHT, padx=5)
        
        # Thêm nút tạo nhiều video
        self.create_multiple_btn = ttk.Button(buttons_frame, text="Tạo Tất Cả Video", command=self.create_multiple_videos, state="disabled")
        self.create_multiple_btn.pack(side=tk.RIGHT, padx=5)
        
        # Status frame
        self.status_frame = ttk.LabelFrame(parent_frame, text="Trạng thái", padding="5")
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="Sẵn sàng...")
        ttk.Label(self.status_frame, textvariable=self.status_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Frame cho kết quả
        result_frame = ttk.LabelFrame(parent_frame, text="Kết quả", padding="5")
        result_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.result_var = tk.StringVar()
        result_entry = ttk.Entry(result_frame, textvariable=self.result_var, width=70)
        result_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        ttk.Button(result_frame, text="Sao chép", command=self.copy_result_url).pack(side=tk.LEFT, padx=5, pady=5)
    
    def create_manage_tab_content(self, parent_frame):
        # Frame điều khiển 
        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Tải danh sách video", command=self.load_videos).pack(side=tk.LEFT, padx=5)
        
        # Frame cho danh sách video
        videos_frame = ttk.LabelFrame(parent_frame, text="Danh sách Video", padding="5")
        videos_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tạo Treeview để hiển thị videos
<<<<<<< HEAD
        columns = ("id", "audio_name", "status", "created_at", "type")
=======
        columns = ("id", "status", "created_at", "type")
>>>>>>> b17c438c4225d19dc8edd19e9fc8d6d19961bb19
        self.videos_tree = ttk.Treeview(videos_frame, columns=columns, show="headings", selectmode="browse")
        
        # Định nghĩa các tiêu đề cột
        self.videos_tree.heading("id", text="Video ID")
<<<<<<< HEAD
        self.videos_tree.heading("audio_name", text="Audio Name")
=======
>>>>>>> b17c438c4225d19dc8edd19e9fc8d6d19961bb19
        self.videos_tree.heading("status", text="Trạng thái")
        self.videos_tree.heading("created_at", text="Thời gian tạo")
        self.videos_tree.heading("type", text="Loại")
        
        # Định nghĩa độ rộng cột
        self.videos_tree.column("id", width=180)
<<<<<<< HEAD
        self.videos_tree.column("audio_name", width=150)
=======
>>>>>>> b17c438c4225d19dc8edd19e9fc8d6d19961bb19
        self.videos_tree.column("status", width=100)
        self.videos_tree.column("created_at", width=150)
        self.videos_tree.column("type", width=100)
        
        # Thêm scrollbar
        scrollbar = ttk.Scrollbar(videos_frame, orient=tk.VERTICAL, command=self.videos_tree.yview)
        self.videos_tree.configure(yscroll=scrollbar.set)
        
        self.videos_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Tạo frame hiển thị thông tin chi tiết video
        details_frame = ttk.LabelFrame(parent_frame, text="Chi tiết Video", padding="5")
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Hiển thị URL
        url_frame = ttk.Frame(details_frame)
        url_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(url_frame, text="Video URL:").pack(side=tk.LEFT, padx=5)
        self.video_url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.video_url_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Nút tải video
        actions_frame = ttk.Frame(details_frame)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Tải video", command=self.download_selected_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Sao chép URL", command=self.copy_video_url).pack(side=tk.LEFT, padx=5)
        
        # Bắt sự kiện khi chọn video
        self.videos_tree.bind("<<TreeviewSelect>>", self.on_video_selected)

    def update_api_key(self):
        api_key = self.api_key_var.get().strip()
        if api_key:
            # Cập nhật API key trong instance của client
            self.client.api_key = api_key
            
            # Nếu đây là API key của người dùng (API key đặc biệt đã định sẵn), cũng cập nhật class constant
            if api_key == "MDViZWM5N2ZhMTdmNDQzOTk0M2MwNjIzM2Q5ODYwZWMtMTc0NTYwNDEzMw==":
                HeyGenClient.API_KEY = api_key
                
            # Cập nhật headers với API key mới
            self.client.headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "x-api-key": api_key
            }
            # Lưu API key vào file
            self.save_api_key(api_key)
            self.update_status(f"Đã cập nhật và lưu API Key: {api_key[:5]}...{api_key[-5:]} (ẩn giữa để bảo mật)")
        else:
            messagebox.showerror("Lỗi", "API Key không được để trống")
            
    def verify_api_key(self):
        """
        Kiểm tra API Key hiện tại có hợp lệ không bằng cách sử dụng API v2
        và hiển thị số token còn lại
        """
        self.update_status("Đang kiểm tra API Key...")
        self.root.update()
        
        # Sử dụng trực tiếp API v2 để kiểm tra
        url = f"{self.client.BASE_URL}/v2/avatars"
        
        try:
            response = requests.get(url, headers=self.client.headers, proxies=self.client.proxies)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data:
                        avatar_count = len(data["data"]["avatars"]) if "avatars" in data["data"] else len(data["data"])
                        
                        # Lấy thông tin về số token còn lại
                        quota_response = self.client.get_remaining_quota()
                        
                        try:
                            # Kiểm tra nếu error là None hoặc null (sẽ được chuyển thành None trong Python)
                            if quota_response.get("error") is None and "data" in quota_response:
                                quota_data = quota_response["data"]
                                
                                # Kiểm tra các định dạng phản hồi có thể có
                                remaining_seconds = None
                                if "remaining_quota" in quota_data:
                                    remaining_seconds = quota_data["remaining_quota"]
                                elif "remaining_tokens" in quota_data:
                                    remaining_seconds = quota_data["remaining_tokens"]
                                elif "quota" in quota_data and "remaining" in quota_data["quota"]:
                                    remaining_seconds = quota_data["quota"]["remaining"]
                                
                                # In ra thông tin debug
                                print(f"Phản hồi quota: {json.dumps(quota_response)}")
                                print(f"Remaining seconds: {remaining_seconds}")
                                
                                # Định dạng thời gian còn lại
                                if remaining_seconds is not None and isinstance(remaining_seconds, (int, float)):
                                    # Định dạng hiển thị HH:MM:SS hoặc MM:SS tùy thuộc vào thời gian
                                    self.remaining_time_format = self.format_remaining_time(remaining_seconds)
                                    
                                    # Hiển thị trong trạng thái
                                    self.update_status(f"API Key hợp lệ. Tìm thấy {avatar_count} avatars")
                                    
                                    # Hiển thị thông báo với số token còn lại
                                    messagebox.showinfo("Thành công", f"API Key hợp lệ!\nTìm thấy {avatar_count} avatars\nThời gian còn lại: {self.remaining_time_format}")
                                    return True
                        except Exception as e:
                            print(f"Lỗi khi xử lý thông tin quota: {e}")
                        
                        # Nếu không lấy được thông tin quota hoặc có lỗi
                        self.remaining_time_format = None
                        self.update_status(f"API Key hợp lệ. Tìm thấy {avatar_count} avatars")
                        messagebox.showinfo("Thành công", f"API Key hợp lệ! Tìm thấy {avatar_count} avatars\n(Không thể lấy thông tin token)")
                        return True
                    else:
                        self.remaining_time_format = None
                        self.update_status("API Key hợp lệ")
                        messagebox.showinfo("Thành công", "API Key hợp lệ!")
                        return True
                except Exception as e:
                    self.remaining_time_format = None
                    self.update_status(f"API Key hợp lệ, nhưng có lỗi khi phân tích phản hồi: {e}")
                    messagebox.showinfo("Thành công", "API Key hợp lệ!")
                    return True
            elif response.status_code == 401:
                self.remaining_time_format = None
                self.update_status("API Key không hợp lệ (401 Unauthorized)")
                messagebox.showerror("Lỗi", "API Key không hợp lệ!")
                return False
            else:
                error_text = f"Mã trạng thái: {response.status_code}"
                try:
                    error_data = response.json()
                    error_text += f", Phản hồi: {json.dumps(error_data)}"
                except:
                    if response.text:
                        error_text += f", Phản hồi: {response.text[:200]}..."
                
                self.remaining_time_format = None
                self.update_status(f"Lỗi khi kiểm tra API Key ({error_text})")
                messagebox.showerror("Lỗi", f"Không thể kiểm tra API Key.\n{error_text}")
                return False
        except Exception as e:
            self.remaining_time_format = None
            self.update_status(f"Lỗi khi kiểm tra API Key: {e}")
            messagebox.showerror("Lỗi", f"Lỗi kết nối khi kiểm tra API Key: {e}")
            return False
    
    def load_avatars(self):
        self.update_status("Đang tải danh sách avatars...")
        self.root.update()
        
        # Xóa dữ liệu cũ
        for item in self.avatars_tree.get_children():
            self.avatars_tree.delete(item)
        
        # Lấy danh sách avatars
        response = self.client.get_all_avatars()
        
        success = False  # Biến để theo dõi xử lý thành công
        
        if "error" in response and response["error"] is not None:
            error_msg = f"Lỗi: {response['error']}"
            self.update_status(error_msg)
            messagebox.showerror("Lỗi", f"Không thể tải danh sách avatars: {response['error']}")
            return
        
        # Lưu ý: API có thể trả về cấu trúc dữ liệu khác nhau
        if "data" in response and "avatars" in response["data"]:
            # Cấu trúc phổ biến
            avatars_data = response["data"]["avatars"]
            
            if avatars_data:
                self.avatars = avatars_data
                self.populate_avatars_tree(avatars_data)
                # Lưu danh sách avatars vào cache
                self.save_avatars_cache()
                success = True
            else:
                self.update_status("Không tìm thấy avatar nào")
        elif "data" in response and isinstance(response["data"], list):
            # Cấu trúc thay thế (mảng avatars trực tiếp trong data)
            avatars_data = response["data"]
            
            if avatars_data:
                self.avatars = avatars_data
                self.populate_avatars_tree_alternative(avatars_data)
                # Lưu danh sách avatars vào cache
                self.save_avatars_cache()
                success = True
            else:
                self.update_status("Không tìm thấy avatar nào")
        
        # Chỉ hiển thị lỗi nếu không xử lý được dữ liệu
        if not success:
            error_msg = "Không thể tải danh sách avatars: Cấu trúc dữ liệu không được hỗ trợ"
            if isinstance(response, dict):
                error_msg += f": {json.dumps(response)}"
            self.update_status(error_msg)
            messagebox.showerror("Lỗi", error_msg)
    
    def populate_avatars_tree(self, avatars_data):
        """Xử lý danh sách avatars với cấu trúc dữ liệu chuẩn"""
        for avatar in avatars_data:
            self.avatars_tree.insert("", tk.END, values=(
                avatar["avatar_id"],
                avatar["avatar_name"],
                avatar.get("gender", ""),
                "Có" if avatar.get("premium", False) else "Không"
            ))
        self.update_status(f"Đã tải {len(avatars_data)} avatars")
        
        # Áp dụng bộ lọc tìm kiếm nếu có
        if self.search_var.get():
            self.filter_avatars()
            
        # Tự động chọn avatar đã lưu trước đó
        if self.selected_avatar_id:
            self.root.after(100, lambda: self.select_avatar_by_id(self.selected_avatar_id))
    
    def populate_avatars_tree_alternative(self, avatars_data):
        """Xử lý danh sách avatars với cấu trúc dữ liệu thay thế"""
        for avatar in avatars_data:
            # Kiểm tra xem dữ liệu có các trường cần thiết không
            avatar_id = avatar.get("id") or avatar.get("avatar_id")
            avatar_name = avatar.get("name") or avatar.get("avatar_name")
            
            if not avatar_id or not avatar_name:
                continue  # Bỏ qua avatar không đầy đủ thông tin
                
            self.avatars_tree.insert("", tk.END, values=(
                avatar_id,
                avatar_name,
                avatar.get("gender", ""),
                "Có" if avatar.get("premium", False) else "Không"
            ))
        self.update_status(f"Đã tải {len(avatars_data)} avatars")
        
        # Áp dụng bộ lọc tìm kiếm nếu có
        if self.search_var.get():
            self.filter_avatars()
            
        # Tự động chọn avatar đã lưu trước đó
        if self.selected_avatar_id:
            self.root.after(100, lambda: self.select_avatar_by_id(self.selected_avatar_id))
    
    def filter_avatars(self, *args):
        """Lọc danh sách avatars theo từ khóa tìm kiếm"""
        search_term = self.search_var.get().lower()
        
        # Xóa tất cả các mục hiện tại
        for item in self.avatars_tree.get_children():
            self.avatars_tree.delete(item)
        
        # Nếu không có từ khóa tìm kiếm, hiển thị tất cả
        if not search_term:
            if "avatar_id" in self.avatars[0] if self.avatars else False:
                self.populate_avatars_tree(self.avatars)
            else:
                self.populate_avatars_tree_alternative(self.avatars)
            return
        
        # Lọc avatars theo từ khóa
        filtered_avatars = []
        for avatar in self.avatars:
            avatar_id = avatar.get("avatar_id") or avatar.get("id", "")
            avatar_name = avatar.get("avatar_name") or avatar.get("name", "")
            
            if (avatar_id.lower().find(search_term) != -1 or 
                avatar_name.lower().find(search_term) != -1):
                filtered_avatars.append(avatar)
        
        # Hiển thị avatars đã lọc
        if "avatar_id" in self.avatars[0] if self.avatars else False:
            self.populate_avatars_tree(filtered_avatars)
        else:
            self.populate_avatars_tree_alternative(filtered_avatars)
        
        self.update_status(f"Tìm thấy {len(filtered_avatars)} avatar khớp với từ khóa: {search_term}")
    
    def clear_search(self):
        """Xóa từ khóa tìm kiếm"""
        self.search_var.set("")
        # filter_avatars sẽ được gọi tự động thông qua trace_add
    
    def on_avatar_selected(self, event):
        selection = self.avatars_tree.selection()
        if selection:
            item = selection[0]
            avatar_id = self.avatars_tree.item(item, "values")[0]
            self.selected_avatar_id = avatar_id
            # Lưu avatar đã chọn
            self.save_selected_avatar(avatar_id)
            self.update_status(f"Đã chọn avatar: {avatar_id}")
            
            # Cập nhật trạng thái nút tạo video
            self.update_create_button_state()
    
    def select_avatar_by_id(self, avatar_id):
        """Chọn avatar trong danh sách dựa vào ID"""
        # Nếu không có dữ liệu avatars, không thể chọn
        if not self.avatars or not self.avatars_tree.get_children():
            return False
        
        # Duyệt qua tất cả các mục trong tree để tìm avatar_id
        for item in self.avatars_tree.get_children():
            current_id = self.avatars_tree.item(item, "values")[0]
            if current_id == avatar_id:
                # Chọn item này
                self.avatars_tree.selection_set(item)
                # Đảm bảo item được hiển thị trong view
                self.avatars_tree.see(item)
                # Cập nhật selected_avatar_id
                self.selected_avatar_id = avatar_id
                self.update_status(f"Đã chọn avatar: {avatar_id}")
                self.update_create_button_state()
                return True
        
        # Nếu không tìm thấy, hiển thị thông báo
        self.update_status(f"Không tìm thấy avatar với ID: {avatar_id}")
        return False
        
    def update_status(self, message):
        # Nếu có thông tin về thời gian còn lại, hiển thị kèm theo
        if hasattr(self, 'remaining_time_format') and self.remaining_time_format:
            status_text = f"{message} | Thời gian tối đa còn lại: {self.remaining_time_format}"
        else:
            status_text = message
            
        self.status_var.set(status_text)
        print(message)
    
    def copy_result_url(self):
        url = self.result_var.get()
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.update_status("Đã sao chép URL vào clipboard")
        else:
            self.update_status("Không có URL để sao chép")
            
    def copy_video_url(self):
        url = self.video_url_var.get()
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.update_status("Đã sao chép URL video vào clipboard")
        else:
            self.update_status("Không có URL để sao chép")
            
    def load_videos(self):
        self.update_status("Đang tải danh sách video...")
        self.root.update()
        
        # Xóa dữ liệu cũ
        for item in self.videos_tree.get_children():
            self.videos_tree.delete(item)
        
        # Lấy danh sách video
        response = self.client.get_all_videos()
        
        if "error" in response and response["error"] is not None:
            error_msg = f"Lỗi: {response['error']}"
            self.update_status(error_msg)
            messagebox.showerror("Lỗi", f"Không thể tải danh sách video: {response['error']}")
            return
        
        # Xử lý phản hồi
        if "data" in response and "videos" in response["data"]:
            videos = response["data"]["videos"]
            
            if videos:
                # Hiển thị danh sách video
                for video in videos:
                    video_id = video.get("video_id", "")
                    status = video.get("status", "")
                    created_at = video.get("created_at", 0)
                    video_type = video.get("type", "")
                    
                    # Chuyển đổi timestamp thành datetime
                    created_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))
                    
<<<<<<< HEAD
                    # Kiểm tra xem video có tên audio tương ứng không
                    audio_name = "N/A"
                    for process_id, process_info in self.processing_videos.items():
                        if process_id == video_id and 'audio_filename' in process_info:
                            audio_name = process_info['audio_filename']
                            break
                    
                    # Thêm vào bảng với cột Audio Name
                    self.videos_tree.insert("", tk.END, values=(
                        video_id,
                        audio_name,
=======
                    self.videos_tree.insert("", tk.END, values=(
                        video_id,
>>>>>>> b17c438c4225d19dc8edd19e9fc8d6d19961bb19
                        status,
                        created_date,
                        video_type
                    ))
                
                total = len(videos)
                self.update_status(f"Đã tải {total} video")
            else:
                self.update_status("Không tìm thấy video nào")
        else:
            error_msg = "Không thể tải danh sách video: Cấu trúc dữ liệu không được hỗ trợ"
            self.update_status(error_msg)
            messagebox.showerror("Lỗi", error_msg)
    
    def on_video_selected(self, event):
        selection = self.videos_tree.selection()
        if selection:
            item = selection[0]
            video_id = self.videos_tree.item(item, "values")[0]
            
            # Lấy thông tin chi tiết về video
            url = f"{self.client.BASE_URL}/v1/video_status.get?video_id={video_id}"
            
            try:
                response = requests.get(url, headers=self.client.headers, proxies=self.client.proxies)
                response.raise_for_status()
                data = response.json()
                
                if "data" in data:
                    video_data = data["data"]
                    video_url = video_data.get("video_url", "")
                    self.video_url_var.set(video_url)
                    
                    status = video_data.get("status", "")
                    
                    # Lấy thông tin về thời lượng video nếu có
                    duration = video_data.get("duration", None)
                    duration_info = ""
                    
                    if duration is not None and isinstance(duration, (int, float)):
                        # Tính toán số credit đã sử dụng
                        credits_used = self.calculate_video_credits(duration)
                        
                        # Định dạng thông tin về thời lượng và credit
                        if credits_used is not None:
                            minutes = int(duration // 60)
                            seconds = int(duration % 60)
                            duration_formatted = f"{minutes}:{seconds:02d}"
                            duration_info = f" | Thời lượng: {duration_formatted} | Credit: {credits_used:.2f}"
                    
                    self.update_status(f"Đã chọn video: {video_id}, trạng thái: {status}{duration_info}")
                else:
                    self.video_url_var.set("")
                    self.update_status(f"Không tìm thấy thông tin chi tiết cho video: {video_id}")
            except Exception as e:
                self.update_status(f"Lỗi khi lấy thông tin video: {str(e)}")
                self.video_url_var.set("")
    
    def download_selected_video(self):
        video_url = self.video_url_var.get()
        
        if not video_url:
            messagebox.showerror("Lỗi", "Không có URL video để tải. Vui lòng chọn một video đã hoàn thành.")
            return
        
        try:
            # Mở hộp thoại lưu file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                filetypes=[("MP4 files", "*.mp4")],
                title="Lưu video"
            )
            
            if file_path:
                self.update_status(f"Đang tải video xuống: {os.path.basename(file_path)}...")
                self.root.update()
                
                # Tải video
                video_content = requests.get(video_url, proxies=self.client.proxies).content
                
                # Lưu vào file
                with open(file_path, "wb") as video_file:
                    video_file.write(video_content)
                    
                self.update_status(f"Đã tải video thành công: {os.path.basename(file_path)}")
        except Exception as e:
            error_msg = f"Lỗi khi tải video: {str(e)}"
            self.update_status(error_msg)
            messagebox.showerror("Lỗi", error_msg)
    
    def select_audio_file(self):
        file_paths = filedialog.askopenfilenames(
            title="Chọn file audio",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.m4a")],
            initialdir=self.input_dir if self.input_dir else None
        )
        if file_paths:
            # Lưu danh sách file được chọn
            self.audio_file_paths = list(file_paths)
            
            # Lưu thư mục chứa file đầu tiên được chọn để sử dụng cho lần sau
            first_file = self.audio_file_paths[0]
            self.input_dir = os.path.dirname(first_file)
            self.save_input_dir(self.input_dir)
            
            # Hiển thị file đầu tiên trong trường nhập liệu
            self.audio_file_path = self.audio_file_paths[0]
            self.audio_file_var.set(f"Đã chọn {len(self.audio_file_paths)} file audio")
            
            self.update_status(f"Đã chọn {len(self.audio_file_paths)} file audio từ thư mục {self.input_dir}")
            self.upload_btn.configure(state="normal")
            
            # Reset audio asset ID khi chọn file mới
            self.audio_asset_id = None
            self.audio_asset_var.set("")
            self.audio_assets = []
            
            # Cập nhật trạng thái nút tạo video
            self.update_create_button_state()
    
    def select_download_dir(self):
        """Chọn thư mục tải về mặc định"""
        dir_path = filedialog.askdirectory(
            title="Chọn thư mục lưu video",
            initialdir=self.download_dir if self.download_dir else None
        )
        if dir_path:
            self.download_dir = dir_path
            self.download_dir_var.set(dir_path)
            self.save_download_dir(dir_path)
            self.update_status(f"Đã chọn thư mục tải về: {dir_path}")
    
    def upload_audio(self):
        if not self.audio_file_paths:
            messagebox.showerror("Lỗi", "Vui lòng chọn file âm thanh trước")
            return
        
        # Reset danh sách audio assets và chỉ số upload
        self.audio_assets = []
        self.current_upload_index = 0
        
        # Bắt đầu quá trình upload từ file đầu tiên
        self.upload_next_audio()
    
    def upload_next_audio(self):
        """Upload file âm thanh tiếp theo trong danh sách"""
        if self.current_upload_index >= len(self.audio_file_paths):
            # Đã upload hết tất cả file
            total_files = len(self.audio_file_paths)
            self.update_status(f"Đã upload xong {total_files} file âm thanh")
            
            # Cập nhật hiển thị asset ID
            if self.audio_assets:
                self.audio_asset_id = self.audio_assets[0]["id"]
                self.audio_asset_var.set(f"Đã upload {len(self.audio_assets)} file")
            
            # Cập nhật trạng thái nút tạo video
            self.update_create_button_state()
            
            # Tự động tạo video nếu đã chọn avatar
            if self.selected_avatar_id and self.auto_download_var.get():
                self.root.after(500, self.create_multiple_videos)
            return
        
        # Lấy file hiện tại cần upload
        current_file = self.audio_file_paths[self.current_upload_index]
        self.update_status(f"Đang upload file âm thanh ({self.current_upload_index + 1}/{len(self.audio_file_paths)}): {os.path.basename(current_file)}...")
        self.root.update()
        
        # Vô hiệu hóa nút upload
        self.upload_btn.configure(state="disabled")
        
        try:
            # Chuẩn bị multipart form data
            with open(current_file, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(current_file)
            
            # Xác định content type
            content_type = "audio/mpeg"  # Mặc định
            if filename.lower().endswith('.wav'):
                content_type = "audio/wav"
            elif filename.lower().endswith('.ogg'):
                content_type = "audio/ogg"
            elif filename.lower().endswith('.m4a'):
                content_type = "audio/m4a"
            
            # URL API upload đúng
            upload_url = "https://upload.heygen.com/v1/asset"
            
            # In thông tin upload để debug
            print(f"Đang upload file: {filename}, Content-Type: {content_type}, Size: {len(file_content)} bytes")
            print(f"Gửi request đến: {upload_url}")
            
            # Tạo headers cho request
            headers = {
                'X-Api-Key': self.client.api_key,
                'Content-Type': content_type
            }
            
            print(f"Headers: {headers}")
            
            # Thực hiện upload bằng cách gửi binary data trực tiếp (không sử dụng multipart form)
            response = requests.post(upload_url, headers=headers, data=file_content, proxies=self.client.proxies)
            
            # In thông tin phản hồi
            print(f"Phản hồi upload - Status: {response.status_code}")
            print(f"Phản hồi upload - Headers: {response.headers}")
            print(f"Phản hồi upload - Text: {response.text[:500]}...")  # Hiển thị 500 ký tự đầu tiên
            
            # Xử lý phản hồi
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # In cấu trúc phản hồi để debug
                    print(f"Cấu trúc phản hồi JSON: {json.dumps(response_data)}")
                    
                    # Kiểm tra cấu trúc phản hồi
                    # Có thể là: {"code": 100, "data": {"id": "asset_id", ...}}
                    if "data" in response_data and "id" in response_data["data"]:
                        asset_id = response_data["data"]["id"]
                        
                        # Thêm vào danh sách audio assets
                        self.audio_assets.append({
                            "id": asset_id, 
                            "filename": filename,
                            "filepath": current_file
                        })
                        
                        upload_success_msg = f"Đã upload file thành công ({self.current_upload_index + 1}/{len(self.audio_file_paths)}): {filename}"
                        self.update_status(upload_success_msg)
                        
                        # Tăng chỉ số và tiếp tục upload file tiếp theo
                        self.current_upload_index += 1
                        self.root.after(500, self.upload_next_audio)
                        return
                    else:
                        error_msg = "Không thể tìm thấy asset_id trong phản hồi"
                        print(f"Cấu trúc phản hồi: {response_data}")
                except json.JSONDecodeError as e:
                    error_msg = f"Lỗi phân tích JSON: {str(e)}"
                    print(f"Nội dung phản hồi: {response.text}")
            else:
                error_msg = f"Lỗi upload: HTTP {response.status_code}"
                try:
                    response_data = response.json()
                    print(f"Chi tiết lỗi: {response_data}")
                    if "message" in response_data:
                        error_msg += f" - {response_data['message']}"
                except:
                    if response.text:
                        error_msg += f" - {response.text[:200]}..."
            
            # Nếu đến đây nghĩa là có lỗi
            self.update_status(f"Lỗi khi upload file: {error_msg}")
            messagebox.showerror("Lỗi", f"Không thể upload file: {error_msg}")
            
        except Exception as e:
            error_msg = f"Lỗi không mong đợi: {str(e)}"
            print(f"Exception detail: {str(e)}, Type: {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            self.update_status(error_msg)
            messagebox.showerror("Lỗi", error_msg)
        
        # Kích hoạt lại nút upload
        self.upload_btn.configure(state="normal")
    
    def update_create_button_state(self):
        if self.selected_avatar_id and (self.audio_asset_id or self.audio_assets):
            self.create_btn.configure(state="normal")
            
            # Kích hoạt nút tạo nhiều video nếu có nhiều file audio được upload
            if hasattr(self, 'audio_assets') and self.audio_assets and len(self.audio_assets) > 0:
                self.create_multiple_btn.configure(state="normal")
            else:
                self.create_multiple_btn.configure(state="disabled")
        else:
            self.create_btn.configure(state="disabled")
            self.create_multiple_btn.configure(state="disabled")
    
    def create_multiple_videos(self):
        """Tạo video cho tất cả file audio đã upload"""
        if not self.selected_avatar_id:
            messagebox.showerror("Lỗi", "Vui lòng chọn một avatar")
            return
        
        if not self.audio_assets:
            messagebox.showerror("Lỗi", "Vui lòng upload file âm thanh trước")
            return
            
        # Nếu không có thư mục tải về và tự động tải về được bật
        if self.auto_download_var.get() and not self.download_dir:
            messagebox.showinfo("Thông báo", "Vui lòng chọn thư mục tải video về trước")
            self.select_download_dir()
            if not self.download_dir:  # Nếu người dùng hủy chọn thư mục
                return
        
        # Vô hiệu hóa nút tạo video
        self.create_btn.configure(state="disabled")
        
        # Tạo video cho từng file audio
        for index, asset in enumerate(self.audio_assets):
            # Tạm dừng một chút giữa các yêu cầu để tránh quá tải API
            self.root.after(index * 200, lambda asset=asset: self.create_video_for_asset(asset))
        
        self.update_status(f"Đã bắt đầu tạo {len(self.audio_assets)} video")
    
    def create_video_for_asset(self, asset):
        """Tạo video cho một asset cụ thể"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            bg_color = self.bg_color_var.get()
            
            asset_id = asset["id"]
            filename = asset["filename"]
            
            self.update_status(f"Đang tạo video cho file: {filename}...")
            
            # In thông tin payload để debug
            payload_info = {
                "avatar_id": self.selected_avatar_id,
                "audio_asset_id": asset_id,
                "background_color": bg_color,
                "width": width,
                "height": height
            }
            print(f"Payload tạo video: {json.dumps(payload_info)}")
            
            # Thực hiện API call
            url = f"{self.client.BASE_URL}/v2/video/generate"
            
            # Chuẩn bị payload theo cấu trúc yêu cầu của API
            payload = {
                "video_inputs": [
                    {
                        "character": {
                            "type": "avatar",
                            "avatar_id": self.selected_avatar_id,
                            "avatar_style": "normal"
                        },
                        "voice": {
                            "type": "audio",
                            "audio_asset_id": asset_id
                        },
                        "background": {
                            "type": "color",
                            "value": bg_color
                        }
                    }
                ],
                "dimension": {
                    "width": width,
                    "height": height
                },
                "caption": False
            }
            
            # Tạo hàm xử lý riêng để chạy trong thread
            def create_video_thread():
                try:
                    # Gửi request
                    response = requests.post(url, json=payload, headers=self.client.headers, proxies=self.client.proxies)
                    
                    # Kiểm tra mã trạng thái và xử lý phản hồi
                    if response.status_code == 200:
                        video_data = response.json()
                        
                        # In phản hồi từ API để debug
                        print(f"Phản hồi API tạo video: {json.dumps(video_data) if isinstance(video_data, dict) else video_data}")
                        
                        # Kiểm tra và xử lý phản hồi
                        if "error" in video_data and video_data["error"] is not None:
                            error_msg = f"Lỗi cho file {filename}: {video_data['error']}"
                            self.update_status(error_msg)
                            print(error_msg)
                            
                            # Kích hoạt lại nút create nếu không còn video nào đang xử lý
                            if not self.processing_videos:
                                self.create_btn.configure(state="normal")
                            return
                        
                        if "data" in video_data and "video_id" in video_data["data"]:
                            video_id = video_data["data"]["video_id"]
                            
                            # Lấy tên file âm thanh để đặt tên cho video (không bao gồm phần mở rộng)
                            audio_filename = os.path.splitext(filename)[0]
                            
                            # Thêm video vào danh sách đang xử lý
                            self.processing_videos[video_id] = {
                                "avatar_id": self.selected_avatar_id,
                                "audio_filename": audio_filename,
                                "filepath": asset["filepath"],
                                "filename": filename,
                                "start_time": time.time()
                            }
                            
                            self.update_status(f"Video đang được tạo cho file {filename} với ID: {video_id}")
                            
                            # Bắt đầu kiểm tra trạng thái video trong main thread
                            self.root.after(100, lambda: self.check_video_status(video_id, audio_filename=audio_filename))
                        else:
                            error_msg = f"Không thể tạo video cho file {filename}: Không tìm thấy video_id trong phản hồi"
                            if isinstance(video_data, dict):
                                error_msg += f": {json.dumps(video_data)}"
                            self.update_status(error_msg)
                            print(error_msg)
                            
                            # Kích hoạt lại nút create nếu không còn video nào đang xử lý
                            if not self.processing_videos:
                                self.create_btn.configure(state="normal")
                    else:
                        error_msg = f"Lỗi khi tạo video cho file {filename}: HTTP {response.status_code}"
                        try:
                            error_data = response.json()
                            if isinstance(error_data, dict) and "message" in error_data:
                                error_msg += f" - {error_data['message']}"
                        except:
                            if response.text:
                                error_msg += f" - {response.text[:200]}..."
                        
                        self.update_status(error_msg)
                        print(error_msg)
                        
                        # Kích hoạt lại nút create nếu không còn video nào đang xử lý
                        if not self.processing_videos:
                            self.create_btn.configure(state="normal")
                except Exception as e:
                    error_msg = f"Lỗi không xác định khi tạo video cho file {filename}: {str(e)}"
                    print(f"Lỗi chi tiết: {str(e)}, {type(e)}")
                    print(f"Traceback: {traceback.format_exc()}")
                    self.update_status(error_msg)
                    print(error_msg)
                    
                    # Kích hoạt lại nút create nếu không còn video nào đang xử lý
                    if not self.processing_videos:
                        self.create_btn.configure(state="normal")
            
            # Khởi tạo thread và chạy
            create_thread = threading.Thread(target=create_video_thread)
            create_thread.daemon = True
            create_thread.start()
            
        except ValueError as e:
            error_msg = f"Lỗi định dạng khi tạo video cho file {filename}: {str(e)}"
            self.update_status(error_msg)
            print(error_msg)
            if not self.processing_videos:
                self.create_btn.configure(state="normal")
        except Exception as e:
            error_msg = f"Lỗi không xác định khi tạo video cho file {filename}: {str(e)}"
            print(f"Lỗi chi tiết: {str(e)}, {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            self.update_status(error_msg)
            print(error_msg)
            if not self.processing_videos:
                self.create_btn.configure(state="normal")
    
    def create_video(self):
        """Hàm xử lý khi nhấn nút tạo video - tùy thuộc vào số lượng file sẽ gọi hàm thích hợp"""
        if not self.selected_avatar_id:
            messagebox.showerror("Lỗi", "Vui lòng chọn một avatar")
            return
        
        # Nếu có nhiều file audio đã upload, sử dụng tính năng tạo nhiều video
        if hasattr(self, 'audio_assets') and self.audio_assets and len(self.audio_assets) > 0:
            self.create_multiple_videos()
            return
        
        # Xử lý trường hợp chỉ có một file audio (phương thức cũ)
        if not self.audio_asset_id:
            messagebox.showerror("Lỗi", "Vui lòng upload file âm thanh trước")
            return
        
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            bg_color = self.bg_color_var.get()
            
            self.update_status(f"Đang tạo video với avatar ID: {self.selected_avatar_id}...")
            self.root.update()
            
            # In thông tin payload để debug
            payload_info = {
                "avatar_id": self.selected_avatar_id,
                "audio_asset_id": self.audio_asset_id,
                "background_color": bg_color,
                "width": width,
                "height": height
            }
            print(f"Payload tạo video: {json.dumps(payload_info)}")
            
            # Thực hiện API call trực tiếp thay vì sử dụng client.create_avatar_video
            url = f"{self.client.BASE_URL}/v2/video/generate"
            
            # Chuẩn bị payload theo cấu trúc yêu cầu của API
            payload = {
                "video_inputs": [
                    {
                        "character": {
                            "type": "avatar",
                            "avatar_id": self.selected_avatar_id,
                            "avatar_style": "normal"
                        },
                        "voice": {
                            "type": "audio",
                            "audio_asset_id": self.audio_asset_id
                        },
                        "background": {
                            "type": "color",
                            "value": bg_color
                        }
                    }
                ],
                "dimension": {
                    "width": width,
                    "height": height
                },
                "caption": False
            }
            
            # Vô hiệu hóa nút tạo video 
            self.create_btn.configure(state="disabled")
            
            # Tạo hàm xử lý riêng để chạy trong thread
            def create_video_thread():
                try:
                    # Gửi request
                    response = requests.post(url, json=payload, headers=self.client.headers, proxies=self.client.proxies)
                    
                    # Kiểm tra mã trạng thái và xử lý phản hồi
                    if response.status_code == 200:
                        video_data = response.json()
                        
                        # In phản hồi từ API để debug
                        print(f"Phản hồi API tạo video: {json.dumps(video_data) if isinstance(video_data, dict) else video_data}")
                        
                        # Kiểm tra và xử lý phản hồi
                        if "error" in video_data and video_data["error"] is not None:
                            error_msg = f"Lỗi: {video_data['error']}"
                            self.update_status(error_msg)
                            messagebox.showerror("Lỗi", f"Không thể tạo video: {video_data['error']}")
                            
                            # Kích hoạt lại nút create nếu không còn video nào đang xử lý
                            if not self.processing_videos:
                                self.create_btn.configure(state="normal")
                            return
                        
                        if "data" in video_data and "video_id" in video_data["data"]:
                            video_id = video_data["data"]["video_id"]
                            
                            # Lấy tên file âm thanh để đặt tên cho video (không bao gồm phần mở rộng)
                            audio_filename = os.path.splitext(os.path.basename(self.audio_file_path))[0] if self.audio_file_path else None
                            
                            # Thêm video vào danh sách đang xử lý
                            self.processing_videos[video_id] = {
                                "avatar_id": self.selected_avatar_id,
                                "audio_filename": audio_filename,
                                "start_time": time.time()
                            }
                            
                            self.update_status(f"Video đang được tạo với ID: {video_id}")
                            
                            # Bắt đầu kiểm tra trạng thái video trong main thread
                            self.root.after(100, lambda: self.check_video_status(video_id, audio_filename=audio_filename))
                        else:
                            error_msg = "Không thể tạo video: Không tìm thấy video_id trong phản hồi"
                            if isinstance(video_data, dict):
                                error_msg += f": {json.dumps(video_data)}"
                            self.update_status(error_msg)
                            messagebox.showerror("Lỗi", error_msg)
                            
                            # Kích hoạt lại nút create nếu không còn video nào đang xử lý
                            if not self.processing_videos:
                                self.create_btn.configure(state="normal")
                    else:
                        error_msg = f"Lỗi khi tạo video: HTTP {response.status_code}"
                        try:
                            error_data = response.json()
                            if isinstance(error_data, dict) and "message" in error_data:
                                error_msg += f" - {error_data['message']}"
                        except:
                            if response.text:
                                error_msg += f" - {response.text[:200]}..."
                        
                        self.update_status(error_msg)
                        messagebox.showerror("Lỗi", error_msg)
                        
                        # Kích hoạt lại nút create nếu không còn video nào đang xử lý
                        if not self.processing_videos:
                            self.create_btn.configure(state="normal")
                except Exception as e:
                    error_msg = f"Lỗi không xác định: {str(e)}"
                    print(f"Lỗi chi tiết: {str(e)}, {type(e)}")
                    print(f"Traceback: {traceback.format_exc()}")
                    self.update_status(error_msg)
                    messagebox.showerror("Lỗi", error_msg)
                    
                    # Kích hoạt lại nút create nếu không còn video nào đang xử lý
                    if not self.processing_videos:
                        self.create_btn.configure(state="normal")
            
            # Khởi tạo thread và chạy
            create_thread = threading.Thread(target=create_video_thread)
            create_thread.daemon = True
            create_thread.start()
            
        except ValueError as e:
            messagebox.showerror("Lỗi", f"Lỗi định dạng: {str(e)}")
            if not self.processing_videos:
                self.create_btn.configure(state="normal")
        except Exception as e:
            error_msg = f"Lỗi không xác định: {str(e)}"
            print(f"Lỗi chi tiết: {str(e)}, {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Lỗi", error_msg)
            if not self.processing_videos:
                self.create_btn.configure(state="normal")
    
    def calculate_video_credits(self, duration_seconds):
        """
        Tính toán số credit API đã sử dụng dựa trên thời lượng video
        
        Args:
            duration_seconds: Thời lượng video tính bằng giây
            
        Returns:
            Số credit API đã sử dụng
        """
        if duration_seconds is None or not isinstance(duration_seconds, (int, float)):
            return None
            
        # Làm tròn lên đến 30 giây tiếp theo
        duration_rounded = (duration_seconds + 29) // 30 * 30
        
        # Chuyển đổi thành phút
        duration_minutes = duration_rounded / 60
        
        # Tính số credit: 0.5 credit mỗi phút
        credits = duration_minutes * 0.5
        
        return credits

    def check_video_status(self, video_id, attempt=0, max_attempts=720, audio_filename=None):
        if attempt >= max_attempts:
            self.update_status(f"Đã hết thời gian chờ xử lý video (60 phút)")
            messagebox.showerror("Lỗi", f"Đã hết thời gian chờ xử lý video (60 phút)")
            if video_id in self.processing_videos:
                del self.processing_videos[video_id]
            
            return
        
        try:
            # Sử dụng endpoint chính xác theo tài liệu API
            url = f"{self.client.BASE_URL}/v1/video_status.get?video_id={video_id}"
            response = requests.get(url, headers=self.client.headers, proxies=self.client.proxies)
            
            print(f"Kiểm tra trạng thái video - Status code: {response.status_code}")
            print(f"Kiểm tra trạng thái video - Response: {response.text[:200]}...")
            
            if response.status_code != 200:
                error_msg = f"Lỗi khi kiểm tra trạng thái: HTTP {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg += f" - {error_data['message']}"
                    except:
                        error_msg += f" - {response.text[:200]}..."
                
<<<<<<< HEAD
                # Xử lý riêng cho lỗi 502 Bad Gateway và các lỗi kết nối
                if response.status_code == 502 or response.status_code >= 500:
                    retry_time = min(10 * (attempt % 6 + 1), 60)  # Tăng dần thời gian thử lại, tối đa 60s
                    self.update_status(f"Lỗi khi kiểm tra trạng thái: HTTP {response.status_code} - Thử lại sau {retry_time} giây")
                    self.root.after(retry_time * 1000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
                    return
                
=======
>>>>>>> b17c438c4225d19dc8edd19e9fc8d6d19961bb19
                # Nếu lỗi không phải 404, thử lại sau
                if response.status_code != 404 and attempt < 3:
                    self.update_status(f"Đang đợi API phản hồi... ({attempt+1}/3)")
                    self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
                    return
                
                self.update_status(error_msg)
                messagebox.showerror("Lỗi", error_msg)
                self.create_btn.configure(state="normal")
                if video_id in self.processing_videos:
                    del self.processing_videos[video_id]
                return
            
            try:
                status_data = response.json()
                
                # In phản hồi để debug
                print(f"Phản hồi trạng thái: {json.dumps(status_data)}")
                
                # Thay đổi ở đây: Truy cập đúng cấu trúc API {"code": 100, "data": {"status": "..."}}
                if "code" in status_data and "data" in status_data:
                    video_data = status_data["data"]
                    status = video_data.get("status", "")
                    
                    # Lấy thời lượng video nếu có
                    duration = video_data.get("duration", None)
                    duration_info = ""
                    
                    if duration is not None and isinstance(duration, (int, float)):
                        # Tính toán số credit đã sử dụng
                        credits_used = self.calculate_video_credits(duration)
                        
                        # Định dạng thông tin về thời lượng và credit
                        if credits_used is not None:
                            minutes = int(duration // 60)
                            seconds = int(duration % 60)
                            duration_formatted = f"{minutes}:{seconds:02d}"
                            duration_info = f" | Thời lượng: {duration_formatted} | Credit: {credits_used:.2f}"
                    
                    if status == "completed":
                        video_url = video_data.get("video_url", "")
                        
                        # Hiển thị thông báo hoàn thành
                        video_info = self.processing_videos.get(video_id, {})
                        filename = video_info.get("filename", "")
                        if filename:
                            self.update_status(f"Video cho file '{filename}' đã xử lý xong{duration_info}")
                        else:
                            self.update_status(f"Video đã xử lý xong: {video_id}{duration_info}")
                        
                        self.result_var.set(video_url)
                        
                        # Kiểm tra nếu đã bật tự động tải về và có thư mục tải về
                        if self.auto_download_var.get() and self.download_dir:
                            try:
                                # Tạo tên file mặc định từ tên file âm thanh nếu có
                                default_filename = f"{audio_filename}.mp4" if audio_filename else f"heygen_video_{video_id}.mp4"
                                file_path = os.path.join(self.download_dir, default_filename)
                                
                                # Kiểm tra xem file đã tồn tại chưa, nếu có thì thêm số vào tên file
                                counter = 1
                                while os.path.exists(file_path):
                                    base_name, ext = os.path.splitext(default_filename)
                                    new_name = f"{base_name}_{counter}{ext}"
                                    file_path = os.path.join(self.download_dir, new_name)
                                    counter += 1

                                self.update_status(f"Đang tự động tải video xuống: {os.path.basename(file_path)}...")
                                self.root.update()
                                
                                # Tải video
                                video_content = requests.get(video_url, proxies=self.client.proxies).content
                                
                                # Lưu vào file
                                with open(file_path, "wb") as video_file:
                                    video_file.write(video_content)
                                    
                                self.update_status(f"Đã tải video thành công: {os.path.basename(file_path)}{duration_info}")
                            except Exception as e:
                                error_msg = f"Lỗi khi tải video: {str(e)}"
                                self.update_status(error_msg)
                                print(error_msg)
                        else:
                            # Hiển thị hộp thoại hỏi người dùng có muốn tải video không
                            download = messagebox.askyesno("Tải video", f"Video đã được tạo thành công!{duration_info}\nBạn có muốn tải video về máy không?")
                            if download:
                                try:
                                    # Tạo tên file mặc định từ tên file âm thanh nếu có
                                    default_filename = f"{audio_filename}.mp4" if audio_filename else f"heygen_video_{video_id}.mp4"
                                    
                                    # Mở hộp thoại lưu file với tên mặc định
                                    file_path = filedialog.asksaveasfilename(
                                        defaultextension=".mp4",
                                        filetypes=[("MP4 files", "*.mp4")],
                                        title="Lưu video",
                                        initialfile=default_filename,
                                        initialdir=self.download_dir if self.download_dir else None
                                    )
                                    
                                    if file_path:
                                        self.update_status(f"Đang tải video xuống: {os.path.basename(file_path)}...")
                                        self.root.update()
                                        
                                        # Tải video
                                        video_content = requests.get(video_url, proxies=self.client.proxies).content
                                        
                                        # Lưu vào file
                                        with open(file_path, "wb") as video_file:
                                            video_file.write(video_content)
                                            
                                        self.update_status(f"Đã tải video thành công: {os.path.basename(file_path)}{duration_info}")
                                except Exception as e:
                                    error_msg = f"Lỗi khi tải video: {str(e)}"
                                    self.update_status(error_msg)
                                    messagebox.showerror("Lỗi", error_msg)
                        
                        # Xóa video này khỏi danh sách đang xử lý
                        if video_id in self.processing_videos:
                            del self.processing_videos[video_id]
                            
                        # Kích hoạt lại nút tạo nếu không còn video nào đang xử lý
                        if not self.processing_videos:
                            self.create_btn.configure(state="normal")
                        return
                    
                    elif status == "failed":
                        error_reason = video_data.get("error", "")
                        error_msg = f"Video xử lý thất bại: {error_reason}" if error_reason else f"Video xử lý thất bại: {video_id}"
                        self.update_status(error_msg)
                        messagebox.showerror("Lỗi", error_msg)
                        
                        # Xóa video này khỏi danh sách đang xử lý
                        if video_id in self.processing_videos:
                            del self.processing_videos[video_id]
                            
                        # Kích hoạt lại nút tạo nếu không còn video nào đang xử lý
                        if not self.processing_videos:
                            self.create_btn.configure(state="normal")
                        return
                    
                    # Nếu vẫn đang xử lý, kiểm tra lại sau 5 giây
                    remaining_seconds = (max_attempts - attempt) * 5
                    remaining_minutes = remaining_seconds // 60
                    remaining_seconds %= 60
                    
                    self.update_status(f"Video đang xử lý ({status}), đã đợi {(attempt+1)*5} giây... Còn lại: {remaining_minutes} phút {remaining_seconds} giây")
                    self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
                else:
                    # Fallback: Nếu cấu trúc không khớp, thử tìm status ở cấp cao nhất
                    status = status_data.get("status", "")
                    
                    if status == "completed":
                        video_url = status_data.get("video_url", "")
                        
                        # Lấy thời lượng video nếu có
                        duration = status_data.get("duration", None)
                        duration_info = ""
                        
                        if duration is not None and isinstance(duration, (int, float)):
                            # Tính toán số credit đã sử dụng
                            credits_used = self.calculate_video_credits(duration)
                            
                            # Định dạng thông tin về thời lượng và credit
                            if credits_used is not None:
                                minutes = int(duration // 60)
                                seconds = int(duration % 60)
                                duration_formatted = f"{minutes}:{seconds:02d}"
                                duration_info = f" | Thời lượng: {duration_formatted} | Credit: {credits_used:.2f}"
                        
                        self.update_status(f"Video đã xử lý xong: {video_id}{duration_info}")
                        self.result_var.set(video_url)
                        
                        # Kiểm tra nếu đã bật tự động tải về và có thư mục tải về
                        if self.auto_download_var.get() and self.download_dir:
                            try:
                                # Tạo tên file mặc định từ tên file âm thanh nếu có
                                default_filename = f"{audio_filename}.mp4" if audio_filename else f"heygen_video_{video_id}.mp4"
                                file_path = os.path.join(self.download_dir, default_filename)
                                
                                # Kiểm tra xem file đã tồn tại chưa, nếu có thì thêm số vào tên file
                                counter = 1
                                while os.path.exists(file_path):
                                    base_name, ext = os.path.splitext(default_filename)
                                    new_name = f"{base_name}_{counter}{ext}"
                                    file_path = os.path.join(self.download_dir, new_name)
                                    counter += 1

                                self.update_status(f"Đang tự động tải video xuống: {os.path.basename(file_path)}...")
                                self.root.update()
                                
                                # Tải video
                                video_content = requests.get(video_url, proxies=self.client.proxies).content
                                
                                # Lưu vào file
                                with open(file_path, "wb") as video_file:
                                    video_file.write(video_content)
                                    
                                self.update_status(f"Đã tải video thành công: {os.path.basename(file_path)}{duration_info}")
                            except Exception as e:
                                error_msg = f"Lỗi khi tải video: {str(e)}"
                                self.update_status(error_msg)
                                print(error_msg)
                        else:
                            # Hiển thị hộp thoại hỏi người dùng có muốn tải video không
                            download = messagebox.askyesno("Tải video", f"Video đã được tạo thành công!{duration_info}\nBạn có muốn tải video về máy không?")
                            if download:
                                try:
                                    # Tạo tên file mặc định từ tên file âm thanh nếu có
                                    default_filename = f"{audio_filename}.mp4" if audio_filename else f"heygen_video_{video_id}.mp4"
                                    
                                    # Mở hộp thoại lưu file với tên mặc định
                                    file_path = filedialog.asksaveasfilename(
                                        defaultextension=".mp4",
                                        filetypes=[("MP4 files", "*.mp4")],
                                        title="Lưu video",
                                        initialfile=default_filename,
                                        initialdir=self.download_dir if self.download_dir else None
                                    )
                                    
                                    if file_path:
                                        self.update_status(f"Đang tải video xuống: {os.path.basename(file_path)}...")
                                        self.root.update()
                                        
                                        # Tải video
                                        video_content = requests.get(video_url, proxies=self.client.proxies).content
                                        
                                        # Lưu vào file
                                        with open(file_path, "wb") as video_file:
                                            video_file.write(video_content)
                                            
                                        self.update_status(f"Đã tải video thành công: {os.path.basename(file_path)}{duration_info}")
                                except Exception as e:
                                    error_msg = f"Lỗi khi tải video: {str(e)}"
                                    self.update_status(error_msg)
                                    messagebox.showerror("Lỗi", error_msg)
                        
                        # Xóa video này khỏi danh sách đang xử lý
                        if video_id in self.processing_videos:
                            del self.processing_videos[video_id]
                            
                        # Kích hoạt lại nút tạo nếu không còn video nào đang xử lý
                        if not self.processing_videos:
                            self.create_btn.configure(state="normal")
                        return
                    elif status == "failed":
                        error_reason = status_data.get("error", "")
                        error_msg = f"Video xử lý thất bại: {error_reason}" if error_reason else f"Video xử lý thất bại: {video_id}"
                        self.update_status(error_msg)
                        messagebox.showerror("Lỗi", error_msg)
                        
                        # Xóa video này khỏi danh sách đang xử lý
                        if video_id in self.processing_videos:
                            del self.processing_videos[video_id]
                            
                        # Kích hoạt lại nút tạo nếu không còn video nào đang xử lý
                        if not self.processing_videos:
                            self.create_btn.configure(state="normal")
                        return
                    else:
                        # Nếu không tìm thấy trạng thái, tiếp tục kiểm tra
                        remaining_seconds = (max_attempts - attempt) * 5
                        remaining_minutes = remaining_seconds // 60
                        remaining_seconds %= 60
                        
                        self.update_status(f"Đang đợi trạng thái từ API, đã đợi {(attempt+1)*5} giây... Còn lại: {remaining_minutes} phút {remaining_seconds} giây")
                        self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
            except json.JSONDecodeError:
                # Nếu không thể parse JSON, có thể API đang xử lý, thử lại sau
                print(f"Không thể parse JSON, đang thử lại sau 5 giây. Response: {response.text[:200]}...")
<<<<<<< HEAD
                
                # Hiển thị thông báo hữu ích cho người dùng
                if "<html>" in response.text:
                    err_msg = f"Lỗi khi kiểm tra trạng thái: HTTP {response.status_code} - {response.text[:100]}"
                    self.update_status(err_msg)
                    
                # Tăng thời gian chờ nếu gặp lỗi JSON decode nhiều lần
                retry_time = min(10 * (attempt % 6 + 1), 60)  # Tăng dần thời gian, tối đa 60s
                self.root.after(retry_time * 1000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
        except Exception as e:
            error_msg = f"Lỗi khi kiểm tra trạng thái: {str(e)}"
            print(f"Chi tiết lỗi: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Đối với các lỗi kết nối, thử lại sau thay vì hiển thị lỗi cho người dùng
            if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout, 
                             requests.exceptions.RequestException)):
                retry_time = min(15 * (attempt % 4 + 1), 60)  # Tăng dần thời gian, tối đa 60s
                self.update_status(f"Lỗi kết nối khi kiểm tra trạng thái - Thử lại sau {retry_time} giây")
                self.root.after(retry_time * 1000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
                return
                
            # Với các lỗi khác, nếu còn trong giới hạn số lần thử, thử lại sau
            if attempt < 5:  # Cho phép thử lại vài lần với các lỗi không rõ nguyên nhân
                self.update_status(f"Lỗi không xác định khi kiểm tra trạng thái - Thử lại sau 10 giây")
                self.root.after(10000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
                return
                
            # Hiển thị lỗi cho người dùng nếu đã thử nhiều lần không thành công
            self.update_status(error_msg)
            messagebox.showerror("Lỗi", error_msg)
=======
                self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
        except Exception as e:
            error_msg = f"Lỗi khi kiểm tra trạng thái: {str(e)}"
            print(f"Lỗi chi tiết: {str(e)}, {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Nếu có lỗi, thử lại vài lần trước khi bỏ
            if attempt < 3:
                self.update_status(f"Lỗi khi kiểm tra ({attempt+1}/3), thử lại sau 5 giây...")
                self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts, audio_filename))
            else:
                self.update_status(error_msg)
                # Xóa video này khỏi danh sách đang xử lý
                if video_id in self.processing_videos:
                    del self.processing_videos[video_id]
                
                # Kích hoạt lại nút tạo nếu không còn video nào đang xử lý
                if not self.processing_videos:
                    self.create_btn.configure(state="normal")
>>>>>>> b17c438c4225d19dc8edd19e9fc8d6d19961bb19
    
    def format_remaining_time(self, seconds):
        """
        Định dạng thời gian còn lại dưới dạng HH:MM:SS hoặc MM:SS
        
        Args:
            seconds: Số giây còn lại
            
        Returns:
            Chuỗi định dạng "HH:MM:SS" nếu lớn hơn 60 phút, hoặc "MM:SS" nếu không
        """
        if seconds is None:
            return None
            
        # Chuyển đổi thành giờ, phút, giây
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        # Nếu có giờ, hiển thị định dạng HH:MM:SS
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            # Không có giờ, hiển thị định dạng MM:SS
            return f"{minutes:02d}:{secs:02d}"
    
    def calculate_credits_from_quota(self, quota):
        """
        Tính toán số credit API từ quota
        
        Args:
            quota: Số quota (thường là số giây) từ API
            
        Returns:
            Số credit API và thời lượng tối đa có thể tạo (phút)
        """
        if quota is None or not isinstance(quota, (int, float)):
            return None, None
            
        # Tính số credit: quota/60
        credits = quota / 60
        
        # Tính thời lượng tối đa có thể tạo: credit * 2 (phút)
        max_duration_minutes = credits * 2
        
        return credits, max_duration_minutes
    
    def format_credits_info(self, credits, max_duration_minutes):
        """
        Định dạng thông tin về số credit và thời lượng tối đa
        
        Args:
            credits: Số credit API
            max_duration_minutes: Thời lượng tối đa có thể tạo (phút)
            
        Returns:
            Chuỗi thông tin định dạng
        """
        if credits is None or max_duration_minutes is None:
            return "Không xác định"
            
        # Chuyển đổi thời lượng tối đa thành phút và giây
        max_duration_mins = int(max_duration_minutes)
        max_duration_secs = int((max_duration_minutes - max_duration_mins) * 60)
        
        # Định dạng thông tin
        max_duration_text = f"{max_duration_mins}:{max_duration_secs:02d}"
        
        return f"{credits:.2f} credit (tối đa {max_duration_text} phút)"
            
    def check_remaining_quota(self):
        """
        Kiểm tra và hiển thị thông tin về số token còn lại
        """
        self.update_status("Đang kiểm tra số credit API còn lại...")
        self.root.update()
        
        # Lấy thông tin quota
        quota_response = self.client.get_remaining_quota()
        
        try:
            # Xử lý phản hồi để lấy thông tin quota
            remaining_quota = None
            
            # Kiểm tra nếu error là None hoặc null (sẽ được chuyển thành None trong Python)
            if quota_response.get("error") is None and "data" in quota_response:
                quota_data = quota_response["data"]
                
                # Kiểm tra các định dạng phản hồi có thể có
                if "remaining_quota" in quota_data:
                    remaining_quota = quota_data["remaining_quota"]
                elif "remaining_tokens" in quota_data:
                    remaining_quota = quota_data["remaining_tokens"]
                elif "quota" in quota_data and "remaining" in quota_data["quota"]:
                    remaining_quota = quota_data["quota"]["remaining"]
                
                # In ra thông tin debug
                print(f"Phản hồi quota: {json.dumps(quota_response)}")
                print(f"Remaining quota: {remaining_quota}")
                
                # Tính toán số credit và thời lượng tối đa
                if remaining_quota is not None and isinstance(remaining_quota, (int, float)):
                    credits, max_duration_minutes = self.calculate_credits_from_quota(remaining_quota)
                    
                    # Định dạng thông tin
                    credits_info = self.format_credits_info(credits, max_duration_minutes)
                    
                    # Chuyển đổi thời lượng tối đa thành giây
                    max_duration_seconds = max_duration_minutes * 60 if max_duration_minutes is not None else None
                    
                    # Định dạng thời gian tối đa
                    if max_duration_seconds is not None:
                        self.remaining_time_format = self.format_remaining_time(max_duration_seconds)
                    else:
                        self.remaining_time_format = None
                    
                    # Hiển thị trong trạng thái
                    self.update_status("Đã cập nhật thông tin credit API")
                    
                    # Hiển thị thông báo
                    messagebox.showinfo("Thông tin credit API", f"Credit còn lại: {credits_info}")
                    return
            
            # Nếu không lấy được thông tin quota
            self.remaining_time_format = None
            self.update_status("Không thể lấy thông tin về số credit API còn lại")
            messagebox.showinfo("Thông tin credit API", "Không thể lấy thông tin về số credit API còn lại")
            
        except Exception as e:
            error_msg = str(e)
            self.remaining_time_format = None
            self.update_status(f"Không thể lấy thông tin credit API: {error_msg}")
            messagebox.showerror("Lỗi", f"Không thể lấy thông tin credit API: {error_msg}")
            
    def verify_api_key(self):
        """
        Kiểm tra API Key hiện tại có hợp lệ không bằng cách sử dụng API v2
        và hiển thị số token còn lại
        """
        self.update_status("Đang kiểm tra API Key...")
        self.root.update()
        
        # Sử dụng trực tiếp API v2 để kiểm tra
        url = f"{self.client.BASE_URL}/v2/avatars"
        
        try:
            response = requests.get(url, headers=self.client.headers, proxies=self.client.proxies)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data:
                        avatar_count = len(data["data"]["avatars"]) if "avatars" in data["data"] else len(data["data"])
                        
                        # Lấy thông tin về số token còn lại
                        quota_response = self.client.get_remaining_quota()
                        
                        try:
                            # Kiểm tra nếu error là None hoặc null (sẽ được chuyển thành None trong Python)
                            if quota_response.get("error") is None and "data" in quota_response:
                                quota_data = quota_response["data"]
                                
                                # Kiểm tra các định dạng phản hồi có thể có
                                remaining_quota = None
                                if "remaining_quota" in quota_data:
                                    remaining_quota = quota_data["remaining_quota"]
                                elif "remaining_tokens" in quota_data:
                                    remaining_quota = quota_data["remaining_tokens"]
                                elif "quota" in quota_data and "remaining" in quota_data["quota"]:
                                    remaining_quota = quota_data["quota"]["remaining"]
                                
                                # In ra thông tin debug
                                print(f"Phản hồi quota: {json.dumps(quota_response)}")
                                print(f"Remaining quota: {remaining_quota}")
                                
                                # Tính toán số credit và thời lượng tối đa
                                if remaining_quota is not None and isinstance(remaining_quota, (int, float)):
                                    credits, max_duration_minutes = self.calculate_credits_from_quota(remaining_quota)
                                    
                                    # Định dạng thông tin
                                    credits_info = self.format_credits_info(credits, max_duration_minutes)
                                    
                                    # Chuyển đổi thời lượng tối đa thành giây
                                    max_duration_seconds = max_duration_minutes * 60 if max_duration_minutes is not None else None
                                    
                                    # Định dạng thời gian tối đa
                                    if max_duration_seconds is not None:
                                        self.remaining_time_format = self.format_remaining_time(max_duration_seconds)
                                    else:
                                        self.remaining_time_format = None
                                    
                                    # Hiển thị trong trạng thái
                                    self.update_status(f"API Key hợp lệ. Tìm thấy {avatar_count} avatars")
                                    
                                    # Hiển thị thông báo với số token còn lại
                                    messagebox.showinfo("Thành công", f"API Key hợp lệ!\nTìm thấy {avatar_count} avatars\nCredit còn lại: {credits_info}")
                                    return True
                        except Exception as e:
                            print(f"Lỗi khi xử lý thông tin quota: {e}")
                        
                        # Nếu không lấy được thông tin quota hoặc có lỗi
                        self.remaining_time_format = None
                        self.update_status(f"API Key hợp lệ. Tìm thấy {avatar_count} avatars")
                        messagebox.showinfo("Thành công", f"API Key hợp lệ! Tìm thấy {avatar_count} avatars\n(Không thể lấy thông tin credit)")
                        return True
                    else:
                        self.remaining_time_format = None
                        self.update_status("API Key hợp lệ")
                        messagebox.showinfo("Thành công", "API Key hợp lệ!")
                    return True
                except Exception as e:
                    self.remaining_time_format = None
                    self.update_status(f"API Key hợp lệ, nhưng có lỗi khi phân tích phản hồi: {e}")
                    messagebox.showinfo("Thành công", "API Key hợp lệ!")
                    return True
            elif response.status_code == 401:
                self.remaining_time_format = None
                self.update_status("API Key không hợp lệ (401 Unauthorized)")
                messagebox.showerror("Lỗi", "API Key không hợp lệ!")
                return False
            else:
                error_text = f"Mã trạng thái: {response.status_code}"
                try:
                    error_data = response.json()
                    error_text += f", Phản hồi: {json.dumps(error_data)}"
                except:
                    if response.text:
                        error_text += f", Phản hồi: {response.text[:200]}..."
                
                self.remaining_time_format = None
                self.update_status(f"Lỗi khi kiểm tra API Key ({error_text})")
                messagebox.showerror("Lỗi", f"Không thể kiểm tra API Key.\n{error_text}")
                return False
        except Exception as e:
            self.remaining_time_format = None
            self.update_status(f"Lỗi khi kiểm tra API Key: {e}")
            messagebox.showerror("Lỗi", f"Lỗi kết nối khi kiểm tra API Key: {e}")
            return False


if __name__ == "__main__":
    root = tk.Tk()
    app = HeyGenVideoCreatorApp(root)
    root.mainloop() 