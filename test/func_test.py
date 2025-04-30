# 工具方法
import json

from util.file_loader import load_file
from util.llm import format_resume, better_resume_by_module


# 定义一个函数，用于读取txt文件
def read_txt(file_path):
    # 打开文件，以只读模式，编码格式为utf-8
    with open(file_path, 'r', encoding='utf-8') as file:
        # 读取文件内容，并去除首尾空格
        return file.read().strip()


resume_path = '../assets/pdf/2.pdf'
content = load_file(resume_path, "../assets/image")
resume_format = read_txt('../assets/txt/resume_format.txt')
response_content = format_resume(resume_format, content)

resume_json = json.loads(response_content)

abc = resume_json["project_experience"]
gh = resume_json["work_experience"]
g = resume_json["education_experience"]

work_experience = read_txt("../assets/txt/greater_resume_module/work_experience.txt")
education_experience = read_txt("../assets/txt/greater_resume_module/education_experience.txt")
project_experience = read_txt("../assets/txt/greater_resume_module/project_experience.txt")

if __name__ == '__main__':
    a = better_resume_by_module(work_experience, gh, "工作经历")
    b = better_resume_by_module(education_experience, g, "教育经历")
    c = better_resume_by_module(project_experience, abc, "项目经历")

    c = json.loads(c)
    a = json.loads(a)
    b = json.loads(b)

    resume_json["project_experience"] = c["project_experience"]
    resume_json["work_experience"] = a["work_experience"]
    resume_json["education_experience"] = b["education_experience"]

    print(resume_json)
