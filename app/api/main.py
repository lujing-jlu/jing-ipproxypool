import asyncio
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from ..core.pool import ProxyPool
from ..core.models import Proxy

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Proxy Pool API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化代理池
proxy_pool = ProxyPool()
background_tasks = set()

# 依赖注入
def get_db():
    db = proxy_pool.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    try:
        # 启动代理池后台任务
        task = asyncio.create_task(proxy_pool.start())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        logger.info("代理池后台任务已启动")
    except Exception as e:
        logger.error(f"启动代理池任务失败: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    # 清理后台任务
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    logger.info("代理池后台任务已停止")

@app.get("/proxy")
def get_proxy(db: Session = Depends(get_db)):
    """获取一个代理"""
    proxy = proxy_pool.get_proxy(db)
    if proxy:
        return proxy.to_dict()
    return {"error": "No valid proxy available"}

@app.get("/proxies")
def get_proxies(valid_only: bool = True, db: Session = Depends(get_db)):
    """获取所有代理"""
    proxies = proxy_pool.get_all_proxies(db, valid_only=valid_only)
    return [proxy.to_dict() for proxy in proxies]

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取代理池统计信息"""
    all_proxies = proxy_pool.get_all_proxies(db, valid_only=False)
    valid_proxies = [p for p in all_proxies if p.is_valid]
    return {
        "total": len(all_proxies),
        "valid": len(valid_proxies),
        "success_rate": len(valid_proxies) / len(all_proxies) if all_proxies else 0
    } 