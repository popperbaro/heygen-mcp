import requests
import json
import traceback
import os # Thêm import os
from typing import Optional, Dict, Any, List, Tuple

# --- Constants ---
BASE_URL = "https://api.heygen.com"

# Placeholder functions for now, will be filled later
def check_heygen_credit(api_key, proxies):
    # Needs actual endpoint if available
    print(f"Checking credit (placeholder) for key ...{api_key[-4:]}")
    # ... (API call logic) ...
    return {"status": "info", "message": "Chức năng kiểm tra credit chưa có API chính thức."}

# --- Upload Audio Function (Corrected based on Official Docs) ---
def upload_audio_to_heygen(api_key: str, file_path: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """
    Uploads a local audio file to HeyGen via the official /v1/asset endpoint 
    and returns the asset ID.

    Args:
        api_key: The HeyGen API key.
        file_path: The local path to the audio file.
        proxies: Optional dictionary of proxies for the request.

    Returns:
        The asset ID (string) from the API response.

    Raises:
        requests.exceptions.RequestException: If the network request fails.
        FileNotFoundError: If the file_path does not exist.
        ValueError: If the API response does not contain the asset ID or indicates an error.
        KeyError: If the expected keys ('data', 'id') are not in the JSON response.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file audio: {file_path}")

    # --- Correct Endpoint URL ---    
    url = "https://upload.heygen.com/v1/asset"
    
    file_name = os.path.basename(file_path)
    # Determine mime type
    mime_type = None
    lower_path = file_path.lower()
    if lower_path.endswith('.mp3') or lower_path.endswith('.mpeg'): 
        mime_type = 'audio/mpeg'
    elif lower_path.endswith('.wav'): 
        mime_type = 'audio/wav' # Note: Docs only mention mpeg, but wav might work?
    elif lower_path.endswith('.m4a'): 
        mime_type = 'audio/mp4' # Note: Docs only mention mpeg
    elif lower_path.endswith('.aac'): 
        mime_type = 'audio/aac' # Note: Docs only mention mpeg
    # Add other types if needed, ensure they match Content-Type header

    if not mime_type:
        raise ValueError(f"Không thể xác định Content-Type cho file: {file_name}. Chỉ hỗ trợ audio (ví dụ: .mp3). Tài liệu chính thức chỉ đề cập audio/mpeg.")

    # --- Correct Headers ---    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": mime_type 
    }

    print(f"[API UPLOAD] POST {url} - File: {file_name}, Content-Type: {mime_type}")

    try:
        with open(file_path, 'rb') as file_data:
            # --- Send raw data using 'data' parameter ---            
            response = requests.post(url, headers=headers, data=file_data, proxies=proxies, timeout=180) # Longer timeout for upload

        print(f"[API UPLOAD] Response Status: {response.status_code}")
        # print(f"[API UPLOAD] Response Body: {response.text[:500]}...") # Uncomment for debugging
        response.raise_for_status() # Raise HTTPError for bad status codes (4xx or 5xx)

        response_data = response.json()

        # --- Extract asset ID from response['data']['id'] ---        
        if response_data and response_data.get('code') == 100: # Check success code
             data_payload = response_data.get('data')
             if data_payload and isinstance(data_payload, dict):
                 # Correct key is 'id' according to docs
                 asset_id = data_payload.get('id') 
                 if asset_id:
                     print(f"[API UPLOAD] Upload thành công. Asset ID: {asset_id}")
                     return asset_id
                 else:
                     # Changed key name in error message
                     raise KeyError("'id' không tìm thấy trong 'data' của phản hồi API upload.")
             else:
                  raise KeyError("'data' không tìm thấy hoặc không phải dictionary trong phản hồi API upload.")
        else:
            error_msg = "Lỗi từ API Upload." 
            if response_data:
                 error_msg += f" Code: {response_data.get('code')}, Message: {response_data.get('message')}" 
                 error_detail = response_data.get('error')
                 if error_detail: error_msg += f", Error: {error_detail}"
            error_msg += f" Response: {response_data}"
            raise ValueError(error_msg)

    except requests.exceptions.RequestException as e:
        error_message = f"Lỗi mạng khi upload asset: {e}"
        if e.response is not None:
            error_message += f"\nResponse Body: {e.response.text[:500]}"
        print(f"[API ERROR] {error_message}")
        raise
    except FileNotFoundError as e:
        print(f"[API ERROR] {e}")
        raise
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"[API ERROR] Lỗi xử lý phản hồi upload asset: {e}")
        raise
    except Exception as e:
        print(f"[API ERROR] Lỗi không xác định khi upload asset: {e}\n{traceback.format_exc()}")
        raise

def generate_heygen_video(api_key: str, audio_input: str, avatar_id: str, output_dir: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """
    Generates an avatar video using either a local audio file path or a public audio URL.
    If a local path is provided, it uploads the file first to get an audio_asset_id.

    Args:
        api_key: The HeyGen API key.
        audio_input: Local path to the audio file OR public URL of the audio file.
        avatar_id: The ID of the avatar to use.
        output_dir: The intended output directory (currently unused in API call).
        proxies: Optional dictionary of proxies for the request.

    Returns:
        The video_id of the generated video task.

    Raises:
        requests.exceptions.RequestException: If any network request fails.
        ValueError: If the audio_input is invalid, upload fails, or API response indicates an error.
        FileNotFoundError: If audio_input is a path and the file is not found.
    """
    audio_url = None
    audio_asset_id = None

    # --- Determine input type and get asset_id or url ---    
    is_url = audio_input.startswith(('http://', 'https://'))
    is_local_file = os.path.exists(audio_input) and not is_url

    if is_local_file:
        print(f"Phát hiện file audio local: {audio_input}. Bắt đầu upload để lấy Asset ID...")
        try:
            audio_asset_id = upload_audio_to_heygen(api_key, audio_input, proxies)
            print(f"Upload thành công. Sử dụng Audio Asset ID: {audio_asset_id}")
        except (requests.exceptions.RequestException, ValueError, FileNotFoundError, KeyError, Exception) as upload_err:
            # Catch specific errors from upload and raise a new ValueError for the generation step
            raise ValueError(f"Lỗi upload audio file: {upload_err}") from upload_err
    elif is_url:
        print(f"Sử dụng URL audio được cung cấp: {audio_input}")
        audio_url = audio_input
    else:
        raise ValueError(f"Đầu vào audio không hợp lệ: '{audio_input}'. Cần URL công khai hoặc đường dẫn file tồn tại.")

    # --- Prepare Payload for /v2/video/generate ---    
    generate_url = f"{BASE_URL}/v2/video/generate"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "content-type": "application/json"
    }

    voice_settings = {"type": "audio"}
    if audio_asset_id:
        voice_settings["audio_asset_id"] = audio_asset_id
    elif audio_url:
        voice_settings["audio_url"] = audio_url
    else:
        raise ValueError("Không có audio_asset_id hoặc audio_url để tạo video.")

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal"
                },
                "voice": voice_settings
            }
        ],
        # --- Add dimension field for 1280x720 resolution ---        
        "dimension": {
            "width": 1280,
            "height": 720
        },
        "test": False
    }

    # --- Call /v2/video/generate API ---    
    try:
        print(f"[API REQUEST] POST {generate_url}")
        # print(f"[API REQUEST] Payload: {json.dumps(payload, indent=2)}") # Uncomment for debugging payload
        response = requests.post(generate_url, headers=headers, json=payload, proxies=proxies, timeout=60)

        print(f"[API RESPONSE] Status Code: {response.status_code}")
        # print(f"[API RESPONSE] Body: {response.text[:500]}...") # Uncomment for debugging response

        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data is None:
            raise ValueError("API tạo video không trả về dữ liệu.")

        error_info = data.get('error')
        if error_info is not None:
            msg = f"Lỗi API tạo video: {error_info.get('message', 'Unknown error')}"
            if error_info.get('code'): msg += f" (Code: {error_info['code']})"
            raise ValueError(msg)

        video_id = data.get('data', {}).get('video_id')
        if video_id:
            print(f"[API RESPONSE] Tạo video thành công. Video ID: {video_id}")
            return video_id
        else:
            raise ValueError(f"Phản hồi API tạo video thành công nhưng không chứa video_id: {data}")

    except requests.exceptions.RequestException as e:
        error_message = f"Lỗi mạng khi tạo video: {e}"
        if e.response is not None:
            error_message += f"\nResponse Body: {e.response.text[:500]}"
        print(f"[API ERROR] {error_message}")
        raise
    except Exception as e:
        print(f"[API ERROR] Lỗi không xác định khi tạo video: {e}\n{traceback.format_exc()}")
        raise

def check_video_status(api_key: str, video_id: str, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Kiểm tra trạng thái của video đang tạo.

    Args:
        api_key (str): API Key.
        video_id (str): ID của video cần kiểm tra.
        proxies (dict | None): Cài đặt proxy.

    Raises:
        ValueError: Nếu API trả về lỗi.
        requests.exceptions.RequestException: Nếu có lỗi mạng.
        Exception: Các lỗi khác.

    Returns:
        dict: Dictionary chứa thông tin trạng thái (status, video_url, error, ...).
    """
    status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key
    }

    try:
        # print(f"[API REQUEST] GET {status_url}") # Có thể bật để debug nhiều hơn
        response = requests.get(status_url, headers=headers, proxies=proxies, timeout=60)
        response.raise_for_status()
        data = response.json()

        if data is None:
            raise ValueError(f"API kiểm tra trạng thái (ID: {video_id}) không trả về dữ liệu.")
        # API v1 dùng code 100 cho thành công
        elif data.get('code') != 100:
            error_info = data.get('error')
            msg = f"Lỗi API kiểm tra trạng thái: {data.get('message', 'Unknown error')}"
            if error_info: # Thêm chi tiết lỗi nếu có
                 msg += f" - {error_info}"
            raise ValueError(msg)
        elif 'data' in data and isinstance(data.get('data'), dict):
             # Trả về toàn bộ dictionary 'data' vì nó chứa status, url, error...
             status_data = data['data']
             # print(f"[API RESPONSE] Trạng thái video {video_id}: {status_data.get('status')}")
             return status_data
        else:
            raise ValueError(f"Phản hồi API kiểm tra trạng thái không hợp lệ: {data}")

    except requests.exceptions.RequestException as e:
        # print(f"[API ERROR] Lỗi mạng khi kiểm tra trạng thái video {video_id}: {e}")
        raise
    except Exception as e:
        # print(f"[API ERROR] Lỗi không xác định khi kiểm tra trạng thái video {video_id}: {e}")
        raise

