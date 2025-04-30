import base64

from util.LLM.text_generation import TextGeneration


def image_to_text(image_path):
    """
    将图像文件转换为文本。

    该函数读取指定路径的图像文件，将其转换为Base64编码的字符串，然后使用文本生成模型提取图像中的文字。

    参数:
    image_path (str): 图像文件的路径。

    返回:
    str: 提取的文字内容。
    """
    with open(image_path, "rb") as f:
        b_image = f.read()
    image = base64.b64encode(b_image).decode('utf-8')
    messages=[
        {
            "role": "user",
            "content": "data:image/JPEG;base64," + image,
            "contentType": "image"
        },
        {
            "role": "user",
            "content": "提取出这个图片中的所有文字，除此之外不要返回任何其他信息",
            "contentType": "text"
        }
    ]
    text_generation = TextGeneration()
    result = text_generation.blue_llm_multimodal(messages)
    return result

def format_resume(resume_format, content):
    """
    根据给定的简历格式和内容，提取简历信息并返回格式化后的简历。

    参数:
    resume_format (str): 简历的JSON格式要求。
    content (str): 原始简历的内容。

    返回:
    str: 格式化后的简历信息。
    """
    messages=[
        {
            "role": "user",
            "content": f"""
你是一个高度专业的简历信息提取专家。
你需要根据下面要求的json格式以及里面的备注说明、基于用户的原简历的信息进行严谨地信息提取。
你的输出格式要求：按照以下严格的JSON格式返回JSON的代码本身，绝对不能生成任何注释说明。
以下是JSON格式要求：{resume_format}
"""
        },
        {
            "role": "user",
            "content": content
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages, 1.0)
    return response

def better_resume(better_resume_format, content):
    messages = [
        {
            "role": "user",
            "content": f"""
你是一个高度专业的简历润色专家，你需要基于用户的原简历的信息进行严谨地详尽丰富修改优化。
内容要求：
- 针对原简历中有的信息，参考模板JSON的注释进行丰富优化表达；
    - 保证基础文本量，
        - 如原简历文字量较多，例如≥2页，则保证原文本量的80%；
        - 如原来的文本量较少，例如少于300字，则扩展扩展至500-700字的范例
- 原简历中没有提及的信息项必须保持为空，绝对不能杜撰任何虚假信息。
输出格式要求：
- 必须严格按照以下的JSON格式返回JSON的代码本身，绝对不能生成任何注释说明。
以下是JSON格式要求：
{better_resume_format}
"""
        },
        {
            "role": "user",
            "content": content
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages, 1.0)
    return response


def resume_judge(resume_judge_format, content):
    messages = [
        {
            "role": "user",
            "content": f"""
你是一个专业简历诊断专家，请严格按照以下要求评价所提供的简历：
1. 基于用户提供的简历内容（非空部分）进行专业诊断
2. 诊断必须包含总评（summary）和评分（score）
3. 总评要求：
   - 使用第二人称"你"进行评价
   - 禁止出现任何人名
   - 简明扼要（100字内）
   - 包含优势和改进建议
4. 输出要求：
   - 严格使用指定JSON格式
   - 直接输出有效JSON代码
   - 禁止任何注释或说明
5. JSON格式模板如下，其中你需要补充的简历诊断内容必须必须做到详细、具体、专业：
{resume_judge_format}"""
        },
        {
            "role": "user",
            "content": f"请诊断以下简历：\n{content}"
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages, 1.0)
    return response
