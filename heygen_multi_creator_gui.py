import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import threading
import time
import json
import os
import traceback
from urllib.parse import urlparse
from customtkinter import CTkScrollableFrame # Import specific class
from datetime import datetime # Import datetime

# Import new modules
import config_manager
import heygen_api

# Placeholder for API interaction functions
def check_heygen_credit(api_key):
    # This function needs the actual HeyGen API endpoint for checking credits if available.
    # For now, it's a placeholder.
    print(f"Checking credit for key ending in ...{api_key[-4:]}")
    # Replace with actual API call
    # endpoint = "..."
    # headers = {'X-Api-Key': api_key}
    # try:
    #     response = requests.get(endpoint, headers=headers)
    #     response.raise_for_status()
    #     data = response.json()
    #     # Process data to get credit info
    #     messagebox.showinfo("Credit Info", f"API Key ...{api_key[-4:]}: Credit info retrieved.") # Placeholder message
    # except requests.exceptions.RequestException as e:
    #     messagebox.showerror("API Error", f"Error checking credit for key ...{api_key[-4:]}: {e}")
    # except Exception as e:
    #     messagebox.showerror("Error", f"An unexpected error occurred: {e}")
    messagebox.showinfo("Info", f"Chức năng kiểm tra credit chưa có API chính thức từ HeyGen. Vui lòng kiểm tra thủ công trên web.")
    return None # Or return actual credit info

def generate_heygen_video(api_key, audio_path, avatar_id, output_dir, progress_callback, log_callback):
    log_callback(f"Bắt đầu tạo video với API Key ...{api_key[-4:]}, Audio: {os.path.basename(audio_path)}, Avatar: {avatar_id}")
    # Placeholder for actual video generation logic
    # Needs implementation using /v2/video/generate and /v1/video_status.get
    # Remember to handle threading and GUI updates safely (using progress_callback, log_callback)
    time.sleep(2) # Simulate API call
    log_callback(f"Đã gửi yêu cầu tạo video cho API Key ...{api_key[-4:]}. Đang chờ xử lý...")
    # Start a separate thread to poll for status
    # ... poll status ...
    # When done:
    # log_callback(f"Video tạo bởi API Key ...{api_key[-4:]} hoàn thành. URL: ...")
    # progress_callback(100) # Example
    pass

def download_video(video_url, output_path, log_callback):
    log_callback(f"Bắt đầu tải video từ: {video_url}")
    try:
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        log_callback(f"Đã tải xong video về: {output_path}")
        messagebox.showinfo("Thành công", f"Đã tải video thành công!\\n{output_path}")
    except requests.exceptions.RequestException as e:
        log_callback(f"Lỗi tải video: {e}")
        messagebox.showerror("Lỗi", f"Không thể tải video: {e}")
    except Exception as e:
        log_callback(f"Lỗi không xác định khi tải video: {e}")
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi không mong muốn: {e}")

