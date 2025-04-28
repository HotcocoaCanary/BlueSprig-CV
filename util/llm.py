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
            "content": f"你是一个高度专业的简历信息提取专家。你需要根据下面要求的json格式以及里面的备注说明、基于用户的原简历的信息进行严谨地信息提取。你的输出格式要求：按照以下严格的JSON格式返回JSON的代码本身，绝对不能生成任何注释说明。以下是JSON格式要求：{resume_format}"
        },
        {
            "role": "user",
            "content": content
        }
    ]
    text_generation = TextGeneration()
    result = text_generation.blue_llm_70B(messages, 1.0)
    return result