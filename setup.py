"""
快速设置脚本
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """创建.env文件"""
    env_path = Path('.env')

    if env_path.exists():
        response = input(".env文件已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("跳过创建.env文件")
            return

    print("\n开始配置环境变量...")
    print("=" * 50)

    # 收集用户输入
    minimax_key = input("请输入MiniMax API Key: ").strip()
    minimax_group = input("请输入MiniMax Group ID (可选，直接回车跳过): ").strip()

    github_token = input("请输入GitHub Token: ").strip()

    print("\nTelegram配置:")
    print("1. 打开Telegram搜索 @BotFather")
    print("2. 发送 /newbot 创建Bot")
    print("3. 搜索 @userinfobot 获取你的Chat ID\n")

    telegram_token = input("请输入Telegram Bot Token: ").strip()
    telegram_chat_id = input("请输入Telegram Chat ID: ").strip()

    # 写入.env文件
    env_content = f"""# ===================================
# API密钥配置
# ===================================

# MiniMax API配置
MINIMAX_API_KEY={minimax_key}
MINIMAX_GROUP_ID={minimax_group}

# GitHub配置
GITHUB_TOKEN={github_token}

# Telegram配置
TELEGRAM_BOT_TOKEN={telegram_token}
TELEGRAM_CHAT_ID={telegram_chat_id}

# 可选：邮件配置
# EMAIL_SENDER=your_email@gmail.com
# EMAIL_PASSWORD=your_app_password
# EMAIL_RECEIVER=receiver@email.com
"""

    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)

    print("\n✓ .env文件创建成功！")


def install_dependencies():
    """安装依赖"""
    print("\n安装Python依赖...")
    print("=" * 50)

    import subprocess

    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            check=True
        )
        print("\n✓ 依赖安装成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 依赖安装失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("新闻聚合系统 - 快速设置")
    print("=" * 50)

    # 检查是否在正确的目录
    if not Path('config/config.yaml').exists():
        print("错误：请在项目根目录运行此脚本")
        return 1

    # 创建.env文件
    create_env_file()

    # 询问是否安装依赖
    response = input("\n是否现在安装Python依赖？(Y/n): ")
    if response.lower() != 'n':
        install_dependencies()

    print("\n" + "=" * 50)
    print("设置完成！")
    print("=" * 50)
    print("\n下一步：")
    print("1. 运行测试：python test_config.py")
    print("2. 启动系统：python main.py")
    print("\n详细文档：README.md")
    print("快速指南：QUICKSTART.md")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
