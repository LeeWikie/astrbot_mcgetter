from pathlib import Path
from typing import List, Optional
from .get_img import generate_server_info_image
from astrbot.api.star import StarTools
import importlib.util
import sys
from astrbot.api import logger

# 数据目录和配置文件路径
DATA_DIR = Path(StarTools.get_data_dir("astrbot_mcgetter"))
CONFIG_FILE = DATA_DIR / "template.txt"
TEMPLATE_DIR = DATA_DIR / "template"

# 确保模板目录存在
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

async def get_img(
    latency: int,
    server_name: str,
    plays_max: int,
    plays_online: int,
    server_version: str,
    icon_base64: Optional[str] = None,
    motd: str = "",
    players_list: Optional[List[str]] = None,
    server_ip: Optional[str] = None,
    is_online: bool = True
) -> str:
    """
    生成服务器信息图片并返回 base64 字符串。
    根据配置文件选择自定义模板或默认模板。
    """
    config = read_config()
    if config == "default":
        return await _generate_default_image(
            latency=latency,
            server_name=server_name,
            plays_max=plays_max,
            plays_online=plays_online,
            server_version=server_version,
            icon_base64=icon_base64,
            motd=motd,
            players_list=players_list,
            server_ip=server_ip,
            is_online=is_online
        )

    # 尝试加载自定义模板
    try:
        template_file = TEMPLATE_DIR / f"{config}.py"
        if not template_file.is_file():
            logger.info(f"模板文件 {template_file} 不存在，使用默认模板。")
            return await _generate_default_image(
                latency=latency,
                server_name=server_name,
                plays_max=plays_max,
                plays_online=plays_online,
                server_version=server_version,
                icon_base64=icon_base64,
                motd=motd,
                players_list=players_list,
                server_ip=server_ip,
                is_online=is_online
            )

        # 动态加载模板模块
        module_name = config
        spec = importlib.util.spec_from_file_location(module_name, template_file)
        if not spec or not spec.loader:
            logger.info(f"无法加载 {template_file} 的模块规格，使用默认模板。")
            return await _generate_default_image(
                latency=latency,
                server_name=server_name,
                plays_max=plays_max,
                plays_online=plays_online,
                server_version=server_version,
                icon_base64=icon_base64,
                motd=motd,
                players_list=players_list,
                server_ip=server_ip,
                is_online=is_online
            )

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # 检查 draw_image 函数是否存在
        if not hasattr(module, "draw_image"):
            logger.info(f"模板 {config} 缺少 'draw_image' 函数，使用默认模板。")
            return await _generate_default_image(
                latency=latency,
                server_name=server_name,
                plays_max=plays_max,
                plays_online=plays_online,
                server_version=server_version,
                icon_base64=icon_base64,
                motd=motd,
                players_list=players_list,
                server_ip=server_ip,
                is_online=is_online
            )

        # 调用自定义模板的 draw_image 函数
        result = await module.draw_image(
            latency=latency,
            server_name=server_name,
            plays_max=plays_max,
            plays_online=plays_online,
            server_version=server_version,
            icon_base64=icon_base64,
            motd=motd,
            players_list=players_list
        )

        # 验证返回结果是否为字符串
        if not isinstance(result, str):
            logger.info(f"模板 {config} 返回的 base64 字符串无效，使用默认模板。")
            return await _generate_default_image(
                latency=latency,
                server_name=server_name,
                plays_max=plays_max,
                plays_online=plays_online,
                server_version=server_version,
                icon_base64=icon_base64,
                motd=motd,
                players_list=players_list,
                server_ip=server_ip,
                is_online=is_online
            )

        return result

    except Exception as e:
        logger.info(f"加载或执行模板 {config} 出错：{e}，使用默认模板。")
        return await _generate_default_image(
            latency=latency,
            server_name=server_name,
            plays_max=plays_max,
            plays_online=plays_online,
            server_version=server_version,
            icon_base64=icon_base64,
            motd=motd,
            players_list=players_list,
            server_ip=server_ip,
            is_online=is_online
        )

async def _generate_default_image(
    latency: int,
    server_name: str,
    plays_max: int,
    plays_online: int,
    server_version: str,
    icon_base64: Optional[str] = None,
    motd: str = "",
    players_list: Optional[List[str]] = None,
    server_ip: Optional[str] = None,
    is_online: bool = True
) -> str:
    """生成默认服务器信息图片的辅助函数。"""
    return await generate_server_info_image(
        motd=motd,
        latency=latency,
        server_name=server_name,
        plays_max=plays_max,
        plays_online=plays_online,
        server_version=server_version,
        icon_base64=icon_base64,
        server_ip=server_ip,
        is_online=is_online
    )

def write_config(template_name: str) -> bool:
    """将模板名称写入配置文件。"""
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            f.write(template_name)
        logger.info(f"成功将 '{template_name}' 写入 {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.info(f"写入 {CONFIG_FILE} 出错：{e}")
        return False

def read_config() -> str:
    """从配置文件读取模板名称，若文件不存在则创建并写入默认值 'default'。"""
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.info(f"配置文件 {CONFIG_FILE} 不存在，创建并写入默认值。")
        write_config("default")
        return "default"
    except Exception as e:
        logger.info(f"读取 {CONFIG_FILE} 出错：{e}")
        return "default"
