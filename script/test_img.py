"""
同步更新后的测试脚本
测试 get_img.py 中的 generate_server_info_image 函数 (MOTD颜色版本)
"""
import asyncio
import base64
from pathlib import Path
# 确保你的文件名是 get_img.py，或者根据实际情况修改
from get_img import generate_server_info_image

async def test_basic_motd():
    """测试 1: 基本测试（标准双行 MOTD）"""
    motd = "欢迎来到我的测试服务器！\n这是一个充满挑战的生存世界。"
    
    result = await generate_server_info_image(
        motd=motd,
        latency=45,
        server_name="我的世界服务器",
        plays_max=20,
        plays_online=5,
        server_version="1.20.4",
        icon_base64=None
    )

    image_data = base64.b64decode(result)
    output_path = Path(__file__).parent / "example_basic.png"
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"基本测试图片已保存到: {output_path}")
    return str(output_path)


async def test_colored_motd():
    """测试 2: 带颜色的 MOTD"""
    motd = "§a欢迎来到 §b我的 §c测试服务器！\n§e这是一个 §6充满挑战 §d的生存世界。"
    
    result = await generate_server_info_image(
        motd=motd,
        latency=35,
        server_name="彩色MOTD测试服",
        plays_max=100,
        plays_online=12,
        server_version="1.21.1",
        icon_base64=None
    )
    
    image_data = base64.b64decode(result)
    output_path = Path(__file__).parent / "example_colored.png"
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"彩色MOTD测试图片已保存到: {output_path}")
    return str(output_path)


async def test_high_ping_red():
    """测试 3: 高延迟测试（变色灯测试）"""
    motd = "§c连接不佳，请检查网络状况。"
    
    result = await generate_server_info_image(
        motd=motd,
        latency=250, # 高延迟
        server_name="国外高延迟服",
        plays_max=50,
        plays_online=3,
        server_version="1.20.2",
        icon_base64=None
    )
    
    image_data = base64.b64decode(result)
    output_path = Path(__file__).parent / "example_high_ping.png"
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"高延迟测试图片已保存到: {output_path}")
    return str(output_path)


async def test_bold_motd():
    """测试 4: 带格式的 MOTD（粗体等）"""
    motd = "§l§a这是粗体绿色文字\n§o§b这是斜体蓝色文字"
    
    result = await generate_server_info_image(
        motd=motd,
        latency=50,
        server_name="格式测试服",
        plays_max=20,
        plays_online=8,
        server_version="1.20.4",
        icon_base64=None
    )
    
    image_data = base64.b64decode(result)
    output_path = Path(__file__).parent / "example_bold.png"
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"格式测试图片已保存到: {output_path}")
    return str(output_path)


async def test_explicit_newline_bug():
    """测试 5: 回归测试：显式换行与颜色标记不再抛错"""
    motd = "§a第一行文本\n§b第二行文本-这是一个非常长的段落，用于测试自动换行是否正确工作且不会触发 textlength 异常。"
    
    result = await generate_server_info_image(
        motd=motd,
        latency=90,
        server_name="回归测试服",
        plays_max=30,
        plays_online=7,
        server_version="1.22.0",
        icon_base64=None
    )
    
    image_data = base64.b64decode(result)
    output_path = Path(__file__).parent / "example_explicit_newline.png"
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"显式换行回归测试图片已保存到: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    print("开始运行同步测试...")
    
    # 执行测试
    path1 = asyncio.run(test_basic_motd())
    path2 = asyncio.run(test_colored_motd())
    path3 = asyncio.run(test_high_ping_red())
    path4 = asyncio.run(test_bold_motd())
    path5 = asyncio.run(test_explicit_newline_bug())
    
    print(f"\n✅ 所有测试完成!")
    print(f"1. 基本测试: {path1}")
    print(f"2. 彩色MOTD: {path2}")
    print(f"3. 高延迟测试: {path3}")
    print(f"4. 格式测试: {path4}")
    print(f"5. 显式换行回归测试: {path5}")
