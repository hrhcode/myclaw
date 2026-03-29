"""
通用响应模型模块
定义API响应的基础模型
"""
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel):
    """
    基础响应模型
    
    所有API响应的基类
    """
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(default="", description="响应消息")
    code: int = Field(default=200, description="响应状态码")


class SuccessResponse(BaseResponse):
    """
    成功响应模型
    
    用于表示操作成功的响应
    """
    success: bool = Field(default=True, description="操作是否成功")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "code": 200
            }
        }


class ErrorResponse(BaseResponse):
    """
    错误响应模型
    
    用于表示操作失败的响应
    """
    success: bool = Field(default=False, description="操作是否成功")
    error: Optional[str] = Field(default=None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "操作失败",
                "code": 400,
                "error": "参数错误"
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应模型
    
    用于返回分页数据的响应
    """
    success: bool = Field(default=True, description="操作是否成功")
    message: str = Field(default="", description="响应消息")
    code: int = Field(default=200, description="响应状态码")
    data: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=10, description="每页记录数")
    total_pages: int = Field(default=0, description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "查询成功",
                "code": 200,
                "data": [],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10
            }
        }
