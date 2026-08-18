class ExtractionError(Exception):
    """当单个文件无法提取时抛出（批处理模式下不致命）。"""
