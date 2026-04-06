"""DAO层共用工具函数。"""


async def commit_or_flush(db, commit: bool = True) -> None:
    """根据 commit 参数决定提交或刷新。

    commit=True  时执行 db.commit()（保持现有行为）
    commit=False 时执行 db.flush()（发送到数据库但不提交，供调用方组合事务）
    """
    if commit:
        await db.commit()
    else:
        await db.flush()