def download_video_file(video_url: str, output_path: str) -> Tuple[bool, str]:
    """Tải nội dung video từ URL về đường dẫn file."""
    try:
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True, f"Đã tải xong video về: {output_path}"
    except requests.exceptions.RequestException as e:
        return False, f"Lỗi tải video: {e}"
    except Exception as e:
        return False, f"Lỗi không xác định khi tải video: {e}"

def fetch_avatar_list(api_key: str, proxies: Optional[Dict[str, str]] = None) -> List[str]:
    """Tải danh sách avatar ID từ API HeyGen.

    Raises:
        ValueError: Nếu có lỗi xảy ra trong quá trình gọi API hoặc xử lý dữ liệu.
    Returns:
        list: Danh sách các chuỗi avatar_id (bao gồm cả talking_photo_id) đã được sắp xếp.
    """
    list_url = "https://api.heygen.com/v2/avatars"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key
    }
    # Danh sách chỉ chứa ID
    id_list = []
    error_msg = None

    try:
        # Log headers and proxies just before the request
        log_msg_headers = {k: (v[:5] + '...' + v[-4:] if k == 'x-api-key' and len(v) > 10 else v) for k, v in headers.items()}
        print(f"[API REQUEST] URL: {list_url}")
        print(f"[API REQUEST] Headers: {log_msg_headers}")
        print(f"[API REQUEST] Proxies: {proxies}")

        response = requests.get(list_url, headers=headers, proxies=proxies, timeout=60)
        response.raise_for_status()
        data = response.json()

        if data is None:
            error_msg = "API không trả về dữ liệu (phản hồi trống)."
        elif data.get('error') is not None:
            error_info = data['error']
            if isinstance(error_info, dict):
                 error_msg = f"Lỗi API HeyGen: {error_info.get('message', 'Unknown error')}"
                 if error_info.get('code'): error_msg += f" (Code: {error_info['code']})"
            elif isinstance(error_info, str):
                 error_msg = f"Lỗi API HeyGen: {error_info}"
            else:
                 error_msg = f"Lỗi API HeyGen không xác định. Phản hồi lỗi: {error_info}"
        elif 'data' in data and isinstance(data.get('data'), dict):
            heygen_data = data['data']
            avatars = heygen_data.get('avatars', [])
            if isinstance(avatars, list):
                for avatar in avatars:
                    # Chỉ lấy avatar_id
                    if isinstance(avatar, dict):
                        id = avatar.get('avatar_id')
                        if id:
                            id_list.append(id)

            talking_photos = heygen_data.get('talking_photos', [])
            if isinstance(talking_photos, list):
                for photo in talking_photos:
                    # Chỉ lấy talking_photo_id
                    if isinstance(photo, dict):
                        id = photo.get('talking_photo_id')
                        if id:
                             id_list.append(id)

            if not id_list:
                 if not avatars and not talking_photos:
                     error_msg = "Tài khoản không có Avatar hoặc Talking Photo nào."
                 else:
                     # Có avatar/photo nhưng không lấy được ID?
                     error_msg = "Không tìm thấy ID hợp lệ trong dữ liệu avatar/photo."
        else:
            error_msg = f"Phản hồi API có cấu trúc không mong đợi."

    except requests.exceptions.HTTPError as e:
         detail = ""
         try: detail = e.response.json().get('error',{}).get('message', e.response.text)
         except: detail = e.response.text
         error_msg = f"Lỗi HTTP từ API: {e.response.status_code} - {detail[:200]}..."
    except requests.exceptions.Timeout:
        error_msg = "Yêu cầu tới API HeyGen bị timeout (quá 60 giây)."
    except requests.exceptions.RequestException as e:
        error_msg = f"Lỗi mạng hoặc kết nối khi gọi API: {e}"
    except json.JSONDecodeError as e_json:
        raw_text = ""
        try: raw_text = response.text
        except: pass
        error_msg = f"Lỗi phân tích phản hồi JSON từ API: {e_json}. Dữ liệu nhận được: {raw_text[:200]}..."
    except Exception as e:
        error_msg = f"Lỗi không xác định trong quá trình tải avatar: {e}"

    # Return results
    if error_msg:
        raise ValueError(error_msg)
    else:
        # Trả về danh sách ID đã sắp xếp
        return sorted(id_list) 

