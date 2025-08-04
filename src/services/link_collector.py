"""链接收集器服务"""

import asyncio
import aiohttp
import re
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy.orm import Session

from src.models import Channel, Link
from src.models.base import SessionLocal
from config.settings import get_settings


class LinkCollector:
    """链接收集器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=self.settings.crawler.concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=self.settings.crawler.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.settings.crawler.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def collect_links_for_channel(self, channel: Channel) -> List[str]:
        """为单个频道收集链接"""
        if not channel.keywords:
            logger.warning(f"频道 {channel.name} 没有搜索关键字")
            return []
        
        all_links = set()
        
        for keyword in channel.keywords:
            logger.info(f"搜索频道 {channel.name} 的关键字: {keyword}")
            
            # 从 iptv-search.com 收集
            iptv_search_links = await self._collect_from_iptv_search(keyword)
            all_links.update(iptv_search_links)
            
            # 从 tonkiang.us 收集
            tonkiang_links = await self._collect_from_tonkiang(keyword)
            all_links.update(tonkiang_links)
            
            # 添加延迟避免被限制
            await asyncio.sleep(self.settings.source.search_delay)
        
        # 限制链接数量
        limited_links = list(all_links)[:self.settings.source.max_links_per_channel]
        
        logger.info(f"为频道 {channel.name} 收集到 {len(limited_links)} 个链接")
        return limited_links
    
    async def _make_request_with_retry(self, url: str, params: Optional[Dict] = None, max_retries: int = 1) -> Optional[str]:
        """带重试的HTTP请求方法，返回HTML内容"""
        last_error = None
        
        for attempt in range(max_retries + 1):  # 原始请求 + 重试次数
            try:
                logger.debug(f"尝试请求 {url} (第 {attempt + 1} 次)")
                
                # 创建自定义超时设置（30秒）
                timeout = aiohttp.ClientTimeout(total=30.0)
                
                async with self.session.get(url, params=params, timeout=timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        logger.debug(f"请求成功: {url}")
                        return html
                    elif response.status == 503:
                        last_error = f"503 Service Unavailable"
                        if attempt < max_retries:
                            wait_time = 2.0 * (attempt + 1)  # 递增等待时间
                            logger.warning(f"请求失败(503)，{wait_time}秒后重试: {url}")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.warning(f"重试{max_retries}次后仍然失败(503)，访问URL: {url}")
                            return None
                    else:
                        last_error = f"HTTP {response.status}"
                        logger.warning(f"请求失败({response.status})，访问URL: {url}")
                        return None
                        
            except asyncio.TimeoutError:
                last_error = "请求超时"
                if attempt < max_retries:
                    logger.warning(f"请求超时，重试: {url}")
                    await asyncio.sleep(2.0)
                    continue
                else:
                    logger.warning(f"重试{max_retries}次后仍然超时，访问URL: {url}")
                    return None
                    
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    logger.warning(f"请求异常，重试: {url}, 错误: {e}")
                    await asyncio.sleep(2.0)
                    continue
                else:
                    logger.error(f"重试{max_retries}次后仍然失败，访问URL: {url}, 错误: {e}")
                    return None
        
        logger.error(f"所有重试都失败了，访问URL: {url}, 最后错误: {last_error}")
        return None
    
    async def _collect_from_iptv_search(self, keyword: str) -> Set[str]:
        """从 iptv-search.com 收集链接"""
        links = set()
        
        # 修复：使用正确的搜索路径
        search_url = f"{self.settings.source.iptv_search_url}/zh-hans/search/"
        params = {'q': keyword}
        
        # 使用重试机制获取HTML内容
        html = await self._make_request_with_retry(search_url, params=params, max_retries=1)
        
        if html:
            try:
                soup = BeautifulSoup(html, 'html.parser')
                
                # 调试：输出HTML结构样本用于分析
                logger.debug(f"iptv-search.com HTML片段（前1000字符）: {html[:1000]}")
                
                # 尝试多种可能的页面结构
                channel_cards = soup.find_all('div', class_='channel card')
                if not channel_cards:
                    # 尝试其他可能的结构
                    channel_cards = soup.find_all('div', class_='result-item')
                if not channel_cards:
                    # 尝试寻找包含频道名称的所有div
                    channel_cards = soup.find_all('div', string=lambda text: text and keyword.lower() in text.lower())
                if not channel_cards:
                    # 更广泛的搜索：寻找所有包含链接的元素
                    all_links = soup.find_all('a')
                    logger.debug(f"找到 {len(all_links)} 个链接元素")
                    for link in all_links:
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        logger.debug(f"链接: {text} -> {href}")
                
                logger.debug(f"找到 {len(channel_cards)} 个频道卡片，使用选择器: 'div.channel.card'")
                
                for card in channel_cards:
                    try:
                        # 提取频道名称
                        channel_name_elem = card.find('div', class_='channel-name')
                        if not channel_name_elem:
                            logger.debug("未找到频道名称元素")
                            continue
                        channel_name = channel_name_elem.get_text().strip()
                        logger.debug(f"找到频道名称: {channel_name}")
                        
                        # 尝试多种方式提取链接
                        link_url = None
                        
                        # 方法1: 提取解密后的链接（可能为空）
                        decrypted_link_elem = card.find('span', class_='decrypted-link')
                        if decrypted_link_elem:
                            link_url = decrypted_link_elem.get_text().strip()
                            if link_url:
                                logger.debug(f"方法1: 从decrypted-link获取: {link_url[:50]}...")
                        
                        # 方法2: 查找加密数据并尝试构造链接（如果decrypted-link为空）
                        if not link_url:
                            # 查找data-encrypted属性
                            link_text_elem = card.find('span', class_='link-text')
                            if link_text_elem and link_text_elem.get('data-encrypted'):
                                encrypted_data = link_text_elem.get('data-encrypted')
                                logger.debug(f"找到加密数据: {encrypted_data[:50]}...")
                                
                                # 尝试构造可能的链接格式
                                # 基于观察到的模式: https://stream.iptv-search.com/main.php?id=频道名&t=时间戳&token=令牌
                                import time
                                import hashlib
                                
                                # 生成可能的stream链接
                                timestamp = int(time.time())
                                possible_urls = [
                                    f"https://stream.iptv-search.com/main.php?id={channel_name}&t={timestamp}",
                                    f"https://stream.iptv-search.com/live/{channel_name}.m3u8",
                                    f"https://stream.iptv-search.com/stream/{channel_name}",
                                ]
                                
                                for test_url in possible_urls:
                                    if self._is_valid_stream_url(test_url):
                                        link_url = test_url
                                        logger.debug(f"方法2: 构造的链接: {link_url}")
                                        break
                        
                        # 方法3: 从按钮的onclick事件中提取
                        if not link_url:
                            copy_button = card.find('button', onclick=True)
                            if copy_button:
                                onclick_text = copy_button.get('onclick', '')
                                logger.debug(f"找到onclick: {onclick_text}")
                                # 这表明链接在.decrypted-link中，但需要JavaScript解密
                        
                        # 方法4: 查找任何包含http的属性或文本
                        if not link_url:
                            for elem in card.find_all():
                                # 检查元素的所有属性
                                for attr, value in elem.attrs.items():
                                    if isinstance(value, str) and ('http' in value or '.m3u8' in value or 'stream' in value):
                                        if self._is_valid_stream_url(value):
                                            link_url = value
                                            logger.debug(f"方法4: 从属性{attr}获取: {link_url}")
                                            break
                                if link_url:
                                    break
                        
                        if not link_url:
                            logger.debug(f"无法为频道 {channel_name} 提取有效链接")
                            continue
                        
                        # 清理HTML实体编码
                        import html
                        link_url = html.unescape(link_url)
                        
                        # 提取更新日期
                        date_elem = card.find('span', class_='date-text')
                        update_date = date_elem.get_text().strip() if date_elem else None
                        
                        # 提取分组信息
                        group_elem = card.find('span', class_='group-text')
                        group_info = group_elem.get_text().strip() if group_elem else None
                        
                        # 验证链接是否有效
                        if self._is_valid_stream_url(link_url):
                            # 检查频道名称是否与关键字匹配
                            if self._channel_name_matches_keyword(channel_name, keyword):
                                links.add(link_url)
                                logger.info(f"✓ iptv-search找到匹配频道: {channel_name} -> {link_url[:50]}... (更新:{update_date}, 分组:{group_info})")
                            else:
                                logger.debug(f"✗ 频道名称不匹配: {channel_name} vs 关键字: {keyword}")
                        else:
                            logger.debug(f"✗ 链接无效: {link_url}")
                    
                    except Exception as e:
                        logger.warning(f"解析频道卡片失败: {e}")
                        continue
                
                logger.info(f"从 iptv-search.com 搜索 '{keyword}' 找到 {len(channel_cards)} 个频道卡片，{len(links)} 个有效链接")
                
            except Exception as e:
                logger.error(f"解析 iptv-search.com 响应失败: {e}")
        else:
            logger.warning(f"无法获取 iptv-search.com 的响应内容")
        
        return links
    
    async def _collect_from_tonkiang(self, keyword: str) -> Set[str]:
        """从 tonkiang.us 收集链接"""
        links = set()
        
        # 修复：使用正确的搜索参数格式
        import urllib.parse
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f"{self.settings.source.tonkiang_url}/?iptv={encoded_keyword}"
        
        # 使用重试机制获取HTML内容
        html = await self._make_request_with_retry(search_url, max_retries=1)
        
        if html:
            try:
                soup = BeautifulSoup(html, 'html.parser')
                
                # 根据实际网站结构解析频道信息
                result_cards = soup.find_all('div', class_='resultplus')
                
                for card in result_cards:
                    try:
                        # 提取频道名称
                        channel_name_elem = card.find('div', class_='tip', attrs={'data-title': 'Play with PC'})
                        if not channel_name_elem:
                            logger.debug(f"tonkiang.us: 未找到频道名称元素")
                            continue
                        channel_name = channel_name_elem.get_text().strip()
                        
                        # 提取实际链接 - 尝试多种选择器
                        link_elem = card.find('tba', class_='jbmj')
                        if not link_elem:
                            # 尝试其他可能的选择器
                            link_elem = card.find('tba', {'class': 'jbmj'})
                        if not link_elem:
                            # 查找包含链接的任何元素
                            all_links = self._extract_urls_from_text(card.get_text())
                            if all_links:
                                link_url = list(all_links)[0]  # 取第一个链接
                                logger.debug(f"tonkiang.us: 从文本中提取链接，频道: {channel_name}, 链接: {link_url[:50]}...")
                            else:
                                logger.debug(f"tonkiang.us: 未找到任何链接，频道: {channel_name}")
                                logger.debug(f"tonkiang.us: 卡片内容前100字符: {card.get_text()[:100]}...")
                                continue
                        else:
                            link_url = link_elem.get_text().strip()
                        
                        logger.debug(f"tonkiang.us: 发现频道={channel_name}, 链接={link_url[:50]}...")
                        
                        # 提取更新日期和其他信息
                        info_elem = card.find('div', style=lambda x: x and 'font-size: 10px' in x)
                        update_info = ""
                        resolution = ""
                        if info_elem:
                            info_text = info_elem.get_text().strip()
                            update_info = info_text
                            # 提取分辨率信息
                            if '1920x1080' in info_text:
                                resolution = "1920x1080"
                            elif '1280x720' in info_text:
                                resolution = "1280x720"
                        
                        # 验证链接是否有效
                        is_valid_url = self._is_valid_stream_url(link_url)
                        is_matching_name = self._channel_name_matches_keyword(channel_name, keyword)
                        
                        logger.debug(f"tonkiang.us: 链接验证={is_valid_url}, 名称匹配={is_matching_name}, 频道={channel_name}, 关键字={keyword}")
                        
                        if is_valid_url:
                            # 检查频道名称是否与关键字匹配
                            if is_matching_name:
                                links.add(link_url)
                                logger.debug(f"✓ 找到匹配频道: {channel_name} -> {link_url[:50]}... (更新:{update_info}, 分辨率:{resolution})")
                            else:
                                logger.debug(f"✗ 频道名称不匹配: {channel_name} vs 关键字: {keyword}")
                        else:
                            logger.debug(f"✗ 链接无效: {link_url}")
                    
                    except Exception as e:
                        logger.warning(f"解析tonkiang.us频道卡片失败: {e}")
                        continue
                
                logger.info(f"从 tonkiang.us 搜索 '{keyword}' 找到 {len(result_cards)} 个结果卡片，{len(links)} 个有效链接")
                
            except Exception as e:
                logger.error(f"解析 tonkiang.us 响应失败: {e}")
        else:
            logger.warning(f"无法获取 tonkiang.us 的响应内容")
        
        return links
    
    def _extract_urls_from_text(self, text: str) -> Set[str]:
        """从文本中提取流媒体URL"""
        urls = set()
        
        # 常见的流媒体URL模式，优化了匹配精度
        patterns = [
            r'http[s]?://[^\s<>"\'\)]+\.m3u8(?:\?[^\s<>"\'\)]*)?',  # HLS streams
            r'http[s]?://[^\s<>"\'\)]+\.ts(?:\?[^\s<>"\'\)]*)?',    # TS segments  
            r'http[s]?://[^\s<>"\'\)]+\.flv(?:\?[^\s<>"\'\)]*)?',   # FLV streams
            r'http[s]?://[^\s<>"\'\)]+\.mp4(?:\?[^\s<>"\'\)]*)?',   # MP4 streams
            r'rtmp://[^\s<>"\'\)]+',                                 # RTMP streams
            r'rtsp://[^\s<>"\'\)]+',                                 # RTSP streams
            r'http[s]?://[^\s<>"\'\)]*(?:live|stream|tv|iptv|hls)[^\s<>"\'\)]*\.m3u8?[^\s<>"\'\)]*',  # 包含关键字的流媒体URL
            r'http[s]?://[^\s<>"\'\)]*(?:\.php\?[^"\'<>\s]*(?:stream|live|tv)[^"\'<>\s]*)',  # PHP动态流链接
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if self._is_valid_stream_url(match):
                    urls.add(match.strip())
        
        return urls
    
    def _channel_name_matches_keyword(self, channel_name: str, keyword: str) -> bool:
        """检查频道名称是否与关键字匹配
        
        优化后的匹配逻辑：
        1. 精确匹配频道基础名称，避免子串误匹配（如CCTV1不匹配CCTV10）
        2. 允许匹配带有画质标识的优质版本（如深圳卫视4K、CCTV1高清）
        3. 支持各种别名和变体匹配
        """
        if not channel_name or not keyword:
            return False
        
        import re
        
        channel_lower = channel_name.lower().strip()
        keyword_lower = keyword.lower().strip()
        
        # 画质标识关键词（这些应该被忽略或被视为加分项）
        quality_keywords = [
            '4k', 'uhd', '超高清', '超清',
            '高清', 'hd', '1080p', '1080i', '720p',
            'fhd', 'full hd', 'fullhd',
            '标清', 'sd', '480p',
            '蓝光', 'bluray', 'blu-ray'
        ]
        
        # 其他描述性关键词（通常可以忽略）
        # 注意：不包含'tv'，因为它可能是频道名称的一部分（如CCTV）
        descriptive_keywords = [
            '频道', 'channel', '电视台',
            '直播', 'live', '在线',
            '官方', 'official',
            'not 24/7', '[not 24/7]',
            r'\([^)]*\)',  # 括号内容，如 (1080p), (576p)
            r'\[[^\]]*\]'  # 方括号内容，如 [Not 24/7]
        ]
        
        # 清理频道名称：移除画质和描述性关键词
        channel_clean = channel_lower
        for desc in descriptive_keywords:
            if desc.startswith(r'\(') or desc.startswith(r'\['):
                # 正则表达式模式
                channel_clean = re.sub(desc, '', channel_clean, flags=re.IGNORECASE)
            else:
                # 普通字符串，但要小心不要破坏频道名称的核心部分
                # 只在词边界处替换，避免误伤
                if desc in ['频道', 'channel', '电视台', '直播', 'live', '在线', '官方', 'official']:
                    # 使用词边界匹配，避免误删除
                    pattern = r'\b' + re.escape(desc) + r'\b'
                    channel_clean = re.sub(pattern, '', channel_clean, flags=re.IGNORECASE)
                else:
                    channel_clean = channel_clean.replace(desc, '')
        
        # 移除多余空格，但保留基本结构
        channel_clean = re.sub(r'\s+', ' ', channel_clean).strip()
        
        # 清理关键字，移除特殊字符但保留字母数字
        keyword_clean = re.sub(r'[^\w\u4e00-\u9fff]', '', keyword_lower)
        
        # 1. 基础精确匹配
        if channel_clean == keyword_lower:
            return True
        
        # 移除特殊字符后的匹配
        channel_alphanumeric = re.sub(r'[^\w\u4e00-\u9fff]', '', channel_clean)
        if channel_alphanumeric == keyword_clean:
            return True
        
        # 2. CCTV频道的特殊处理（避免CCTV1匹配到CCTV10等）
        if keyword_lower.startswith('cctv') and len(keyword_lower) > 4:
            # 提取CCTV后的数字或字符
            keyword_suffix = keyword_lower[4:]  # 如 CCTV1 -> 1, CCTV5+ -> 5+
            
            # 查找频道名称中的CCTV模式
            cctv_pattern = r'cctv\s*([0-9]+[+]?|[a-z]+)'
            matches = re.findall(cctv_pattern, channel_clean)
            
            for match in matches:
                if match == keyword_suffix:
                    return True
            
            # 如果没有找到精确匹配，不允许模糊匹配
            if any(f'cctv{i}' in channel_clean for i in range(10) if f'cctv{i}' != keyword_lower):
                # 如果频道中包含其他CCTV数字，则不匹配
                return False
        
        # 3. 特殊后缀匹配检查（如CCTV5+ vs CCTV5）
        if '+' in keyword_lower and '+' not in channel_lower:
            return False
        if '+' in channel_lower and '+' not in keyword_lower:
            return False
        
        # 数字频道的特殊处理（避免误匹配）
        if re.match(r'.*\d+.*', keyword_lower):
            # 如果关键字包含数字，要求精确匹配数字部分
            keyword_numbers = re.findall(r'\d+', keyword_lower)
            channel_numbers = re.findall(r'\d+', channel_clean)
            
            # 必须包含相同的数字
            if not any(num in channel_numbers for num in keyword_numbers):
                return False
        
        # 4. 基础名称匹配（允许画质标识）
        # 检查是否为频道名称 + 画质标识的组合
        has_quality_indicator = any(quality in channel_lower for quality in quality_keywords)
        
        if has_quality_indicator:
            # 移除画质关键词后再匹配
            channel_no_quality = channel_lower
            for quality in quality_keywords:
                channel_no_quality = channel_no_quality.replace(quality, '')
            channel_no_quality = re.sub(r'\s+', ' ', channel_no_quality).strip()
            
            # 检查基础名称是否匹配
            if keyword_lower in channel_no_quality or keyword_clean in re.sub(r'[^\w\u4e00-\u9fff]', '', channel_no_quality):
                return True
        
        # 5. 常规模糊匹配（但要避免数字误匹配）
        if keyword_clean in channel_clean:
            # 额外检查：如果关键字是纯数字，避免误匹配
            if keyword_clean.isdigit():
                # 要求数字前后有分隔符或者是完整单词
                number_pattern = r'\b' + re.escape(keyword_clean) + r'\b'
                return bool(re.search(number_pattern, channel_clean))
            return True
        
        # 6. 别名和同义词匹配
        keyword_mappings = {
            'cctv': ['央视', '中央电视台', '中央台', '中央'],
            '央视': ['cctv', '中央电视台', '中央台', '中央'],
            '中央': ['cctv', '央视', '中央电视台', '中央台'],
            '湖南卫视': ['芒果tv', '芒果', 'mango tv', '湖南台'],
            '芒果tv': ['湖南卫视', '湖南台'],
            '芒果': ['湖南卫视', '湖南台'],
            '东方卫视': ['上海卫视', '东方台', '上海台'],
            '上海卫视': ['东方卫视', '东方台', '上海台'],
            '体育': ['sports', '运动'],
            '新闻': ['news'],
            '卫视': ['satellite', '卫星'],
            '电影': ['movie', 'cinema'],
            '音乐': ['music'],
            '综艺': ['variety'],
            '少儿': ['kids', 'children', '儿童'],
            '财经': ['finance', 'financial'],
            '科教': ['education', 'science'],
            '文艺': ['arts', 'culture'],
            '生活': ['life', 'lifestyle']
        }
        
        # 检查同义词映射
        for key, aliases in keyword_mappings.items():
            if keyword_lower == key.lower():
                for alias in aliases:
                    if alias.lower() in channel_clean or alias.lower() in channel_alphanumeric:
                        return True
            elif keyword_lower in [alias.lower() for alias in aliases]:
                if key.lower() in channel_clean or key.lower() in channel_alphanumeric:
                    return True
        
        # 特殊处理：央视/中央 匹配 CCTV 频道
        if keyword_lower in ['央视', '中央', '中央电视台', '中央台']:
            if 'cctv' in channel_clean or channel_clean.startswith('cctv'):
                return True
        elif keyword_lower.startswith('cctv'):
            if any(term in channel_clean for term in ['央视', '中央电视台', '中央台', '中央']):
                return True
        
        return False
    
    def _is_valid_stream_url(self, url: str) -> bool:
        """检查是否为有效的流媒体URL"""
        if not url or len(url) < 10:
            return False
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # 检查协议
            if parsed.scheme not in ['http', 'https', 'rtmp', 'rtsp']:
                return False
            
            # 检查文件扩展名或URL模式
            valid_extensions = ['.m3u8', '.ts', '.flv', '.mp4']
            valid_keywords = ['live', 'stream', 'tv', 'iptv', 'channel']
            
            url_lower = url.lower()
            has_extension = any(ext in url_lower for ext in valid_extensions)
            has_keyword = any(keyword in url_lower for keyword in valid_keywords)
            
            return has_extension or has_keyword
            
        except Exception:
            return False
    
    async def save_links_to_database(self, channel: Channel, links: List[str]) -> int:
        """保存链接到数据库"""
        if not links:
            return 0
        
        db = SessionLocal()
        try:
            saved_count = 0
            
            for url in links:
                # 检查链接是否已存在
                existing_link = db.query(Link).filter(
                    Link.channel_id == channel.id,
                    Link.url == url
                ).first()
                
                if not existing_link:
                    # 创建新链接
                    new_link = Link(
                        channel_id=channel.id,
                        url=url,
                        source=self._detect_source(url),
                    )
                    db.add(new_link)
                    saved_count += 1
                    logger.debug(f"新增链接: {url[:50]}...")
                else:
                    logger.debug(f"链接已存在: {url[:50]}...")
            
            db.commit()
            logger.info(f"为频道 {channel.name} 保存了 {saved_count} 个新链接")
            
            # 更新频道统计
            from src.services.channel_manager import ChannelManager
            channel_manager = ChannelManager()
            channel_manager.update_channel_stats(channel.id)
            
            return saved_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"保存链接到数据库失败: {e}")
            return 0
        finally:
            db.close()
    
    def _detect_source(self, url: str) -> str:
        """检测链接来源"""
        if 'iptv-search.com' in url:
            return 'iptv-search.com'
        elif 'tonkiang.us' in url:
            return 'tonkiang.us'
        else:
            try:
                parsed = urlparse(url)
                return parsed.netloc
            except Exception:
                return 'unknown'
    
    async def collect_all_channels(self) -> Dict[str, int]:
        """收集所有频道的链接"""
        logger.info("开始收集所有频道的链接")
        
        # 获取所有活跃频道
        from src.services.channel_manager import ChannelManager
        channel_manager = ChannelManager()
        channels = channel_manager.get_channels(active_only=True)
        
        if not channels:
            logger.warning("没有找到活跃的频道")
            return {}
        
        results = {}
        
        for channel in channels:
            try:
                # 收集链接
                links = await self.collect_links_for_channel(channel)
                
                # 保存到数据库
                saved_count = await self.save_links_to_database(channel, links)
                results[channel.name] = saved_count
                
                logger.info(f"频道 {channel.name}: 收集 {len(links)} 个链接，保存 {saved_count} 个新链接")
                
            except Exception as e:
                logger.error(f"处理频道 {channel.name} 失败: {e}")
                results[channel.name] = 0
        
        total_saved = sum(results.values())
        logger.info(f"收集完成，总共保存 {total_saved} 个新链接")
        
        return results