from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import Optional, List, Tuple, Dict
from pathlib import Path
import re

# Minecraft 1.8.9 标准颜色代码 (包含暗色和亮色变体)
MC_COLORS = {
    '0': (0, 0, 0),         # Black
    '1': (0, 0, 170),       # Dark Blue
    '2': (0, 170, 0),       # Dark Green
    '3': (0, 170, 170),     # Dark Aqua
    '4': (170, 0, 0),       # Dark Red
    '5': (170, 0, 170),     # Dark Purple
    '6': (255, 170, 0),     # Gold
    '7': (170, 170, 170),   # Gray
    '8': (85, 85, 85),      # Dark Gray
    '9': (85, 85, 255),     # Blue
    'a': (85, 255, 85),     # Green
    'b': (85, 255, 255),    # Aqua
    'c': (255, 85, 85),     # Red
    'd': (255, 85, 255),    # Light Purple
    'e': (255, 255, 85),    # Yellow
    'f': (255, 255, 255),   # White
}

class TextSegment:
    def __init__(self, text: str, color: Tuple[int, int, int], is_bold: bool = False):
        self.text = text
        self.color = color
        self.is_bold = is_bold

def parse_minecraft_string(text: str, default_color=(170, 170, 170)) -> List[TextSegment]:
    """解析带有 § 代码的字符串为片段列表"""
    segments = []
    current_text = ""
    current_color = default_color
    is_bold = False
    
    i = 0
    while i < len(text):
        if text[i] == '§' and i + 1 < len(text):
            if current_text:
                segments.append(TextSegment(current_text, current_color, is_bold))
                current_text = ""
            
            code = text[i+1].lower()
            if code in MC_COLORS:
                current_color = MC_COLORS[code]
                is_bold = False # 切换颜色会重置加粗状态 (MC特性)
            elif code == 'l':
                is_bold = True
            elif code == 'r':
                current_color = default_color
                is_bold = False
            i += 2
        else:
            current_text += text[i]
            i += 1
    
    if current_text:
        segments.append(TextSegment(current_text, current_color, is_bold))
    return segments

async def load_font(font_name: str, size: int):
    font_dir = Path(__file__).resolve().parent.parent / 'fonts'
    font_path = font_dir / f"{font_name}.ttf"
    try:
        return ImageFont.truetype(str(font_path), size)
    except:
        return ImageFont.load_default()

async def fetch_icon(icon_base64: Optional[str] = None) -> Optional[Image.Image]:
    if not icon_base64: return None
    try:
        if "," in icon_base64:
            icon_base64 = icon_base64.split(",", 1)[1]
        icon_data = base64.b64decode(icon_base64)
        return Image.open(io.BytesIO(icon_data)).convert("RGBA")
    except:
        return None

