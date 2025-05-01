import json
# 工具方法
from util.file_loader import load_file
from util.llm import format_resume, llm_chat


# 定义一个函数，用于读取txt文件
def read_txt(file_path):
    # 打开文件，以只读模式，编码格式为utf-8
    with open(file_path, 'r', encoding='utf-8') as file:
        # 读取文件内容，并去除首尾空格
        return file.read().strip()


# 读取简历文件
resume_path = 'assets/pdf/1.pdf'
content = load_file(resume_path)

# 获取标准解析简历json格式
resume_format = read_txt('assets/txt/resume_format.txt')
response_content = format_resume(resume_format, content)

# ### 3. 根据规范化简历json，生成当前简历各个模块的评分，优化后的版本以及优化建议，提供多轮对话，可以按照用户的想法继续优化

# #### 3.1. 简历优化版本

# 简历json数据
resume_json = json.loads(response_content)

from util.llm import better_resume_by_module

work_experience_content = resume_json["work_experience"]
education_experience_content = resume_json["education_experience"]
project_experience_content = resume_json["project_experience"]

work_experience_format = read_txt("assets/txt/greater_resume_module/work_experience.txt")
education_experience_format = read_txt("assets/txt/greater_resume_module/education_experience.txt")
project_experience_format = read_txt("assets/txt/greater_resume_module/project_experience.txt")

work = better_resume_by_module(work_experience_format, work_experience_content, "工作经历")
education = better_resume_by_module(education_experience_format, education_experience_content, "教育经历")
project = better_resume_by_module(project_experience_format, project_experience_content, "项目经历")

project = json.loads(project)
work = json.loads(work)
education = json.loads(education)

resume_json["project_experience"] = project
resume_json["work_experience"] = work
resume_json["education_experience"] = education

# #### 3.2. 简历优化对话

# 获取原始简历
resume_json_old = json.loads(response_content)

# 获取优化后的简历
resume_json_new = resume_json

# 简历信息输出以及优化对话窗口
BETTER_RESUME_MOD_LIST = ["work_experience", "education_experience", "project_experience"]

# 遍历resume_json_old中的每个键值对
for key, value in resume_json_old.items():
    # 如果键不在BETTER_RESUME_MOD_LIST中，直接输出
    if key not in BETTER_RESUME_MOD_LIST:
        print(f"{key}模块信息如下：")
        print(f"{value}")
        print("#######################################################")
    # 如果键在BETTER_RESUME_MOD_LIST中，输出old原有的值
    else:
        print(f"{key}模块信息如下：")
        print(f"{value}")
        print(
            f"{key}模块初步优化后的结果如下，如果有问题或者建议可以直接指正，没有请输入“没有问题”，我们将进行下一个模块的优化")
        print(f"{key} (new): {resume_json_new[key]}")
        a = input()
        while a != "没有问题":
            format_content = read_txt("assets/txt/greater_resume_module/" + key + ".txt")
            message = [{
                "role": "user",
                "content": f"{a}"
                           f"当前内容{resume_json_old[key]}"
                           f"你的输出格式要求：必须严格保持原有的JSON格式。"
            }]
            better_part_content = llm_chat(message)
            print(f"按照你的要求，优化后的结果如下，如果有问题或者建议可以直接指正，我将会按照你的要求重新优化" + better_part_content)
            a = input()
        print("#######################################################")
