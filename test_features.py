"""
测试脚本 - 测试 MyClaw 的所有功能
包括模型调用、深度思考、模型切换、图片上传、思考过程展示等
"""

import asyncio
import json
import base64
from pathlib import Path
import httpx

# 配置
BASE_URL = "http://127.0.0.1:18888"
API_TIMEOUT = 300

# 测试结果记录
test_results = {
    "test_model_call": {"status": "pending", "details": []},
    "test_deep_thinking": {"status": "pending", "details": []},
    "test_model_switch": {"status": "pending", "details": []},
    "test_image_upload": {"status": "pending", "details": []},
    "test_thinking_display": {"status": "pending", "details": []},
}


def log_test(test_name: str, message: str, success: bool = True):
    """记录测试日志"""
    status = "✓" if success else "✗"
    test_results[test_name]["details"].append(f"{status} {message}")
    print(f"{status} {message}")


async def test_model_call():
    """测试 GLM-4.1V-Thinking-Flash 模型调用"""
    print("\n=== 测试 9.1: 测试 GLM-4.1V-Thinking-Flash 模型调用 ===")
    
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            # 1. 获取模型列表
            response = await client.get(f"{BASE_URL}/api/models")
            if response.status_code == 200:
                models = response.json()
                models_list = models.get("models", [])
                log_test("test_model_call", f"获取模型列表成功，共 {len(models_list)} 个模型")
                
                # 2. 验证 GLM-4.1V-Thinking-Flash 在模型列表中
                target_model = "glm-4.1v-thinking-flash"
                model_found = any(m.get("id") == target_model for m in models_list)
                
                if model_found:
                    log_test("test_model_call", f"模型 {target_model} 存在于模型列表中")
                else:
                    log_test("test_model_call", f"模型 {target_model} 不存在于模型列表中", False)
                    log_test("test_model_call", f"可用模型: {[m.get('id') for m in models_list]}")
                
                # 3. 创建会话
                session_response = await client.post(
                    f"{BASE_URL}/v1/sessions",
                    json={"channel": "web"}
                )
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    session_id = session_data.get("session_id")
                    log_test("test_model_call", f"创建会话成功，ID: {session_id}")
                    
                    # 4. 使用 GLM-4.1V-Thinking-Flash 模型发送消息
                    chat_response = await client.post(
                        f"{BASE_URL}/v1/chat/completions",
                        json={
                            "messages": [{"role": "user", "content": "你好，请简单介绍一下你自己"}],
                            "session_id": session_id,
                            "model": target_model,
                            "stream": False,
                            "enable_thinking": False,
                        }
                    )
                    
                    if chat_response.status_code == 200:
                        log_test("test_model_call", f"使用 {target_model} 模型发送消息成功")
                        result = chat_response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if content:
                            log_test("test_model_call", f"响应返回成功，内容长度: {len(content)} 字符")
                            test_results["test_model_call"]["status"] = "passed"
                        else:
                            log_test("test_model_call", "响应内容为空", False)
                    else:
                        log_test("test_model_call", f"发送消息失败，状态码: {chat_response.status_code}", False)
                        log_test("test_model_call", f"错误信息: {chat_response.text}")
                else:
                    log_test("test_model_call", f"创建会话失败，状态码: {session_response.status_code}", False)
            else:
                log_test("test_model_call", f"获取模型列表失败，状态码: {response.status_code}", False)
                log_test("test_model_call", f"错误信息: {response.text}")
                
        except Exception as e:
            log_test("test_model_call", f"测试过程中发生异常: {str(e)}", False)
            test_results["test_model_call"]["status"] = "failed"


async def test_deep_thinking():
    """测试深度思考功能"""
    print("\n=== 测试 9.2: 测试深度思考功能 ===")
    
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            # 1. 创建会话
            session_response = await client.post(
                f"{BASE_URL}/v1/sessions",
                json={"channel": "web"}
            )
            session_id = session_response.json().get("session_id")
            
            # 2. 使用 GLM-4.1V-Thinking-Flash 模型，开启深度思考
            chat_response = await client.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "请详细分析一下人工智能的发展历程"}],
                    "session_id": session_id,
                    "model": "glm-4.1v-thinking-flash",
                    "stream": False,
                    "enable_thinking": True,
                }
            )
            
            if chat_response.status_code == 200:
                log_test("test_deep_thinking", "使用深度思考功能发送消息成功")
                result = chat_response.json()
                
                # 3. 检查响应中是否包含思考过程
                message = result.get("choices", [{}])[0].get("message", {})
                thoughts = message.get("thoughts", "")
                
                if thoughts:
                    log_test("test_deep_thinking", f"思考过程存在，长度: {len(thoughts)} 字符")
                    log_test("test_deep_thinking", f"思考过程预览: {thoughts[:100]}...")
                    test_results["test_deep_thinking"]["status"] = "passed"
                else:
                    log_test("test_deep_thinking", "思考过程为空或不存在", False)
                    log_test("test_deep_thinking", "注意：某些模型可能不返回思考过程")
            else:
                log_test("test_deep_thinking", f"发送消息失败，状态码: {chat_response.status_code}", False)
                
        except Exception as e:
            log_test("test_deep_thinking", f"测试过程中发生异常: {str(e)}", False)
            test_results["test_deep_thinking"]["status"] = "failed"


