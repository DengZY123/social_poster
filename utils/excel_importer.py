"""
Excel文件导入工具
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
from loguru import logger

from core.models import PublishTask


class ExcelImporter:
    """Excel导入器"""
    
    def __init__(self):
        self.required_columns = ["标题", "内容"]
        self.optional_columns = ["图片路径", "发布时间", "话题"]
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """验证Excel文件"""
        try:
            file_path = Path(file_path)
            
            # 检查文件存在
            if not file_path.exists():
                return False, "文件不存在"
            
            # 检查文件扩展名
            if file_path.suffix.lower() not in ['.xlsx', '.xls']:
                return False, "文件格式不正确，请使用Excel文件（.xlsx或.xls）"
            
            # 尝试读取文件
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                return False, f"读取Excel文件失败: {e}"
            
            # 检查是否为空
            if df.empty:
                return False, "Excel文件为空"
            
            # 检查必要列
            missing_columns = []
            for col in self.required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                return False, f"缺少必要列: {', '.join(missing_columns)}"
            
            return True, "文件验证通过"
            
        except Exception as e:
            logger.error(f"验证Excel文件失败: {e}")
            return False, f"验证失败: {e}"
    
    def import_tasks(self, file_path: str, start_time: Optional[datetime] = None, 
                    interval_minutes: int = 30) -> Tuple[bool, str, List[PublishTask]]:
        """
        导入任务
        
        Args:
            file_path: Excel文件路径
            start_time: 开始发布时间，如果为None则使用文件中的时间或当前时间
            interval_minutes: 发布间隔（分钟）
            
        Returns:
            (是否成功, 消息, 任务列表)
        """
        try:
            # 验证文件
            is_valid, message = self.validate_file(file_path)
            if not is_valid:
                return False, message, []
            
            # 读取Excel
            df = pd.read_excel(file_path)
            logger.info(f"读取Excel文件: {len(df)} 行数据")
            
            tasks = []
            current_time = start_time or datetime.now()
            
            for index, row in df.iterrows():
                try:
                    task = self._create_task_from_row(row, current_time, index, interval_minutes)
                    if task:
                        tasks.append(task)
                        # 下一个任务的时间
                        current_time = task.publish_time
                        from datetime import timedelta
                        current_time += timedelta(minutes=interval_minutes)
                    
                except Exception as e:
                    logger.warning(f"跳过第 {index + 2} 行（索引 {index}）: {e}")
                    continue
            
            if not tasks:
                return False, "没有成功导入任何任务", []
            
            logger.info(f"成功导入 {len(tasks)} 个任务")
            return True, f"成功导入 {len(tasks)} 个任务", tasks
            
        except Exception as e:
            logger.error(f"导入Excel失败: {e}")
            return False, f"导入失败: {e}", []
    
    def _create_task_from_row(self, row: pd.Series, base_time: datetime, 
                             index: int, interval_minutes: int) -> Optional[PublishTask]:
        """从行数据创建任务"""
        try:
            # 必要字段
            title = str(row["标题"]).strip()
            content = str(row["内容"]).strip()
            
            if not title or title == "nan":
                raise ValueError("标题为空")
            if not content or content == "nan":
                raise ValueError("内容为空")
            
            # 可选字段
            images = self._parse_images(row.get("图片路径", ""))
            topics = self._parse_topics(row.get("话题", ""))
            publish_time = self._parse_publish_time(row.get("发布时间"), base_time, index, interval_minutes)
            
            # 创建任务
            task = PublishTask.create_new(
                title=title,
                content=content,
                images=images,
                topics=topics,
                publish_time=publish_time
            )
            
            logger.debug(f"创建任务: {title} (发布时间: {publish_time})")
            return task
            
        except Exception as e:
            logger.warning(f"创建任务失败: {e}")
            raise
    
    def _parse_images(self, image_str: str) -> List[str]:
        """解析图片路径"""
        if not image_str or str(image_str).strip() == "nan":
            return []
        
        # 支持多种分隔符
        separators = [',', ';', '|', '\n']
        image_paths = [image_str]
        
        for sep in separators:
            if sep in image_str:
                image_paths = image_str.split(sep)
                break
        
        # 清理路径
        valid_paths = []
        for path in image_paths:
            path = path.strip()
            if path:
                # 判断是否为URL
                if path.startswith(('http://', 'https://')):
                    # URL直接添加
                    valid_paths.append(path)
                    logger.debug(f"添加图片URL: {path}")
                else:
                    # 本地文件检查是否存在
                    if Path(path).exists():
                        valid_paths.append(str(Path(path).absolute()))
                        logger.debug(f"添加本地图片: {path}")
                    else:
                        logger.warning(f"本地图片文件不存在: {path}")
        
        return valid_paths
    
    def _parse_topics(self, topic_str: str) -> List[str]:
        """解析话题标签"""
        if not topic_str or str(topic_str).strip() == "nan":
            return []
        
        # 支持多种分隔符
        separators = [',', ';', '|', '\n', ' ']
        topics = [topic_str]
        
        for sep in separators:
            if sep in topic_str:
                topics = topic_str.split(sep)
                break
        
        # 清理话题
        clean_topics = []
        for topic in topics:
            topic = topic.strip()
            if topic:
                # 确保话题以#开头
                if not topic.startswith('#'):
                    topic = f'#{topic}'
                clean_topics.append(topic)
        
        return clean_topics
    
    def _parse_publish_time(self, time_str, base_time: datetime, 
                           index: int, interval_minutes: int) -> datetime:
        """解析发布时间"""
        # 如果有指定时间，尝试解析
        if time_str and str(time_str).strip() != "nan":
            try:
                # 尝试多种时间格式
                time_formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M",
                    "%Y/%m/%d %H:%M:%S",
                    "%Y/%m/%d %H:%M",
                    "%m-%d %H:%M",
                    "%m/%d %H:%M"
                ]
                
                time_str = str(time_str).strip()
                
                for fmt in time_formats:
                    try:
                        parsed_time = datetime.strptime(time_str, fmt)
                        
                        # 如果只有月日，补充年份
                        if parsed_time.year == 1900:
                            parsed_time = parsed_time.replace(year=datetime.now().year)
                        
                        # 确保是未来时间
                        if parsed_time <= datetime.now():
                            if parsed_time.year == datetime.now().year:
                                # 如果是今年，可能是明年的时间
                                parsed_time = parsed_time.replace(year=datetime.now().year + 1)
                            else:
                                # 如果已经过了，加上间隔时间
                                from datetime import timedelta
                                parsed_time = datetime.now() + timedelta(minutes=(index + 1) * interval_minutes)
                        
                        logger.debug(f"解析时间成功: {time_str} -> {parsed_time}")
                        return parsed_time
                        
                    except ValueError:
                        continue
                
                logger.warning(f"无法解析时间格式: {time_str}，使用默认时间")
                
            except Exception as e:
                logger.warning(f"解析时间失败: {e}")
        
        # 使用基准时间 + 索引 * 间隔
        from datetime import timedelta
        return base_time + timedelta(minutes=index * interval_minutes)
    
    def create_template(self, file_path: str) -> bool:
        """创建Excel模板文件"""
        try:
            # 创建示例数据
            data = {
                "标题": [
                    "今日分享 - 美食推荐",
                    "生活小贴士 - 整理收纳",
                    "旅行记录 - 海边度假"
                ],
                "内容": [
                    "今天给大家推荐一家超好吃的餐厅！\n环境优雅，服务贴心，价格实惠。\n#美食推荐 #餐厅探店",
                    "分享几个实用的收纳小技巧，让你的家更整洁！\n1. 利用收纳盒分类存放\n2. 垂直空间充分利用\n#生活技巧 #整理收纳",
                    "海边度假的美好时光～\n蓝天白云，海浪拍岸，心情格外舒畅！\n#旅行 #海边度假 #美好时光"
                ],
                "图片路径": [
                    "images/news1.png",
                    "images/news1.png",
                    "images/news1.png"
                ],
                "发布时间": [
                    "2024-12-25 09:00",
                    "2024-12-25 15:30", 
                    "2024-12-25 20:00"
                ],
                "话题": [
                    "美食推荐,餐厅探店",
                    "生活技巧,整理收纳",
                    "旅行,海边度假,美好时光"
                ]
            }
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 保存到Excel
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            logger.info(f"Excel模板创建成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建Excel模板失败: {e}")
            return False