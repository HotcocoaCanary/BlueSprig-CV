import json

class JsonValidationError(Exception):
    """
    Custom exception for JSON validation errors.
    """
    pass


def validate_and_clean_json(json_str: str) -> str:
    """
    接收一个 JSON 字符串，执行以下操作：
    1. 去除所有 // 单行注释和 /* */ 多行注释，但保留字符串内的注释标记
    2. 将所有单引号(')替换为双引号(")
    3. 检验所有 [ ] 和 { } 是否正确匹配闭合
    4. 验证 JSON 格式是否合法

    :param json_str: 输入的 JSON 字符串
    :return: 清理后的 JSON 字符串
    :raises JsonValidationError: 如果校验或解析失败，抛出异常并附带错误信息
    """
    def remove_comments(s: str) -> str:
        result = []
        i = 0
        n = len(s)
        in_string = False
        string_char = ''
        while i < n:
            ch = s[i]
            # 字符串开始/结束检测
            if ch in ('"', "'"):
                if not in_string:
                    in_string = True
                    string_char = ch
                elif s[i-1] != "\\" and ch == string_char:
                    in_string = False
                result.append(ch)
                i += 1
            # 非字符串内，检测注释
            elif not in_string and i+1 < n and s[i:i+2] == '//':
                # 跳到行尾
                i += 2
                while i < n and s[i] != '\n':
                    i += 1
            elif not in_string and i+1 < n and s[i:i+2] == '/*':
                # 跳到 */
                i += 2
                while i+1 < n and s[i:i+2] != '*/':
                    i += 1
                i += 2
            else:
                result.append(ch)
                i += 1
        return ''.join(result)

    # 1. 去除注释
    no_comments = remove_comments(json_str)

    # 2. 替换单引号为双引号
    normalized = no_comments.replace("'", '"')

    # 3. 检查括号匹配
    stack = []
    pairs = {'}': '{', ']': '['}
    for idx, char in enumerate(normalized):
        if char in ['{', '[']:
            stack.append((char, idx))
        elif char in ['}', ']']:
            if not stack or stack[-1][0] != pairs[char]:
                raise JsonValidationError(
                    f"不匹配的闭合符号 '{char}' 出现在位置 {idx}")
            stack.pop()
    if stack:
        unclosed, pos = stack[-1]
        raise JsonValidationError(
            f"未闭合的符号 '{unclosed}'，起始位置 {pos}")

    # 4. 验证 JSON 格式
    try:
        json.loads(normalized)
    except json.JSONDecodeError as e:
        raise JsonValidationError(f"JSON 解析失败：{e}")

    return normalized