import requests
import json
import time
import os
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
        response = requests.get(url, headers=self.headers)
        return response.json()
    
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
        
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái của video
        
        Args:
            video_id: ID của video cần kiểm tra
            
        Returns:
            Dict chứa thông tin về trạng thái video
        """
        url = f"{self.BASE_URL}/v1/video_status/{video_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def wait_for_video_completion(self, video_id: str, polling_interval: int = 5, max_attempts: int = 60) -> Dict[str, Any]:
        """
        Đợi cho đến khi video hoàn thành xử lý
        
        Args:
            video_id: ID của video cần kiểm tra
            polling_interval: Thời gian giữa các lần kiểm tra (giây)
            max_attempts: Số lần kiểm tra tối đa
            
        Returns:
            Dict chứa thông tin về video đã hoàn thành
        """
        attempt = 0
        while attempt < max_attempts:
            status_data = self.get_video_status(video_id)
            
            if "data" in status_data and "status" in status_data["data"]:
                status = status_data["data"]["status"]
                
                if status == "completed":
                    print(f"Video đã xử lý xong: {video_id}")
                    return status_data
                elif status == "failed":
                    print(f"Video xử lý thất bại: {video_id}")
                    return status_data
                
                print(f"Video đang xử lý ({status}), đợi {polling_interval} giây...")
            else:
                print(f"Không thể lấy trạng thái video, đợi {polling_interval} giây...")
            
            time.sleep(polling_interval)
            attempt += 1
        
        raise TimeoutError(f"Đã hết thời gian chờ xử lý video sau {max_attempts} lần kiểm tra")


def main():
    """
    Hàm chính để demo tạo video avatar với HeyGen API
    """
    client = HeyGenClient()
    
    # Lấy danh sách tất cả avatars
    print("Đang lấy danh sách avatars...")
    avatars_data = client.get_all_avatars()
    
    if "data" in avatars_data and "avatars" in avatars_data["data"]:
        avatars = avatars_data["data"]["avatars"]
        if avatars:
            print(f"Tìm thấy {len(avatars)} avatars:")
            for i, avatar in enumerate(avatars[:5]):  # Chỉ hiển thị 5 avatars đầu tiên
                print(f"{i+1}. {avatar['avatar_name']} (ID: {avatar['avatar_id']})")
            
            # Sử dụng avatar đầu tiên cho ví dụ
            selected_avatar = avatars[0]
            avatar_id = selected_avatar["avatar_id"]
            print(f"\nĐã chọn avatar: {selected_avatar['avatar_name']} (ID: {avatar_id})")
            
            # Tạo video với audio URL (đây là ví dụ, cần thay thế bằng URL thực)
            audio_url = "https://example.com/path/to/audio.mp3"  # Thay thế URL này
            
            print(f"\nĐang tạo video với avatar ID: {avatar_id} và audio URL: {audio_url}")
            video_data = client.create_avatar_video(
                avatar_id=avatar_id,
                audio_url=audio_url,
                background_color="#008000"  # Màu nền xanh lá
            )
            
            if "data" in video_data and "video_id" in video_data["data"]:
                video_id = video_data["data"]["video_id"]
                print(f"Video đang được tạo với ID: {video_id}")
                
                # Đợi video hoàn thành
                print("Đang đợi video hoàn thành xử lý...")
                result = client.wait_for_video_completion(video_id)
                
                if "data" in result and "video_url" in result["data"]:
                    print(f"Video đã sẵn sàng: {result['data']['video_url']}")
                else:
                    print("Không thể lấy URL video.")
            else:
                print("Không thể tạo video:", video_data)
        else:
            print("Không tìm thấy avatar nào.")
    else:
        print("Không thể lấy danh sách avatars:", avatars_data)


if __name__ == "__main__":
    main() 