from util.file_loader import load_file
from util.llm import image_to_text, format_resume


def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()


def get_format_resume(resume_path):
    content_list = load_file(resume_path)
    # 将content_list读取为json，并将每一项的内容进行拼接
    content= ""
    for item in content_list:
        if item["type"] == "text":
            content += item["content"]
        else:
            text = image_to_text(item["content"])
            content += text

    resume_format = read_txt('assets/txt/resume_format.txt')
    response_content = format_resume(resume_format, content)

    return response_content