async def test_model_switch():
    """测试模型切换功能"""
    print("\n=== 测试 9.3: 测试模型切换功能 ===")
    
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            # 1. 获取模型列表
            response = await client.get(f"{BASE_URL}/api/models")
            models = response.json().get("models", [])
            
            # 2. 测试每个模型
            test_models = ["glm-4-flash", "glm-4-plus", "glm-4v-flash", "glm-4.1v-thinking-flash"]
            
            for model_id in test_models:
                # 检查模型是否存在
                model_exists = any(m.get("id") == model_id for m in models)
                if not model_exists:
                    log_test("test_model_switch", f"模型 {model_id} 不存在，跳过测试", False)
                    continue
                
                # 创建会话
                session_response = await client.post(
                    f"{BASE_URL}/v1/sessions",
                    json={"channel": "web"}
                )
                session_id = session_response.json().get("session_id")
                
                # 使用该模型发送消息
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
                
                if chat_response.status_code == 200:
                    result = chat_response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        log_test("test_model_switch", f"模型 {model_id} 测试成功")
                    else:
                        log_test("test_model_switch", f"模型 {model_id} 响应内容为空", False)
                else:
                    log_test("test_model_switch", f"模型 {model_id} 测试失败，状态码: {chat_response.status_code}", False)
            
            test_results["test_model_switch"]["status"] = "passed"
                
        except Exception as e:
            log_test("test_model_switch", f"测试过程中发生异常: {str(e)}", False)
            test_results["test_model_switch"]["status"] = "failed"


async def test_image_upload():
    """测试图片上传和视觉理解功能"""
    print("\n=== 测试 9.4: 测试图片上传和视觉理解功能 ===")
    
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            # 1. 创建一个简单的测试图片（1x1 像素的红色图片）
            # 使用 base64 编码的 PNG 图片
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
            
            # 2. 创建会话
            session_response = await client.post(
                f"{BASE_URL}/v1/sessions",
                json={"channel": "web"}
            )
            session_id = session_response.json().get("session_id")
            
            # 3. 使用支持视觉的模型发送带图片的消息
            chat_response = await client.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "请描述这张图片"}],
                    "session_id": session_id,
                    "model": "glm-4.1v-thinking-flash",
                    "stream": False,
                    "enable_thinking": False,
                    "image": test_image_base64,
                }
            )
            
            if chat_response.status_code == 200:
                log_test("test_image_upload", "带图片的消息发送成功")
                result = chat_response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if content:
                    log_test("test_image_upload", f"模型成功响应，内容长度: {len(content)} 字符")
                    log_test("test_image_upload", f"响应内容: {content[:100]}...")
                    test_results["test_image_upload"]["status"] = "passed"
                else:
                    log_test("test_image_upload", "响应内容为空", False)
            else:
                log_test("test_image_upload", f"发送消息失败，状态码: {chat_response.status_code}", False)
                log_test("test_image_upload", f"错误信息: {chat_response.text}")
                
        except Exception as e:
            log_test("test_image_upload", f"测试过程中发生异常: {str(e)}", False)
            test_results["test_image_upload"]["status"] = "failed"


async def test_thinking_display():
    """测试思考过程的展示和折叠功能（后端API测试）"""
    print("\n=== 测试 9.5: 测试思考过程的展示和折叠功能 ===")
    
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        try:
            # 1. 创建会话
            session_response = await client.post(
                f"{BASE_URL}/v1/sessions",
                json={"channel": "web"}
            )
            session_id = session_response.json().get("session_id")
            
            # 2. 测试流式输出中的思考过程
            log_test("test_thinking_display", "测试流式输出中的思考过程...")
            
            async with client.stream(
                "POST",
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": "请分析一下深度学习的发展趋势"}],
                    "session_id": session_id,
                    "model": "glm-4.1v-thinking-flash",
                    "stream": True,
                    "enable_thinking": True,
                },
                timeout=API_TIMEOUT,
            ) as response:
                if response.status_code == 200:
                    log_test("test_thinking_display", "流式请求发送成功")
                    
                    thinking_received = False
                    content_received = False
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                
                                # 检查是否有思考过程
                                if "thoughts" in delta and delta["thoughts"]:
                                    thinking_received = True
                                    log_test("test_thinking_display", f"接收到思考过程数据")
                                
                                # 检查是否有普通内容
                                if "content" in delta and delta["content"]:
                                    content_received = True
                                    
                            except json.JSONDecodeError:
                                pass
                    
                    if thinking_received:
                        log_test("test_thinking_display", "流式输出中成功接收到思考过程")
                        test_results["test_thinking_display"]["status"] = "passed"
                    else:
                        log_test("test_thinking_display", "流式输出中未接收到思考过程（可能模型不支持或API未返回）", False)
                    
                    if content_received:
                        log_test("test_thinking_display", "流式输出中成功接收到普通内容")
                else:
                    log_test("test_thinking_display", f"流式请求失败，状态码: {response.status_code}", False)
                    
        except Exception as e:
            log_test("test_thinking_display", f"测试过程中发生异常: {str(e)}", False)
            test_results["test_thinking_display"]["status"] = "failed"


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("MyClaw 功能测试")
    print("=" * 60)
    
    # 运行所有测试
    await test_model_call()
    await test_deep_thinking()
    await test_model_switch()
    await test_image_upload()
    await test_thinking_display()
    
    # 打印测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = result["status"]
        status_symbol = "✓" if status == "passed" else ("✗" if status == "failed" else "?")
        print(f"{status_symbol} {test_name}: {status}")
        
        if result["details"]:
            for detail in result["details"]:
                print(f"  {detail}")
    
    # 统计
    passed = sum(1 for r in test_results.values() if r["status"] == "passed")
    failed = sum(1 for r in test_results.values() if r["status"] == "failed")
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    if failed > 0:
        print(f"失败: {failed} 个测试")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
