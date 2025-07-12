#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户名提取功能
"""

import re
from typing import Optional


def extract_quoted_username(text: str) -> Optional[str]:
    """
    从文本中提取被引号包裹的真实用户名
    
    Args:
        text: 包含用户名的文本
        
    Returns:
        提取到的用户名，如果没有找到则返回None
        
    Examples:
        - '"张三"加入了群聊' -> '张三'
        - '"内部测试账号"通过扫描你分享的二维码加入群聊' -> '内部测试账号'
        - '"李四"被邀请加入群聊' -> '李四'
        - '"老胡@omni-rpa"邀请"胡言蹊"加入了群聊' -> '胡言蹊' (被邀请者)
    """
    if not text:
        return None
        
    # 使用正则表达式匹配被双引号包裹的内容
    # 匹配模式：双引号开始，非双引号字符，双引号结束
    pattern = r'"([^"]*)"'
    matches = re.findall(pattern, text)
    
    if matches:
        # 如果是邀请场景（包含"邀请"关键词且有多个引号），返回最后一个用户名（被邀请者）
        if "邀请" in text and len(matches) >= 2:
            # 返回最后一个匹配的用户名（被邀请者）
            username = matches[-1].strip()
            if username:
                return username
        else:
            # 其他情况返回第一个匹配的用户名
            username = matches[0].strip()
            if username:
                return username
    
    return None


def test_username_extraction():
    """测试用户名提取功能"""
    test_cases = [
        # 基本测试用例
        ('"张三"加入了群聊', '张三'),
        ('"内部测试账号"通过扫描你分享的二维码加入群聊', '内部测试账号'),
        ('"李四"被邀请加入群聊', '李四'),
        
        # 邀请场景测试用例
        ('"老胡@omni-rpa"邀请"胡言蹊"加入了群聊', '胡言蹊'),
        ('"管理员"邀请"新用户"加入了群聊', '新用户'),
        ('"张三"邀请"李四"加入了群聊', '李四'),
        
        # 包含特殊字符的用户名
        ('"测试用户-123"加入了群聊', '测试用户-123'),
        ('"用户@example.com"通过扫描二维码加入群聊', '用户@example.com'),
        
        # 包含空格和标点符号的用户名
        ('"张 三"加入了群聊', '张 三'),
        ('"用户，测试"通过邀请加入群聊', '用户，测试'),
        
        # 没有引号的情况
        ('张三加入了群聊', None),
        ('没有引号的文本', None),
        
        # 空字符串
        ('', None),
        
        # 只有引号没有内容
        ('""加入了群聊', None),
        
        # 多个引号的情况（应该返回第一个）
        ('"用户1"和"用户2"都加入了群聊', '用户1'),
    ]
    
    print("开始测试用户名提取功能...")
    print("=" * 50)
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = extract_quoted_username(input_text)
        status = "✓" if result == expected else "✗"
        print(f"测试 {i}: {status}")
        print(f"  输入: {input_text}")
        print(f"  期望: {expected}")
        print(f"  实际: {result}")
        print()
    
    print("=" * 50)
    print("测试完成！")


if __name__ == "__main__":
    test_username_extraction() 