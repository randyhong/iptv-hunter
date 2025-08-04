"""链接检测器服务"""

import asyncio
import aiohttp
import subprocess
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from loguru import logger
from sqlalchemy.orm import Session

from src.models import Link, CheckResult, LinkStatus
from src.models.base import SessionLocal
from config.settings import get_settings


class LinkChecker:
    """链接检测器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=self.settings.checker.concurrent_checks)
        timeout = aiohttp.ClientTimeout(total=self.settings.checker.timeout)
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
    
    async def check_link(self, link: Link) -> CheckResult:
        """检测单个链接"""
        logger.debug(f"检测链接: {link.url[:50]}...")
        
        # 先进行HTTP检测
        http_result = await self._check_http(link)
        
        # 如果HTTP检测成功，再进行FFmpeg检测
        ffmpeg_result = None
        if http_result.is_success:
            ffmpeg_result = await self._check_with_ffmpeg(link)
        
        # 合并检测结果
        final_result = self._merge_check_results(link, http_result, ffmpeg_result)
        
        # 更新链接状态
        await self._update_link_status(link, final_result)
        
        return final_result
    
    async def _check_http(self, link: Link) -> CheckResult:
        """HTTP可用性检测"""
        start_time = time.time()
        
        try:
            # 对于IPTV流，先尝试HEAD请求，如果失败则尝试GET请求获取少量数据
            response = None
            
            try:
                # 首先尝试HEAD请求
                async with self.session.head(link.url, allow_redirects=True) as resp:
                    response = resp
                    response_time = time.time() - start_time
                    
                    if resp.status == 200:
                        return CheckResult.create_success(
                            link_id=link.id,
                            check_type="http",
                            response_time=response_time,
                            http_status=resp.status,
                            content_type=resp.headers.get('Content-Type'),
                            content_length=int(resp.headers.get('Content-Length', 0)),
                            http_headers=dict(resp.headers),
                        )
                    elif resp.status in [405, 501]:  # Method Not Allowed, Not Implemented
                        # HEAD不支持，尝试GET请求
                        pass
                    else:
                        return CheckResult.create_failure(
                            link_id=link.id,
                            check_type="http",
                            error_message=f"HTTP错误: {resp.status}",
                            http_status=resp.status,
                        )
            except (aiohttp.ClientError, asyncio.TimeoutError):
                # HEAD请求失败，尝试GET请求
                pass
            
            # 尝试GET请求获取前1KB数据
            headers = {'Range': 'bytes=0-1023'}  # 只获取前1KB
            async with self.session.get(link.url, headers=headers, allow_redirects=True) as resp:
                response_time = time.time() - start_time
                
                # 检查HTTP状态码 (200 OK 或 206 Partial Content)
                if resp.status in [200, 206]:
                    # 尝试读取少量数据以验证流是否可用
                    try:
                        data = await resp.read()
                        if len(data) > 0:
                            return CheckResult.create_success(
                                link_id=link.id,
                                check_type="http",
                                response_time=response_time,
                                http_status=resp.status,
                                content_type=resp.headers.get('Content-Type'),
                                content_length=int(resp.headers.get('Content-Length', len(data))),
                                http_headers=dict(resp.headers),
                            )
                    except Exception:
                        pass
                
                return CheckResult.create_failure(
                    link_id=link.id,
                    check_type="http",
                    error_message=f"HTTP错误: {resp.status}",
                    http_status=resp.status,
                )
                    
        except asyncio.TimeoutError:
            return CheckResult.create_failure(
                link_id=link.id,
                check_type="http",
                error_message="HTTP请求超时",
                is_timeout=True,
            )
        except Exception as e:
            return CheckResult.create_failure(
                link_id=link.id,
                check_type="http",
                error_message=f"HTTP检测失败: {str(e)}",
            )
    
    async def _check_with_ffmpeg(self, link: Link) -> Optional[CheckResult]:
        """使用FFmpeg检测流媒体内容"""
        try:
            # 构建ffprobe命令
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                '-analyzeduration', '5000000',  # 5秒分析时长
                '-probesize', '5000000',        # 5MB探测大小
                link.url
            ]
            
            start_time = time.time()
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.settings.checker.ffmpeg_timeout
                )
                response_time = time.time() - start_time
                
                if process.returncode == 0:
                    # 解析FFmpeg输出
                    probe_data = json.loads(stdout.decode())
                    return self._parse_ffmpeg_result(link, probe_data, response_time)
                else:
                    error_msg = stderr.decode() if stderr else "FFmpeg检测失败"
                    return CheckResult.create_failure(
                        link_id=link.id,
                        check_type="ffmpeg",
                        error_message=error_msg,
                    )
                    
            except asyncio.TimeoutError:
                process.kill()
                return CheckResult.create_failure(
                    link_id=link.id,
                    check_type="ffmpeg",
                    error_message="FFmpeg检测超时",
                    is_timeout=True,
                )
                
        except FileNotFoundError:
            logger.warning("未找到ffprobe命令，跳过FFmpeg检测")
            return None
        except Exception as e:
            return CheckResult.create_failure(
                link_id=link.id,
                check_type="ffmpeg",
                error_message=f"FFmpeg检测异常: {str(e)}",
            )
    
    def _parse_ffmpeg_result(self, link: Link, probe_data: Dict, response_time: float) -> CheckResult:
        """解析FFmpeg检测结果"""
        try:
            format_info = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            # 查找视频和音频流
            video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)
            audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), None)
            
            # 提取基本信息
            duration = float(format_info.get('duration', 0))
            bitrate = int(format_info.get('bit_rate', 0))
            
            # 视频信息
            video_codec = video_stream.get('codec_name') if video_stream else None
            resolution = None
            fps = None
            if video_stream:
                width = video_stream.get('width', 0)
                height = video_stream.get('height', 0)
                if width and height:
                    resolution = f"{width}x{height}"
                
                fps_str = video_stream.get('r_frame_rate', '0/1')
                try:
                    if '/' in fps_str:
                        num, den = fps_str.split('/')
                        fps = float(num) / float(den) if float(den) != 0 else 0
                except:
                    fps = 0
            
            # 音频信息
            audio_codec = audio_stream.get('codec_name') if audio_stream else None
            
            # 计算质量评分
            video_quality = self._calculate_video_quality(video_stream)
            audio_quality = self._calculate_audio_quality(audio_stream)
            stability_score = self._calculate_stability_score(format_info, streams)
            overall_score = int((video_quality + audio_quality + stability_score) / 3)
            
            return CheckResult.create_success(
                link_id=link.id,
                check_type="ffmpeg",
                response_time=response_time,
                video_codec=video_codec,
                audio_codec=audio_codec,
                resolution=resolution,
                bitrate=bitrate,
                fps=fps,
                duration=duration,
                video_quality=video_quality,
                audio_quality=audio_quality,
                stability_score=stability_score,
                overall_score=overall_score,
            )
            
        except Exception as e:
            return CheckResult.create_failure(
                link_id=link.id,
                check_type="ffmpeg",
                error_message=f"解析FFmpeg结果失败: {str(e)}",
            )
    
    def _calculate_video_quality(self, video_stream: Optional[Dict]) -> int:
        """计算视频质量评分 (1-10)"""
        if not video_stream:
            return 1
        
        score = 5  # 基础分
        
        # 分辨率评分
        width = video_stream.get('width', 0)
        height = video_stream.get('height', 0)
        if height >= 1080:
            score += 3
        elif height >= 720:
            score += 2
        elif height >= 480:
            score += 1
        
        # 帧率评分
        fps_str = video_stream.get('r_frame_rate', '0/1')
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                fps = float(num) / float(den) if float(den) != 0 else 0
                if fps >= 50:
                    score += 2
                elif fps >= 30:
                    score += 1
        except:
            pass
        
        return min(10, max(1, score))
    
    def _calculate_audio_quality(self, audio_stream: Optional[Dict]) -> int:
        """计算音频质量评分 (1-10)"""
        if not audio_stream:
            return 1
        
        score = 5  # 基础分
        
        # 采样率评分
        sample_rate = audio_stream.get('sample_rate')
        if sample_rate:
            rate = int(sample_rate)
            if rate >= 48000:
                score += 2
            elif rate >= 44100:
                score += 1
        
        # 声道数评分
        channels = audio_stream.get('channels', 0)
        if channels >= 6:  # 5.1声道
            score += 2
        elif channels >= 2:  # 立体声
            score += 1
        
        return min(10, max(1, score))
    
    def _calculate_stability_score(self, format_info: Dict, streams: List[Dict]) -> int:
        """计算稳定性评分 (1-10)"""
        score = 5  # 基础分
        
        # 比特率稳定性
        bitrate = format_info.get('bit_rate')
        if bitrate and int(bitrate) > 0:
            score += 2
        
        # 流数量合理性
        if len(streams) >= 2:  # 至少有视频和音频
            score += 1
        
        return min(10, max(1, score))
    
    def _merge_check_results(self, link: Link, http_result: CheckResult, ffmpeg_result: Optional[CheckResult]) -> CheckResult:
        """合并检测结果"""
        if not http_result.is_success:
            return http_result
        
        if not ffmpeg_result:
            # 没有FFmpeg检测结果（比如ffprobe未安装），HTTP成功就认为链接可用
            http_result.overall_score = 6  # 中等评分，因为没有详细的流信息
            return http_result
        
        if not ffmpeg_result.is_success:
            # HTTP成功但FFmpeg失败，仍然认为链接可用，但降低评分
            http_result.overall_score = 4  # 较低评分，可能有质量问题
            # 不设置error_message，因为HTTP检测成功
            return http_result
        
        # 两者都成功，合并信息
        merged = http_result
        merged.video_codec = ffmpeg_result.video_codec
        merged.audio_codec = ffmpeg_result.audio_codec
        merged.resolution = ffmpeg_result.resolution
        merged.bitrate = ffmpeg_result.bitrate
        merged.fps = ffmpeg_result.fps
        merged.duration = ffmpeg_result.duration
        merged.video_quality = ffmpeg_result.video_quality
        merged.audio_quality = ffmpeg_result.audio_quality
        merged.stability_score = ffmpeg_result.stability_score
        merged.overall_score = ffmpeg_result.overall_score
        
        return merged
    
    async def _update_link_status(self, link: Link, result: CheckResult):
        """更新链接状态"""
        db = SessionLocal()
        try:
            # 重新查询链接对象以确保在当前会话中
            db_link = db.query(Link).filter(Link.id == link.id).first()
            if not db_link:
                logger.error(f"未找到链接 ID: {link.id}")
                return
            
            # 创建新的检测结果对象，避免会话冲突
            new_result = CheckResult(
                link_id=result.link_id,
                check_type=result.check_type,
                status=result.status,
                response_time=result.response_time,
                http_status=result.http_status,
                content_type=result.content_type,
                video_codec=result.video_codec,
                audio_codec=result.audio_codec,
                resolution=result.resolution,
                bitrate=result.bitrate,
                fps=result.fps,
                overall_score=result.overall_score,
                is_success=result.is_success,
                is_timeout=result.is_timeout,
                error_message=result.error_message,
                check_time=result.check_time
            )
            db.add(new_result)
            
            # 更新链接信息
            db_link.last_checked = new_result.check_time
            db_link.check_count += 1
            
            if new_result.is_success:
                db_link.status = LinkStatus.ACTIVE
                db_link.is_valid = True
                db_link.success_count += 1
                db_link.last_success = new_result.check_time
                db_link.response_time = new_result.response_time
                db_link.quality_score = new_result.overall_score or 0
                db_link.resolution = new_result.resolution
                db_link.codec = new_result.video_codec
                db_link.bitrate = new_result.bitrate
                db_link.fps = new_result.fps
                db_link.error_message = None
            else:
                db_link.fail_count += 1
                db_link.error_message = new_result.error_message
                
                if new_result.is_timeout:
                    db_link.status = LinkStatus.TIMEOUT
                elif new_result.http_status == 403:
                    db_link.status = LinkStatus.FORBIDDEN
                else:
                    db_link.status = LinkStatus.ERROR
                
                # 连续失败太多次标记为无效
                if db_link.fail_count >= 3:
                    db_link.is_valid = False
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新链接状态失败: {e}")
        finally:
            db.close()
    
    async def check_links_batch(self, links: List[Link]) -> Dict[str, Any]:
        """批量检测链接"""
        if not links:
            return {"total": 0, "success": 0, "failed": 0}
        
        logger.info(f"开始批量检测 {len(links)} 个链接")
        
        # 创建任务
        tasks = [self.check_link(link) for link in links]
        
        # 执行检测
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        success_count = 0
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"检测链接 {links[i].url[:50]} 异常: {result}")
                failed_count += 1
            elif hasattr(result, 'is_success') and result.is_success:
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"批量检测完成: 成功 {success_count}, 失败 {failed_count}")
        
        return {
            "total": len(links),
            "success": success_count,
            "failed": failed_count,
            "success_rate": (success_count / len(links)) * 100 if links else 0
        }
    
    async def check_all_links(self, channel_id: Optional[int] = None) -> Dict[str, Any]:
        """检测所有链接"""
        db = SessionLocal()
        try:
            query = db.query(Link)
            
            if channel_id:
                query = query.filter(Link.channel_id == channel_id)
            
            # 只检测活跃的链接或未检测的链接
            links = query.filter(
                (Link.status.in_([LinkStatus.UNKNOWN, LinkStatus.ACTIVE])) |
                (Link.last_checked.is_(None))
            ).all()
            
            return await self.check_links_batch(links)
            
        finally:
            db.close()