# --- Main Application Class ---
class HeyGenMultiCreatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Load initial config FIRST to get geometry
        initial_config = config_manager.load_config(self._initial_log)

        self.title("HeyGen Multi-Account Video Creator")
        # Apply geometry from config BEFORE setting appearance/theme
        try:
            self.geometry(initial_config["window_geometry"])
            self._initial_log(f"Áp dụng geometry từ config: {initial_config['window_geometry']}")
        except Exception as e:
             self._initial_log(f"Lỗi áp dụng geometry: {e}. Dùng mặc định.")
             self.geometry("850x650+100+100") # Fallback default

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Set other attributes from loaded config
        self.api_keys = initial_config["api_keys"]
        self.avatar_id = ctk.StringVar(value=initial_config["avatar_id"])
        self.output_dir = ctk.StringVar(value=initial_config["output_dir"])
        self.proxy_settings = initial_config["proxy"]
        self.avatar_list_cache = None
        self.current_video_jobs = {}
        # Add storage for credit labels
        self.api_key_credit_labels = [None] * 5
        # Add storage for video list widgets
        self.video_list_widgets = [None] * 5

        # Widget storage (initialize before creating tabs)
        self.proxy_entries = {}
        self.api_key_entries = []
        self.api_key_labels = [None] * 5
        self.tab_generation_widgets = [None] * 5
        self.load_avatar_button = None # Initialize
        self.avatar_combobox = None # Initialize
        self.log_textbox = None # Initialize

        # --- Create Tabs ---
        self.notebook = ctk.CTkTabview(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.tab_settings = self.notebook.add("Cài đặt & API")
        self.tab_gen = [self.notebook.add(f"Tạo Video {i+1}") for i in range(5)]
        self.tab_proxy = self.notebook.add("Proxy")

        # --- Populate Tabs ---
        self.create_settings_tab()
        for i in range(5):
            self.create_generation_tab(self.tab_gen[i], i)
        self.create_proxy_tab()

        # --- Finalize Setup ---
        # Apply loaded config values to widgets AFTER they are created
        self._apply_loaded_config(initial_config)
        self.log("Ứng dụng đã sẵn sàng.")

        # Bind window closing event to save config
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # KHÔNG tự động tải API nữa, thay vào đó là tải cache
        # if any(key for key in self.api_keys if key.strip()):
        #      self.log("Tự động tải danh sách avatar khi khởi động...")
        #      self.load_avatars() # Call the existing load function
        self._load_avatar_cache_on_startup()

    def _initial_log(self, message):
        # Simple log for config loading before main log textbox exists
        print(f"CONFIG_LOAD: {message}")

    def log(self, message):
        # Ensure log_textbox is created before logging
        if self.log_textbox:
            # Thread-safe logging to the log text area
            self.log_textbox.configure(state='normal')
            self.log_textbox.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
            self.log_textbox.configure(state='disabled')
            self.log_textbox.see(tk.END) # Scroll to the end
        else:
            print(f"LOG_EARLY: {message}") # Fallback if called too early

    def update_progress(self, tab_index, value):
        # Placeholder for updating progress bars on generation tabs
        self.log(f"Tiến trình Tab {tab_index + 1}: {value}%")
        pass

    def create_settings_tab(self):
        tab = self.tab_settings
        tab.grid_columnconfigure(1, weight=1)

        # API Keys Section
        api_frame = ctk.CTkFrame(tab)
        api_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        api_frame.grid_columnconfigure(1, weight=1)
        api_frame.grid_columnconfigure(2, weight=0) # Keep button fixed size
        ctk.CTkLabel(api_frame, text="Quản lý API Keys", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, pady=(5, 10))

        self.api_key_entries = [] # Reset here before populating
        for i in range(5):
            ctk.CTkLabel(api_frame, text=f"API Key {i+1}:").grid(row=i+1, column=0, padx=5, pady=5, sticky="w")
            entry = ctk.CTkEntry(api_frame, width=350)
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="ew")
            self.api_key_entries.append(entry)
            entry.bind("<KeyRelease>", lambda event, idx=i: self.update_api_key(idx, event.widget.get()))
            
            # --- Add Check Credit Button ---            
            check_button = ctk.CTkButton(api_frame, text="Kiểm tra", width=80,
                                         command=lambda idx=i: self._check_credit_for_key(idx))
            check_button.grid(row=i+1, column=2, padx=(5, 10), pady=5)

        # Avatar Section
        avatar_frame = ctk.CTkFrame(tab)
        avatar_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        avatar_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(avatar_frame, text="Thiết lập Avatar", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, pady=(5, 10))

        # Thêm ô tìm kiếm
        ctk.CTkLabel(avatar_frame, text="Tìm kiếm ID:").grid(row=1, column=0, padx=5, pady=(10,0), sticky="w")
        self.avatar_search_entry = ctk.CTkEntry(avatar_frame, placeholder_text="Nhập để lọc ID...", width=350)
        self.avatar_search_entry.grid(row=1, column=1, padx=5, pady=(10,0), sticky="ew")
        self.avatar_search_entry.bind("<KeyRelease>", self._filter_avatar_list)

        # ComboBox để chọn ID
        ctk.CTkLabel(avatar_frame, text="Chọn Avatar ID:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.avatar_combobox = ctk.CTkComboBox(avatar_frame, values=[], width=350, command=self.on_avatar_select, state="disabled")
        self.avatar_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        # self.avatar_combobox.set(self.avatar_id.get()) # Không set ở đây nữa, _update_avatar_combobox sẽ làm

        # Nút tải danh sách -> đổi thành nút Cập nhật
        self.load_avatar_button = ctk.CTkButton(avatar_frame, text="Cập nhật DS", command=self.force_update_avatars) # Đổi command
        self.load_avatar_button.grid(row=2, column=2, padx=5, pady=5)

        # Output Directory Section
        output_frame = ctk.CTkFrame(tab)
        # Dời Output Directory xuống row 3
        output_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        output_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(output_frame, text="Thư mục đầu ra", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5, 10))

        ctk.CTkLabel(output_frame, text="Đường dẫn:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        output_entry = ctk.CTkEntry(output_frame, textvariable=self.output_dir, width=400)
        output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        output_button = ctk.CTkButton(output_frame, text="Chọn thư mục", command=self.select_output_dir)
        output_button.grid(row=1, column=2, padx=5, pady=5)

        # Log Section
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        tab.grid_rowconfigure(4, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(log_frame, text="Logs Hoạt động", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=(5, 5), sticky="w")
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Save/Load Config Buttons
        config_button_frame = ctk.CTkFrame(tab)
        config_button_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        # Use self.save_config_action and self.load_config_action as commands
        save_button = ctk.CTkButton(config_button_frame, text="Lưu Cấu Hình", command=self.save_config_action)
        save_button.pack(side="left", padx=5)
        load_button = ctk.CTkButton(config_button_frame, text="Tải Cấu Hình", command=self.load_config_action)
        load_button.pack(side="left", padx=5)

    def update_api_key(self, index, key):
        if index < len(self.api_keys):
            # Strip whitespace from the key
            clean_key = key.strip()
            self.api_keys[index] = clean_key
            try:
                if index < len(self.api_key_labels) and self.api_key_labels[index] is not None:
                   label_widget = self.api_key_labels[index]
                   # Display using the clean key
                   display_key = f"API Key: ...{clean_key[-4:]}" if clean_key else "API Key: (Chưa thiết lập)"
                   label_widget.configure(text=display_key)
            except Exception as e:
                 print(f"Error updating API key label for tab {index}: {e}")

    def select_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)
            self.log(f"Đã chọn thư mục đầu ra: {directory}")

    # --- Avatar Loading, Searching and Selection ---
    def _load_avatar_cache_on_startup(self):
        """Tries to load avatar list from cache file on startup."""
        self.log("Đang kiểm tra cache danh sách avatar...")
        cached_list = config_manager.load_avatar_cache(self.log)
        if cached_list is not None: # Kiểm tra None vì hàm trả về None nếu lỗi/không có file
            self.avatar_list_cache = cached_list
            self.log("Đã sử dụng danh sách ID từ cache.")
            # Kích hoạt combobox và cập nhật hiển thị
            if self.avatar_combobox:
                self.avatar_combobox.configure(state="normal")
            if self.avatar_search_entry:
                self.avatar_search_entry.configure(state="normal")
            self._filter_avatar_list() # Cập nhật combobox với dữ liệu cache
        else:
            self.log("Không có cache avatar hợp lệ. Cần nhấn 'Cập nhật DS' để tải.")
            # Giữ combobox và search bị disable
            if self.avatar_combobox: self.avatar_combobox.configure(state="disabled")
            if self.avatar_search_entry: self.avatar_search_entry.configure(state="disabled")

    def force_update_avatars(self):
        """Forces fetching the avatar list from API, ignoring cache."""
        self.log("Buộc cập nhật danh sách avatar từ API...")
        self.avatar_list_cache = None # Xóa cache trong bộ nhớ để load_avatars gọi API
        # Xóa nội dung ô search để hiển thị list đầy đủ sau khi cập nhật
        if self.avatar_search_entry: self.avatar_search_entry.delete(0, tk.END)
        self.load_avatars() # Gọi hàm load cũ, nó sẽ thấy cache là None và gọi API

    def load_avatars(self):
        """Loads avatar list, preferring cache if available, otherwise fetches from API."""
        # Hàm này giờ chỉ được gọi bởi force_update hoặc tự động khi cache None
        if self.avatar_list_cache is not None:
            # Trường hợp này ít khi xảy ra trừ khi gọi nhầm
            self.log("Danh sách avatar đã có trong cache, không cần tải lại.")
            # Đảm bảo UI được cập nhật đúng
            self._filter_avatar_list()
            return

        # --- Phần còn lại là gọi API như cũ --- 
        api_key_to_use = next((key for key in self.api_keys if key), None)
        if not api_key_to_use:
            messagebox.showwarning("Thiếu API Key", "Vui lòng nhập ít nhất một API Key hợp lệ trong Cài đặt để tải danh sách Avatar.")
            # Kích hoạt lại nút nếu có lỗi
            if self.load_avatar_button: self.load_avatar_button.configure(state="normal")
            return

        self.log(f"Đang tải danh sách Avatar ID từ API bằng Key ...{api_key_to_use[-4:]}...")
        if self.load_avatar_button: self.load_avatar_button.configure(state="disabled")
        if self.avatar_combobox: self.avatar_combobox.configure(state="disabled")
        if self.avatar_search_entry: self.avatar_search_entry.configure(state="disabled")

        self.log("Bắt đầu luồng tải avatar API...")
        thread = threading.Thread(target=self._fetch_avatar_list_thread_safe, args=(api_key_to_use,), daemon=True)
        thread.start()

    def _fetch_avatar_list_thread_safe(self, api_key):
        """Wrapper to call API and handle exceptions for thread execution."""
        try:
            self.log(f"Thread API Key ...{api_key[-4:]}: Bắt đầu tải danh sách avatar...")
            proxies = self._get_current_proxies()
            id_list = heygen_api.fetch_avatar_list(api_key, proxies)
            self.avatar_list_cache = id_list # Cập nhật cache trong bộ nhớ
            self.log(f"Thread API Key ...{api_key[-4:]}: Tải thành công {len(id_list)} avatar ID.")

            # --- Lưu cache vào file --- 
            config_manager.save_avatar_cache(id_list, self.log)
            # ---------------------------

            self.after(0, self._update_avatar_ui_after_fetch, None, True)
        except Exception as e:
            error_message = str(e)
            self.log(f"LỖI (Thread API Key ...{api_key[-4:]}): {error_message}")
            self.after(0, self._update_avatar_ui_after_fetch, error_message, False)

    def _update_avatar_ui_after_fetch(self, error_msg, success):
         self.log("UI Update: Bắt đầu cập nhật giao diện sau khi tải avatar.")
         if self.load_avatar_button: self.load_avatar_button.configure(state="normal")
         if self.avatar_search_entry: self.avatar_search_entry.configure(state="normal")

         if success and self.avatar_list_cache is not None:
             if self.avatar_combobox:
                 self.avatar_combobox.configure(state="normal")
             self._filter_avatar_list()
         else:
             if self.avatar_combobox:
                 self.avatar_combobox.configure(state="disabled", values=[])
             # Không xóa cache ở đây nữa vì có thể muốn giữ lại cache cũ nếu API lỗi
             # self.avatar_list_cache = None

         if error_msg:
             self.log(f"Lỗi tải danh sách Avatar: {error_msg}")
             messagebox.showerror("Lỗi tải Avatar", error_msg)
         elif success and not self.avatar_list_cache:
             self.log("API trả về danh sách avatar ID trống.")

    def _filter_avatar_list(self, event=None):
        """Lọc danh sách ID trong ComboBox dựa trên ô tìm kiếm."""
        if not self.avatar_list_cache or not self.avatar_combobox or not self.avatar_search_entry:
            return

        search_term = self.avatar_search_entry.get().lower()
        filtered_ids = [id_val for id_val in self.avatar_list_cache if search_term in id_val.lower()] if search_term else self.avatar_list_cache

        # Xác định ID cần được chọn sau khi lọc
        current_id_from_var = self.avatar_id.get()
        id_to_select = ""
        if current_id_from_var in filtered_ids:
            id_to_select = current_id_from_var
        elif filtered_ids:
            id_to_select = filtered_ids[0]

        # --- Cập nhật ComboBox --- 
        # 1. Lưu và tạm thời xóa command callback
        original_command = self.avatar_combobox.cget("command")
        self.avatar_combobox.configure(command=None)

        # 2. Cập nhật danh sách giá trị
        self.avatar_combobox.configure(values=filtered_ids)

        # 3. Đặt giá trị được chọn (nếu có)
        self.avatar_combobox.set(id_to_select)
        self.log(f"_filter_avatar_list: Set combobox to '{id_to_select}'")

        # 4. Khôi phục command callback
        self.avatar_combobox.configure(command=original_command)

        # 5. Cập nhật biến self.avatar_id nếu giá trị được set khác giá trị hiện tại
        #    (Vì command callback đã bị tắt nên cần cập nhật thủ công nếu cần)
        if id_to_select != current_id_from_var:
            self.avatar_id.set(id_to_select)
            if id_to_select:
                self.log(f"_filter_avatar_list: Updated self.avatar_id to '{id_to_select}'")
            else:
                self.log("_filter_avatar_list: Cleared self.avatar_id as selection is empty.")

    def on_avatar_select(self, _=None):
        """Xử lý KHI NGƯỜI DÙNG chọn một ID từ ComboBox."""
        # Hàm này giờ chỉ xử lý sự kiện do người dùng tương tác
        if not self.avatar_combobox:
            return

        selected_id = self.avatar_combobox.get()
        current_stored_id = self.avatar_id.get()
        self.log(f"on_avatar_select (USER ACTION): Combobox get() = '{selected_id}', Stored ID = '{current_stored_id}'")

        if selected_id != current_stored_id:
            self.avatar_id.set(selected_id)
            self.log(f"==> USER ACTION: Updated Avatar ID to: {selected_id}")
        # else: self.log("on_avatar_select: No change needed from user action.")

    # --- Generation Tab Creation and Actions ---
    def create_generation_tab(self, tab, index):
        tab.grid_columnconfigure(1, weight=1)
        # Adjust row configuration for new elements
        tab.grid_rowconfigure(3, weight=0) # Button row
        tab.grid_rowconfigure(4, weight=1) # History List Frame
        tab.grid_rowconfigure(5, weight=1) # Current Job Log Textbox (optional, maybe remove later)

        tab_widgets = {}

        # --- Row 0: API Key Info Frame (includes Check button) ---        
        api_info_frame = ctk.CTkFrame(tab)
        api_info_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=(10,5), sticky="ew")
        api_info_frame.grid_columnconfigure(0, weight=0) 
        api_info_frame.grid_columnconfigure(1, weight=1) 
        api_info_frame.grid_columnconfigure(2, weight=0) 
        
        api_key_label = ctk.CTkLabel(api_info_frame, text=f"API Key: (Chưa thiết lập)", font=ctk.CTkFont(weight="bold"))
        api_key_label.grid(row=0, column=0, padx=(5,10), pady=5, sticky="w")
        if index < len(self.api_key_labels): self.api_key_labels[index] = api_key_label
            
        credit_label = ctk.CTkLabel(api_info_frame, text="Quota: (Chưa kiểm tra)", text_color="gray")
        credit_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        if index < len(self.api_key_credit_labels): self.api_key_credit_labels[index] = credit_label
        
        check_button_tab = ctk.CTkButton(api_info_frame, text="Kiểm tra", width=80,
                                         command=lambda idx=index: self._check_credit_for_key(idx))
        check_button_tab.grid(row=0, column=2, padx=(5, 10), pady=5, sticky="e")

        if index < len(self.api_keys) and self.api_keys[index]:
             self.update_api_key(index, self.api_keys[index])

        # --- Row 1: Audio Input ---        
        audio_frame = ctk.CTkFrame(tab)
        audio_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        audio_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(audio_frame, text="File Audio / URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        audio_entry = ctk.CTkEntry(audio_frame, placeholder_text="Nhập URL hoặc chọn file audio (.mp3, .wav,...)", width=300)
        audio_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        audio_button = ctk.CTkButton(audio_frame, text="Chọn File", width=80,
                                     command=lambda e=audio_entry: self.select_audio_file(e))
        audio_button.grid(row=0, column=2, padx=5, pady=5)
        tab_widgets['audio_entry'] = audio_entry

        # --- Row 2: Action Buttons ---        
        action_frame = ctk.CTkFrame(tab)
        action_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        generate_button = ctk.CTkButton(action_frame, text="Tạo Video",
                                         command=lambda idx=index, audio_w=audio_entry: self.start_video_generation(idx, audio_w.get()))
        generate_button.pack(side="left", padx=10, pady=5)
        tab_widgets['generate_button'] = generate_button
        download_button = ctk.CTkButton(action_frame, text="Tải Video", state="disabled",
                                        command=lambda idx=index: self.download_generated_video(idx))
        download_button.pack(side="left", padx=10, pady=5)
        tab_widgets['download_button'] = download_button # Keep track for auto-download enable

        # --- Row 3: Video List Actions ---         
        list_action_frame = ctk.CTkFrame(tab)
        list_action_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=(5,0), sticky="ew")
        
        fetch_list_button = ctk.CTkButton(list_action_frame, text="Tải danh sách video đã tạo", 
                                          command=lambda idx=index: self._fetch_video_list(idx))
        fetch_list_button.pack(side="left", padx=5, pady=5)
        # Maybe add refresh button later

        # --- Row 4: Fetched Video List Display ---         
        history_list_frame = ctk.CTkFrame(tab, fg_color="transparent") # Frame to hold the label + scrollable frame
        history_list_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=(0,5), sticky="nsew")
        history_list_frame.grid_columnconfigure(0, weight=1)
        history_list_frame.grid_rowconfigure(1, weight=1) # Make scrollable frame expand
        
        ctk.CTkLabel(history_list_frame, text="Video đã tạo (từ API):", anchor="w").grid(row=0, column=0, sticky="ew", padx=5, pady=(0,2))
        
        # Use CTkScrollableFrame to display the list
        video_scrollable_list = CTkScrollableFrame(history_list_frame, label_text="") # Remove label here
        video_scrollable_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=0)
        tab_widgets['video_scrollable_list'] = video_scrollable_list
        # We will add items (frames with labels/buttons) to this scrollable frame later

        # --- Row 5: Current Job Log (Optional - Keep for now) ---         
        log_frame = ctk.CTkFrame(tab)
        log_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        # Using CTkTextbox to log progress of the CURRENTLY generating video in this tab
        current_job_log = ctk.CTkTextbox(log_frame, wrap="word", state="disabled", height=100)
        current_job_log.pack(expand=True, fill="both", padx=5, pady=5)
        tab_widgets['current_job_log'] = current_job_log 
        # Note: We need to update _add_video_to_list to use this textbox
        # And the polling log inside _generate_and_poll_video should probably write here too.

        # Store main tab widgets if needed later
        if index < len(self.tab_generation_widgets):
            self.tab_generation_widgets[index] = tab_widgets 
        # Store the scrollable list separately for easier access
        if index < len(self.video_list_widgets):
             self.video_list_widgets[index] = video_scrollable_list

    def select_audio_file(self, entry_widget):
        # --- Set Default Directory ---        
        default_input_dir = "G:/Work/MMO/MP3" # Use forward slashes for consistency
        if not os.path.isdir(default_input_dir): 
            default_input_dir = os.getcwd() # Fallback if default doesn't exist
            
        filepath = filedialog.askopenfilename(
            initialdir=default_input_dir, # Set initial directory
            title="Chọn file audio",
            filetypes=(("Audio Files", "*.mp3 *.wav *.m4a *.aac"), ("All Files", "*.*"))
        )
        if filepath:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filepath)
            self.log(f"Đã chọn file audio: {filepath}")
            
    def start_video_generation(self, tab_index, audio_input):
        api_key = self.api_keys[tab_index]
        avatar = self.avatar_id.get()
        output = self.output_dir.get()

        if not api_key:
            messagebox.showerror("Lỗi", f"Vui lòng nhập API Key {tab_index + 1} trong tab Cài đặt.")
            return
        
        # --- Kiểm tra audio_input cơ bản ---        
        if not audio_input:
            messagebox.showerror("Lỗi", f"Vui lòng nhập URL audio hoặc chọn file audio cho Tab {tab_index + 1}.")
            return
        
        # Kiểm tra URL hoặc sự tồn tại của file sẽ được thực hiện trong heygen_api.py

        if not avatar:
            messagebox.showerror("Lỗi", "Vui lòng chọn hoặc nhập Avatar ID trong tab Cài đặt.")
            return
        if not output or not os.path.isdir(output):
            messagebox.showerror("Lỗi", "Vui lòng chọn một thư mục đầu ra hợp lệ trong tab Cài đặt.")
            return

        self.log(f"Tab {tab_index+1}: Chuẩn bị tạo video với đầu vào: {audio_input}")
        # Run generation and status polling in a separate thread
        # Truyền trực tiếp audio_input (path hoặc URL) vào thread
        thread = threading.Thread(target=self._generate_and_poll_video,
                                  args=(tab_index, api_key, audio_input, avatar, output),
                                  daemon=True)
        thread.start()

    def _generate_and_poll_video(self, tab_index, api_key, audio_input, avatar_id, output_dir):
        """Handles submitting video generation, polling, and auto-downloading."""
        video_id = None
        listbox_widget = self.tab_generation_widgets[tab_index].get('video_scrollable_list')
        
        # --- Lấy tên hiển thị (tên file hoặc phần cuối URL) ---        
        try:
            if os.path.exists(audio_input) and not audio_input.startswith(('http://', 'https://')):
                 display_name = os.path.basename(audio_input)
            else:
                 # Cố gắng lấy tên file từ URL
                 display_name = os.path.basename(audio_input.split('?')[0]) 
                 if not display_name: # Nếu URL không có tên file rõ ràng
                     display_name = audio_input[-50:] + "..."
        except Exception as e:
            self.log(f"Lỗi lấy tên hiển thị cho audio input '{audio_input}': {e}")
            display_name = f"Input_{tab_index+1}" # Fallback

        try:
            self.log(f"Thread Tab {tab_index+1}: Bắt đầu xử lý tạo video...")
            proxies = self._get_current_proxies()
            video_id = heygen_api.generate_heygen_video(api_key, audio_input, avatar_id, output_dir, proxies)
            self.log(f"Thread Tab {tab_index+1}: Đã gửi yêu cầu tạo video. Video ID: {video_id}")
            job_info = f"{video_id} - Audio: {display_name} - (Pending)"
            self.after(0, self._add_video_to_list, tab_index, job_info)

            poll_interval = 10
            max_polls = 100 # Tăng từ 60 lên 100 để có timeout 1000 giây
            poll_count = 0
            result_video_url = None

            while poll_count < max_polls:
                poll_count += 1
                status_data = heygen_api.check_video_status(api_key, video_id, proxies)
                current_status = status_data.get("status")
                self.log(f"Thread Tab {tab_index+1}: Video {video_id} - Trạng thái: {current_status}")
                status_text = f" ({current_status})"
                if current_status == "failed":
                    error_detail = status_data.get("error", {}).get("message", "Unknown error")
                    status_text = f" (Thất bại: {error_detail})"
                elif current_status == "completed":
                    result_video_url = status_data.get("video_url")
                    status_text = " (Hoàn thành)"

                updated_job_info = f"{video_id} - Audio: {display_name} -{status_text}"
                self.log(f"Update ListBox (cần cải thiện): {updated_job_info}")

                if current_status == "completed":
                    self.log(f"Thread Tab {tab_index+1}: Video {video_id} hoàn thành! URL: {result_video_url}")
                    self.after(0, self._enable_download_button, tab_index, video_id, result_video_url)
                    
                    # --- Auto Download ---                    
                    if result_video_url:
                        self.log(f"Thread Tab {tab_index+1}: Tự động tải video {video_id}...")
                        
                        # --- Construct filename based on audio_input ---                        
                        try:
                            base_name = ""
                            if os.path.exists(audio_input) and not audio_input.startswith(('http://', 'https://')):
                                # It's a local file path
                                base_name = os.path.splitext(os.path.basename(audio_input))[0]
                            elif audio_input.startswith(('http://', 'https://')):
                                # It's a URL, try to parse filename
                                parsed_path = os.path.basename(urlparse(audio_input).path)
                                base_name = os.path.splitext(parsed_path)[0]
                            
                            if not base_name:
                                # Fallback if parsing failed or name is empty
                                base_name = f"{video_id}_video"
                                
                            download_filename_unsafe = f"{base_name}.mp4"
                            # Ensure filename is safe
                            download_filename = "".join(c for c in download_filename_unsafe if c.isalnum() or c in ('.', '-', '_')).rstrip()
                            if not download_filename:
                                download_filename = f"{video_id}.mp4" # Final fallback
                                
                        except Exception as name_ex:
                             self.log(f"Lỗi xử lý tên file cho video {video_id}: {name_ex}. Dùng ID.")
                             download_filename = f"{video_id}.mp4"
                             
                        save_path = os.path.join(output_dir, download_filename)
                        self.log(f"Thread Tab {tab_index+1}: Lưu về: {save_path}")
                        try:
                            success, message = heygen_api.download_video_file(result_video_url, save_path)
                            if success:
                                self.log(f"Thread Tab {tab_index+1}: Tự động tải thành công: {message}")
                            else:
                                self.log(f"Thread Tab {tab_index+1}: Lỗi tự động tải: {message}")
                                # Optionally inform user via main thread if auto-download fails
                                # self.after(0, messagebox.showwarning, f"Lỗi Tải Tự Động Tab {tab_index+1}", f"Không thể tự động tải video {video_id}:\n{message}")
                        except Exception as dl_ex:
                            self.log(f"Thread Tab {tab_index+1}: Lỗi nghiêm trọng khi tự động tải: {dl_ex}")
                    # --------------------                    
                    break
                elif current_status == "failed":
                    self.log(f"Thread Tab {tab_index+1}: Video {video_id} thất bại.")
                    break
                time.sleep(poll_interval)
            else:
                self.log(f"Thread Tab {tab_index+1}: Video {video_id} không hoàn thành sau {max_polls * poll_interval} giây.")
                updated_job_info = f"{video_id} - Audio: {display_name} - (Timeout/Unknown)"
                self.log(f"Update ListBox (cần cải thiện): {updated_job_info}")

        except ValueError as ve:
            # Bắt lỗi cụ thể từ generate_heygen_video (bao gồm cả lỗi upload)
             error_message = f"Lỗi tạo video Tab {tab_index+1}: {ve}"
             self.log(error_message)
             self.after(0, messagebox.showerror, f"Lỗi Video Tab {tab_index+1}", error_message)
        except Exception as e:
            # Bắt các lỗi không mong muốn khác
            error_message = f"Lỗi nghiêm trọng trong quá trình tạo/theo dõi video Tab {tab_index+1}: {e}\n{traceback.format_exc()}"
            self.log(error_message)
            if video_id:
                 updated_job_info = f"{video_id} - Audio: {display_name} - (Lỗi: {e})"
                 self.log(f"Update ListBox (cần cải thiện): {updated_job_info}")
            self.after(0, messagebox.showerror, f"Lỗi Video Tab {tab_index+1}", f"Lỗi không mong muốn: {e}")

    def _add_video_to_list(self, tab_index, job_info):
        """Adds NEW video job info to the CURRENT job log textbox."""
        try:
            # Target the new textbox for current job logs
            log_textbox = self.tab_generation_widgets[tab_index]['current_job_log']
            log_textbox.configure(state="normal")
            # Clear previous log? Or append?
            # log_textbox.delete("1.0", tk.END) # Optional: Clear before adding new job log
            log_textbox.insert(tk.END, f"{time.strftime('%H:%M:%S')} - Bắt đầu: {job_info}\n")
            log_textbox.configure(state="disabled")
            log_textbox.see(tk.END)
        except Exception as e:
            self.log(f"Lỗi thêm vào current_job_log Tab {tab_index+1}: {e}")
            
    # --- Video List Fetching Methods --- 
    def _fetch_video_list(self, tab_index):
        """Starts thread to fetch video list for the given tab's API key."""
        self.log(f"Tab {tab_index + 1}: Bắt đầu tải danh sách video...")
        # TODO: Add visual indicator (disable button?)
        if tab_index >= len(self.api_keys):
             return
        api_key = self.api_keys[tab_index]
        if not api_key:
            messagebox.showerror("Lỗi", f"Vui lòng nhập API Key {tab_index + 1} trước.")
            return
            
        thread = threading.Thread(target=self._get_video_list_thread_safe, args=(tab_index, api_key), daemon=True)
        thread.start()
        
    def _get_video_list_thread_safe(self, tab_index, api_key):
        """Calls API to get video list in a separate thread."""
        try:
            proxies = self._get_current_proxies()
            video_data = heygen_api.list_videos(api_key, proxies, limit=100) # Fetch first 100
            # Update GUI in main thread
            self.after(0, self._update_video_list_display, tab_index, video_data.get('videos', []), None)
        except Exception as e:
            error_message = f"Lỗi tải danh sách video Key {tab_index + 1}: {e}"
            self.log(error_message)
            # Update GUI in main thread on error
            self.after(0, self._update_video_list_display, tab_index, [], str(e))
            
    def _update_video_list_display(self, tab_index, video_list, error_message):
        """Updates the video list display in the scrollable frame."""
        if tab_index >= len(self.video_list_widgets) or not self.video_list_widgets[tab_index]:
             self.log(f"Lỗi: Không tìm thấy video_list_widget cho tab {tab_index + 1}")
             return
             
        scrollable_frame = self.video_list_widgets[tab_index]
        
        # Clear previous items
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
            
        if error_message:
            error_label = ctk.CTkLabel(scrollable_frame, text=f"Lỗi tải danh sách: {error_message}", text_color="red", wraplength=350)
            error_label.pack(pady=10, padx=10)
            return
            
        if not video_list:
            no_videos_label = ctk.CTkLabel(scrollable_frame, text="(Không có video nào được tìm thấy)")
            no_videos_label.pack(pady=10, padx=10)
            return
            
        # Populate with new video items
        for video_info in video_list:
            video_id = video_info.get('video_id', 'N/A')
            status = video_info.get('status', 'N/A')
            created_timestamp = video_info.get('created_at', 0)
            
            # Convert timestamp to readable format
            try:
                created_dt = datetime.fromtimestamp(created_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except:
                created_dt = "N/A"
            
            item_frame = ctk.CTkFrame(scrollable_frame)
            item_frame.pack(fill="x", padx=5, pady=3)
            item_frame.grid_columnconfigure(0, weight=1) # ID and Date
            item_frame.grid_columnconfigure(1, weight=0) # Status
            item_frame.grid_columnconfigure(2, weight=0) # Download Button
            
            info_text = f"ID: {video_id}\nNgày tạo: {created_dt}"
            ctk.CTkLabel(item_frame, text=info_text, justify="left").grid(row=0, column=0, padx=5, pady=2, sticky="w")
            
            status_color = "gray"
            if status == "completed": status_color = "green"
            elif status == "failed": status_color = "red"
            elif status == "processing": status_color = "orange"
            ctk.CTkLabel(item_frame, text=f"Trạng thái: {status}", text_color=status_color).grid(row=0, column=1, padx=5, pady=2, sticky="e")
            
            download_button = ctk.CTkButton(item_frame, text="Tải xuống", width=80,
                                            state="normal" if status == "completed" else "disabled",
                                            command=lambda v_id=video_id: self._download_listed_video(tab_index, v_id))
            download_button.grid(row=0, column=2, padx=5, pady=2)
            
        self.log(f"Tab {tab_index + 1}: Đã hiển thị {len(video_list)} video.")

    def _download_listed_video(self, tab_index, video_id):
        """Initiates download for a video selected from the list."""
        self.log(f"Tab {tab_index + 1}: Chuẩn bị tải video {video_id} từ danh sách...")

        # 1. Get API Key for this tab
        if tab_index >= len(self.api_keys) or not self.api_keys[tab_index]:
            messagebox.showerror("Lỗi", f"Không tìm thấy API Key hợp lệ cho Tab {tab_index + 1}.")
            return
        api_key = self.api_keys[tab_index]
        output_dir = self.output_dir.get()
        if not output_dir or not os.path.isdir(output_dir):
             messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đầu ra hợp lệ trong tab Cài đặt trước khi tải.")
             return

        # 2. Start a thread to get status/URL and then download
        thread = threading.Thread(target=self._get_status_and_download_thread,
                                  args=(tab_index, api_key, video_id, output_dir),
                                  daemon=True)
        thread.start()

    def _get_status_and_download_thread(self, tab_index, api_key, video_id, output_dir):
        """Thread worker: gets video status, then prompts for save and downloads."""
        fresh_video_url = None
        try:
            # a. Call check_video_status to get the fresh video_url
            self.log(f"Thread DL Tab {tab_index + 1}: Lấy URL mới nhất cho video {video_id}...")
            proxies = self._get_current_proxies()
            status_data = heygen_api.check_video_status(api_key, video_id, proxies)
            
            if status_data.get('status') == 'completed':
                fresh_video_url = status_data.get('video_url')
                if not fresh_video_url:
                    self.log(f"Thread DL Tab {tab_index + 1}: Lỗi - Video {video_id} hoàn thành nhưng không có URL.")
                    self.after(0, messagebox.showerror, f"Lỗi Tải Video Tab {tab_index + 1}", f"Video {video_id} đã hoàn thành nhưng không tìm thấy URL để tải.")
                    return
            else:
                self.log(f"Thread DL Tab {tab_index + 1}: Video {video_id} chưa hoàn thành (Trạng thái: {status_data.get('status')}). Không thể tải.")
                self.after(0, messagebox.showwarning, f"Thông Tin Tab {tab_index + 1}", f"Video {video_id} chưa hoàn thành hoặc bị lỗi. Không thể tải.")
                return

            # b. If URL obtained:
            #    i. Prompt user for save location using filedialog.asksaveasfilename
            #       This needs to run in the main thread using self.after
            self.log(f"Thread DL Tab {tab_index + 1}: Lấy URL thành công cho {video_id}. Chuẩn bị hỏi nơi lưu...")
            self.after(0, self._prompt_and_start_download, tab_index, video_id, fresh_video_url, output_dir)

        except Exception as e:
             error_message = f"Lỗi khi lấy trạng thái/URL cho video {video_id}: {e}"
             self.log(f"Thread DL Tab {tab_index + 1}: {error_message}")
             self.after(0, messagebox.showerror, f"Lỗi Tải Video Tab {tab_index + 1}", error_message)

    def _prompt_and_start_download(self, tab_index, video_id, video_url, output_dir):
        """Runs in main thread: Prompts user for save path and starts download thread."""
        suggested_filename = f"{video_id}.mp4" # Simple name for listed videos
        save_path = filedialog.asksaveasfilename(
            initialdir=output_dir,
            initialfile=suggested_filename,
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")]
        )
        
        if save_path:
            self.log(f"Tab {tab_index+1}: Bắt đầu tải video {video_id} về: {save_path}")
            # Start the actual download in another thread
            dl_thread = threading.Thread(target=self._download_video_file_thread, # New dedicated download func
                                       args=(video_url, save_path),
                                       daemon=True)
            dl_thread.start()
        else:
            self.log(f"Tab {tab_index+1}: Người dùng đã hủy tải video {video_id}.")

    def _download_video_file_thread(self, video_url, save_path):
         """Dedicated thread for downloading a single video file."""
         log_prefix = f"Thread DL Tab {tab_index + 1} ({video_id}): "
         try:
             success, message = heygen_api.download_video_file(video_url, save_path)
             if success:
                 self.log(f"{log_prefix}{message}")
                 self.after(0, messagebox.showinfo, f"Thành Công Tab {tab_index + 1}", f"Đã tải video {video_id} thành công!\n{save_path}")
             else:
                 self.log(f"{log_prefix}Lỗi tải - {message}")
                 self.after(0, messagebox.showerror, f"Lỗi Tải Video Tab {tab_index + 1}", f"Không thể tải video {video_id}:\n{message}")
         except Exception as e:
             error_msg = f"Lỗi nghiêm trọng khi tải video {video_id}: {e}"
             self.log(f"{log_prefix}{error_msg}")
             self.after(0, messagebox.showerror, f"Lỗi Tải Video Tab {tab_index + 1}", error_msg)

    def get_selected_video_info(self, tab_index):
         # This needs significant improvement. CTkTextbox isn't ideal for selection.
         # We need to store job info (id, status, url) elsewhere and link to list items.
         self.log(f"Lấy thông tin video đã chọn (hiện không hoạt động tốt với CTkTextbox) Tab {tab_index+1}")
         return None # Placeholder - cannot reliably get selection

    def create_proxy_tab(self):
        tab = self.tab_proxy
        tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab, text="Cài đặt Proxy (Tùy chọn)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(tab, text="HTTP Proxy:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        http_proxy_entry = ctk.CTkEntry(tab, placeholder_text="http://user:pass@host:port", width=400)
        http_proxy_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        http_proxy_entry.bind("<KeyRelease>", lambda e: self.update_proxy("http", e.widget.get()))

        ctk.CTkLabel(tab, text="HTTPS Proxy:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        https_proxy_entry = ctk.CTkEntry(tab, placeholder_text="http://user:pass@host:port", width=400)
        https_proxy_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        https_proxy_entry.bind("<KeyRelease>", lambda e: self.update_proxy("https", e.widget.get()))

        ctk.CTkLabel(tab, text="Để trống nếu không sử dụng proxy.", font=ctk.CTkFont(size=10)).grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # Store widgets for loading config later
        self.proxy_entries = {'http': http_proxy_entry, 'https': https_proxy_entry}

    def update_proxy(self, proto, value):
        self.proxy_settings[proto] = value.strip() if value else ""
        self.log(f"Đã cập nhật {proto.upper()} proxy.")

    def _get_current_proxies(self):
        return self.proxy_settings if any(self.proxy_settings.values()) else None

    # --- Configuration Save/Load Actions ---
    def save_config_action(self, show_success_message=True):
        """Action triggered by the Save Config button or on closing."""
        cleaned_api_keys = [entry.get().strip() for entry in self.api_key_entries]
        current_avatar_id = self.avatar_id.get()
        current_geometry = self.geometry() # Lấy geometry hiện tại
        self.log(f"Đang lưu Avatar ID: '{current_avatar_id}'")
        self.log(f"Đang lưu Geometry: '{current_geometry}'")
        config_data = {
            "api_keys": cleaned_api_keys,
            "avatar_id": current_avatar_id,
            "output_dir": self.output_dir.get(),
            "proxy": self.proxy_settings,
            "window_geometry": current_geometry # Thêm geometry vào dữ liệu lưu
        }
        self.api_keys = cleaned_api_keys
        save_successful = config_manager.save_config(config_data, self.log)
        if save_successful and show_success_message:
            messagebox.showinfo("Thành công", "Đã lưu cấu hình thành công!")
        return save_successful

    def load_config_action(self):
        """Action triggered by the Load Config button."""
        loaded_config = config_manager.load_config(self.log)
        self._apply_loaded_config(loaded_config)
        messagebox.showinfo("Hoàn tất", "Đã tải và áp dụng cấu hình.")

    def _apply_loaded_config(self, config):
        """Applies the loaded configuration data to the GUI widgets and internal state."""
        self.log("Áp dụng cấu hình đã tải...")

        # Geometry đã được áp dụng trong __init__

        # Apply API Keys
        loaded_keys = config.get("api_keys", [""] * 5)
        self.api_keys = loaded_keys
        for i in range(min(len(loaded_keys), 5)):
            if i < len(self.api_key_entries):
                self.api_key_entries[i].delete(0, tk.END)
                self.api_key_entries[i].insert(0, loaded_keys[i])
            self.update_api_key(i, loaded_keys[i])

        # Apply Avatar ID to the variable
        loaded_avatar_id = config.get("avatar_id", "Conrad_standing_house_front")
        self.avatar_id.set(loaded_avatar_id)
        self.log(f"Đã tải Avatar ID từ config: {loaded_avatar_id}")

        # Reset cache, combobox values sẽ được cập nhật khi list được tải
        self.avatar_list_cache = None # Lưu cache là list ID đầy đủ
        if self.avatar_combobox:
            self.avatar_combobox.configure(values=[], state="disabled")
            # Xóa nội dung ô search khi load config
        if hasattr(self, 'avatar_search_entry') and self.avatar_search_entry:
            self.avatar_search_entry.delete(0, tk.END)

        # Apply Output Directory
        self.output_dir.set(config.get("output_dir", os.getcwd()))

        # Apply Proxy Settings
        loaded_proxy = config.get("proxy", {"http": "", "https": ""})
        self.proxy_settings = loaded_proxy
        if 'http' in self.proxy_entries and self.proxy_entries['http']:
            self.proxy_entries['http'].delete(0, tk.END)
            self.proxy_entries['http'].insert(0, loaded_proxy.get("http", ""))
        if 'https' in self.proxy_entries and self.proxy_entries['https']:
            self.proxy_entries['https'].delete(0, tk.END)
            self.proxy_entries['https'].insert(0, loaded_proxy.get("https", ""))

        self.log("Đã áp dụng cấu hình.")

    # --- Window Closing Handler ---
    def on_closing(self):
        """Called when the user tries to close the window."""
        self.log("Đang lưu cấu hình trước khi thoát...")
        # Attempt to save configuration
        save_successful = self.save_config_action(show_success_message=False)
        if save_successful:
            self.log("Đã lưu cấu hình. Đang thoát.")
        else:
            if messagebox.askokcancel("Lỗi Lưu Cấu Hình", "Không thể lưu cấu hình hiện tại. Bạn vẫn muốn thoát?"):
                self.log("Thoát mà không lưu cấu hình do lỗi.")
            else:
                self.log("Hủy thoát để sửa lỗi lưu cấu hình.")
                return
        self.destroy()

    # --- Credit Check Methods --- 
    def _check_credit_for_key(self, index):
        """Starts a thread to check credit for the selected API key."""
        if index >= len(self.api_keys):
            return
        api_key = self.api_keys[index]
        if not api_key:
            messagebox.showwarning("Thiếu API Key", f"Vui lòng nhập API Key {index + 1} trước khi kiểm tra.")
            return
        
        # Update label to show checking status
        if self.api_key_credit_labels[index]:
            self.api_key_credit_labels[index].configure(text="Quota: Đang kiểm tra...", text_color="orange")

        self.log(f"Bắt đầu kiểm tra quota cho API Key {index + 1}...")
        thread = threading.Thread(target=self._get_quota_thread_safe, args=(index, api_key), daemon=True)
        thread.start()

    def _get_quota_thread_safe(self, index, api_key):
        """Calls the API to get quota in a separate thread."""
        try:
            proxies = self._get_current_proxies()
            quota_data = heygen_api.get_remaining_quota(api_key, proxies)
            # Update GUI in main thread on success
            self.after(0, self._update_credit_display, index, quota_data, None)
        except Exception as e:
            error_message = f"Lỗi kiểm tra quota Key {index + 1}: {e}"
            self.log(error_message)
            # Update GUI in main thread on error
            self.after(0, self._update_credit_display, index, None, str(e))

    def _update_credit_display(self, index, quota_data, error_message):
        """Updates the credit label AND logs the result."""
        log_prefix = f"Quota Key {index + 1}: "
        display_text = ""
        text_color = "gray"
        log_message = ""

        if error_message:
            display_text = f"Quota: Lỗi ({error_message[:30]}...)"
            text_color = "red"
            log_message = f"{log_prefix}Lỗi - {error_message}"
        elif quota_data:
            try:
                remaining_quota = float(quota_data.get('remaining_quota', 0))
                tokens = remaining_quota / 60
                minutes = remaining_quota / 30
                display_text = f"Quota: {remaining_quota:.2f} ({tokens:.1f} Tokens / {minutes:.1f} Phút)"
                text_color = "green"
                log_message = f"{log_prefix}{display_text}"
            except Exception as parse_err:
                display_text = "Quota: Lỗi xử lý data"
                text_color = "red"
                log_message = f"{log_prefix}Lỗi xử lý data - {parse_err}"
        else:
            display_text = "Quota: Lỗi không xác định"
            text_color = "red"
            log_message = f"{log_prefix}Lỗi không xác định khi cập nhật hiển thị quota."

        # --- Update Label ---        
        if index < len(self.api_key_credit_labels) and self.api_key_credit_labels[index]:
            label = self.api_key_credit_labels[index]
            label.configure(text=display_text, text_color=text_color)
        
        # --- Log Result ---        
        if log_message:
            self.log(log_message)

    def _enable_download_button(self, tab_index, video_id, video_url):
         """Enables download button and stores URL (run in main thread)."""
         # TODO: Need a better way to associate URL with the list item / enable download
         # For now, just enable the button generally and store last completed URL per tab?
         try:
             # Store URL somewhere accessible by download_generated_video
             # Maybe a dictionary: self.completed_videos[tab_index] = {"id": video_id, "url": video_url}
             if not hasattr(self, 'last_completed_url'):
                 self.last_completed_url = [None] * 5
             self.last_completed_url[tab_index] = video_url

             button = self.tab_generation_widgets[tab_index]['download_button']
             button.configure(state="normal")
             self.log(f"UI Update Tab {tab_index+1}: Đã kích hoạt nút Tải Video cho {video_id}")
         except Exception as e:
              self.log(f"Lỗi kích hoạt nút tải video Tab {tab_index+1}: {e}")

    def download_generated_video(self, tab_index):
        # Problem: How to know WHICH video to download if multiple completed?
        # Using the simple 'last completed' URL for now.
        video_url = self.last_completed_url[tab_index] if hasattr(self, 'last_completed_url') and tab_index < len(self.last_completed_url) else None

        if not video_url:
            messagebox.showwarning("Chú ý", f"Không tìm thấy URL video đã hoàn thành cho Tab {tab_index + 1}.\nHãy chắc chắn một video đã hoàn thành gần đây.")
            return

        suggested_filename = f"heygen_video_{tab_index+1}_{int(time.time())}.mp4"
        save_path = filedialog.asksaveasfilename(initialdir=self.output_dir.get(),
                                                 initialfile=suggested_filename,
                                                 defaultextension=".mp4",
                                                 filetypes=[("MP4 Video", "*.mp4")])
        if save_path:
            self.log(f"Bắt đầu tải video cho Tab {tab_index+1} về: {save_path}")
            # Run download in a thread
            thread = threading.Thread(target=self._download_video_thread,
                                      args=(video_url, save_path),
                                      daemon=True)
            thread.start()

    def _download_video_thread(self, video_url, save_path):
        """Calls the download function from heygen_api in a thread."""
        try:
            success, message = heygen_api.download_video_file(video_url, save_path)
            if success:
                self.log(message)
                self.after(0, messagebox.showinfo, "Thành công", f"Đã tải video thành công!\n{save_path}")
            else:
                self.log(message) # Log the error message
                self.after(0, messagebox.showerror, "Lỗi Tải Video", message)
        except Exception as e:
            error_msg = f"Lỗi nghiêm trọng khi tải video: {e}"
            self.log(error_msg)
            self.after(0, messagebox.showerror, "Lỗi Tải Video", error_msg)

if __name__ == "__main__":
    app = HeyGenMultiCreatorApp()
    # Config is now loaded inside __init__ after widgets are created
    app.mainloop() 