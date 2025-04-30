import os
import uuid
from docx import Document
import fitz  # PyMuPDF

from util.llm import image_to_text


def load_file(file_path: str, image_output_dir: str = "assets/image") -> list:
    content_list = _get_file_list(file_path, image_output_dir)
    # 将content_list读取为json，并将每一项的内容进行拼接
    content = ""
    for item in content_list:
        if item["type"] == "text":
            content += item["content"] + """。
            
            
            """+"\n\n"
        else:
            text = image_to_text(item["content"])
            content += text  + """。
            
            
            """+"\n\n"

    return content


def _get_file_list(file_path: str, image_output_dir: str = "assets/image") -> list:
    """
    加载文件并提取内容和图片
    :param file_path: 文件路径（支持.docx和.pdf）
    :param image_output_dir: 图片保存目录
    :return: 包含文件内容的数组
    """
    # 创建图片保存目录
    if not os.path.exists(image_output_dir):
        os.makedirs(image_output_dir)

    if file_path.lower().endswith('.docx'):
        return _process_word(file_path, image_output_dir)
    elif file_path.lower().endswith('.pdf'):
        return _process_pdf(file_path, image_output_dir)
    else:
        raise ValueError("Unsupported file format")


def _process_word(file_path: str, image_dir: str) -> list:
    """处理Word文档"""
    doc = Document(file_path)
    result = []
    position = 0
    img_counter = 1

    for para in doc.paragraphs:
        current_text = ""
        for run in para.runs:
            # 检查是否存在图片
            if 'graphic' in run._element.xml:
                # 提取图片
                for shape in run.element.xpath('.//pic:pic'):
                    blip = shape.xpath('.//a:blip/@r:embed')[0]
                    image_part = doc.part.related_parts[blip]
                    image_data = image_part.blob

                    # 生成唯一文件名
                    ext = image_part.content_type.split('/')[-1]
                    filename = f"word_img_{img_counter}_{uuid.uuid4().hex[:6]}.{ext}"
                    img_path = os.path.join(image_dir, filename)

                    # 保存图片
                    with open(img_path, 'wb') as f:
                        f.write(image_data)

                    # 如果有暂存文本先保存
                    if current_text:
                        result.append({
                            "position": position,
                            "type": "text",
                            "content": current_text
                        })
                        position += 1
                        current_text = ""

                    # 添加图片记录
                    result.append({
                        "position": position,
                        "type": "image",
                        "content": img_path
                    })
                    position += 1
                    img_counter += 1

            # 收集文本内容
            current_text += run.text

        # 保存段落文本
        if current_text.strip():
            result.append({
                "position": position,
                "type": "text",
                "content": current_text.strip()
            })
            position += 1

    return result


def _process_pdf(file_path: str, image_dir: str) -> list:
    """处理PDF文档"""
    doc = fitz.open(file_path)
    result = []
    position = 0
    img_counter = 1

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # 按顺序处理页面元素
        blocks = page.get_text("dict", sort=True)["blocks"]

        for block in blocks:
            if block["type"] == 0:  # 文本块
                text = "\n".join(["".join(span["text"] for span in line["spans"])
                                  for line in block["lines"]])
                if text.strip():
                    result.append({
                        "position": position,
                        "type": "text",
                        "content": text.strip()
                    })
                    position += 1
            elif block["type"] == 1:  # 图片块
                if 'xref' in block:
                    try:
                        img = doc.extract_image(block["xref"])
                        if img:
                            # 生成唯一文件名
                            ext = img["ext"]
                            filename = f"pdf_img_{img_counter}_{uuid.uuid4().hex[:6]}.{ext}"
                            img_path = os.path.join(image_dir, filename)

                            # 保存图片
                            with open(img_path, 'wb') as f:
                                f.write(img["image"])

                            # 添加图片记录
                            result.append({
                                "position": position,
                                "type": "image",
                                "content": img_path
                            })
                            position += 1
                            img_counter += 1
                    except Exception as e:
                        print(f"Error extracting image: {e}")

    return result
