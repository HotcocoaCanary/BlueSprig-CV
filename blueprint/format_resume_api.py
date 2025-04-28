import json
import os
import uuid

from flask import Blueprint, request, jsonify

from service.resume_service import get_format_resume

format_resume_bp = Blueprint('format_resume', __name__)


@format_resume_bp.route('/format_resume', methods=['POST'])
def format_resume_docs():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400
    file = request.files['file']

    # 定义合法的文件扩展名集合
    valid_extensions = {'.doc', '.docx', '.pdf'}

    # 获取文件扩展名
    _, file_extension = os.path.splitext(file.filename)

    # 检查文件是否合法
    if file_extension.lower() not in valid_extensions:
        return jsonify({'error': '文件上传格式不符'}), 400

    # 生成唯一的文件名
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"

    # 定义保存路径
    save_path = os.path.join('assets', 'docs' if file_extension.lower() in ['.doc', '.docx'] else 'pdf',
                             unique_filename)

    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 保存文件
    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({'error': '保存文件错误', 'details': str(e)}), 500

    result = get_format_resume(save_path)
    # 将result以json形式返回
    if result:
        result_json = json.loads(result)
        return jsonify(result_json), 200
    else:
        return jsonify({'error': '请求错误'}), 500
