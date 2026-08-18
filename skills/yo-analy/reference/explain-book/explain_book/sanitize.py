from __future__ import annotations


# 用于隐藏文档携带型提示注入的隐形码点。按攻击形态分组，使每个条目背后的
# 理由始终便于审查。
#
# 1. 零宽与隐形间隔符。渲染为空无，因此夹在它们之间的文字对阅读页面的人
#    不可见，对模型却清清楚楚。
_ZERO_WIDTH_CODEPOINTS = frozenset({
    0x200B,  # 零宽空格（ZERO WIDTH SPACE）
    0x200C,  # 零宽不连字（ZERO WIDTH NON-JOINER）
    0x200D,  # 零宽连字（ZERO WIDTH JOINER）
    0x2060,  # 单词连接符（WORD JOINER）
    0xFEFF,  # 零宽不换行空格（ZERO WIDTH NO-BREAK SPACE）/ 位于非开头位置时即 BOM
    0x00AD,  # 软连字符（SOFT HYPHEN）—— 除换行断词处外不可见
    0x034F,  # 组合字形连接符（COMBINING GRAPHEME JOINER）—— 完全无渲染效果
    0x180E,  # 蒙古文元音分隔符（MONGOLIAN VOWEL SEPARATOR）
    0x2061,  # 函数应用符（FUNCTION APPLICATION）
    0x2062,  # 隐形乘号（INVISIBLE TIMES）
    0x2063,  # 隐形分隔符（INVISIBLE SEPARATOR）
    0x2064,  # 隐形加号（INVISIBLE PLUS）
})

# 2. 双向格式控制符 —— Trojan Source 类攻击（CVE-2021-42574）。它们不改变
#    模型读到的字符序列，改变的是人*看到*的顺序。精心构造的一行可以显示为
#    无害的学习建议，而模型读到的却是注入的指令，于是批准某个生成 skill 的
#    审查者与加载它的 agent 看到的并不一致。移除它们后，渲染顺序与逻辑顺序
#    保持一致。
#
#    正常的从右到左书籍不受影响：Unicode 双向算法从字符本身推导方向，因此
#    阿拉伯文和希伯来文即使没有这些控制符仍会从右到左渲染。被丢弃的只是
#    显式的嵌入、覆盖与隔离符，而连贯的正文基本上从不需要它们。
_BIDI_CONTROL_CODEPOINTS = frozenset({
    0x200E,  # 从左到右标记（LEFT-TO-RIGHT MARK）
    0x200F,  # 从右到左标记（RIGHT-TO-LEFT MARK）
    0x061C,  # 阿拉伯字母标记（ARABIC LETTER MARK）
    0x202A,  # 从左到右嵌入（LEFT-TO-RIGHT EMBEDDING）
    0x202B,  # 从右到左嵌入（RIGHT-TO-LEFT EMBEDDING）
    0x202C,  # 弹出方向格式（POP DIRECTIONAL FORMATTING）
    0x202D,  # 从左到右覆盖（LEFT-TO-RIGHT OVERRIDE）
    0x202E,  # 从右到左覆盖（RIGHT-TO-LEFT OVERRIDE）
    0x2066,  # 从左到右隔离（LEFT-TO-RIGHT ISOLATE）
    0x2067,  # 从右到左隔离（RIGHT-TO-LEFT ISOLATE）
    0x2068,  # 首个强方向隔离（FIRST STRONG ISOLATE）
    0x2069,  # 弹出方向隔离（POP DIRECTIONAL ISOLATE）
})

# 3. 不属于格式控制符（因此基于类别的过滤会漏掉它们）、但仍渲染为空白
#    宽度的字符。与空格不同，它们是字母，因此能挺过空白归一化，可用来
#    填充隐藏文本。
_INVISIBLE_LETTER_CODEPOINTS = frozenset({
    0x115F,  # 韩文初声填充符（HANGUL CHOSEONG FILLER）
    0x1160,  # 韩文中声填充符（HANGUL JUNGSEONG FILLER）
    0x3164,  # 韩文填充符（HANGUL FILLER）
    0xFFA0,  # 半宽韩文填充符（HALFWIDTH HANGUL FILLER）
})

_INVISIBLE_CODEPOINTS = (
    _ZERO_WIDTH_CODEPOINTS
    | _BIDI_CONTROL_CODEPOINTS
    | _INVISIBLE_LETTER_CODEPOINTS
)

# 4. Unicode 标签块。原本是语言标签，如今被用来把整段 ASCII 载荷走私成
#    隐形的"标签"字符。
_TAG_BLOCK_START = 0xE0000
_TAG_BLOCK_END = 0xE007F


def is_invisible_codepoint(codepoint: int) -> bool:
    """码点渲染为空无、应当被剥离时返回 True。

    导出本函数，好让针对生成 skill 的扫描器能精确标记提取层剥离了哪些
    字符。当两侧的集合发生漂移时，提取器放过的字符会让扫描器随后报警
    —— 更糟的情况是两层都没有覆盖它。
    """
    return (
        codepoint in _INVISIBLE_CODEPOINTS
        or _TAG_BLOCK_START <= codepoint <= _TAG_BLOCK_END
    )


def sanitize_extracted_text(text: str) -> tuple[str, int]:
    """移除用于文档携带型提示注入的隐形码点。"""
    kept: list[str] = []
    removed = 0

    for character in text:
        if is_invisible_codepoint(ord(character)):
            removed += 1
            continue
        kept.append(character)

    return "".join(kept), removed
