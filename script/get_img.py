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

# MOTD 格式代码
MOTD_FORMATS = {
    'l': 'bold',      # 粗体
    'o': 'italic',    # 斜体
    'n': 'underline', # 下划线
    'm': 'strikethrough', # 删除线
    'k': 'obfuscated',    # 乱码
}

def parse_motd(motd: str) -> List[Tuple[str, Tuple[int, int, int], dict]]:
    """
    解析 MOTD 字符串，返回带有颜色和样式信息的片段列表
    
    Returns:
        List of (text, color, styles) tuples
    """
    if not motd:
        return [("", (100, 116, 139), {})]
    
    fragments = []
    current_text = ""
    current_color = (100, 116, 139)  # 默认灰色
    current_styles = set()
    
    i = 0
    while i < len(motd):
        if motd[i] == '§' and i + 1 < len(motd):
            # 保存当前文本
            if current_text:
                fragments.append((current_text, current_color, current_styles.copy()))
                current_text = ""
            
            code = motd[i + 1].lower()
            if code in MOTD_COLORS:
                current_color = MOTD_COLORS[code]
            elif code == 'r':
                # 重置所有样式
                current_color = (100, 116, 139)
                current_styles = set()
            elif code in MOTD_FORMATS:
                current_styles.add(MOTD_FORMATS[code])
            
            i += 2
        else:
            current_text += motd[i]
            i += 1
    
    # 保存最后一段文本
    if current_text:
        fragments.append((current_text, current_color, current_styles.copy()))
    
    return fragments if fragments else [("", (100, 116, 139), {})]

def wrap_text_with_styles(text: str, font, max_width: int, draw: ImageDraw.Draw) -> List[Tuple[str, int, int]]:
    """
    根据像素宽度精确折行，返回 (文本, 起始x, 起始y) 列表
    """
    lines = []
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        if not paragraph:
            lines.append(("", 0, 0))
            continue
        
        current_line = ""
        for char in paragraph:
            test_line = current_line + char
            if draw.textlength(test_line, font=font) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append((current_line, 0, 0))
                current_line = char
        
        if current_line:
            lines.append((current_line, 0, 0))
    
    return lines

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

    # 字体预加载 - Bold用于标题，Medium用于其它
    fonts = await load_font(28)
    font_bold = fonts['bold']
    font_medium = fonts['medium']
    
    font_main = await _load_single_font(Path(__file__).resolve().parent.parent / 'fonts' / 'PingFang Medium.ttf', 18)
    font_motd = await _load_single_font(Path(__file__).resolve().parent.parent / 'fonts' / 'PingFang Medium.ttf', 20)
    font_small = await _load_single_font(Path(__file__).resolve().parent.parent / 'fonts' / 'PingFang Medium.ttf', 14)

    # 解析 MOTD
    motd_fragments = parse_motd(motd)

    # 计算 MOTD 区域需要的行数和高度
    padding = 30
    card_padding = 25
    img_w = 580
    max_text_width = img_w - (padding * 2) - (card_padding * 2)
    
    # 临时 draw 对象用于计算宽度
    temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    
    # 合并所有文本用于计算行数（去掉格式符）
    plain_motd = re.sub(r'§[0-9a-fklmnor]', '', motd)
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
    
    line_spacing = 10
    motd_total_height = len(motd_lines) * (20 + line_spacing)
    
    base_content_height = 180 
    img_h = base_content_height + motd_total_height + padding * 2

    # 正式绘图
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
        draw.text((icon_x + 20, icon_y + 15), "MC", font=font_bold, fill=(255,255,255))

    # 标题 & 版本
    text_x = icon_x + icon_size + 18
    draw.text((text_x, icon_y + 2), server_name, font=font_bold, fill=COLOR_TITLE)
    
    ver_text = f" {server_version} "
    vw = draw.textlength(ver_text, font=font_small)
    draw.rounded_rectangle([text_x, icon_y + 42, text_x + vw + 8, icon_y + 64], radius=4, fill=(240, 246, 255))
    draw.text((text_x + 4, icon_y + 45), ver_text, font=font_small, fill=COLOR_PRIMARY)

    # 状态行 (延迟 & 人数)
    status_y = icon_y + icon_size + 20
    lat_color = COLOR_SUCCESS if latency < 100 else COLOR_WARN if latency < 250 else COLOR_DANGER
    draw.ellipse([icon_x, status_y + 6, icon_x + 10, status_y + 16], fill=lat_color)
    draw.text((icon_x + 18, status_y), f"{latency}ms", font=font_main, fill=COLOR_SUBTITLE)
    
    online_str = f"{plays_online} / {plays_max}"
    ow = draw.textlength(online_str, font=font_main)
    draw.text((img_w - padding - card_padding - ow, status_y), online_str, font=font_main, fill=COLOR_TITLE)
    draw.text((img_w - padding - card_padding - ow - 50, status_y), "在线:", font=font_main, fill=COLOR_SUBTITLE)

    # 分割线
    line_y = status_y + 35
    draw.line([icon_x, line_y, img_w - padding - card_padding, line_y], fill=COLOR_BORDER, width=1)

    # MOTD 区域 - 带颜色支持
    motd_start_y = line_y + 15
    
    # 绘制带颜色的 MOTD
    current_y = motd_start_y
    for line in motd_lines:
        current_x = icon_x
        line_content = line
        
        # 查找这一行对应的带颜色的片段
        # 简化处理：整行使用默认颜色或根据行首的颜色代码
        line_color = COLOR_SUBTITLE
        line_text = line_content
        
        # 检查行首是否有颜色代码
        for fragment_text, fragment_color, fragment_styles in motd_fragments:
            if line_content.startswith(fragment_text[:min(5, len(fragment_text))]) if fragment_text else False:
                line_color = fragment_color
                break
        
        draw.text((current_x, current_y), line_text, font=font_motd, fill=line_color)
        current_y += 20 + line_spacing

    # 3. 导出
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
