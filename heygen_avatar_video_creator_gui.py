import sys
import os
import time
import json
import requests
import traceback
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, List, Optional


class HeyGenClient:
    """
    Client để tương tác với HeyGen API để tạo video avatar
    """
    
    BASE_URL = "https://api.heygen.com"
    API_KEY = "OTJmNzE4N2EwZmJkNGY4ZDkzY2VmNTc4NmJlMDlkYmQtMTc0NTM0MjE3Mg=="
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Khởi tạo client với API key
        
        Args:
            api_key: API key của HeyGen, sẽ sử dụng API key mặc định nếu không được cung cấp
        """
        self.api_key = api_key or self.API_KEY
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
    
    def get_all_avatars(self) -> Dict[str, Any]:
        """
        Lấy danh sách tất cả avatars có sẵn
        
        Returns:
            Dict chứa thông tin về tất cả avatars
        """
        url = f"{self.BASE_URL}/v2/avatars"
        try:
            response = requests.get(url, headers=self.headers)
            
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
            
            response = requests.post(url, files=files, headers=headers)
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
            response = requests.post(url, json=payload, headers=self.headers)
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
            response = requests.get(url, headers=self.headers)
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
            response = requests.get(url, headers=self.headers)
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


class HeyGenVideoCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HeyGen Avatar Video Creator")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        self.client = HeyGenClient()
        self.avatars = []
        self.selected_avatar_id = None
        self.audio_file_path = None
        self.audio_asset_id = None
        
        self.create_ui()
        
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
        
        # Nội dung Tab tạo video
        self.create_tab_content(create_tab)
        
        # Nội dung Tab quản lý video
        self.create_manage_tab_content(manage_tab)
        
    def create_tab_content(self, parent_frame):
        # API Key
        api_frame = ttk.LabelFrame(parent_frame, text="API Key", padding="5")
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.api_key_var = tk.StringVar(value=self.client.API_KEY)
        ttk.Label(api_frame, text="API Key:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(api_frame, textvariable=self.api_key_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        api_buttons_frame = ttk.Frame(api_frame)
        api_buttons_frame.pack(side=tk.LEFT)
        
        ttk.Button(api_buttons_frame, text="Cập nhật", command=self.update_api_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(api_buttons_frame, text="Kiểm tra", command=self.verify_api_key).pack(side=tk.LEFT, padx=5)
        
        # Frame cho danh sách avatars
        avatars_frame = ttk.LabelFrame(parent_frame, text="Danh sách Avatars", padding="5")
        avatars_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Nút tải danh sách avatars
        ttk.Button(avatars_frame, text="Tải danh sách avatars", command=self.load_avatars).pack(anchor=tk.W, padx=5, pady=5)
        
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
        
        # Tạo video button
        buttons_frame = ttk.Frame(parent_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.create_btn = ttk.Button(buttons_frame, text="Tạo Video", command=self.create_video, state="disabled")
        self.create_btn.pack(side=tk.RIGHT, padx=5)
        
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
        columns = ("id", "status", "created_at", "type")
        self.videos_tree = ttk.Treeview(videos_frame, columns=columns, show="headings", selectmode="browse")
        
        # Định nghĩa các tiêu đề cột
        self.videos_tree.heading("id", text="Video ID")
        self.videos_tree.heading("status", text="Trạng thái")
        self.videos_tree.heading("created_at", text="Thời gian tạo")
        self.videos_tree.heading("type", text="Loại")
        
        # Định nghĩa độ rộng cột
        self.videos_tree.column("id", width=180)
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
            self.client.API_KEY = api_key  # Cập nhật API_KEY trong client
            self.client.api_key = api_key  # Cập nhật api_key trong client
            # Cập nhật headers với API key mới
            self.client.headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "x-api-key": api_key
            }
            self.update_status(f"Đã cập nhật API Key: {api_key[:5]}...{api_key[-5:]} (ẩn giữa để bảo mật)")
        else:
            messagebox.showerror("Lỗi", "API Key không được để trống")
            
    def verify_api_key(self):
        """
        Kiểm tra API Key hiện tại có hợp lệ không bằng cách sử dụng API v2
        """
        self.update_status("Đang kiểm tra API Key...")
        self.root.update()
        
        # Sử dụng trực tiếp API v2 để kiểm tra
        url = f"{self.client.BASE_URL}/v2/avatars"
        
        try:
            response = requests.get(url, headers=self.client.headers)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data:
                        avatar_count = len(data["data"]["avatars"]) if "avatars" in data["data"] else len(data["data"])
                        self.update_status(f"API Key hợp lệ. Tìm thấy {avatar_count} avatars")
                        messagebox.showinfo("Thành công", f"API Key hợp lệ! Tìm thấy {avatar_count} avatars")
                    else:
                        self.update_status("API Key hợp lệ")
                        messagebox.showinfo("Thành công", "API Key hợp lệ!")
                    return True
                except Exception as e:
                    self.update_status(f"API Key hợp lệ, nhưng có lỗi khi phân tích phản hồi: {e}")
                    messagebox.showinfo("Thành công", "API Key hợp lệ!")
                    return True
            elif response.status_code == 401:
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
                
                self.update_status(f"Lỗi khi kiểm tra API Key ({error_text})")
                messagebox.showerror("Lỗi", f"Không thể kiểm tra API Key.\n{error_text}")
                return False
        except Exception as e:
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
                self.process_avatars(avatars_data)
                success = True
            else:
                self.update_status("Không tìm thấy avatar nào")
        elif "data" in response and isinstance(response["data"], list):
            # Cấu trúc thay thế (mảng avatars trực tiếp trong data)
            avatars_data = response["data"]
            
            if avatars_data:
                self.avatars = avatars_data
                self.process_avatars_alternative(avatars_data)
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
    
    def process_avatars(self, avatars_data):
        """Xử lý danh sách avatars với cấu trúc dữ liệu chuẩn"""
        for avatar in avatars_data:
            self.avatars_tree.insert("", tk.END, values=(
                avatar["avatar_id"],
                avatar["avatar_name"],
                avatar.get("gender", ""),
                "Có" if avatar.get("premium", False) else "Không"
            ))
        self.update_status(f"Đã tải {len(avatars_data)} avatars")
    
    def process_avatars_alternative(self, avatars_data):
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
    
    def on_avatar_selected(self, event):
        selection = self.avatars_tree.selection()
        if selection:
            item = selection[0]
            avatar_id = self.avatars_tree.item(item, "values")[0]
            self.selected_avatar_id = avatar_id
            self.update_status(f"Đã chọn avatar: {avatar_id}")
            
            # Cập nhật trạng thái nút tạo video
            self.update_create_button_state()
    
    def select_audio_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file audio",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.m4a")]
        )
        if file_path:
            self.audio_file_path = file_path
            self.audio_file_var.set(file_path)
            self.update_status(f"Đã chọn file: {file_path}")
            self.upload_btn.configure(state="normal")
            
            # Reset audio asset ID khi chọn file mới
            self.audio_asset_id = None
            self.audio_asset_var.set("")
            
            # Cập nhật trạng thái nút tạo video
            self.update_create_button_state()
    
    def upload_audio(self):
        if not self.audio_file_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn file âm thanh trước")
            return
        
        self.update_status(f"Đang upload file âm thanh: {os.path.basename(self.audio_file_path)}...")
        self.root.update()
        
        # Vô hiệu hóa nút upload
        self.upload_btn.configure(state="disabled")
        
        try:
            # Chuẩn bị multipart form data
            with open(self.audio_file_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(self.audio_file_path)
            
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
            response = requests.post(upload_url, headers=headers, data=file_content)
            
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
                        self.audio_asset_id = response_data["data"]["id"]
                        self.audio_asset_var.set(self.audio_asset_id)
                        
                        upload_success_msg = f"Đã upload file thành công. Asset ID: {self.audio_asset_id}"
                        self.update_status(upload_success_msg)
                        messagebox.showinfo("Thành công", upload_success_msg)
                        
                        # Cập nhật trạng thái nút tạo video
                        self.update_create_button_state()
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
        if self.selected_avatar_id and self.audio_asset_id:
            self.create_btn.configure(state="normal")
        else:
            self.create_btn.configure(state="disabled")
    
    def create_video(self):
        if not self.selected_avatar_id:
            messagebox.showerror("Lỗi", "Vui lòng chọn một avatar")
            return
        
        if not self.audio_asset_id:
            messagebox.showerror("Lỗi", "Vui lòng upload file âm thanh trước")
            return
        
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            bg_color = self.bg_color_var.get()
            
            self.update_status(f"Đang tạo video với avatar ID: {self.selected_avatar_id}...")
            self.root.update()
            
            # Vô hiệu hóa nút tạo video
            self.create_btn.configure(state="disabled")
            
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
            
            # Gửi request
            response = requests.post(url, json=payload, headers=self.client.headers)
            
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
                    self.create_btn.configure(state="normal")
                    return
                
                if "data" in video_data and "video_id" in video_data["data"]:
                    video_id = video_data["data"]["video_id"]
                    self.update_status(f"Video đang được tạo với ID: {video_id}")
                    
                    # Bắt đầu kiểm tra trạng thái video
                    self.root.after(100, lambda: self.check_video_status(video_id))
                else:
                    error_msg = "Không thể tạo video: Không tìm thấy video_id trong phản hồi"
                    if isinstance(video_data, dict):
                        error_msg += f": {json.dumps(video_data)}"
                    self.update_status(error_msg)
                    messagebox.showerror("Lỗi", error_msg)
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
                self.create_btn.configure(state="normal")
        
        except ValueError as e:
            messagebox.showerror("Lỗi", f"Lỗi định dạng: {str(e)}")
            self.create_btn.configure(state="normal")
        except Exception as e:
            error_msg = f"Lỗi không xác định: {str(e)}"
            print(f"Lỗi chi tiết: {str(e)}, {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Lỗi", error_msg)
            self.create_btn.configure(state="normal")
    
    def check_video_status(self, video_id, attempt=0, max_attempts=180):
        if attempt >= max_attempts:
            self.update_status("Đã hết thời gian chờ xử lý video")
            messagebox.showerror("Lỗi", "Đã hết thời gian chờ xử lý video")
            self.create_btn.configure(state="normal")
            return
        
        try:
            # Sử dụng endpoint chính xác theo tài liệu API
            url = f"{self.client.BASE_URL}/v1/video_status.get?video_id={video_id}"
            response = requests.get(url, headers=self.client.headers)
            
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
                
                # Nếu lỗi không phải 404, thử lại sau
                if response.status_code != 404 and attempt < 3:
                    self.update_status(f"Đang đợi API phản hồi... ({attempt+1}/3)")
                    self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts))
                    return
                
                self.update_status(error_msg)
                messagebox.showerror("Lỗi", error_msg)
                self.create_btn.configure(state="normal")
                return
            
            try:
                status_data = response.json()
                
                # In phản hồi để debug
                print(f"Phản hồi trạng thái: {json.dumps(status_data)}")
                
                # Thay đổi ở đây: Truy cập đúng cấu trúc API {"code": 100, "data": {"status": "..."}}
                if "code" in status_data and "data" in status_data:
                    video_data = status_data["data"]
                    status = video_data.get("status", "")
                    
                    if status == "completed":
                        video_url = video_data.get("video_url", "")
                        
                        self.update_status(f"Video đã xử lý xong: {video_id}")
                        self.result_var.set(video_url)
                        
                        # Hiển thị hộp thoại hỏi người dùng có muốn tải video không
                        download = messagebox.askyesno("Tải video", "Video đã được tạo thành công! Bạn có muốn tải video về máy không?")
                        if download:
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
                                    video_content = requests.get(video_url).content
                                    
                                    # Lưu vào file
                                    with open(file_path, "wb") as video_file:
                                        video_file.write(video_content)
                                        
                                    self.update_status(f"Đã tải video thành công: {os.path.basename(file_path)}")
                                    messagebox.showinfo("Thành công", f"Đã tải video thành công: {os.path.basename(file_path)}")
                            except Exception as e:
                                error_msg = f"Lỗi khi tải video: {str(e)}"
                                self.update_status(error_msg)
                                messagebox.showerror("Lỗi", error_msg)
                        
                        messagebox.showinfo("Thành công", "Video đã được tạo thành công!")
                        self.create_btn.configure(state="normal")
                        return
                    
                    elif status == "failed":
                        error_reason = video_data.get("error", "")
                        error_msg = f"Video xử lý thất bại: {error_reason}" if error_reason else f"Video xử lý thất bại: {video_id}"
                        self.update_status(error_msg)
                        messagebox.showerror("Lỗi", error_msg)
                        self.create_btn.configure(state="normal")
                        return
                    
                    # Nếu vẫn đang xử lý, kiểm tra lại sau 5 giây
                    self.update_status(f"Video đang xử lý ({status}), đã đợi {(attempt+1)*5} giây...")
                    self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts))
                else:
                    # Fallback: Nếu cấu trúc không khớp, thử tìm status ở cấp cao nhất
                    status = status_data.get("status", "")
                    
                    if status == "completed":
                        video_url = status_data.get("video_url", "")
                        self.update_status(f"Video đã xử lý xong: {video_id}")
                        self.result_var.set(video_url)
                        messagebox.showinfo("Thành công", "Video đã được tạo thành công!")
                        self.create_btn.configure(state="normal")
                        return
                    elif status == "failed":
                        error_reason = status_data.get("error", "")
                        error_msg = f"Video xử lý thất bại: {error_reason}" if error_reason else f"Video xử lý thất bại: {video_id}"
                        self.update_status(error_msg)
                        messagebox.showerror("Lỗi", error_msg)
                        self.create_btn.configure(state="normal")
                        return
                    else:
                        # Nếu không tìm thấy trạng thái, tiếp tục kiểm tra
                        self.update_status(f"Đang đợi trạng thái từ API, đã đợi {(attempt+1)*5} giây...")
                        self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts))
            except json.JSONDecodeError:
                # Nếu không thể parse JSON, có thể API đang xử lý, thử lại sau
                self.update_status(f"Đang đợi API phản hồi... ({attempt+1}/3)")
                self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts))
        except Exception as e:
            error_msg = f"Lỗi khi kiểm tra trạng thái video: {str(e)}"
            print(f"Lỗi chi tiết: {str(e)}, {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Thử lại nếu chưa vượt quá số lần thử
            if attempt < 3:
                self.update_status(f"Gặp lỗi, thử lại sau... ({attempt+1}/3)")
                self.root.after(5000, lambda: self.check_video_status(video_id, attempt+1, max_attempts))
            else:
                self.update_status(error_msg)
                messagebox.showerror("Lỗi", error_msg)
                self.create_btn.configure(state="normal")
    
    def update_status(self, message):
        self.status_var.set(message)
        print(message)
    
    def copy_result_url(self):
        url = self.result_var.get()
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.update_status("Đã sao chép URL vào clipboard")
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
                    
                    self.videos_tree.insert("", tk.END, values=(
                        video_id,
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
                response = requests.get(url, headers=self.client.headers)
                response.raise_for_status()
                data = response.json()
                
                if "data" in data:
                    video_data = data["data"]
                    video_url = video_data.get("video_url", "")
                    self.video_url_var.set(video_url)
                    
                    status = video_data.get("status", "")
                    self.update_status(f"Đã chọn video: {video_id}, trạng thái: {status}")
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
                video_content = requests.get(video_url).content
                
                # Lưu vào file
                with open(file_path, "wb") as video_file:
                    video_file.write(video_content)
                    
                self.update_status(f"Đã tải video thành công: {os.path.basename(file_path)}")
                messagebox.showinfo("Thành công", f"Đã tải video thành công: {os.path.basename(file_path)}")
        except Exception as e:
            error_msg = f"Lỗi khi tải video: {str(e)}"
            self.update_status(error_msg)
            messagebox.showerror("Lỗi", error_msg)
    
    def copy_video_url(self):
        url = self.video_url_var.get()
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.update_status("Đã sao chép URL video vào clipboard")
        else:
            self.update_status("Không có URL để sao chép")


if __name__ == "__main__":
    root = tk.Tk()
    app = HeyGenVideoCreatorApp(root)
    root.mainloop() 