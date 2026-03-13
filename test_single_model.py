"""
测试单个模型 - 调试 glm-4-plus 的问题
"""

import asyncio
import httpx

BASE_URL = "http://127.0.0.1:18888"


async def test_model(model_id: str):
    """测试单个模型"""
    print(f"\n=== 测试模型: {model_id} ===")
    
    async with httpx.AsyncClient(timeout=300) as client:
        try:
            # 创建会话
            session_response = await client.post(
                f"{BASE_URL}/v1/sessions",
                json={"channel": "web"}
            )
            
            if session_response.status_code != 200:
                print(f"创建会话失败: {session_response.status_code}")
                print(f"响应: {session_response.text}")
                return False
            
            session_id = session_response.json().get("session_id")
            print(f"创建会话成功: {session_id}")
            
            # 发送消息
            chat_response = await client.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "你好"}],
                    "session_id": session_id,
                    "model": model_id,
                    "stream": False,
                    "enable_thinking": False,
                }
            )
            
            print(f"响应状态码: {chat_response.status_code}")
            
            if chat_response.status_code == 200:
                result = chat_response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"响应内容: {content[:100]}...")
                return True
            else:
                print(f"发送消息失败")
                print(f"响应内容: {chat_response.text}")
                return False
                
        except Exception as e:
            print(f"测试过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """运行测试"""
    models_to_test = ["glm-4-flash", "glm-4-plus", "glm-4v-flash", "glm-4.1v-thinking-flash"]
    
    for model_id in models_to_test:
        success = await test_model(model_id)
        if success:
            print(f"✓ {model_id} 测试通过")
        else:
            print(f"✗ {model_id} 测试失败")


if __name__ == "__main__":
    asyncio.run(main())
