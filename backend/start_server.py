"""
后端启动脚本

确保在 Uvicorn 启动之前设置 Windows 事件循环策略
"""
import sys
import asyncio

# Windows 系统需要设置事件循环策略以支持子进程
if sys.platform == "win32":
    # 获取当前事件循环策略
    current_policy = asyncio.get_event_loop_policy()
    print(f"✓ 当前事件循环策略: {type(current_policy).__name__}")
    
    # 设置 Windows 事件循环策略
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print(f"✓ 已设置 Windows 事件循环策略为 WindowsProactorEventLoopPolicy")
    
    # 验证设置是否成功
    new_policy = asyncio.get_event_loop_policy()
    print(f"✓ 验证后事件循环策略: {type(new_policy).__name__}")

# 导入并启动 FastAPI 应用
if __name__ == "__main__":
    import uvicorn
    
    # 禁用 reload 模式，避免事件循环策略被重置
    # 如果需要开发时的热重载，可以使用其他工具如 watchfiles
    print("\n启动 Uvicorn 服务器...")
    print("注意: reload 模式已禁用，以确保事件循环策略正确")
    print("如需热重载功能，请使用 watchfiles 或其他开发工具\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False  # 禁用 reload
    )
