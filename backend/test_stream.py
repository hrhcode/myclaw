"""
测试流式输出思考过程
"""
import asyncio
import sys
from app.agent import get_agent

async def test_thinking_stream():
    """测试思考过程的流式输出"""
    agent = get_agent()
    
    print("=== 开始测试流式输出 ===")
    print()
    
    chunk_count = 0
    thoughts_chunks = 0
    content_chunks = 0
    
    async for chunk in agent.process_message_stream(
        session_id="test-stream",
        user_message="你好",
        enable_thinking=True,
        model="glm-4.1v-thinking-flash"
    ):
        chunk_count += 1
        
        if isinstance(chunk, dict):
            if "thoughts" in chunk:
                thoughts_chunks += 1
                # 立即打印，不换行
                sys.stdout.write(f"[思考{thoughts_chunks}] {chunk['thoughts']}")
                sys.stdout.flush()
        else:
            content_chunks += 1
            sys.stdout.write(f"[内容{content_chunks}] {chunk}")
            sys.stdout.flush()
    
    print()
    print()
    print(f"=== 测试完成 ===")
    print(f"总 chunk 数: {chunk_count}")
    print(f"思考 chunk 数: {thoughts_chunks}")
    print(f"内容 chunk 数: {content_chunks}")

if __name__ == "__main__":
    asyncio.run(test_thinking_stream())
