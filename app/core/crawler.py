import asyncio
import re
import logging
import json
from typing import List, Dict
import aiohttp
import chardet
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from .models import Proxy

# 配置日志
logger = logging.getLogger(__name__)


class ProxyCrawler:
    def __init__(self):
        self.ua = UserAgent()
        self.sources = {
            # GitHub代理列表
            'proxylist': {
                'urls': [
                    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
                    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt'
                ],
                'parser': self.parse_proxylist
            },
            'monosans': {
                'urls': [
                    'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
                    'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt',
                    'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt'
                ],
                'parser': self.parse_proxylist
            },
            'prxchk': {
                'urls': [
                    'https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt',
                    'https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt',
                    'https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt'
                ],
                'parser': self.parse_proxylist
            },
            'hookzof': {
                'urls': [
                    'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt',
                ],
                'parser': self.parse_proxylist
            },
            'rdavydov': {
                'urls': [
                    'https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt',
                    'https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt',
                    'https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt'
                ],
                'parser': self.parse_proxylist
            },
            'jetkai': {
                'urls': [
                    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
                    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt',
                    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt',
                    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt'
                ],
                'parser': self.parse_proxylist
            },
            'proxyscrape': {
                'urls': [
                    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all',
                    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all'
                ],
                'parser': self.parse_proxylist
            },
            'proxyspace': {
                'urls': ['https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=all&timeout=10000&proxy_format=ipport&format=text'],
                'parser': self.parse_proxylist
            },
            'geonode': {
                'urls': ['https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps%2Csocks4%2Csocks5&anonymityLevel=elite&anonymityLevel=anonymous'],
                'parser': self.parse_geonode
            }
        }

    async def fetch_page(self, url: str) -> str:
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1'
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30, ssl=False) as response:
                    if response.status == 200:
                        content = await response.read()
                        # 检测编码
                        encoding = chardet.detect(
                            content)['encoding'] or 'utf-8'
                        html = content.decode(encoding, errors='ignore')
                        logger.debug(f"成功获取页面: {url}")
                        return html
                    else:
                        logger.warning(f"获取页面失败 {url}, 状态码: {response.status}")
                        return ''
        except Exception as e:
            logger.error(f"获取页面出错 {url}: {str(e)}")
            return ''

    def parse_proxylist(self, content: str) -> List[Dict]:
        proxies = []
        if not content:
            return proxies
        try:
            for line in content.splitlines():
                try:
                    if not line or ':' not in line:
                        continue
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        host = parts[0]
                        port = int(parts[1])
                        # 根据URL判断协议类型
                        protocol = 'http'
                        if 'socks4' in line.lower():
                            protocol = 'socks4'
                        elif 'socks5' in line.lower():
                            protocol = 'socks5'
                        elif 'https' in line.lower():
                            protocol = 'https'

                        if self._validate_proxy_format(host, port, protocol):
                            proxies.append({
                                'host': host,
                                'port': port,
                                'protocol': protocol,
                                'source': 'proxylist'
                            })
                except:
                    continue
        except Exception as e:
            logger.error(f"解析proxylist代理失败: {str(e)}")
        return proxies

    def parse_geonode(self, content: str) -> List[Dict]:
        proxies = []
        if not content:
            return proxies
        try:
            data = json.loads(content)  # 使用json.loads替代eval
            for item in data.get('data', []):
                try:
                    host = item.get('ip')
                    port = int(item.get('port'))
                    protocol = item.get('protocols', ['http'])[0].lower()
                    if self._validate_proxy_format(host, port, protocol):
                        proxies.append({
                            'host': host,
                            'port': port,
                            'protocol': protocol,
                            'source': 'geonode'
                        })
                except:
                    continue
        except Exception as e:
            logger.error(f"解析geonode代理失败: {str(e)}")
        return proxies

    def _validate_proxy_format(self, host: str, port: int, protocol: str) -> bool:
        try:
            ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            if not re.match(ip_pattern, host):
                return False
            if not (0 <= port <= 65535):
                return False
            if protocol not in ['http', 'https', 'socks4', 'socks5']:
                return False
            return True
        except Exception as e:
            logger.error(f"验证代理格式失败: {str(e)}")
            return False

    async def crawl(self) -> List[Proxy]:
        logger.info("开始爬取代理...")
        all_proxies = []
        tasks = []

        # 创建爬取任务
        for source_name, source_info in self.sources.items():
            for url in source_info['urls']:
                tasks.append((source_name, url, self.fetch_page(url)))

        # 并发爬取页面
        results = []
        for source_name, url, task in tasks:
            try:
                page = await task
                results.append((source_name, page))
            except Exception as e:
                logger.error(f"爬取 {source_name} ({url}) 失败: {str(e)}")
                continue

        logger.info(f"完成页面爬取，获取到 {len(results)} 个页面")

        # 解析页面
        for source_name, page in results:
            if not page:
                continue
            try:
                source_info = self.sources[source_name]
                proxies = source_info['parser'](page)
                if proxies:
                    logger.info(f"从 {source_name} 解析到 {len(proxies)} 个代理")
                    for proxy_dict in proxies:
                        proxy = Proxy(
                            host=proxy_dict['host'],
                            port=proxy_dict['port'],
                            protocol=proxy_dict['protocol'],
                            source=source_name
                        )
                        all_proxies.append(proxy)
            except Exception as e:
                logger.error(f"解析 {source_name} 代理失败: {str(e)}")

        # 去重
        unique_proxies = []
        seen = set()
        for proxy in all_proxies:
            key = f"{proxy.host}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)

        logger.info(f"爬取完成，共获取到 {len(unique_proxies)} 个唯一代理")
        return unique_proxies
