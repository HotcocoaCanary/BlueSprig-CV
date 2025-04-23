import json
import os

from flask import Blueprint, request, jsonify

from service.resume_service import get_format_resume

format_resume_bp = Blueprint('format_resume', __name__)


@format_resume_bp.route('/format_resume', methods=['POST'])
def format_resume_docs():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    # 检查文件是否合法
    if file:
        # 获取文件扩展名
        _, file_extension = os.path.splitext(file.filename)
        # 定义保存路径
        if file_extension.lower() in ['.doc', '.docx']:
            save_path = os.path.join('assets', 'docs', file.filename)
        elif file_extension.lower() in ['.pdf']:
            save_path = os.path.join('assets', 'pdf', file.filename)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # 保存文件
        file.save(save_path)
        result = get_format_resume(save_path)
        # 将result以json形式返回
        if result:
            result_json = json.loads(result)
            return jsonify(result_json), 200
        else:
            return jsonify({'error': 'Failed to format resume'}), 500
    return jsonify({'error': 'Something went wrong'}), 500

