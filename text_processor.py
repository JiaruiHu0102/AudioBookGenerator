import os
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import PyPDF2
from typing import List, Tuple, Optional, Callable
from config import TextProcessConfig

class TextProcessor:
    def __init__(self):
        self.config = TextProcessConfig
        
        # 目录相关的关键词，只保留目录相关的
        self.toc_keywords = [
            "^目\\s*录\\s*$",  # 严格匹配独立的"目录"行
            "^contents\\s*$",
            "^catalog\\s*$", 
            "^index\\s*$",
            "第.{1,10}章.*?\\d+\\s*$",  # 匹配带页码的章节行
            "chapter.*?\\d+\\s*$",
            "第.{1,10}节.*?\\d+\\s*$",
            "section.*?\\d+\\s*$"
        ]
        self.toc_pattern = re.compile("|".join(self.toc_keywords), re.IGNORECASE)
        
        # 句子结束标记
        self.sentence_ends = ["。", "！", "？", "…", ".", "!", "?", ";", "；"]
        self.sentence_pattern = f'[{"".join(self.sentence_ends)}]'
        
        # 创建引号映射字典
        self.quote_types = {
            '"': True,  # 标准双引号
            '"': True,  # U+201C LEFT DOUBLE QUOTATION MARK (中文左双引号)
            '"': True,  # U+201D RIGHT DOUBLE QUOTATION MARK (中文右双引号)
            '\u201c': True,  # U+201C LEFT DOUBLE QUOTATION MARK
            '\u201d': True,  # U+201D RIGHT DOUBLE QUOTATION MARK
            '\u0022': True,  # U+0022 QUOTATION MARK
            '\u301d': True,  # U+301D REVERSED DOUBLE PRIME QUOTATION MARK
            '\u301e': True,  # U+301E DOUBLE PRIME QUOTATION MARK
            '\u301f': True,  # U+301F LOW DOUBLE PRIME QUOTATION MARK
            '\u2033': True,  # U+2033 DOUBLE PRIME
        }
    
    def is_toc_line(self, line: str) -> bool:
        """判断是否是目录行"""
        line = line.strip()
        # 如果是空行
        if not line:
            return True
            
        # 如果是典型的目录行（短文本+页码）
        if len(line) < 50 and re.search(r'.+\s+\d+\s*$', line):
            return True
            
        # 如果匹配目录关键词模式
        if self.toc_pattern.search(line):
            return True
            
        return False
    
    def find_sentence_end(self, text: str, start: int) -> int:
        """从指定位置开始寻找最近的句子结束位置"""
        min_pos = len(text)
        for end in self.sentence_ends:
            pos = text.find(end, start)
            if pos != -1 and pos < min_pos:
                min_pos = pos
        return min_pos if min_pos < len(text) else -1
    
    def _clean_text(self, text: str) -> str:
        """清理文本中的多余空格和换行"""
        # 将多个连续空白字符（包括空格、制表符、换行等）替换为单个空格
        text = re.sub(r'\s+', ' ', text)
        # 删除中文字符之间的空格
        text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)
        # 删除中文标点前后的空格
        text = re.sub(r'\s*([，。！？；：、])\s*', r'\1', text)
        # 删除引号内部的空格
        text = re.sub(r'([""''])\s+(.+?)\s+([""''])', r'\1\2\3', text)
        # 删除括号内部的空格
        text = re.sub(r'([（\(])\s+(.+?)\s+([）\)])', r'\1\2\3', text)
        return text.strip()

    def split_text_with_progress(self, text: str, batch_size: int, 
                               progress_callback: Callable[[int], None]) -> List[str]:
        """按批次大小分割文本，在中文句号和中文右引号组合附近进行分段"""
        # 步骤1: 清理整个文本
        original_length = len(text)
        text = self._clean_text(text)
        
        segments = []
        lines = text.split('\n')
        
        # 为确保处理连贯性，不再按行处理，而是将所有行连接起来后统一处理
        full_text = ' '.join([line.strip() for line in lines if line.strip() and not self.is_toc_line(line.strip())])
        
        # 如果文本太短，直接返回整个文本
        if len(full_text) <= batch_size:
            return [full_text]
        
        # 步骤2: 在中文句号和中文右引号组合附近分段
        segments = []
        start_pos = 0
        segment_count = 0
        
        # 预计分段数量，用于进度报告
        estimated_segments = max(1, len(full_text) // batch_size)
        
        while start_pos < len(full_text):
            # 更新进度
            progress = min(99, int((segment_count / estimated_segments) * 99))
            progress_callback(progress)
            
            # 计算当前批次的理想结束位置
            ideal_end = min(start_pos + batch_size, len(full_text))
            
            # 如果已经到达文本末尾，则直接添加剩余内容
            if ideal_end >= len(full_text):
                segment = full_text[start_pos:]
                segments.append(segment)
                segment_count += 1
                break
            
            # 在理想位置附近查找中文句号'。'和中文右引号'\u201d'组合
            best_break_pos = start_pos + batch_size - 1  # 默认为批次大小位置
            
            # 向后查找最近的合适断点
            for i in range(ideal_end - 1, start_pos, -1):
                if i + 1 < len(full_text) and full_text[i] == '。' and full_text[i + 1] == '\u201d':
                    best_break_pos = i + 1  # 包含中文句号和右引号
                    break
            
            # 如果没找到中文句号和右引号组合，则尝试只查找中文句号
            if best_break_pos == start_pos + batch_size - 1:
                for i in range(ideal_end - 1, start_pos, -1):
                    if full_text[i] == '。':
                        best_break_pos = i  # 包含中文句号
                        break
            
            # 如果还是没找到，则尝试查找其他句子结束标记
            if best_break_pos == start_pos + batch_size - 1:
                for i in range(ideal_end - 1, start_pos, -1):
                    if full_text[i] in self.sentence_ends:
                        best_break_pos = i  # 包含其他句子结束标记
                        break
            
            # 获取分段（包含断点字符）
            segment = full_text[start_pos:best_break_pos + 1]
            segments.append(segment)
            
            segment_count += 1
            
            # 更新下一段的起始位置
            start_pos = best_break_pos + 1
        
        return segments
    
    def _split_by_sentence(self, text: str, batch_size: int, progress_callback: Callable[[int], None]) -> List[str]:
        """按句子结束标记分割文本"""
        segments = []
        current_segment = ""
        
        # 查找所有句子结束标记的位置
        sentence_end_positions = []
        for i, char in enumerate(text):
            if char in self.sentence_ends:
                sentence_end_positions.append(i)
        
        if not sentence_end_positions:
            # 如果没有找到句子结束标记，则按固定长度分割
            for i in range(0, len(text), batch_size):
                segment = text[i:min(i + batch_size, len(text))]
                if segment:
                    segments.append(segment)
            return segments
        
        start_pos = 0
        for i, pos in enumerate(sentence_end_positions):
            # 更新进度
            progress = min(40, int((i / len(sentence_end_positions)) * 40))
            progress_callback(progress)
            
            # 当前句子（包括结束标记）
            sentence = text[start_pos:pos + 1]
            
            # 如果添加当前句子会超出批次大小
            if len(current_segment) + len(sentence) > batch_size and current_segment:
                segments.append(current_segment)
                current_segment = sentence
            else:
                current_segment += sentence
            
            start_pos = pos + 1
        
        # 添加最后一个段落
        if current_segment:
            segments.append(current_segment)
        
        # 如果最后一个结束标记之后还有内容
        if start_pos < len(text):
            remaining = text[start_pos:]
            
            # 如果剩余内容较短且已有段落，添加到最后一个段落
            if len(remaining) < batch_size // 3 and segments:
                segments[-1] += remaining
            else:
                segments.append(remaining)
        
        return segments
    
    def process_text_with_progress(self, text: str, settings: dict,
                                 progress_callback: Callable[[int], None]) -> List[str]:
        """处理文本并报告进度"""
        try:
            # 检查原始文本是否为空
            if not text or len(text.strip()) < 10:
                return []
                
            # 去除英文（如果需要）- 30% 进度
            processed_text = text
            if settings.get('remove_english', True):
                processed_text = self.remove_english(text)
                # 检查处理后的文本是否为空
                if not processed_text or len(processed_text.strip()) < 10:
                    processed_text = text  # 如果处理后文本不足，使用原始文本
                progress_callback(30)
            else:
                progress_callback(30)
            
            # 确保batch_size是有效的
            batch_size = settings.get('batch_size', 5000)
            if batch_size < 100:
                batch_size = 5000  # 使用默认值
            
            # 按批次分割文本 - 40% 进度
            segments = self.split_text_with_progress(
                processed_text, 
                batch_size,
                lambda p: progress_callback(30 + p)  # 进度从30%开始
            )
            
            # 检查是否有分割出的段落
            if not segments:
                # 如果无法正常分段，尝试简单分段
                if processed_text and len(processed_text.strip()) > 10:
                    # 简单地按照句号分段，然后再按照batch_size合并
                    simple_segments = []
                    current_segment = ""
                    
                    # 按句号分割
                    sentences = re.split(r'([。！？；.!?;]', processed_text)
                    i = 0
                    while i < len(sentences):
                        if i + 1 < len(sentences):
                            sentence = sentences[i] + sentences[i+1]  # 句子内容 + 句号
                            i += 2
                        else:
                            sentence = sentences[i]
                            i += 1
                            
                        if len(current_segment) + len(sentence) <= batch_size:
                            current_segment += sentence
                        else:
                            if current_segment:
                                simple_segments.append(current_segment)
                            current_segment = sentence
                    
                    if current_segment:  # 添加最后一段
                        simple_segments.append(current_segment)
                        
                    segments = simple_segments
            
            # 完成处理 - 100% 进度
            progress_callback(100)
            
            return segments
            
        except Exception as e:
            print(f"处理文本时出错: {e}")
            return []
    
    def convert_to_txt(self, file_path: str) -> Optional[str]:
        """将EPUB或PDF文件转换为TXT内容"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.epub':
                return self._convert_epub(file_path)
            elif ext == '.pdf':
                return self._convert_pdf(file_path)
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"不支持的文件格式: {ext}")
        except Exception as e:
            print(f"文件转换失败: {e}")
            return None
    
    def _convert_epub(self, epub_path: str) -> str:
        """转换EPUB文件为纯文本"""
        try:
            book = epub.read_epub(epub_path)
            text_content = []
            
            # 按顺序处理所有项目，只关注文本
            for item in book.get_items():
                try:
                    # 只处理文档类型
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        content = item.get_content()
                        if content:
                            soup = BeautifulSoup(content, 'html.parser')
                            # 移除script和style标签
                            for script in soup(["script", "style"]):
                                script.decompose()
                            
                            # 提取纯文本
                            text = soup.get_text()
                            # 清理文本
                            text = self._clean_text(text)
                            if text:
                                text_content.append(text)
                except Exception:
                    # 静默跳过错误
                    continue
            
            if not text_content:
                raise ValueError("未能从EPUB中提取任何文本内容")
                
            # 将所有文本连接起来
            return '\n'.join(text_content)
            
        except Exception as e:
            print(f"EPUB转换失败: {e}")
            raise ValueError(f"EPUB转换失败: {e}")
    
    def _convert_pdf(self, pdf_path: str) -> str:
        """转换PDF文件为纯文本"""
        text_content = []
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    # 清理文本
                    text = self._clean_text(text)
                    text_content.append(text)
        
        return '\n'.join(text_content)
    
    def remove_english(self, text: str) -> str:
        """去除英文内容（包括括号、引号中的英文）"""
        # 去除括号及其内容中包含英文的部分
        text = re.sub(r'[\(（]([^）\)]*[a-zA-Z]+[^）\)]*)[）\)]', '', text)
        # 去除引号及其内容中包含英文的部分
        text = re.sub(r'[""《]([^""》]*[a-zA-Z]+[^"">]*)[""》]', '', text)
        # 只去除英文字母，保留数字
        text = re.sub(r'[a-zA-Z]+', '', text)
        # 清理文本
        return self._clean_text(text)
    
    def split_text(self, text: str, method: str) -> List[str]:
        """根据指定方法切分文本"""
        if method == "cut0":
            # 不切分
            return [text]
        elif method == "cut1":
            # 每4句话切分
            sentences = re.split(r'[。！？；.!?;]', text)
            chunks = []
            current_chunk = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                current_chunk.append(sentence)
                if len(current_chunk) >= 4:
                    chunks.append('。'.join(current_chunk) + '。')
                    current_chunk = []
            
            if current_chunk:
                chunks.append('。'.join(current_chunk) + '。')
            return chunks
            
        elif method == "cut2":
            # 每50字切分
            chunks = []
            for i in range(0, len(text), 50):
                chunk = text[i:i+50]
                if chunk:
                    chunks.append(chunk)
            return chunks
            
        elif method == "cut3":
            # 按中文句号切分
            return [s.strip() + '。' for s in text.split('。') if s.strip()]
            
        elif method == "cut4":
            # 按英文句号切分
            return [s.strip() + '.' for s in text.split('.') if s.strip()]
            
        elif method == "cut5":
            # 按所有标点符号切分
            pattern = f'[{self.config.PUNCTUATION["all"]}]'
            sentences = re.split(pattern, text)
            return [s.strip() + '。' for s in sentences if s.strip()]
        
        else:
            raise ValueError(f"不支持的切分方法: {method}")
    
    def process_for_multi_speaker(self, text: str) -> List[Tuple[str, str]]:
        """处理多人朗读的文本，返回(角色, 文本)列表"""
        # 使用正则表达式匹配对话
        pattern = r'([^：""]*)(：[""]|:"|说道：")(.*?)([""」』])'
        matches = re.finditer(pattern, text)
        
        results = []
        last_end = 0
        
        for match in matches:
            # 添加对话前的旁白（如果有）
            narration = text[last_end:match.start()].strip()
            if narration:
                results.append(("旁白", narration))
            
            # 添加对话
            speaker = match.group(1).strip()
            content = match.group(3).strip()
            if speaker and content:
                results.append((speaker, content))
            
            last_end = match.end()
        
        # 添加最后的旁白（如果有）
        final_narration = text[last_end:].strip()
        if final_narration:
            results.append(("旁白", final_narration))
        
        return results
    
    def process_text(self, file_path: str, settings: dict) -> Tuple[List[str], Optional[List[Tuple[str, str]]]]:
        """处理文本文件，返回处理后的文本段落和角色信息（如果是多人朗读）"""
        # 转换文件
        text = self.convert_to_txt(file_path)
        if not text:
            return [], None
        
        # 去除英文（如果需要）
        if settings.get('remove_english', True):
            text = self.remove_english(text)
        
        # 切分文本
        split_method = settings.get('split_method', 'cut5')
        segments = self.split_text(text, split_method)
        
        # 处理多人朗读
        if settings.get('is_multi_speaker', False):
            character_segments = []
            for segment in segments:
                character_segments.extend(self.process_for_multi_speaker(segment))
            return segments, character_segments
        
        return segments, None 