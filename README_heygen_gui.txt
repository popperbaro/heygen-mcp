=== HƯỚNG DẪN SỬ DỤNG HEYGEN MCP DESKTOP ===

HeyGen MCP Desktop là ứng dụng giao diện cho HeyGen MCP Server, giúp bạn dễ dàng tạo video với avatar AI
thông qua API của HeyGen mà không cần dùng WebUI hay Claude Desktop.

=== YÊU CẦU HỆ THỐNG ===

1. Python 3.10 trở lên (với tkinter và requests)
2. HeyGen MCP Server đã cài đặt
3. API key từ HeyGen (https://www.heygen.com/)

=== CÁCH CÀI ĐẶT ===

1. Đảm bảo đã cài đặt HeyGen MCP Server (chạy file "install_heygen_improved.bat" hoặc "install_admin.bat")
2. Chạy file "start_heygen_gui.bat" để bắt đầu ứng dụng

=== HƯỚNG DẪN SỬ DỤNG ===

1. Tab Cấu hình:
   - Nhập API key từ HeyGen
   - Nhấn "Lưu API Key" để lưu vào biến môi trường
   - Nhấn "Kiểm tra số dư Credit" để xem số dư còn lại
   - Nhấn "Lấy danh sách giọng nói" để tải danh sách giọng nói
   - Nhấn "Lấy danh sách nhóm avatar" để tải danh sách nhóm avatar

2. Tab Tạo Video:
   - Chọn nhóm avatar từ danh sách
   - Chọn avatar cụ thể
   - Chọn giọng nói
   - Nhập tiêu đề (tùy chọn)
   - Nhập nội dung video
   - Nhấn "Tạo Video" để bắt đầu tạo video

3. Tab Trạng thái Video:
   - Nhập Video ID (tự động điền nếu bạn vừa tạo video)
   - Nhấn "Kiểm tra trạng thái" để xem tiến trình
   - Video sẽ tự động tải về thư mục Videos/HeyGen khi hoàn thành
   - Nhấn "Mở thư mục chứa video" để xem video đã tải

=== LƯU Ý ===

- Mỗi video tạo ra sẽ tiêu tốn credit từ tài khoản HeyGen của bạn
- Quá trình tạo video có thể mất từ vài phút đến vài giờ tùy thuộc vào độ dài
- Video sẽ tự động tải về khi hoàn thành và được lưu trong thư mục Videos/HeyGen
- Bạn có thể kiểm tra tiến độ video bằng cách nhấn "Kiểm tra trạng thái" nhiều lần

=== KHẮC PHỤC SỰ CỐ ===

Nếu gặp lỗi "ImportError: No module named 'heygen_mcp'":
- Đảm bảo đã cài đặt HeyGen MCP Server

Nếu gặp lỗi "No module named 'tkinter'":
- Cài đặt lại Python và đảm bảo chọn tùy chọn "tcl/tk and IDLE"

Nếu gặp lỗi "No module named 'requests'":
- Chạy lệnh: pip install requests

Các lỗi khác:
- Kiểm tra khu vực log ở cuối cửa sổ ứng dụng
- Đảm bảo API key hợp lệ và còn credit 