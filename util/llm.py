import base64
import os
import uuid

from util.LLM.ASR import LASRClient
from util.LLM.text_generation import TextGeneration
from util.LLM.tts import TTS
from util.json_op import validate_and_clean_json


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
    messages = [
        {
            "role": "user",
            "content": "data:image/JPEG;base64," + image,
            "contentType": "image"
        },
        {
            "role": "user",
            "content": "提取出这个图片中的所有文字，可以按照你的理解将不通顺的地方或者错别字更正，除此之外不要返回任何其他信息",
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
    system_prompt = f"""
            你是一个高度专业的简历信息提取专家。
            你需要根据下面要求的json格式以及里面的备注说明、基于用户的原简历的信息进行严谨地信息提取。
            你的输出格式要求：按照以下严格的JSON格式返回JSON的代码本身，绝对不能生成任何注释说明。
            以下是JSON格式要求：{resume_format}
    """
    messages = [
        {
            "role": "user",
            "content": f"请帮我提取简历信息，内容如下:"
                       f"{content}"
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages, system_prompt=system_prompt, temperature=0.01)
    return validate_and_clean_json(response)


def better_resume_by_module(better_resume_format_part, content_part, part_name):
    system_prompt = f"""
        你是一个高度专业的简历{part_name}模块润色专家，你需要针对用户的原简历的{part_name}信息进行严谨地详尽丰富修改优化。要求逻辑清晰，语义通顺。
        你的输出格式要求：必须按照以下严格的JSON格式返回JSON的代码本身，绝对不能生成任何注释说明。
        以下是JSON格式要求：
        {better_resume_format_part}
    """
    messages = [
        {
            "role": "user",
            "content": f"请帮我优化{part_name}模块,内容如下:"
                       f"{content_part}"
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages, system_prompt=system_prompt, temperature=1.0)
    return validate_and_clean_json(response)


def llm_chat(messages, json=False):
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages)
    return validate_and_clean_json(response) if json else response


def resume_judge(resume_judge_format, content, job_name=""):
    common_prompt = f"""
        你是一个专业的简历诊断专家，请严格按照以下要求评价所提供的简历：
        1. 基于用户提供的简历内容
        2. 诊断必须包含总评（summary）和评分（score）
        3. 总评要求：
           - 简明扼要（150字内）
           - 包含优势和改进建议，每一个建议针对到简历中的具体部分中
        4. 输出要求：
           - 严格使用指定JSON格式
           - 直接输出有效JSON代码
           - 禁止任何注释或说明
        5. JSON格式模板如下，其中你需要补充的简历诊断内容必须必须做到详细、具体、专业：
        {resume_judge_format}
    """

    if job_name != "":
        system_prompt = f"\n\n你是一个专业的{job_name}岗位的简历诊断专家。" + \
                        common_prompt.split("你是一个专业的简历诊断专家，", 1)[1]
    else:
        system_prompt = common_prompt

    messages = [
        {
            "role": "user",
            "content": f"简历内容如下:"
                       f"{content}"
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages, system_prompt=system_prompt, temperature=1.0)
    return validate_and_clean_json(response)


def resume_json2md(resume_json, md_path):
    messages = [
        {
            "role": "user",
            "content": f"请按照你的理解将简历的json格式转换为markdown格式，确保json中的所有信息都有体现，并可以添加一些样式增加美观"
                       f"{resume_json}"
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages)

    # 确保路径存在，没有文件新建文件
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(response)


def generate_interview_questions(resume_json):
    template = """
    {
        questions: [
            "问题1",
            "问题2",
            "问题3"
        ],
    }
    """
    messages = [
        {
            "role": "user",
            "content": f"""
                请根据用户的简历生成面试题，要求如下：
                1. 每个问题必须针对简历中的具体内容
                2. 生成的问题数量不超过10个
                3. 根据用户面试的岗位标准
                以JSON格式返回，按照以下JSON模板返回：{template}
                简历内容：
                {resume_json}
            """
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages)
    return validate_and_clean_json(response)


def generate_questions_audio(questions_list):
    tts = TTS(output_dir="assets/audio")
    questions_audio_list = []
    for item in questions_list:
        questions_audio_list.append(tts.generate_audio(engineid="short_audio_synthesis_jovi", vcn="yige", text=item))
    return questions_audio_list


# 面试结果
def interview_result(interview_result_format, resume_json, answers_result):
    system_prompt = f"""
            你是一个专业的面试分析专家，请严格按照以下要求评价所提供的面试结果，我只能提供求职者的文本信息，你只需要关注文本回答就好：
            1. 基于用户提供的简历内容
            3. 总评要求：
               - 简明扼要（150字内）
               - 包含优势和改进建议，每一个建议针对到简历中的具体部分中
            4. 输出要求：
               - 严格使用指定JSON格式
               - 直接输出有效JSON代码
               - 禁止任何注释或说明
            5. JSON格式模板如下，其中你需要补充的简历诊断内容必须必须做到详细、具体、专业：
            {interview_result_format}
        """
    messages = [
        {
            "role": "user",
            "content": f"简历内容如下:"
                       f"{resume_json}"
        },
        {
            "role": "user",
            "content": f"面试结果如下:"
                       f"{answers_result}"
        }
    ]
    text_generation = TextGeneration()
    response = text_generation.blue_llm_70B(messages, system_prompt=system_prompt, temperature=1.0)
    return validate_and_clean_json(response)


def audio2text(audio_path):
    client = LASRClient()
    result = client.transcribe(audio_path)

    results = result["data"]["result"]

    # 结果处理
    final_text = []
    last_end = 0

    # 按时间戳排序（虽然服务端应该已经有序）
    sorted_results = sorted(results, key=lambda x: x["bg"])

    for segment in sorted_results:
        # 校验必要字段
        if "onebest" not in segment or "bg" not in segment or "ed" not in segment:
            raise ValueError("Invalid segment format")

        # 时间戳校验（可选）
        if segment["bg"] < last_end:
            print(f"Warning: Overlapping timestamps at {segment['bg']}")

        last_end = segment["ed"]

        # 拼接文本
        final_text.append(segment["onebest"].strip())

    # 处理结尾标点（根据需求可选）
    return " ".join(final_text).replace("。", "。 ")  # 添加空格分隔句号

if __name__ == "__main__":
    print(audio2text("../assets/audio/面试问题3.m4a"))