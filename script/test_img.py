"""
同步更新后的测试脚本
测试 get_img.py 中的 generate_server_info_image 函数 (MOTD版本)
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


async def test_long_motd():
    """测试 2: 超长 MOTD（测试自动折行和高度自适应）"""
    motd = (
        "这是一个非常非常长的服务器公告，用来测试代码中的自动折行逻辑是否正常工作。"
        "如果这个公告足够长，图片的高度应该会根据内容的行数自动向下延伸，"
        "而不会导致文字重叠或超出边框。"
    )
    
    result = await generate_server_info_image(
        motd=motd,
        latency=35,
        server_name="长公告压力测试服",
        plays_max=100,
        plays_online=12,
        server_version="1.21.1",
        icon_base64=None
    )
    
    image_data = base64.b64decode(result)
    output_path = Path(__file__).parent / "example_long_motd.png"
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"长公告测试图片已保存到: {output_path}")
    return str(output_path)


async def test_high_ping_red():
    """测试 3: 高延迟测试（变色灯测试）"""
    motd = "连接不佳，请检查网络状况。"
    
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


if __name__ == "__main__":
    print("开始运行同步测试...")
    
    # 执行测试
    path1 = asyncio.run(test_basic_motd())
    path2 = asyncio.run(test_long_motd())
    path3 = asyncio.run(test_high_ping_red())
    
    print(f"\n✅ 所有测试完成!")
    print(f"1. 标准测试: {path1}")
    print(f"2. 长文折行: {path2}")
    print(f"3. 状态变色: {path3}")