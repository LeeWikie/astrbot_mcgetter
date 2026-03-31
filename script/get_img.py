from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import Optional, List

async def load_font(font_size):
    system_fonts = [
        '/System/Library/Fonts/PingFang.ttc', # macOS
        'C:/Windows/Fonts/msyh.ttc',           # Windows
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', # Linux
        'msyh.ttf'
    ]
    for path in system_fonts:
        try:
            return ImageFont.truetype(path, font_size)
        except:
            continue
    return ImageFont.load_default()

def wrap_text(text: str, font, max_width: int, draw: ImageDraw.Draw) -> List[str]:
    """根据像素宽度精确折行"""
    lines = []
    # 按照显式换行符先分割
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
            continue
        
        current_line = ""
        for char in paragraph:
            test_line = current_line + char
            # 获取当前行在指定字体下的像素长度
            if draw.textlength(test_line, font=font) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        lines.append(current_line)
    return lines

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
    icon_base64: Optional[str] = None
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

    # 字体预加载（用于计算高度）
    font_title = await load_font(28)
    font_main = await load_font(18)
    font_motd = await load_font(20)
    font_small = await load_font(14)

    # 1. 核心逻辑：先在虚拟画布上计算换行和高度
    padding = 30
    card_padding = 25
    img_w = 580
    max_text_width = img_w - (padding * 2) - (card_padding * 2)
    
    # 临时创建 draw 对象用于计算宽度
    temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    motd_lines = wrap_text(motd.replace('§l', '').replace('§r', ''), font_motd, max_text_width, temp_draw)
    
    line_spacing = 10
    motd_total_height = len(motd_lines) * (20 + line_spacing)
    
    # 重新计算整张图的总高度
    # 顶部边距(30) + 标题区(100) + 状态区(40) + 分割线(20) + MOTD区 + 底部边距(30)
    base_content_height = 180 
    img_h = base_content_height + motd_total_height + padding * 2

    # 2. 正式绘图
    img = Image.new("RGB", (img_w, img_h), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    # 绘制大圆角卡片
    card_box = [padding, padding, img_w - padding, img_h - padding]
    draw.rounded_rectangle(card_box, radius=18, fill=COLOR_CARD)
    draw.rounded_rectangle(card_box, radius=18, outline=COLOR_BORDER, width=1)

    # 图标绘制
    icon_size = 72
    icon_x, icon_y = padding + card_padding, padding + card_padding
    server_icon = await fetch_icon(icon_base64)
    
    if server_icon:
        server_icon = server_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (icon_size, icon_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, icon_size, icon_size), radius=12, fill=255)
        img.paste(server_icon, (icon_x, icon_y), mask)
    else:
        draw.rounded_rectangle([icon_x, icon_y, icon_x+icon_size, icon_y+icon_size], radius=12, fill=COLOR_PRIMARY)
        draw.text((icon_x + 20, icon_y + 15), "MC", font=font_title, fill=(255,255,255))

    # 标题 & 版本
    text_x = icon_x + icon_size + 18
    draw.text((text_x, icon_y + 2), server_name, font=font_title, fill=COLOR_TITLE)
    
    ver_text = f" {server_version} "
    vw = draw.textlength(ver_text, font=font_small)
    draw.rounded_rectangle([text_x, icon_y + 42, text_x + vw + 8, icon_y + 64], radius=4, fill=(240, 246, 255))
    draw.text((text_x + 4, icon_y + 45), ver_text, font=font_small, fill=COLOR_PRIMARY)

    # 状态行 (延迟 & 人数)
    status_y = icon_y + icon_size + 20
    # 延迟灯
    lat_color = COLOR_SUCCESS if latency < 100 else COLOR_WARN if latency < 250 else COLOR_DANGER
    draw.ellipse([icon_x, status_y + 6, icon_x + 10, status_y + 16], fill=lat_color)
    draw.text((icon_x + 18, status_y), f"{latency}ms", font=font_main, fill=COLOR_SUBTITLE)
    
    # 在线人数 (右对齐)
    online_str = f"{plays_online} / {plays_max}"
    ow = draw.textlength(online_str, font=font_main)
    draw.text((img_w - padding - card_padding - ow, status_y), online_str, font=font_main, fill=COLOR_TITLE)
    draw.text((img_w - padding - card_padding - ow - 50, status_y), "在线:", font=font_main, fill=COLOR_SUBTITLE)

    # 分割线 (收紧间距)
    line_y = status_y + 35
    draw.line([icon_x, line_y, img_w - padding - card_padding, line_y], fill=COLOR_BORDER, width=1)

    # MOTD 区域 (紧凑对齐)
    motd_start_y = line_y + 15
    for i, line in enumerate(motd_lines):
        draw.text((icon_x, motd_start_y + i * (20 + line_spacing)), line, font=font_motd, fill=COLOR_SUBTITLE)

    # 3. 导出
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")