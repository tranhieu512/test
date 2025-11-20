import requests
import re
import os
from datetime import datetime

# ----------------- Cấu hình nguồn và đích -----------------
# Định nghĩa các nguồn cần tải, kèm theo Regex lọc (nếu cần) và Tên Nhóm Chuẩn hóa
SOURCES = [
    # (URL, Regex lọc (giữ lại dòng khớp + 1 dòng kế tiếp), Tên nhóm chuẩn hóa mới)
    ("https://raw.githubusercontent.com/kupjta/iptv/main/kupjtv.m3u", 
     r'"VTV"', 
     "Nhóm Kênh VTV"),
     
    ("https://raw.githubusercontent.com/kupjta/iptv/main/kupjtv.m3u", 
     r'"HTV"|"HTVC"', 
     "Nhóm Kênh HTV/HTVC"),
     
    ("https://raw.githubusercontent.com/vuminhthanh12/vuminhthanh12/refs/heads/main/vmttv", 
     r'"VTVcab"', 
     "hóm Kênh VTVcab"),

    ("https://raw.githubusercontent.com/vuminhthanh12/vuminhthanh12/refs/heads/main/vmttv", 
     r'"SCTV"', 
     "Nhóm Kênh SCTV"),

    ("https://raw.githubusercontent.com/kupjta/iptv/main/kupjtv.m3u", 
     r'"Địa phương"', 
     "Nhóm Kênh Địa phương"),
    
    ("https://raw.githubusercontent.com/vuminhthanh12/vuminhthanh12/refs/heads/main/vmttv", 
     r'"📦| In The Box"', 
     "In The Box"),
    
    ("https://raw.githubusercontent.com/vuminhthanh12/vuminhthanh12/refs/heads/main/vmttv", 
     r',*HBO.*$|,*AXN.*$', 
     "Nhóm Kênh Quốc Tế"),
    

]

FINAL_OUTPUT_FILE = "MIN.m3u"
ALL_M3U_LINES = ["#EXTM3U\n"] # Dòng header đầu tiên

def fetch_and_process_m3u(url, filter_regex, new_group_title):
    """Tải file M3U, lọc kênh, và chuẩn hóa Group Title."""
    print(f"--- Đang xử lý nguồn: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi tải {url}: {e}")
        return []

    lines = response.text.splitlines()
    processed_lines = []
    
    # Duyệt qua từng dòng để tìm #EXTINF
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 1. Bỏ qua các dòng không phải #EXTINF
        if not line.startswith('#EXTINF'):
            i += 1
            continue
            
        # 2. Lọc kênh: Kiểm tra xem dòng EXTINF có khớp với Regex lọc không
        if re.search(filter_regex, line):
        # 3. Chuẩn hóa Group Title
            line = re.sub(r'group-title="[^"]*"', f'group-title="{new_group_title}"', line)
            
            processed_lines.append(line + '\n') # Thêm dòng EXTINF đã xử lý
            
        # 4. Logic new: Tìm kiếm tất cả các dòng va URL thực 
            j = i + 1
            url_found = False
            while j < len(lines):
                next_line = lines[j].strip()

                if not next_line:
                    # Bỏ qua dòng trống
                    j+=1
                    continue
                
                # a) Nếu gặp EXTINF mới, dừng tìm URL 
                if next_line.startswith('#EXTINF'):
                    break
                    
                # b) Nếu tìm thấy URL hợp lệ (không trống và không bắt đầu bằng '#')
                if next_line and not next_line.startswith('#'):
                    processed_lines.append(next_line + '\n') # Thêm URL
                    url_found=True
                    i = j # Bắt đầu tìm kiếm EXTINF tiếp theo từ dòng này 
                    break # Thoát khỏi vòng lặp tìm URL
                
                # c) Nếu là dòng trống hoặc thẻ mở rộng (như #EXTGRP)
                if next_line.startswith('#'):
                    # Thêm dòng thẻ mở rộng vào trước URL
                    processed_lines.append(next_line + '\n')
                j += 1
            
            # Nếu tìm thấy URL, i đã được cập nhật, ta tiếp tục vòng lặp chính 
            # Nếu không tìm thấy URL (vi du: gap EXTINF tiep theo), ta phải cập nhật i
            if not url_found:
                 i = j
        else:
            # Nếu không khớp với bộ lọc, chuyển sang dòng tiếp theo
            i += 1


    return processed_lines
# ----------------- Thực thi chính -----------------
if __name__ == "__main__":
    for url, regex, group in SOURCES:
        channel_list = fetch_and_process_m3u(url, regex, group)
        ALL_M3U_LINES.extend(channel_list)
        
    # Xóa các dòng trắng thừa
    final_content = [line for line in ALL_M3U_LINES if line.strip()]
    
    try:
        with open(FINAL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.writelines(final_content)
        print(f"\n✅ Tổng hợp thành công {len(final_content)} dòng vào {FINAL_OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Lỗi khi ghi file: {e}")
