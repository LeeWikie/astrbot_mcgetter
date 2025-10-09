from pathlib import Path
from typing import List, Optional, Dict, Any
from .get_img import generate_server_info_image
from astrbot.api.star import StarTools
import importlib.util
import sys

# 获取数据目录
data_path = Path(StarTools.get_data_dir("astrbot_mcgetter"))
# 配置文件路径
filename = data_path / "template.txt"
# 自定义模板路径
code_path = data_path / "template"

# 确保 template 目录存在
code_path.mkdir(parents=True, exist_ok=True)

async def get_img(
    players_list: list,
    latency: int,
    server_name: str,
    plays_max: int,
    plays_online: int,
    server_version: str,
    icon_base64: Optional[str] = None
) -> str:
    """
    生成服务器信息的图片并返回 base64 字符串。
    根据配置文件选择默认模板或自定义模板。
    """
    config = read_config()
    
    if config and config != 'default':
        # 尝试使用自定义模板
        try:
            template_file = code_path / f"{config}.py"
            if not template_file.is_file():
                print(f"Template file {template_file} does not exist, falling back to default.")
                return await generate_server_info_image(
                    players_list=players_list,
                    latency=latency,
                    server_name=server_name,
                    plays_max=plays_max,
                    plays_online=plays_online,
                    server_version=server_version,
                    icon_base64=icon_base64
                )
            
            # 动态加载模板模块
            module_name = config
            spec = importlib.util.spec_from_file_location(module_name, template_file)
            if spec is None or spec.loader is None:
                print(f"Failed to load module spec for {template_file}, falling back to default.")
                return await generate_server_info_image(
                    players_list=players_list,
                    latency=latency,
                    server_name=server_name,
                    plays_max=plays_max,
                    plays_online=plays_online,
                    server_version=server_version,
                    icon_base64=icon_base64
                )
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 检查 draw_image 函数是否存在
            if not hasattr(module, 'draw_image'):
                print(f"Template {config} does not have a 'draw_image' function, falling back to default.")
                return await generate_server_info_image(
                    players_list=players_list,
                    latency=latency,
                    server_name=server_name,
                    plays_max=plays_max,
                    plays_online=plays_online,
                    server_version=server_version,
                    icon_base64=icon_base64
                )
            
            # 调用自定义模板的 draw_image 函数
            result = await module.draw_image(
                players_list=players_list,
                latency=latency,
                server_name=server_name,
                plays_max=plays_max,
                plays_online=plays_online,
                server_version=server_version,
                icon_base64=icon_base64
            )
            
            # 验证返回结果是否为字符串
            if not isinstance(result, str):
                print(f"Template {config} did not return a valid base64 string, falling back to default.")
                return await generate_server_info_image(
                    players_list=players_list,
                    latency=latency,
                    server_name=server_name,
                    plays_max=plays_max,
                    plays_online=plays_online,
                    server_version=server_version,
                    icon_base64=icon_base64
                )
            
            return result
            
        except Exception as e:
            print(f"Error loading or executing template {config}: {e}, falling back to default.")
            return await generate_server_info_image(
                players_list=players_list,
                latency=latency,
                server_name=server_name,
                plays_max=plays_max,
                plays_online=plays_online,
                server_version=server_version,
                icon_base64=icon_base64
            )
    
    # 默认实现
    return await generate_server_info_image(
        players_list=players_list,
        latency=latency,
        server_name=server_name,
        plays_max=plays_max,
        plays_online=plays_online,
        server_version=server_version,
        icon_base64=icon_base64
    )

def write_config(string: str):
    """将字符串写入到配置文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(string)
        print(f"Successfully wrote '{string}' to {filename}")
    except Exception as e:
        print(f"Error writing to file {filename}: {e}")

def read_config() -> str:
    """从配置文件读取字符串，若文件不存在则创建并写入默认值 'default'"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"File {filename} not found, creating it with default string.")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('default')
        return 'default'
    except Exception as e:
        print(f"Error reading from file {filename}: {e}")
        return 'default'

# 示例用法
if __name__ == "__main__":
    async def main():
        # 示例参数
        players_list = ["player1", "player2"]
        latency = 50
        server_name = "My Minecraft Server"
        plays_max = 20
        plays_online = 5
        server_version = "1.20.1"
        icon_base64 = None

        # 写入配置文件（示例：使用名为 'custom' 的模板）
        write_config("custom")

        # 获取图片 base64 字符串
        result = await get_img(
            players_list=players_list,
            latency=latency,
            server_name=server_name,
            plays_max=plays_max,
            plays_online=plays_online,
            server_version=server_version,
            icon_base64=icon_base64
        )
        print(f"Generated image base64: {result[:50]}...")  # 仅打印前50个字符

    import asyncio
    asyncio.run(main())