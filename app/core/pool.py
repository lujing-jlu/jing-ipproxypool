import asyncio
import logging
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from .models import Proxy, init_db
from .crawler import ProxyCrawler
from .validator import ProxyValidator

# 配置日志
logger = logging.getLogger(__name__)


class ProxyPool:
    def __init__(self, db_url: str = None):
        if db_url is None:
            # 确保data目录存在
            os.makedirs('data', exist_ok=True)
            db_url = 'sqlite:///data/proxies.db'

        self.SessionLocal = init_db(db_url)
        self.crawler = ProxyCrawler()
        self.validator = ProxyValidator()
        logger.info("代理池初始化完成")

    async def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    async def add_proxies(self, proxies: list[Proxy], db: Session):
        if not proxies:
            return

        added_count = 0
        for proxy in proxies:
            stmt = select(Proxy).where(
                Proxy.host == proxy.host,
                Proxy.port == proxy.port,
                Proxy.protocol == proxy.protocol
            )
            existing = db.execute(stmt).scalar()
            if not existing:
                db.add(proxy)
                added_count += 1
        db.commit()
        logger.info(f"新增 {added_count} 个代理")

    async def remove_invalid_proxies(self, db: Session):
        stmt = delete(Proxy).where(
            (Proxy.fail_count > 3) |
            (Proxy.last_check < datetime.utcnow() - timedelta(hours=1))
        )
        result = db.execute(stmt)
        db.commit()
        logger.info(f"清理 {result.rowcount} 个无效代理")

    def get_all_proxies(self, db: Session, valid_only: bool = True) -> list[Proxy]:
        stmt = select(Proxy)
        if valid_only:
            stmt = stmt.where(Proxy.is_valid == True)
        proxies = list(db.execute(stmt).scalars())
        logger.debug(f"获取 {len(proxies)} 个代理")
        return proxies

    async def refresh_proxies(self):
        logger.info("开始刷新代理池...")
        db = self.SessionLocal()
        try:
            # 爬取新代理
            logger.info("开始爬取新代理...")
            new_proxies = await self.crawler.crawl()
            if new_proxies:
                logger.info(f"爬取到 {len(new_proxies)} 个新代理")
                # 验证新代理
                logger.info("开始验证新代理...")
                validated_proxies = await self.validator.validate_proxies(new_proxies)
                # 添加到数据库
                await self.add_proxies(validated_proxies, db)

            # 验证现有代理
            logger.info("开始验证现有代理...")
            existing_proxies = self.get_all_proxies(db, valid_only=False)
            if existing_proxies:
                validated_existing = await self.validator.validate_proxies(existing_proxies)
                for proxy in validated_existing:
                    db.merge(proxy)
                db.commit()

            # 清理无效代理
            await self.remove_invalid_proxies(db)
            logger.info("代理池刷新完成")
        except Exception as e:
            logger.error(f"刷新代理池时发生错误: {str(e)}")
            raise  # 重新抛出异常，让上层处理
        finally:
            db.close()

    def get_proxy(self, db: Session) -> Proxy:
        stmt = select(Proxy).where(
            Proxy.is_valid == True
        ).order_by(Proxy.response_time.asc())
        return db.execute(stmt).scalar()

    async def start(self):
        logger.info("代理池服务启动")
        while True:
            try:
                await self.refresh_proxies()
                logger.info("等待5分钟后进行下一次刷新...")
                await asyncio.sleep(300)  # 每5分钟刷新一次
            except asyncio.CancelledError:
                logger.info("代理池服务停止")
                break
            except Exception as e:
                logger.error(f"代理池服务发生错误: {str(e)}")
                await asyncio.sleep(60)  # 发生错误时等待1分钟后重试
