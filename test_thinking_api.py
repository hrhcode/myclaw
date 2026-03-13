"""
详细测试脚本 - 检查智谱AI API的原始响应
"""

import asyncio
import json
from zhipuai import ZhipuAI

# 配置
API_KEY = "657bbe320cd74c8caafd6b2bb9c9d81b.WETpW5A48QVly2pX"
MODEL = "glm-4.1v-thinking-flash"


async def test_thinking_api():
    """测试智谱AI API的思考过程返回"""
    print("=" * 60)
    print("测试智谱AI API的思考过程返回")
    print("=" * 60)
    
    client = ZhipuAI(api_key=API_KEY)
    
    # 测试1: 非流式请求
    print("\n=== 测试1: 非流式请求 ===")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "请详细分析一下人工智能的发展历程"}],
        )
        
        print(f"响应类型: {type(response)}")
        print(f"响应对象属性: {dir(response)}")
        
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            print(f"\nChoice属性: {dir(choice)}")
            
            if hasattr(choice, 'message'):
                message = choice.message
                print(f"\nMessage属性: {dir(message)}")
                print(f"Message内容: {message.content}")
                
                # 检查所有可能的思考过程字段
                for attr in dir(message):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(message, attr)
                            if not callable(value) and value is not None:
                                print(f"  {attr}: {value}")
                        except:
                            pass
    except Exception as e:
        print(f"非流式请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2: 流式请求
    print("\n\n=== 测试2: 流式请求 ===")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "请详细分析一下人工智能的发展历程"}],
            stream=True,
        )
        
        chunk_count = 0
        for chunk in response:
            chunk_count += 1
            if chunk_count <= 5:  # 只打印前5个chunk
                print(f"\nChunk {chunk_count}:")
                print(f"  类型: {type(chunk)}")
                print(f"  属性: {dir(chunk)}")
                
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta'):
                        delta = choice.delta
                        print(f"  Delta属性: {dir(delta)}")
                        
                        # 检查所有可能的字段
                        for attr in dir(delta):
                            if not attr.startswith('_'):
                                try:
                                    value = getattr(delta, attr)
                                    if not callable(value) and value is not None:
                                        if attr == 'content':
                                            print(f"  {attr}: {value[:50]}...")
                                        else:
                                            print(f"  {attr}: {value}")
                                except:
                                    pass
            elif chunk_count == 6:
                print(f"\n... (剩余 {chunk_count - 5} 个chunk未显示)")
                break
    except Exception as e:
        print(f"流式请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试3: 检查不同模型的响应
    print("\n\n=== 测试3: 检查不同模型的响应 ===")
    models_to_test = ["glm-4-flash", "glm-4.1v-thinking-flash"]
    
    for model in models_to_test:
        print(f"\n模型: {model}")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "你好"}],
            )
            
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message'):
                    message = choice.message
                    print(f"  响应内容: {message.content[:100]}...")
                    
                    # 检查是否有思考过程相关的字段
                    thinking_fields = []
                    for attr in dir(message):
                        if 'think' in attr.lower() or 'reason' in attr.lower():
                            thinking_fields.append(attr)
                    
                    if thinking_fields:
                        print(f"  发现思考相关字段: {thinking_fields}")
                        for field in thinking_fields:
                            value = getattr(message, field)
                            print(f"    {field}: {value}")
                    else:
                        print(f"  未发现思考相关字段")
        except Exception as e:
            print(f"  测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_thinking_api())
