from PIL import Image, ImageDraw, ImageFont, ImageFilter
import asyncio
import io
from pathlib import Path
import base64
from typing import Optional

async def load_font(font_size, weight="regular"):
    """
    加载更美观的字体
    weight: 'bold' 或 'regular'
    """
    system_fonts = [
        # macOS
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        # Windows
        'C:/Windows/Fonts/msyhhl.ttc',  # 微软雅黑细体
        'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
        # Linux 苹方字体 (需手动下载安装)
        '/usr/share/fonts/opentype/PingFang.ttc',
        '/usr/share/fonts/truetype/PingFang.ttc',
        '/usr/share/fonts/PingFang.ttc',
        '~/.fonts/PingFang.ttc',
        '~/.local/share/fonts/PingFang.ttc',
        # Linux 其他中文字体
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc'
    ]
    
    for path in system_fonts:
        try:
            # 尝试加载
            return ImageFont.truetype(path, font_size)
        except OSError:
            continue
    
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
    players_list: list,
    latency: int,
    server_name: str,
    plays_max: int,
    plays_online: int,
    server_version: str,
    icon_base64: Optional[str] = None
) -> str:
    # --- 现代配色方案 ---
    COLOR_BG = (248, 250, 252)        # 极浅蓝灰 (Slate 50)
    COLOR_CARD = (255, 255, 255)      # 纯白
    COLOR_TITLE = (30, 41, 59)        # 深灰蓝 (Slate 800)
    COLOR_SUBTITLE = (100, 116, 139)  # 中灰蓝 (Slate 500)
    COLOR_PRIMARY = (59, 130, 246)    # 品牌蓝 (Blue 500)
    COLOR_SUCCESS = (34, 197, 94)     # 成功绿 (Green 500)
    COLOR_WARN = (245, 158, 11)       # 警告橙 (Amber 500)
    COLOR_DANGER = (239, 68, 68)      # 危险红 (Red 500)
    COLOR_BORDER = (226, 232, 240)    # 边框色 (Slate 200)

    # 字体加载
    font_bold = await load_font(28)
    font_main = await load_font(18)
    font_small = await load_font(14)

    # 动态高度计算
    padding = 30
    player_chip_height = 35
    players_per_row = 3
    rows = (len(players_list) + players_per_row - 1) // players_per_row
    content_height = 180 + (max(1, rows) * player_chip_height)
    
    img_w, img_h = 560, content_height + padding * 2
    img = Image.new("RGB", (img_w, img_h), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    # 1. 绘制主体卡片投影效果 (简单模拟)
    draw.rounded_rectangle([padding, padding, img_w-padding, img_h-padding], radius=16, fill=COLOR_CARD)
    # 绘制一层极淡边框
    draw.rounded_rectangle([padding, padding, img_w-padding, img_h-padding], radius=16, outline=COLOR_BORDER, width=1)

    # 2. 绘制图标
    icon_x, icon_y = padding + 25, padding + 25
    icon_size = 80
    server_icon = await fetch_icon(icon_base64)
    
    if server_icon:
        server_icon = server_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        # 圆角剪切图标
        mask = Image.new("L", (icon_size, icon_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, icon_size, icon_size), radius=12, fill=255)
        img.paste(server_icon, (icon_x, icon_y), mask)
    else:
        # 无图标时画一个带字母的占位符
        draw.rounded_rectangle([icon_x, icon_y, icon_x+icon_size, icon_y+icon_size], radius=12, fill=COLOR_PRIMARY)
        draw.text((icon_x+28, icon_y+20), server_name[0] if server_name else "?", font=font_bold, fill=(255,255,255))

    # 3. 服务器名称与版本
    text_offset_x = icon_x + icon_size + 20
    draw.text((text_offset_x, icon_y + 5), server_name, font=font_bold, fill=COLOR_TITLE)
    
    # 版本号胶囊
    ver_w = draw.textlength(f" {server_version} ", font=font_small)
    draw.rounded_rectangle([text_offset_x, icon_y + 45, text_offset_x + ver_w + 10, icon_y + 65], radius=5, fill=COLOR_BG)
    draw.text((text_offset_x + 5, icon_y + 47), server_version, font=font_small, fill=COLOR_SUBTITLE)

    # 4. 状态栏 (延迟 & 在线人数)
    status_y = icon_y + icon_size + 30
    
    # 延迟指示器
    lat_color = COLOR_SUCCESS if latency < 80 else COLOR_WARN if latency < 150 else COLOR_DANGER
    draw.ellipse([icon_x, status_y + 6, icon_x + 8, status_y + 14], fill=lat_color)
    draw.text((icon_x + 18, status_y), f"{latency}ms", font=font_main, fill=COLOR_SUBTITLE)

    # 在线人数
    online_txt = f"在线人数: {plays_online} / {plays_max}"
    tw = draw.textlength(online_txt, font=font_main)
    draw.text((img_w - padding - 25 - tw, status_y), online_txt, font=font_main, fill=COLOR_TITLE)

    # 分割线
    line_y = status_y + 35
    draw.line([icon_x, line_y, img_w - padding - 25, line_y], fill=COLOR_BORDER, width=1)

    # 5. 玩家列表 (采用网格排列)
    list_y = line_y + 20
    if players_list:
        for i, player in enumerate(players_list):
            row = i // players_per_row
            col = i % players_per_row
            px = icon_x + col * ((img_w - 2*padding - 50) // players_per_row)
            py = list_y + row * player_chip_height
            
            # 玩家小点
            draw.ellipse([px, py + 7, px + 4, py + 11], fill=COLOR_PRIMARY)
            # 玩家名字（截断处理）
            display_name = player[:10] + ".." if len(player) > 10 else player
            draw.text((px + 12, py), display_name, font=font_main, fill=COLOR_SUBTITLE)
    else:
        draw.text((icon_x, list_y), "目前没有玩家在线", font=font_main, fill=COLOR_SUBTITLE)

    # 导出
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")