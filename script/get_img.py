from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import Optional, List, Tuple
from pathlib import Path
import re

# MOTD 颜色代码映射
MOTD_COLORS = {
    '0': (0, 0, 0), '1': (0, 0, 170), '2': (0, 170, 0), '3': (0, 170, 170),
    '4': (170, 0, 0), '5': (170, 0, 170), '6': (255, 170, 0), '7': (170, 170, 170),
    '8': (85, 85, 85), '9': (85, 85, 255), 'a': (85, 255, 85), 'b': (85, 255, 255),
    'c': (255, 85, 85), 'd': (255, 85, 255), 'e': (255, 255, 85), 'f': (255, 255, 255),
}

def parse_motd(motd: str) -> List[Tuple[str, Tuple[int, int, int]]]:
    """解析 MOTD 颜色"""
    if not motd:
        return [("", (100, 116, 139))]
    fragments = []
    current_text = ""
    current_color = (100, 116, 139)
    i = 0
    while i < len(motd):
        if motd[i] == '§' and i + 1 < len(motd):
            if current_text:
                fragments.append((current_text, current_color))
                current_text = ""
            code = motd[i + 1].lower()
            current_color = MOTD_COLORS.get(code, (100, 116, 139))
            i += 2
        else:
            current_text += motd[i]
            i += 1
    if current_text:
        fragments.append((current_text, current_color))
    return fragments

async def load_font(font_name: str, size: int):
    """加载字体辅助函数"""
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
    f_tiny = await load_font("PingFang Medium", 13)

    # --- 预计算阶段 ---
    padding = 25
    card_inner_padding = 20
    img_w = 600
    icon_size = 100
    
    # 解析 MOTD 折行
    max_motd_w = img_w - (padding + card_inner_padding) * 2
    plain_motd = re.sub(r'§[0-9a-fklmnor]', '', motd) if is_online else "服务器目前处于离线状态"
    display_motd = motd if is_online else "§8服务器目前处于离线状态"
    
    temp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    motd_lines = []
    for paragraph in plain_motd.split('\n'):
        line = ""
        for char in paragraph:
            if temp_draw.textlength(line + char, font=f_motd) <= max_motd_w:
                line += char
            else:
                motd_lines.append(line)
                line = char
        motd_lines.append(line)

    # 动态计算高度
    header_h = icon_size + card_inner_padding * 2 # 140
    motd_h = len(motd_lines) * 28 + 20 # 文本行高 + 底部留白
    card_h = header_h + 10 + motd_h # 10是分割线间距
    img_h = card_h + padding * 2

    # --- 开始绘图 ---
    img = Image.new("RGB", (img_w, img_h), color=C_BG)
    draw = ImageDraw.Draw(img)

    # 1. 绘制卡片底框
    card_box = [padding, padding, img_w - padding, img_h - padding]
    draw.rounded_rectangle(card_box, radius=18, fill=C_CARD)
    draw.rounded_rectangle(card_box, radius=18, outline=C_BORDER, width=1)

    # 2. 绘制图标
    ix, iy = padding + card_inner_padding, padding + card_inner_padding
    server_icon = await fetch_icon(icon_base64)
    if server_icon:
        server_icon = server_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (icon_size, icon_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, icon_size, icon_size), radius=14, fill=255)
        img.paste(server_icon, (ix, iy), mask)
    else:
        bg_color = C_PRIMARY if is_online else C_OFFLINE
        draw.rounded_rectangle([ix, iy, ix+icon_size, iy+icon_size], radius=14, fill=bg_color)
        icon_txt = "MC" if is_online else "OFF"
        draw.text((ix+28, iy+32), icon_txt, font=f_bold, fill=(255,255,255))

    # 3. 绘制右侧文字信息 (垂直堆叠)
    tx = ix + icon_size + 20
    # 行1: 标题
    draw.text((tx, iy - 2), server_name, font=f_bold, fill=C_TITLE)
    
    # 行2: 版本勋章 (上下堆叠第一行)
    v_txt = f" {server_version} "
    vw = draw.textlength(v_txt, font=f_tiny)
    draw.rounded_rectangle([tx, iy + 36, tx + vw + 6, iy + 54], radius=4, fill=(240, 246, 255))
    draw.text((tx + 3, iy + 37), v_txt, font=f_tiny, fill=C_PRIMARY)
    
    # 行3: IP 地址 (上下堆叠第二行)
    if server_ip:
        draw.text((tx, iy + 62), server_ip, font=f_tiny, fill=C_SUB)

    # 行4: 状态与人数 (对齐图标底部)
    status_y = iy + 82
    if is_online:
        # 延迟小圆点
        lat_c = C_ONLINE if latency < 100 else (245, 158, 11) if latency < 250 else (239, 68, 68)
        draw.ellipse([tx, status_y + 5, tx + 10, status_y + 15], fill=lat_c)
        draw.text((tx + 18, status_y), f"{latency}ms", font=f_main, fill=C_SUB)
        # 人数 (靠右对齐)
        online_txt = f"{plays_online} / {plays_max}"
        ow = draw.textlength(online_txt, font=f_main)
        draw.text((img_w - padding - card_inner_padding - ow, status_y), online_txt, font=f_main, fill=C_TITLE)
        draw.text((img_w - padding - card_inner_padding - ow - 45, status_y), "在线:", font=f_main, fill=C_SUB)
    else:
        draw.ellipse([tx, status_y + 5, tx + 10, status_y + 15], fill=C_OFFLINE)
        draw.text((tx + 18, status_y), "服务器已离线", font=f_main, fill=C_OFFLINE)

    # 4. 分割线
    line_y = iy + icon_size + card_inner_padding
    draw.line([ix, line_y, img_w - padding - card_inner_padding, line_y], fill=C_BORDER, width=1)

    # 5. 绘制 MOTD
    curr_y = line_y + 15
    fragments = parse_motd(display_motd)
    
    # 简单的分行渲染逻辑
    for line in motd_lines:
        temp_x = ix
        # 查找这行文字对应的颜色（此处为简化逻辑，如果需要完美颜色需更复杂解析，目前先保证不重叠）
        line_color = C_SUB if is_online else C_OFFLINE
        # 匹配颜色片段
        for f_text, f_color in fragments:
            if f_text in line:
                line_color = f_color
                break
        draw.text((temp_x, curr_y), line, font=f_motd, fill=line_color)
        curr_y += 28

    # 导出
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")