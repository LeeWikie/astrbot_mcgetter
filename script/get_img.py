from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import Optional, List, Tuple
from pathlib import Path
import re

# MOTD 颜色代码映射
MOTD_COLORS = {
    '0': (0, 0, 0),           # 黑色
    '1': (0, 0, 170),         # 深蓝色
    '2': (0, 170, 0),         # 深绿色
    '3': (0, 170, 170),       # 深青色
    '4': (170, 0, 0),         # 深红色
    '5': (170, 0, 170),       # 紫色
    '6': (255, 170, 0),       # 金色
    '7': (170, 170, 170),     # 灰色
    '8': (85, 85, 85),        # 深灰色
    '9': (85, 85, 255),       # 蓝色
    'a': (85, 255, 85),       # 绿色
    'b': (85, 255, 255),      # 青色
    'c': (255, 85, 85),       # 红色
    'd': (255, 85, 255),      # 粉红色
    'e': (255, 255, 85),      # 黄色
    'f': (255, 255, 255),     # 白色
}

def parse_motd(motd: str) -> List[Tuple[str, Tuple[int, int, int], dict]]:
    """
    解析 MOTD 字符串，返回带有颜色信息的片段列表
    """
    if not motd:
        return [("", (100, 116, 139), {})]
    
    fragments = []
    current_text = ""
    current_color = (100, 116, 139)
    
    i = 0
    while i < len(motd):
        if motd[i] == '§' and i + 1 < len(motd):
            if current_text:
                fragments.append((current_text, current_color, {}))
                current_text = ""
            
            code = motd[i + 1].lower()
            if code in MOTD_COLORS:
                current_color = MOTD_COLORS[code]
            elif code == 'r':
                current_color = (100, 116, 139)
            i += 2
        else:
            current_text += motd[i]
            i += 1
    
    if current_text:
        fragments.append((current_text, current_color, {}))
    
    return fragments if fragments else [("", (100, 116, 139), {})]

async def load_font(font_size):
    """加载两种字体"""
    font_dir = Path(__file__).resolve().parent.parent / 'fonts'
    return {
        'bold': await _load_single_font(font_dir / 'PingFang Bold.ttf', font_size),
        'medium': await _load_single_font(font_dir / 'PingFang Medium.ttf', font_size)
    }

