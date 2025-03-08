import asyncio
import time
import logging
from typing import Optional, Tuple, List
import aiohttp
from datetime import datetime
from .models import Proxy

logger = logging.getLogger(__name__)

class ProxyValidator:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.test_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/PNG"
        
    async def validate_proxy(self, proxy: Proxy) -> Tuple[bool, Optional[float]]:
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy.url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        logger.debug(f"代理 {proxy.url} 验证成功，响应时间: {response_time:.2f}秒")
                        return True, response_time
                    logger.debug(f"代理 {proxy.url} 验证失败，状态码: {response.status}")
                    return False, None
        except Exception as e:
            logger.debug(f"代理 {proxy.url} 验证出错: {str(e)}")
            return False, None
            
    async def validate_proxies(self, proxies: List[Proxy]) -> List[Proxy]:
        if not proxies:
            return []
            
        logger.info(f"开始验证 {len(proxies)} 个代理...")
        chunk_size = 200  # 每批验证的代理数量
        validated_proxies = []
        valid_count = 0
        total_count = len(proxies)
        processed_count = 0
        
        # 分批处理代理
        for i in range(0, total_count, chunk_size):
            chunk = proxies[i:i + chunk_size]
            tasks = []
            chunk_proxies = []
            
            for proxy in chunk:
                try:
                    # 确保fail_count有初始值
                    if proxy.fail_count is None:
                        proxy.fail_count = 0
                    if proxy.response_time is None:
                        proxy.response_time = 999999
                        
                    task = self.validate_proxy(proxy)
                    tasks.append(task)
                    chunk_proxies.append(proxy)
                except Exception as e:
                    logger.error(f"创建验证任务失败: {str(e)}")
                    continue
                    
            if not tasks:
                continue
                
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for proxy, result in zip(chunk_proxies, results):
                    try:
                        proxy.last_check = datetime.utcnow()
                        
                        if isinstance(result, tuple):
                            is_valid, response_time = result
                            proxy.is_valid = is_valid
                            proxy.response_time = response_time if response_time is not None else 999999
                            if not is_valid:
                                proxy.fail_count = (proxy.fail_count or 0) + 1
                            else:
                                proxy.fail_count = 0
                                valid_count += 1
                        else:
                            proxy.is_valid = False
                            proxy.fail_count = (proxy.fail_count or 0) + 1
                            proxy.response_time = 999999
                            
                        validated_proxies.append(proxy)
                    except Exception as e:
                        logger.error(f"处理验证结果失败: {str(e)}")
                        continue
                    
                processed_count += len(chunk_proxies)
                logger.info(f"验证进度: {processed_count}/{total_count}, 当前有效: {valid_count}")
                
            except Exception as e:
                logger.error(f"验证代理批次失败: {str(e)}")
                continue
                
            # 短暂暂停，避免请求过于频繁
            await asyncio.sleep(1)
            
        logger.info(f"代理验证完成，{valid_count}/{total_count} 个有效")
        return validated_proxies 