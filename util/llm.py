import base64

from util.LLM.text_generation import TextGeneration


def image_to_text(image_path):
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
    result = text_generation.blue_llm_70B(messages)
    return result