async def generate_server_info_image(
    motd: str,
    latency: int,
    server_name: str,
    plays_max: int,
    plays_online: int,
    server_version: str,
    icon_base64: Optional[str] = None,
    server_ip: Optional[str] = None,
    is_online: bool = True
) -> str:
    # --- 颜色与样式配置 ---
    C_BG = (242, 245, 248)
    C_CARD = (255, 255, 255)
    C_TITLE = (30, 41, 59)
    C_SUB = (100, 116, 139)
    C_PRIMARY = (59, 130, 246)
    C_BORDER = (235, 238, 242)
    C_ONLINE = (34, 197, 94)
    C_OFFLINE = (156, 163, 175)

    # 字体加载
    f_bold = await load_font("PingFang Bold", 26)
    f_main = await load_font("PingFang Medium", 18)
    f_motd = await load_font("PingFang Medium", 20)
    f_motd_bold = await load_font("PingFang Bold", 20)
    f_ip_bold = await load_font("PingFang Bold", 14) # IP专用加粗
    f_tiny = await load_font("PingFang Medium", 13)

    # --- 预计算阶段 ---
    padding, card_inner = 25, 20
    img_w = 600
    icon_size = 100
    max_motd_w = img_w - (padding + card_inner) * 2
    
    # 离线处理
    display_motd = motd if is_online else "§8服务器目前处于离线状态"
    
    # 解析并模拟换行
    temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    all_segments = parse_minecraft_string(display_motd, default_color=C_SUB)
    
    lines_segments: List[List[TextSegment]] = []
    current_line_segments = []
    current_w = 0
    
    for seg in all_segments:
        # 对每一个片段处理可能的长文本换行
        words = seg.text # 这里不按空格分，MC按字符宽度
        active_font = f_motd_bold if seg.is_bold else f_motd
        
        current_segment_text = ""
        for char in words:
            char_w = temp_draw.textlength(char, font=active_font)
            if current_w + char_w > max_motd_w:
                # 换行
                if current_segment_text:
                    current_line_segments.append(TextSegment(current_segment_text, seg.color, seg.is_bold))
                lines_segments.append(current_line_segments)
                # 重置
                current_line_segments = []
                current_segment_text = char
                current_w = char_w
            else:
                current_segment_text += char
                current_w += char_w
        
        if current_segment_text:
            current_line_segments.append(TextSegment(current_segment_text, seg.color, seg.is_bold))
            
    if current_line_segments:
        lines_segments.append(current_line_segments)

    # 动态计算高度
    header_h = icon_size + card_inner * 2
    motd_h = len(lines_segments) * 28 + 15
    card_h = header_h + 10 + motd_h
    img_h = card_h + padding * 2

    # --- 开始绘图 ---
    img = Image.new("RGB", (img_w, img_h), color=C_BG)
    draw = ImageDraw.Draw(img)

    # 1. 绘制卡片
    card_box = [padding, padding, img_w - padding, img_h - padding]
    draw.rounded_rectangle(card_box, radius=18, fill=C_CARD)
    draw.rounded_rectangle(card_box, radius=18, outline=C_BORDER, width=1)

    # 2. 绘制图标
    ix, iy = padding + card_inner, padding + card_inner
    server_icon = await fetch_icon(icon_base64)
    if server_icon:
        server_icon = server_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (icon_size, icon_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, icon_size, icon_size), radius=14, fill=255)
        img.paste(server_icon, (ix, iy), mask)
    else:
        bg_c = C_PRIMARY if is_online else C_OFFLINE
        draw.rounded_rectangle([ix, iy, ix+icon_size, iy+icon_size], radius=14, fill=bg_c)
        draw.text((ix+28, iy+32), "MC" if is_online else "OFF", font=f_bold, fill=(255,255,255))

    # 3. 绘制右侧文字
    tx = ix + icon_size + 20
    draw.text((tx, iy - 2), server_name, font=f_bold, fill=C_TITLE)
    
    # 绘制版本勋章
    v_txt = f" {server_version} "
    vw = draw.textlength(v_txt, font=f_tiny)
    draw.rounded_rectangle([tx, iy + 36, tx + vw + 6, iy + 54], radius=4, fill=(240, 246, 255))
    draw.text((tx + 3, iy + 37), v_txt, font=f_tiny, fill=C_PRIMARY)
    
    # 绘制 IP (加粗)
    if server_ip:
        draw.text((tx, iy + 62), server_ip, font=f_ip_bold, fill=C_SUB)

    # 状态行
    status_y = iy + 82
    if is_online:
        lat_c = C_ONLINE if latency < 100 else (245, 158, 11) if latency < 250 else (239, 68, 68)
        draw.ellipse([tx, status_y + 5, tx + 10, status_y + 15], fill=lat_c)
        draw.text((tx + 18, status_y), f"{latency}ms", font=f_main, fill=C_SUB)
        # 人数
        online_txt = f"{plays_online} / {plays_max}"
        ow = draw.textlength(online_txt, font=f_main)
        draw.text((img_w - padding - card_inner - ow, status_y), online_txt, font=f_main, fill=C_TITLE)
        draw.text((img_w - padding - card_inner - ow - 45, status_y), "在线:", font=f_main, fill=C_SUB)
    else:
        draw.ellipse([tx, status_y + 5, tx + 10, status_y + 15], fill=C_OFFLINE)
        draw.text((tx + 18, status_y), "服务器已离线", font=f_main, fill=C_OFFLINE)

    # 4. 分割线
    line_y = iy + icon_size + card_inner
    draw.line([ix, line_y, img_w - padding - card_inner, line_y], fill=C_BORDER, width=1)

    # 5. 绘制 MOTD (多颜色片段渲染)
    curr_y = line_y + 15
    for line_segs in lines_segments:
        curr_x = ix
        for seg in line_segs:
            active_f = f_motd_bold if seg.is_bold else f_motd
            draw.text((curr_x, curr_y), seg.text, font=active_f, fill=seg.color)
            curr_x += draw.textlength(seg.text, font=active_f)
        curr_y += 28

    # 导出
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")