# --- Get Remaining Quota Function ---
def get_remaining_quota(api_key: str, proxies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Fetches the remaining API quota for the given API key.

    Args:
        api_key: The HeyGen API key.
        proxies: Optional dictionary of proxies for the request.

    Returns:
        The 'data' part of the JSON response containing quota information.

    Raises:
        requests.exceptions.RequestException: If the network request fails.
        ValueError: If the API response indicates an error or is not valid.
        KeyError: If the expected keys ('data', 'remaining_quota') are not in the response.
    """
    url = f"{BASE_URL}/v2/user/remaining_quota"
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }

    print(f"[API QUOTA] GET {url} for key ...{api_key[-4:]}")

    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=60)

        print(f"[API QUOTA] Response Status: {response.status_code}")
        response.raise_for_status() # Raise HTTPError for bad status codes (4xx or 5xx)

        response_data = response.json()
        # print(f"[API QUOTA] Response Body: {response_data}") # Uncomment for debugging

        # Check for API-level errors reported in the JSON body
        if response_data.get('error') is not None:
             error_info = response_data['error']
             msg = f"Lỗi API lấy quota: {error_info.get('message', 'Unknown error')}"
             if error_info.get('code'): msg += f" (Code: {error_info['code']})"
             raise ValueError(msg)
        
        # Check if 'data' exists and contains 'remaining_quota'
        data_payload = response_data.get('data')
        if data_payload and isinstance(data_payload, dict) and 'remaining_quota' in data_payload:
             print(f"[API QUOTA] Lấy quota thành công cho key ...{api_key[-4:]}: {data_payload.get('remaining_quota')}")
             return data_payload # Return the whole 'data' dictionary
        else:
             # Handle cases where response is successful but doesn't contain expected data
             raise KeyError(f"Phản hồi API quota thành công nhưng cấu trúc không hợp lệ hoặc thiếu 'remaining_quota'. Response: {response_data}")

    except requests.exceptions.RequestException as e:
        error_message = f"Lỗi mạng khi lấy quota: {e}"
        if e.response is not None:
            error_message += f"\nResponse Body: {e.response.text[:500]}"
        print(f"[API ERROR] {error_message}")
        raise
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"[API ERROR] Lỗi xử lý phản hồi quota: {e}")
        raise
    except Exception as e:
        print(f"[API ERROR] Lỗi không xác định khi lấy quota: {e}\n{traceback.format_exc()}")
        raise 

# --- List Videos Function ---
def list_videos(api_key: str, proxies: Optional[Dict[str, str]] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Retrieves a list of videos associated with the API key.
    Currently fetches only the first page based on the limit.

    Args:
        api_key: The HeyGen API key.
        proxies: Optional dictionary of proxies for the request.
        limit: The maximum number of videos to retrieve (default 100).

    Returns:
        The 'data' part of the JSON response containing the video list and pagination token.

    Raises:
        requests.exceptions.RequestException: If the network request fails.
        ValueError: If the API response indicates an error or is not valid.
        KeyError: If the expected keys ('data', 'videos') are not in the response.
    """
    url = f"{BASE_URL}/v1/video.list"
    params = {"limit": limit}
    headers = {
        "accept": "application/json",
        "X-Api-Key": api_key
    }

    print(f"[API LIST] GET {url} for key ...{api_key[-4:]} with limit {limit}")

    try:
        response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=60)

        print(f"[API LIST] Response Status: {response.status_code}")
        response.raise_for_status() # Raise HTTPError for bad status codes (4xx or 5xx)

        response_data = response.json()
        # print(f"[API LIST] Response Body: {response_data}") # Uncomment for debugging

        # Check for API-level errors (code != 100 for v1)
        if response_data.get('code') != 100:
             error_msg = f"Lỗi API lấy danh sách video: Code {response_data.get('code')}, Message: {response_data.get('message')}" 
             error_detail = response_data.get('error')
             if error_detail: error_msg += f", Error: {error_detail}"
             raise ValueError(error_msg)
        
        # Check if 'data' exists and contains 'videos' list
        data_payload = response_data.get('data')
        if data_payload and isinstance(data_payload, dict) and 'videos' in data_payload and isinstance(data_payload['videos'], list):
             print(f"[API LIST] Lấy danh sách thành công cho key ...{api_key[-4:]}. Số lượng: {len(data_payload['videos'])}")
             return data_payload # Return the whole 'data' dictionary (includes videos and token)
        else:
             raise KeyError(f"Phản hồi API list video thành công nhưng cấu trúc không hợp lệ hoặc thiếu 'videos'. Response: {response_data}")

    except requests.exceptions.RequestException as e:
        error_message = f"Lỗi mạng khi lấy danh sách video: {e}"
        if e.response is not None:
            error_message += f"\nResponse Body: {e.response.text[:500]}"
        print(f"[API ERROR] {error_message}")
        raise
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"[API ERROR] Lỗi xử lý phản hồi danh sách video: {e}")
        raise
    except Exception as e:
        print(f"[API ERROR] Lỗi không xác định khi lấy danh sách video: {e}\n{traceback.format_exc()}")
        raise 