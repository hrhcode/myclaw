"""
工具 Schema 转换

负责将工具定义转换为智谱 AI 工具调用格式
"""
from typing import Dict, Any, List
from app.tools.base import ToolDefinition, ToolParameter


def tool_to_zhipu_schema(tool: ToolDefinition) -> Dict[str, Any]:
    """
    将工具定义转换为智谱 AI 工具调用格式
    
    Args:
        tool: 工具定义
        
    Returns:
        智谱工具 Schema 字典
    """
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
    }


def tools_to_zhipu_schemas(tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
    """
    将多个工具定义转换为智谱 AI 工具调用格式列表
    
    Args:
        tools: 工具定义列表
        
    Returns:
        智谱工具 Schema 列表
    """
    return [tool_to_zhipu_schema(tool) for tool in tools]


def parameter_to_json_schema(param: ToolParameter) -> Dict[str, Any]:
    """
    将工具参数转换为 JSON Schema 格式
    
    Args:
        param: 工具参数定义
        
    Returns:
        JSON Schema 格式的参数定义
    """
    schema: Dict[str, Any] = {
        "type": param.type,
        "description": param.description
    }
    
    if param.enum:
        schema["enum"] = param.enum
    if param.default is not None:
        schema["default"] = param.default
    
    return schema
