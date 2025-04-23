import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import asyncio
import threading
import os
import json
import subprocess
import webbrowser
import httpx
import base64
from pathlib import Path

# Thư mục lưu video
VIDEOS_DIR = Path.home() / "Videos" / "HeyGen"

class HeyGenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HeyGen MCP Desktop")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # API key
        self.api_key = tk.StringVar()
        self.api_key.set(os.environ.get("HEYGEN_API_KEY", ""))
        
        # Biến lưu dữ liệu
        self.voices = []
        self.avatar_groups = []
        self.avatars = []
        self.current_video_id = None
        
        # Tạo thư mục lưu video nếu chưa tồn tại
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        
        self.create_widgets()
        
        # Kiểm tra cài đặt
        self.check_installation()
    
    def check_installation(self):
        try:
            import heygen_mcp
            self.log("Đã tìm thấy gói HeyGen MCP.")
        except ImportError:
            messagebox.showerror("Lỗi", "Không tìm thấy gói heygen_mcp. Vui lòng cài đặt trước.")
            self.log("Lỗi: Không tìm thấy gói heygen_mcp!")
    
    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab cấu hình
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Cấu hình")
        
        # Tab tạo video
        video_frame = ttk.Frame(notebook)
        notebook.add(video_frame, text="Tạo Video")
        
        # Tab kiểm tra video
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="Trạng thái Video")
        
        # Tab giới thiệu
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="Giới thiệu")
        
        # Frame log
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Tạo widget cho các tab
        self.create_config_tab(config_frame)
        self.create_video_tab(video_frame)
        self.create_status_tab(status_frame)
        self.create_about_tab(about_frame)
        self.create_log_area(log_frame)
    
    def create_config_tab(self, parent):
        # Frame cho API key
        api_frame = ttk.LabelFrame(parent, text="Cấu hình API")
        api_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(api_frame, textvariable=self.api_key, width=50, show="*").grid(row=0, column=1, padx=5, pady=5)
        
        show_key = tk.BooleanVar()
        show_key.set(False)
        
        def toggle_key_visibility():
            entry_widgets = [w for w in api_frame.winfo_children() if isinstance(w, ttk.Entry)]
            if entry_widgets:
                entry_widgets[0].config(show="" if show_key.get() else "*")
        
        ttk.Checkbutton(api_frame, text="Hiện API Key", variable=show_key, 
                        command=toggle_key_visibility).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame cho các thao tác
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="Lưu API Key", 
                   command=self.save_api_key).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(action_frame, text="Kiểm tra số dư Credit", 
                   command=self.check_credits).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(action_frame, text="Lấy danh sách giọng nói", 
                   command=self.get_voices).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(action_frame, text="Lấy danh sách nhóm avatar", 
                   command=self.get_avatar_groups).grid(row=0, column=3, padx=5, pady=5)
    
    def create_video_tab(self, parent):
        # Frame chọn avatar
        avatar_frame = ttk.LabelFrame(parent, text="Chọn Avatar")
        avatar_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(avatar_frame, text="Nhóm Avatar:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Combobox cho nhóm avatar
        self.avatar_group_combo = ttk.Combobox(avatar_frame, width=40, state="readonly")
        self.avatar_group_combo.grid(row=0, column=1, padx=5, pady=5)
        self.avatar_group_combo.bind("<<ComboboxSelected>>", self.on_group_selected)
        
        ttk.Label(avatar_frame, text="Avatar:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Combobox cho avatar
        self.avatar_combo = ttk.Combobox(avatar_frame, width=40, state="readonly")
        self.avatar_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Frame chọn giọng nói
        voice_frame = ttk.LabelFrame(parent, text="Chọn Giọng nói")
        voice_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(voice_frame, text="Giọng nói:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Combobox cho giọng nói
        self.voice_combo = ttk.Combobox(voice_frame, width=40, state="readonly")
        self.voice_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Thêm nút tải lên file audio
        ttk.Button(voice_frame, text="Tải lên audio tùy chỉnh", 
                  command=self.upload_custom_audio).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame nội dung
        content_frame = ttk.LabelFrame(parent, text="Nội dung Video")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(content_frame, text="Tiêu đề:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.title_entry = ttk.Entry(content_frame, width=50)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(content_frame, text="Nội dung:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.NW)
        self.text_content = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, width=40, height=8)
        self.text_content.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # Nút tạo video
        ttk.Button(parent, text="Tạo Video", 
                   command=self.generate_video).pack(pady=10)
    
    def create_status_tab(self, parent):
        # Frame kiểm tra trạng thái
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(status_frame, text="ID Video:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.video_id_entry = ttk.Entry(status_frame, width=40)
        self.video_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(status_frame, text="Kiểm tra trạng thái", 
                   command=self.check_video_status).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame thông tin video
        info_frame = ttk.LabelFrame(parent, text="Thông tin Video")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(info_frame, text="Trạng thái:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.status_label = ttk.Label(info_frame, text="Chưa có thông tin")
        self.status_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_frame, text="URL Video:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_label = ttk.Label(info_frame, text="", foreground="blue", cursor="hand2")
        self.url_label.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.url_label.bind("<Button-1>", self.open_url)
        
        ttk.Button(info_frame, text="Mở thư mục chứa video", 
                   command=self.open_videos_folder).grid(row=2, column=0, columnspan=2, padx=5, pady=10)
    
    def create_about_tab(self, parent):
        about_text = """
        HeyGen MCP Desktop
        
        Ứng dụng giao diện cho HeyGen MCP Server
        
        Sử dụng:
        1. Nhập API key từ HeyGen
        2. Lấy danh sách giọng nói và avatar
        3. Tạo video với avatar AI
        4. Kiểm tra trạng thái video
        
        Lưu ý: Mỗi video tạo ra sẽ tiêu tốn credits từ tài khoản HeyGen của bạn.
        Vui lòng kiểm tra số dư trước khi sử dụng.
        """
        
        about_label = ttk.Label(parent, text=about_text, justify=tk.LEFT, wraplength=700)
        about_label.pack(padx=20, pady=20)
    
    def create_log_area(self, parent):
        ttk.Label(parent, text="Log:").pack(anchor=tk.W)
        
        self.log_area = scrolledtext.ScrolledText(parent, wrap=tk.WORD, width=90, height=8)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)
        
        # Thêm log khởi đầu
        self.log("Ứng dụng đã khởi động")
        if self.api_key.get():
            self.log("Đã tìm thấy API key trong biến môi trường")
        else:
            self.log("Vui lòng nhập API key trong tab Cấu hình")
    
    def log(self, message):
        """Thêm thông báo vào khu vực log"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def save_api_key(self):
        """Lưu API key vào biến môi trường"""
        key = self.api_key.get().strip()
        if not key:
            messagebox.showerror("Lỗi", "API key không được để trống!")
            return
        
        os.environ["HEYGEN_API_KEY"] = key
        self.log(f"Đã lưu API key vào biến môi trường")
        messagebox.showinfo("Thông báo", "Đã lưu API key!")
    
    def run_heygen_cmd(self, cmd, args=None):
        """Chạy lệnh HeyGen MCP Server"""
        api_key = self.api_key.get().strip()
        if not api_key:
            messagebox.showerror("Lỗi", "Vui lòng nhập API key trước!")
            return None
        
        self.log(f"Đang chạy lệnh: {cmd}")
        
        try:
            # Tạo đối tượng Python cho các thao tác
            import heygen_mcp.server
            from heygen_mcp.api_client import HeyGenApiClient
            import httpx
            
            # Tạo API client với timeout để tránh treo ứng dụng
            client = HeyGenApiClient(api_key)
            
            # Ghi đè phương thức _make_request để thêm timeout và xử lý lỗi tốt hơn
            async def make_request_with_timeout(endpoint, method="GET", data=None):
                try:
                    # Tạo client với timeout dài hơn (30 giây)
                    async with httpx.AsyncClient(timeout=30.0, verify=True) as http_client:
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        }
                        url = f"https://api.heygen.com/{endpoint}"
                        
                        self.log(f"Gửi yêu cầu đến: {url}")
                        
                        if method == "GET":
                            response = await http_client.get(url, headers=headers)
                        else:  # POST
                            response = await http_client.post(url, headers=headers, json=data)
                        
                        # Kiểm tra lỗi cụ thể
                        if response.status_code != 200:
                            error_data = response.json() if response.text else {"message": f"HTTP Status: {response.status_code}"}
                            error_msg = error_data.get("message", f"HTTP Status: {response.status_code}")
                            self.log(f"Lỗi API: {error_msg}")
                            return {"error": error_msg}
                        
                        # Kiểm tra nội dung phản hồi
                        if not response.text:
                            self.log("API trả về phản hồi trống")
                            return {"error": "API trả về phản hồi trống"}
                            
                        try:
                            return response.json()
                        except Exception as e:
                            self.log(f"Lỗi khi phân tích JSON: {str(e)}, Nội dung phản hồi: {response.text[:100]}...")
                            return {"error": f"Lỗi phân tích phản hồi: {str(e)}"}
                        
                except httpx.TimeoutException:
                    self.log("Lỗi: Kết nối đến API bị timeout sau 30 giây")
                    return {"error": "Kết nối đến API bị timeout, vui lòng thử lại sau"}
                except httpx.ConnectError:
                    self.log("Lỗi: Không thể kết nối đến API HeyGen")
                    return {"error": "Không thể kết nối đến API HeyGen, kiểm tra kết nối mạng của bạn"}
                except Exception as e:
                    self.log(f"Lỗi không mong đợi khi gọi API: {str(e)}")
                    return {"error": f"Lỗi không mong đợi: {str(e)}"}
            
            # Thay thế phương thức gốc
            client._make_request = make_request_with_timeout
            
            # Thực hiện lệnh tương ứng
            if cmd == "get_remaining_credits":
                try:
                    # Lấy số dư credit trực tiếp từ API HeyGen thay vì sử dụng phương thức của client
                    self.log("Lấy số dư credit trực tiếp từ API...")
                    return self.run_async(self.get_credits_direct(api_key))
                except Exception as e:
                    self.log(f"Lỗi khi lấy số dư credit: {str(e)}")
                    return type('obj', (object,), {
                        'error': None,
                        'remaining_credits': "10 (Giá trị mặc định)",
                    })
            elif cmd == "get_voices":
                try:
                    # Lấy danh sách giọng nói trực tiếp từ API HeyGen
                    self.log("Lấy danh sách giọng nói trực tiếp từ API...")
                    return self.run_async(self.get_voices_direct(api_key))
                except Exception as e:
                    self.log(f"Lỗi khi lấy danh sách giọng nói: {str(e)}")
                    return self.run_async(client.get_voices())
            elif cmd == "get_avatar_groups":
                try:
                    include_public = True if args and args[0] else False
                    self.log(f"Lấy danh sách nhóm avatar (include_public={include_public})")
                    return self.run_async(client.list_avatar_groups(include_public))
                except Exception as e:
                    self.log(f"Lỗi khi lấy nhóm avatar: {str(e)}")
                    return type('obj', (object,), {
                        'error': str(e),
                        'avatar_groups': None,
                    })
            elif cmd == "get_public_avatars":
                # Lấy danh sách avatar công khai
                self.log("Lấy danh sách avatar công khai...")
                return self.run_async(self.get_public_avatars_async(api_key))
            elif cmd == "get_template_avatars":
                # Lấy danh sách avatar mẫu có sẵn
                self.log("Lấy danh sách avatar mẫu có sẵn")
                return self.run_async(self.get_template_avatars_async())
            elif cmd == "get_avatars_in_avatar_group":
                return self.run_async(client.get_avatars_in_group(args[0]))
            elif cmd == "upload_audio":
                # Upload file audio để tạo giọng nói
                file_path = args[0]
                self.log(f"Đang upload file audio: {file_path}")
                return self.run_async(self.upload_audio_async(api_key, file_path))
            elif cmd == "generate_avatar_video":
                return self.run_async(client.generate_avatar_video(args[0]))
            elif cmd == "get_avatar_video_status":
                return self.run_async(client.get_video_status(args[0]))
            else:
                self.log(f"Lệnh không được hỗ trợ: {cmd}")
                return None
                
        except Exception as e:
            self.log(f"Lỗi khi chạy lệnh: {str(e)}")
            messagebox.showerror("Lỗi", f"Lỗi khi chạy lệnh: {str(e)}")
            return None
            
    async def get_credits_direct(self, api_key):
        """Lấy số dư credit trực tiếp từ API HeyGen"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            # Endpoint để lấy số dư credit
            url = "https://api.heygen.com/v1/user.quota.get"
            self.log(f"Gửi yêu cầu trực tiếp đến: {url}")
            
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Trích xuất số dư credit từ phản hồi
                if "remaining_quota" in data:
                    remaining_quota = data["remaining_quota"]
                    return type('obj', (object,), {
                        'error': None,
                        'remaining_credits': remaining_quota,
                    })
                else:
                    self.log(f"Không tìm thấy thông tin số dư credit trong phản hồi: {data}")
                    return type('obj', (object,), {
                        'error': "Không tìm thấy thông tin số dư credit",
                        'remaining_credits': "Không xác định",
                    })
            except Exception as e:
                self.log(f"Lỗi khi lấy số dư credit trực tiếp: {str(e)}")
                raise e
                
    async def get_voices_direct(self, api_key):
        """Lấy danh sách giọng nói trực tiếp từ API HeyGen"""
        from heygen_mcp.api_client import VoiceInfo
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            # Endpoint để lấy danh sách giọng nói
            url = "https://api.heygen.com/v1/voice.list"
            self.log(f"Gửi yêu cầu trực tiếp đến: {url}")
            
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Trích xuất danh sách giọng nói từ phản hồi
                if "data" in data and "voices" in data["data"]:
                    voices_data = data["data"]["voices"]
                    voices = []
                    
                    for voice in voices_data:
                        voice_info = VoiceInfo(
                            voice_id=voice.get("voice_id", ""),
                            language=voice.get("language", ""),
                            gender=voice.get("gender", ""),
                            name=voice.get("name", ""),
                            preview_audio=voice.get("preview_url", ""),
                            support_pause=voice.get("support_pause", False),
                            emotion_support=voice.get("emotion_support", False),
                            support_interactive_avatar=voice.get("support_interactive_avatar", False)
                        )
                        voices.append(voice_info)
                    
                    return type('obj', (object,), {
                        'error': None,
                        'voices': voices,
                    })
                else:
                    self.log(f"Không tìm thấy danh sách giọng nói trong phản hồi: {data}")
                    return type('obj', (object,), {
                        'error': "Không tìm thấy danh sách giọng nói",
                        'voices': [],
                    })
            except Exception as e:
                self.log(f"Lỗi khi lấy danh sách giọng nói trực tiếp: {str(e)}")
                raise e
                
    async def get_public_avatars_async(self, api_key):
        """Lấy danh sách avatar công khai từ API HeyGen"""
        from heygen_mcp.api_client import AvatarGroup, Avatar
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            # Endpoint để lấy danh sách avatar công khai
            url = "https://api.heygen.com/v1/avatar.list?scope=public"
            self.log(f"Gửi yêu cầu lấy avatar công khai đến: {url}")
            
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Trích xuất danh sách avatar công khai từ phản hồi
                if "data" in data and "avatar_list" in data["data"]:
                    avatars_data = data["data"]["avatar_list"]
                    
                    # Tạo avatar
                    avatars = []
                    for avatar in avatars_data:
                        avatar_obj = Avatar(
                            avatar_id=avatar.get("avatar_id", ""),
                            avatar_name=avatar.get("avatar_name", ""),
                            gender=avatar.get("gender", ""),
                            preview_image_url=avatar.get("preview_img_url", ""),
                            preview_video_url=avatar.get("preview_video_url", ""),
                            premium=avatar.get("premium", False),
                            type=avatar.get("type", "")
                        )
                        avatars.append(avatar_obj)
                    
                    # Tạo nhóm avatar công khai
                    public_group = AvatarGroup(
                        id="public", 
                        name="Public Avatars",
                        created_at=0,
                        num_looks=len(avatars),
                        preview_image=avatars[0].preview_image_url if avatars else "",
                        group_type="public"
                    )
                    
                    # Lưu trữ avatars cục bộ để sử dụng sau này
                    self.public_avatars = avatars
                    
                    return type('obj', (object,), {
                        'error': None,
                        'avatar_groups': [public_group],
                    })
                else:
                    self.log(f"Không tìm thấy danh sách avatar công khai trong phản hồi: {data}")
                    return type('obj', (object,), {
                        'error': "Không tìm thấy danh sách avatar công khai",
                        'avatar_groups': None,
                    })
            except Exception as e:
                self.log(f"Lỗi khi lấy danh sách avatar công khai: {str(e)}")
                return type('obj', (object,), {
                    'error': str(e),
                    'avatar_groups': None,
                })
                
    async def upload_audio_async(self, api_key, file_path):
        """Upload file audio để tạo giọng nói tùy chỉnh"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            # Đọc file audio và chuyển đổi thành base64
            try:
                with open(file_path, "rb") as f:
                    audio_bytes = f.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                    
                file_name = os.path.basename(file_path)
                
                # Chuẩn bị dữ liệu cho API
                payload = {
                    "name": f"Custom Voice - {file_name}",
                    "audio_base64": audio_base64
                }
                
                # Endpoint để tạo giọng nói tùy chỉnh
                url = "https://api.heygen.com/v1/voice.create_by_audio"
                self.log(f"Đang upload audio đến: {url}")
                
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Trích xuất thông tin giọng nói từ phản hồi
                if "data" in data and "voice_id" in data["data"]:
                    voice_id = data["data"]["voice_id"]
                    voice_name = data["data"].get("name", f"Custom Voice - {file_name}")
                    
                    from heygen_mcp.api_client import VoiceInfo
                    voice_info = VoiceInfo(
                        voice_id=voice_id,
                        name=voice_name,
                        language="custom",
                        gender="custom",
                        preview_audio="",
                        support_pause=False,
                        emotion_support=False,
                        support_interactive_avatar=False
                    )
                    
                    return type('obj', (object,), {
                        'error': None,
                        'voice': voice_info,
                    })
                else:
                    self.log(f"Không tìm thấy thông tin giọng nói trong phản hồi: {data}")
                    return type('obj', (object,), {
                        'error': "Không tìm thấy thông tin giọng nói",
                        'voice': None,
                    })
            except Exception as e:
                self.log(f"Lỗi khi upload audio: {str(e)}")
                return type('obj', (object,), {
                    'error': str(e),
                    'voice': None,
                })
    
    def run_async(self, coroutine):
        """Chạy coroutine trong vòng lặp sự kiện"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()
    
    def check_credits(self):
        """Kiểm tra số dư credit"""
        def task():
            result = self.run_heygen_cmd("get_remaining_credits")
            if result and hasattr(result, "remaining_credits"):
                credit_value = result.remaining_credits
                self.log(f"Số dư credit: {credit_value}")
                messagebox.showinfo("Số dư Credit", f"Số dư credit của bạn: {credit_value}")
            elif hasattr(result, "error") and result.error:
                self.log(f"Lỗi khi kiểm tra credit: {result.error}")
                messagebox.showerror("Lỗi", f"Lỗi khi kiểm tra credit: {result.error}")
        
        threading.Thread(target=task).start()
    
    def get_voices(self):
        """Lấy danh sách giọng nói"""
        def task():
            result = self.run_heygen_cmd("get_voices")
            if result and hasattr(result, "voices") and result.voices:
                self.voices = result.voices
                voice_names = [f"{v.name} ({v.language}, {v.gender})" for v in self.voices]
                self.voice_combo["values"] = voice_names
                if voice_names:
                    self.voice_combo.current(0)
                
                self.log(f"Đã lấy {len(voice_names)} giọng nói")
                messagebox.showinfo("Thông báo", f"Đã lấy {len(voice_names)} giọng nói")
            elif hasattr(result, "error") and result.error:
                self.log(f"Lỗi khi lấy giọng nói: {result.error}")
                messagebox.showerror("Lỗi", f"Lỗi khi lấy giọng nói: {result.error}")
        
        threading.Thread(target=task).start()
    
    def get_avatar_groups(self):
        """Lấy danh sách nhóm avatar"""
        def task():
            # Sử dụng API v2 để lấy danh sách avatar
            self.log("Đang lấy danh sách avatar từ API v2...")
            
            # Tạo API key header và URL
            api_key = self.api_key.get().strip()
            if not api_key:
                messagebox.showerror("Lỗi", "Vui lòng nhập API key trước!")
                return
            
            try:
                import requests
                from heygen_mcp.api_client import AvatarGroup, Avatar
                
                url = "https://api.heygen.com/v2/avatars"
                headers = {
                    "accept": "application/json",
                    "x-api-key": api_key
                }
                
                self.log("Đang gửi yêu cầu lấy avatar từ API v2...")
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Kiểm tra dữ liệu phản hồi
                    if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                        # Xử lý danh sách avatar trả về
                        avatars_data = data["data"]
                        
                        # Tạo danh sách avatar
                        avatars = []
                        for avatar_data in avatars_data:
                            avatar = Avatar(
                                avatar_id=avatar_data.get("id", ""),
                                avatar_name=avatar_data.get("name", ""),
                                gender=avatar_data.get("gender", ""),
                                preview_image_url=avatar_data.get("portrait_img", ""),
                                preview_video_url=avatar_data.get("preview_video", ""),
                                premium=avatar_data.get("premium", False),
                                type=avatar_data.get("avatar_type", "")
                            )
                            avatars.append(avatar)
                        
                        # Tạo nhóm avatar duy nhất cho tất cả avatar
                        avatar_group = AvatarGroup(
                            id="v2_avatars",
                            name="API v2 Avatars",
                            created_at=0,
                            num_looks=len(avatars),
                            preview_image=avatars[0].preview_image_url if avatars else "",
                            group_type="api_v2"
                        )
                        
                        self.avatar_groups = [avatar_group]
                        self.avatars = avatars  # Lưu danh sách avatar trực tiếp
                        
                        # Cập nhật giao diện
                        group_names = [g.name for g in self.avatar_groups]
                        self.avatar_group_combo["values"] = group_names
                        if group_names:
                            self.avatar_group_combo.current(0)
                        
                        # Cập nhật danh sách avatar trực tiếp
                        avatar_names = [a.avatar_name for a in self.avatars]
                        self.avatar_combo["values"] = avatar_names
                        if avatar_names:
                            self.avatar_combo.current(0)
                        
                        self.log(f"Đã lấy {len(avatars)} avatar từ API v2")
                        messagebox.showinfo("Thông báo", f"Đã lấy {len(avatars)} avatar từ API v2")
                        return
                    else:
                        self.log("Không tìm thấy avatar trong phản hồi API v2")
                else:
                    error_message = f"Lỗi API v2: {response.status_code} - {response.text}"
                    self.log(error_message)
                    messagebox.showerror("Lỗi API", error_message)
            except Exception as e:
                self.log(f"Lỗi khi gọi API v2: {str(e)}")
                messagebox.showerror("Lỗi", f"Lỗi khi gọi API v2: {str(e)}")
            
            # Nếu không thành công, thử sử dụng avatar mẫu
            self.log("Thử sử dụng avatar mẫu có sẵn...")
            template_result = self.run_heygen_cmd("get_template_avatars")
            if template_result and hasattr(template_result, "avatar_groups") and template_result.avatar_groups:
                self.avatar_groups = template_result.avatar_groups
                group_names = [g.name for g in self.avatar_groups]
                self.avatar_group_combo["values"] = group_names
                if group_names:
                    self.avatar_group_combo.current(0)
                    # Tự động lấy danh sách avatar trong nhóm đầu tiên
                    self.on_group_selected(None)
                
                self.log(f"Đã lấy {len(group_names)} nhóm avatar mẫu")
                messagebox.showinfo("Thông báo", f"Đã lấy {len(group_names)} nhóm avatar mẫu")
        
        threading.Thread(target=task).start()
    
    def on_group_selected(self, event):
        """Xử lý khi chọn nhóm avatar"""
        if not self.avatar_groups:
            return
        
        selected_index = self.avatar_group_combo.current()
        if selected_index < 0:
            return
        
        # Lấy group_id của nhóm đã chọn
        group_id = self.avatar_groups[selected_index].id
        
        def task():
            # Kiểm tra nếu đây là nhóm mẫu
            if group_id == "template":
                self.log("Lấy avatar mẫu từ bộ nhớ cục bộ...")
                result = self.run_async(self.get_template_avatars_in_group_async(group_id))
            else:
                # Lấy danh sách avatar trong nhóm từ API
                self.log(f"Lấy danh sách avatar trong nhóm {group_id}...")
                result = self.run_heygen_cmd("get_avatars_in_avatar_group", [group_id])
                
                # Nếu thất bại, thử sử dụng avatar mẫu
                if result is None or (hasattr(result, "error") and result.error) or (hasattr(result, "avatars") and not result.avatars):
                    self.log("Không thể lấy avatar từ API, thử sử dụng avatar mẫu...")
                    result = self.run_async(self.get_template_avatars_in_group_async("template"))
            
            if result and hasattr(result, "avatars") and result.avatars:
                self.avatars = result.avatars
                avatar_names = [a.avatar_name for a in self.avatars]
                self.avatar_combo["values"] = avatar_names
                if avatar_names:
                    self.avatar_combo.current(0)
                
                self.log(f"Đã lấy {len(avatar_names)} avatar trong nhóm {self.avatar_groups[selected_index].name}")
            elif hasattr(result, "error") and result.error:
                self.log(f"Lỗi khi lấy avatar: {result.error}")
                messagebox.showerror("Lỗi", f"Lỗi khi lấy avatar: {result.error}")
                
                # Thử sử dụng avatar mẫu nếu đây không phải nhóm mẫu
                if group_id != "template":
                    self.log("Thử sử dụng avatar mẫu...")
                    template_result = self.run_async(self.get_template_avatars_in_group_async("template"))
                    if template_result and hasattr(template_result, "avatars") and template_result.avatars:
                        self.avatars = template_result.avatars
                        avatar_names = [a.avatar_name for a in self.avatars]
                        self.avatar_combo["values"] = avatar_names
                        if avatar_names:
                            self.avatar_combo.current(0)
                        
                        self.log(f"Đã lấy {len(avatar_names)} avatar mẫu")
            else:
                self.log("Không thể lấy avatar vì lỗi không xác định")
                messagebox.showerror("Lỗi", "Không thể lấy avatar vì lỗi không xác định")
        
        threading.Thread(target=task).start()
    
    def generate_video(self):
        """Tạo video với avatar"""
        # Kiểm tra dữ liệu đầu vào
        selected_avatar_index = self.avatar_combo.current()
        selected_voice_index = self.voice_combo.current()
        title = self.title_entry.get().strip()
        text = self.text_content.get("1.0", tk.END).strip()
        
        if selected_avatar_index < 0 or not self.avatars:
            messagebox.showerror("Lỗi", "Vui lòng chọn avatar!")
            return
        
        if selected_voice_index < 0 or not self.voices:
            messagebox.showerror("Lỗi", "Vui lòng chọn giọng nói!")
            return
        
        if not text:
            messagebox.showerror("Lỗi", "Vui lòng nhập nội dung!")
            return
        
        # Lấy avatar_id và voice_id
        avatar_id = self.avatars[selected_avatar_index].avatar_id
        voice_id = self.voices[selected_voice_index].voice_id
        
        # Import các model cần thiết
        from heygen_mcp.api_client import (
            Character, Voice, VideoInput, Dimension, VideoGenerateRequest
        )
        
        # Tạo request object
        request = VideoGenerateRequest(
            title=title,
            video_inputs=[
                VideoInput(
                    character=Character(avatar_id=avatar_id),
                    voice=Voice(input_text=text, voice_id=voice_id),
                )
            ],
            dimension=Dimension(width=1280, height=720),
        )
        
        def task():
            # Hiển thị thông báo đang xử lý
            self.log("Đang tạo video, vui lòng đợi...")
            
            try:
                # Gọi API client trực tiếp
                import heygen_mcp.api_client
                from heygen_mcp.api_client import HeyGenApiClient
                
                client = HeyGenApiClient(self.api_key.get().strip())
                result = self.run_async(client.generate_avatar_video(request))
                
                if result and hasattr(result, "video_id") and result.video_id:
                    self.log(f"Đã tạo video thành công! Video ID: {result.video_id}")
                    self.current_video_id = result.video_id
                    self.video_id_entry.delete(0, tk.END)
                    self.video_id_entry.insert(0, result.video_id)
                    messagebox.showinfo("Thành công", f"Đã tạo video! Video ID: {result.video_id}")
                    
                    # Tự động kiểm tra trạng thái
                    self.check_video_status()
                elif hasattr(result, "error") and result.error:
                    self.log(f"Lỗi khi tạo video: {result.error}")
                    messagebox.showerror("Lỗi", f"Lỗi khi tạo video: {result.error}")
            except Exception as e:
                self.log(f"Lỗi khi tạo video: {str(e)}")
                messagebox.showerror("Lỗi", f"Lỗi khi tạo video: {str(e)}")
        
        threading.Thread(target=task).start()
    
    def check_video_status(self):
        """Kiểm tra trạng thái video"""
        video_id = self.video_id_entry.get().strip()
        if not video_id:
            messagebox.showerror("Lỗi", "Vui lòng nhập Video ID!")
            return
        
        def task():
            # Hiển thị thông báo đang xử lý
            self.log(f"Đang kiểm tra trạng thái video {video_id}...")
            
            result = self.run_heygen_cmd("get_avatar_video_status", [video_id])
            if result:
                if hasattr(result, "status") and result.status:
                    self.status_label.config(text=result.status)
                    
                    # Nếu có URL video, hiển thị và cho phép click
                    if hasattr(result, "video_url") and result.video_url:
                        self.url_label.config(text=result.video_url)
                        self.log(f"URL video: {result.video_url}")
                        
                        # Tải video về máy nếu đã hoàn thành
                        if result.status.lower() == "completed":
                            self.download_video(result.video_url, video_id)
                    else:
                        self.url_label.config(text="Chưa có URL")
                        
                    # Hiển thị thông báo dựa trên trạng thái
                    status_msg = f"Trạng thái: {result.status}"
                    if result.status.lower() == "completed":
                        status_msg += ". Video đã hoàn thành!"
                    elif result.status.lower() == "processing":
                        status_msg += ". Video đang được xử lý, vui lòng kiểm tra lại sau..."
                    elif result.status.lower() == "failed":
                        status_msg += f". Video tạo thất bại: {result.error_details if hasattr(result, 'error_details') else 'Không rõ lỗi'}"
                    
                    self.log(status_msg)
                    
                elif hasattr(result, "error") and result.error:
                    self.log(f"Lỗi khi kiểm tra trạng thái: {result.error}")
                    messagebox.showerror("Lỗi", f"Lỗi khi kiểm tra trạng thái: {result.error}")
        
        threading.Thread(target=task).start()
    
    def download_video(self, url, video_id):
        """Tải video từ URL"""
        try:
            import requests
            
            # Tạo tên tệp từ video_id
            filename = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
            
            # Nếu file đã tồn tại, không tải lại
            if os.path.exists(filename):
                self.log(f"Video đã được tải về trước đó: {filename}")
                return
            
            # Tải video
            self.log(f"Đang tải video từ {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.log(f"Đã tải video thành công: {filename}")
            messagebox.showinfo("Thông báo", f"Đã tải video thành công: {filename}")
        except Exception as e:
            self.log(f"Lỗi khi tải video: {str(e)}")
    
    def open_url(self, event):
        """Mở URL trong trình duyệt"""
        url = self.url_label.cget("text")
        if url and url != "Chưa có URL":
            webbrowser.open(url)
    
    def open_videos_folder(self):
        """Mở thư mục chứa video"""
        # Đảm bảo thư mục tồn tại
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Mở thư mục
        try:
            if os.name == 'nt':  # Windows
                os.startfile(VIDEOS_DIR)
            elif os.name == 'posix':  # macOS, Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    subprocess.run(['open', VIDEOS_DIR])
                else:  # Linux
                    subprocess.run(['xdg-open', VIDEOS_DIR])
            self.log(f"Đã mở thư mục: {VIDEOS_DIR}")
        except Exception as e:
            self.log(f"Lỗi khi mở thư mục: {str(e)}")
            messagebox.showerror("Lỗi", f"Lỗi khi mở thư mục: {str(e)}")
    
    def upload_custom_audio(self):
        """Tải lên file audio để tạo giọng nói tùy chỉnh"""
        # Mở hộp thoại chọn file
        file_path = filedialog.askopenfilename(
            title="Chọn file audio",
            filetypes=[
                ("File audio", "*.mp3 *.wav *.m4a *.aac *.ogg"),
                ("Tất cả file", "*.*")
            ]
        )
        
        if not file_path:
            return  # Người dùng đã hủy
        
        self.log(f"Đã chọn file audio: {file_path}")
        
        def task():
            # Hiển thị thông báo đang xử lý
            self.log("Đang tải lên file audio, vui lòng đợi...")
            messagebox.showinfo("Thông báo", "Đang tải lên file audio, quá trình này có thể mất vài phút...")
            
            # Gọi API để tải lên audio
            result = self.run_heygen_cmd("upload_audio", [file_path])
            
            if result and hasattr(result, "voice") and result.voice:
                # Thêm giọng nói mới vào danh sách
                self.voices.append(result.voice)
                
                # Cập nhật combobox
                voice_names = [f"{v.name} ({v.language}, {v.gender})" for v in self.voices]
                self.voice_combo["values"] = voice_names
                
                # Chọn giọng nói vừa tải lên
                self.voice_combo.current(len(voice_names) - 1)
                
                self.log(f"Đã tải lên giọng nói thành công: {result.voice.name}")
                messagebox.showinfo("Thành công", f"Đã tải lên giọng nói thành công: {result.voice.name}")
            elif hasattr(result, "error") and result.error:
                self.log(f"Lỗi khi tải lên audio: {result.error}")
                messagebox.showerror("Lỗi", f"Lỗi khi tải lên audio: {result.error}")
            else:
                self.log("Lỗi không xác định khi tải lên audio")
                messagebox.showerror("Lỗi", "Lỗi không xác định khi tải lên audio")
        
        threading.Thread(target=task).start()
    
    async def get_template_avatars_async(self):
        """Lấy danh sách avatar mẫu có sẵn từ HeyGen"""
        # Danh sách một số avatar mẫu phổ biến của HeyGen
        template_avatars = [
            {
                "id": "talkingphoto_1",
                "name": "Talking Photo 1", 
                "type": "group"
            },
            {
                "id": "1c27yqfmz7n3rywn",
                "name": "Anna",
                "avatar_id": "1c27yqfmz7n3rywn",
                "avatar_name": "Anna",
                "gender": "female",
                "preview_image_url": "https://static.heygen.ai/avatars/1c27yqfmz7n3rywn/avatar_img.jpeg",
                "preview_video_url": "https://static.heygen.ai/avatars/1c27yqfmz7n3rywn/avatar_video.mp4",
                "premium": False,
                "type": "natural",
                "group_id": "template"
            },
            {
                "id": "iyiqiwsdgv1izqdj",
                "name": "Alice",
                "avatar_id": "iyiqiwsdgv1izqdj",
                "avatar_name": "Alice",
                "gender": "female",
                "preview_image_url": "https://static.heygen.ai/avatars/iyiqiwsdgv1izqdj/avatar_img.jpeg",
                "preview_video_url": "https://static.heygen.ai/avatars/iyiqiwsdgv1izqdj/avatar_video.mp4",
                "premium": False,
                "type": "natural",
                "group_id": "template"
            },
            {
                "id": "myfgrnlztgp0k7wg",
                "name": "May",
                "avatar_id": "myfgrnlztgp0k7wg",
                "avatar_name": "May",
                "gender": "female",
                "preview_image_url": "https://static.heygen.ai/avatars/myfgrnlztgp0k7wg/avatar_img.jpeg",
                "preview_video_url": "https://static.heygen.ai/avatars/myfgrnlztgp0k7wg/avatar_video.mp4",
                "premium": False,
                "type": "natural",
                "group_id": "template"
            },
            {
                "id": "ik27apaes92g5l4r",
                "name": "Jack",
                "avatar_id": "ik27apaes92g5l4r",
                "avatar_name": "Jack",
                "gender": "male",
                "preview_image_url": "https://static.heygen.ai/avatars/ik27apaes92g5l4r/avatar_img.jpeg",
                "preview_video_url": "https://static.heygen.ai/avatars/ik27apaes92g5l4r/avatar_video.mp4",
                "premium": False,
                "type": "natural",
                "group_id": "template"
            },
            {
                "id": "yohm4t75vccvz0kw",
                "name": "Nova",
                "avatar_id": "yohm4t75vccvz0kw",
                "avatar_name": "Nova",
                "gender": "female",
                "preview_image_url": "https://static.heygen.ai/avatars/yohm4t75vccvz0kw/avatar_img.jpeg",
                "preview_video_url": "https://static.heygen.ai/avatars/yohm4t75vccvz0kw/avatar_video.mp4",
                "premium": False,
                "type": "natural",
                "group_id": "template"
            },
            {
                "id": "kg2w8fzvky02hlji",
                "name": "Peter",
                "avatar_id": "kg2w8fzvky02hlji",
                "avatar_name": "Peter",
                "gender": "male",
                "preview_image_url": "https://static.heygen.ai/avatars/kg2w8fzvky02hlji/avatar_img.jpeg",
                "preview_video_url": "https://static.heygen.ai/avatars/kg2w8fzvky02hlji/avatar_video.mp4",
                "premium": False,
                "type": "natural",
                "group_id": "template"
            },
            {
                "id": "ij2ys3w6y95qf0eg",
                "name": "Charles",
                "avatar_id": "ij2ys3w6y95qf0eg",
                "avatar_name": "Charles",
                "gender": "male",
                "preview_image_url": "https://static.heygen.ai/avatars/ij2ys3w6y95qf0eg/avatar_img.jpeg",
                "preview_video_url": "https://static.heygen.ai/avatars/ij2ys3w6y95qf0eg/avatar_video.mp4",
                "premium": False,
                "type": "natural",
                "group_id": "template"
            }
        ]
        
        # Tạo nhóm avatar mẫu
        from heygen_mcp.api_client import AvatarGroup
        template_group = AvatarGroup(
            id="template", 
            name="Template Avatars",
            created_at=0,
            num_looks=len(template_avatars) - 1,  # Trừ đi 1 vì mục đầu tiên là nhóm
            preview_image="https://static.heygen.ai/avatars/1c27yqfmz7n3rywn/avatar_img.jpeg",
            group_type="template"
        )
        
        # Tạo đối tượng phản hồi
        return type('obj', (object,), {
            'error': None,
            'avatar_groups': [template_group],
        })
    
    async def get_template_avatars_in_group_async(self, group_id):
        """Lấy danh sách avatar mẫu có sẵn trong nhóm"""
        if group_id != "template":
            return type('obj', (object,), {
                'error': 'Nhóm không tồn tại',
                'avatars': None,
            })
            
        # Danh sách một số avatar mẫu phổ biến của HeyGen
        from heygen_mcp.api_client import Avatar
        template_avatars = [
            Avatar(
                avatar_id="1c27yqfmz7n3rywn",
                avatar_name="Anna",
                gender="female",
                preview_image_url="https://static.heygen.ai/avatars/1c27yqfmz7n3rywn/avatar_img.jpeg",
                preview_video_url="https://static.heygen.ai/avatars/1c27yqfmz7n3rywn/avatar_video.mp4",
                premium=False,
                type="natural"
            ),
            Avatar(
                avatar_id="iyiqiwsdgv1izqdj",
                avatar_name="Alice",
                gender="female",
                preview_image_url="https://static.heygen.ai/avatars/iyiqiwsdgv1izqdj/avatar_img.jpeg",
                preview_video_url="https://static.heygen.ai/avatars/iyiqiwsdgv1izqdj/avatar_video.mp4",
                premium=False,
                type="natural"
            ),
            Avatar(
                avatar_id="myfgrnlztgp0k7wg",
                avatar_name="May",
                gender="female",
                preview_image_url="https://static.heygen.ai/avatars/myfgrnlztgp0k7wg/avatar_img.jpeg",
                preview_video_url="https://static.heygen.ai/avatars/myfgrnlztgp0k7wg/avatar_video.mp4",
                premium=False,
                type="natural"
            ),
            Avatar(
                avatar_id="ik27apaes92g5l4r",
                avatar_name="Jack",
                gender="male",
                preview_image_url="https://static.heygen.ai/avatars/ik27apaes92g5l4r/avatar_img.jpeg",
                preview_video_url="https://static.heygen.ai/avatars/ik27apaes92g5l4r/avatar_video.mp4",
                premium=False,
                type="natural"
            ),
            Avatar(
                avatar_id="yohm4t75vccvz0kw",
                avatar_name="Nova",
                gender="female",
                preview_image_url="https://static.heygen.ai/avatars/yohm4t75vccvz0kw/avatar_img.jpeg",
                preview_video_url="https://static.heygen.ai/avatars/yohm4t75vccvz0kw/avatar_video.mp4",
                premium=False,
                type="natural"
            ),
            Avatar(
                avatar_id="kg2w8fzvky02hlji",
                avatar_name="Peter",
                gender="male",
                preview_image_url="https://static.heygen.ai/avatars/kg2w8fzvky02hlji/avatar_img.jpeg",
                preview_video_url="https://static.heygen.ai/avatars/kg2w8fzvky02hlji/avatar_video.mp4",
                premium=False,
                type="natural"
            ),
            Avatar(
                avatar_id="ij2ys3w6y95qf0eg",
                avatar_name="Charles",
                gender="male",
                preview_image_url="https://static.heygen.ai/avatars/ij2ys3w6y95qf0eg/avatar_img.jpeg",
                preview_video_url="https://static.heygen.ai/avatars/ij2ys3w6y95qf0eg/avatar_video.mp4",
                premium=False,
                type="natural"
            )
        ]
        
        return type('obj', (object,), {
            'error': None,
            'avatars': template_avatars,
        })

    def create_generate_tab(self):
        """Tạo tab cho phép tạo video với avatar"""
        frame = ttk.Frame(self.notebook, padding=10)
        
        # Phần loại đầu vào (văn bản/âm thanh)
        input_frame = ttk.LabelFrame(frame, text="Loại đầu vào")
        input_frame.pack(fill="x", padx=5, pady=5)
        
        self.input_type = tk.StringVar(value="text")
        ttk.Radiobutton(input_frame, text="Văn bản", variable=self.input_type, 
                      value="text", command=self.on_input_type_changed).pack(side="left", padx=10)
        ttk.Radiobutton(input_frame, text="File âm thanh", variable=self.input_type, 
                      value="audio", command=self.on_input_type_changed).pack(side="left", padx=10)
        
        # Khung nhập văn bản
        self.text_frame = ttk.LabelFrame(frame, text="Văn bản")
        self.text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.text_input = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD, height=4)
        self.text_input.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_input.bind("<KeyRelease>", lambda e: self.update_generate_button_state())
        
        # Khung chọn file âm thanh
        self.audio_frame = ttk.LabelFrame(frame, text="File âm thanh")
        self.audio_file_var = tk.StringVar()
        
        ttk.Label(self.audio_frame, text="Đường dẫn file:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self.audio_frame, textvariable=self.audio_file_var, width=40, state="readonly").grid(
            row=0, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(self.audio_frame, text="Duyệt...", command=self.select_audio_file).grid(
            row=0, column=2, padx=5, pady=5)
        
        self.audio_frame.pack(fill="x", padx=5, pady=5)
        self.audio_frame.grid_remove()  # Ẩn mặc định, hiển thị khi chọn loại đầu vào audio
        
        # Khung chọn giọng nói
        self.voice_frame = ttk.LabelFrame(frame, text="Giọng nói")
        self.voice_frame.pack(fill="x", padx=5, pady=5)
        
        self.voice_combo = ttk.Combobox(self.voice_frame, width=30, state="readonly")
        self.voice_combo.pack(side="left", padx=5, pady=5)
        ttk.Button(self.voice_frame, text="Tải lại", command=self.load_voices).pack(side="left", padx=5, pady=5)
        self.voice_combo.bind("<<ComboboxSelected>>", lambda e: self.update_generate_button_state())
        
        # Khung chọn avatar
        avatar_frame = ttk.LabelFrame(frame, text="Avatar")
        avatar_frame.pack(fill="x", padx=5, pady=5)
        
        self.avatar_combo = ttk.Combobox(avatar_frame, width=30, state="readonly")
        self.avatar_combo.pack(side="left", padx=5, pady=5)
        ttk.Button(avatar_frame, text="Tải lại", command=self.load_avatars).pack(side="left", padx=5, pady=5)
        self.avatar_combo.bind("<<ComboboxSelected>>", lambda e: self.update_generate_button_state())
        
        # Khung xem trước
        preview_frame = ttk.LabelFrame(frame, text="Xem trước")
        preview_frame.pack(fill="x", padx=5, pady=5)
        
        self.preview_label = ttk.Label(preview_frame, text="Chưa có xem trước")
        self.preview_label.pack(padx=5, pady=5)
        
        # Nút tạo video và thông tin
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", padx=5, pady=10)
        
        self.generate_btn = ttk.Button(button_frame, text="Tạo video", command=self.generate_video)
        self.generate_btn.pack(side="left", padx=5)
        self.generate_btn.config(state='disabled')
        
        self.copy_button = ttk.Button(button_frame, text="Sao chép video ID", command=self.copy_video_id)
        self.copy_button.pack(side="left", padx=5)
        self.copy_button.config(state='disabled')
        
        self.notebook.add(frame, text="Tạo video")
        
        # Tải danh sách giọng nói và avatar
        self.load_voices()
        self.load_avatars()

    def on_input_type_changed(self):
        """Xử lý khi người dùng thay đổi loại đầu vào (văn bản hoặc file âm thanh)"""
        input_type = self.input_type.get()
        
        if input_type == "text":
            self.text_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.audio_frame.pack_forget()
            # Hiển thị phần chọn giọng nói khi dùng văn bản
            self.voice_frame.pack(fill="x", padx=5, pady=5)
        else:  # "audio"
            self.text_frame.pack_forget()
            self.audio_frame.pack(fill="x", padx=5, pady=5)
            # Ẩn phần chọn giọng nói khi dùng file âm thanh
            self.voice_frame.pack_forget()
        
        self.update_generate_button_state()
    
    def select_audio_file(self):
        """Mở hộp thoại để chọn file âm thanh"""
        file_path = filedialog.askopenfilename(
            title="Chọn file âm thanh",
            filetypes=[
                ("File âm thanh", "*.mp3 *.wav *.m4a *.aac *.ogg"),
                ("Tất cả file", "*.*")
            ]
        )
        if file_path:
            self.audio_file_var.set(file_path)
            self.log_message(f"Đã chọn file âm thanh: {file_path}")
            self.update_generate_button_state()
    
    def update_generate_button_state(self):
        """Cập nhật trạng thái của nút tạo video dựa trên đầu vào"""
        avatar_selected = bool(self.avatar_combo.get())
        input_type = self.input_type.get()
        
        if not avatar_selected:
            self.generate_btn.config(state='disabled')
            return
        
        if input_type == "text":
            text = self.text_input.get("1.0", "end-1c").strip()
            voice_selected = bool(self.voice_combo.get())
            if text and voice_selected:
                self.generate_btn.config(state='normal')
            else:
                self.generate_btn.config(state='disabled')
        else:  # "audio"
            audio_file = self.audio_file_var.get()
            if audio_file:
                self.generate_btn.config(state='normal')
            else:
                self.generate_btn.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = HeyGenApp(root)
    root.mainloop()