async def _load_single_font(font_path: Path, font_size: int):
    """加载单个字体文件"""
    try:
        return ImageFont.truetype(str(font_path), font_size)
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
    # --- 颜色定义 ---
    COLOR_BG = (242, 245, 248)
    COLOR_CARD = (255, 255, 255)
    COLOR_TITLE = (30, 41, 59)
    COLOR_SUBTITLE = (100, 116, 139)
    COLOR_PRIMARY = (59, 130, 246)
    COLOR_BORDER = (235, 238, 242)
    COLOR_SUCCESS = (34, 197, 94)
    COLOR_WARN = (245, 158, 11)
    COLOR_DANGER = (239, 68, 68)
    COLOR_OFFLINE = (156, 163, 175)  # 离线灰色

    # 字体预加载
    fonts = await load_font(28)
    font_bold = fonts['bold']
    font_medium = fonts['medium']
    
    font_main = await _load_single_font(Path(__file__).resolve().parent.parent / 'fonts' / 'PingFang Medium.ttf', 18)
    font_motd = await _load_single_font(Path(__file__).resolve().parent.parent / 'fonts' / 'PingFang Medium.ttf', 20)
    font_small = await _load_single_font(Path(__file__).resolve().parent.parent / 'fonts' / 'PingFang Medium.ttf', 14)
    font_tiny = await _load_single_font(Path(__file__).resolve().parent.parent / 'fonts' / 'PingFang Medium.ttf', 12)

    # 计算 MOTD 区域
    padding = 25
    img_w = 580
    max_text_width = img_w - padding * 4 - 120  # 左边距 + 右边距 + 图标宽度
    
    temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    
    # 离线状态显示
    if not is_online:
        plain_motd = "服务器离线"
        display_motd = "§c服务器离线"
    else:
        plain_motd = re.sub(r'§[0-9a-fklmnor]', '', motd) if motd else "服务器在线"
        display_motd = motd or "§a服务器在线"
    
    motd_lines = []
    paragraphs = plain_motd.split('\n')
    for paragraph in paragraphs:
        if not paragraph:
            motd_lines.append("")
            continue
        current_line = ""
        for char in paragraph:
            test_line = current_line + char
            if temp_draw.textlength(test_line, font=font_motd) <= max_text_width:
                current_line = test_line
            else:
                if current_line:
                    motd_lines.append(current_line)
                current_line = char
        if current_line:
            motd_lines.append(current_line)
    
    line_spacing = 8
    motd_total_height = len(motd_lines) * (20 + line_spacing)
    
    base_content_height = 140
    img_h = base_content_height + motd_total_height + padding * 2

    # 正式绘图
    img = Image.new("RGB", (img_w, img_h), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    # 卡片背景
    card_box = [padding, padding, img_w - padding, img_h - padding]
    draw.rounded_rectangle(card_box, radius=16, fill=COLOR_CARD)
    draw.rounded_rectangle(card_box, radius=16, outline=COLOR_BORDER, width=1)

    # 图标区域 - 增大到 100x100
    icon_size = 100
    icon_x, icon_y = padding + 15, padding + 15
    server_icon = await fetch_icon(icon_base64)
    
    if server_icon:
        server_icon = server_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (icon_size, icon_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, icon_size, icon_size), radius=12, fill=255)
        img.paste(server_icon, (icon_x, icon_y), mask)
    else:
        # 离线状态显示灰色图标
        if is_online:
            draw.rounded_rectangle([icon_x, icon_y, icon_x+icon_size, icon_y+icon_size], radius=12, fill=COLOR_PRIMARY)
            draw.text((icon_x + 25, icon_y + 30), "MC", font=font_bold, fill=(255,255,255))
        else:
            draw.rounded_rectangle([icon_x, icon_y, icon_x+icon_size, icon_y+icon_size], radius=12, fill=COLOR_OFFLINE)
            draw.text((icon_x + 20, icon_y + 30), "OFF", font=font_bold, fill=(255,255,255))

    # 右侧信息区域
    text_x = icon_x + icon_size + 20
    text_width = img_w - text_x - padding - 15
    
    # 标题
    draw.text((text_x, icon_y), server_name, font=font_bold, fill=COLOR_TITLE)
    
    # 版本 - 同一行
    ver_text = f" {server_version} "
    vw = draw.textlength(ver_text, font=font_tiny)
    draw.rounded_rectangle([text_x, icon_y + 32, text_x + vw + 6, icon_y + 48], radius=3, fill=(240, 246, 255))
    draw.text((text_x + 3, icon_y + 33), ver_text, font=font_tiny, fill=COLOR_PRIMARY)
    
    # 服务器IP - 版本后面
    if server_ip:
        ip_x = text_x + vw + 12
        draw.text((ip_x, icon_y + 33), server_ip, font=font_tiny, fill=COLOR_SUBTITLE)
    
    # 状态行 - 延迟 & 人数
    status_y = icon_y + icon_size + 10
    
    if is_online:
        lat_color = COLOR_SUCCESS if latency < 100 else COLOR_WARN if latency < 250 else COLOR_DANGER
        draw.ellipse([text_x, status_y + 6, text_x + 10, status_y + 16], fill=lat_color)
        draw.text((text_x + 16, status_y), f"{latency}ms", font=font_main, fill=COLOR_SUBTITLE)
        
        online_str = f"{plays_online} / {plays_max}"
        ow = draw.textlength(online_str, font=font_main)
        draw.text((img_w - padding - 15 - ow, status_y), online_str, font=font_main, fill=COLOR_TITLE)
        draw.text((img_w - padding - 15 - ow - 50, status_y), "在线:", font=font_main, fill=COLOR_SUBTITLE)
    else:
        # 离线状态
        draw.ellipse([text_x, status_y + 6, text_x + 10, status_y + 16], fill=COLOR_OFFLINE)
        draw.text((text_x + 16, status_y), "离线", font=font_main, fill=COLOR_OFFLINE)

    # 分割线
    line_y = status_y + 35
    draw.line([padding + 15, line_y, img_w - padding - 15, line_y], fill=COLOR_BORDER, width=1)

    # MOTD 区域
    motd_start_y = line_y + 12
    
    current_y = motd_start_y
    for line in motd_lines:
        line_color = COLOR_OFFLINE if not is_online else COLOR_SUBTITLE
        
        # 检查颜色代码
        for frag_text, frag_color, _ in parse_motd(display_motd):
            if frag_text and line.startswith(frag_text[:min(5, len(frag_text))]):
                line_color = frag_color
                break
        
        draw.text((text_x, current_y), line, font=font_motd, fill=line_color)
        current_y += 20 + line_spacing

    # 导出
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
