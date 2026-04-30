#!/usr/bin/env python3
"""APK签名服务 - 局域网可访问的APK签名网页"""

import json
import os
import sys
import zipfile
import subprocess
import tempfile
import shutil
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import threading
from datetime import datetime

# 配置
CONFIG_FILE = "config.json"
HOST = "0.0.0.0"
DEFAULT_PORT = 8080
MAX_PORT_ATTEMPTS = 10

# 全局变量
CONFIG = {}
TEMP_DIR = tempfile.mkdtemp(prefix="apk_signer_")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    """加载JSON配置文件"""
    global CONFIG
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"配置文件 {CONFIG_FILE} 不存在")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
    return CONFIG

def get_template_html():
    """返回HTML模板"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APK 签名工具</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 28px;
            margin-bottom: 8px;
        }
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        .content {
            padding: 30px;
        }
        .form-group {
            margin-bottom: 24px;
        }
        label {
            display: block;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .required::after {
            content: " *";
            color: #e74c3c;
        }
        select, input[type="text"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 15px;
            transition: all 0.3s;
            background: white;
        }
        select:focus, input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .file-upload {
            border: 2px dashed #ddd;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #fafafa;
        }
        .file-upload:hover {
            border-color: #667eea;
            background: #f0f0ff;
        }
        .file-upload.dragover {
            border-color: #667eea;
            background: #e8e8ff;
        }
        .file-upload input {
            display: none;
        }
        .file-upload-icon {
            font-size: 48px;
            color: #667eea;
            margin-bottom: 10px;
        }
        .file-upload-text {
            color: #666;
            font-size: 14px;
        }
        .file-upload-text strong {
            color: #667eea;
        }
        .file-info {
            margin-top: 10px;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 8px;
            display: none;
        }
        .file-info.show {
            display: block;
        }
        .file-info .filename {
            font-weight: 600;
            color: #2e7d32;
            word-break: break-all;
        }
        .file-info .filesize {
            color: #666;
            font-size: 13px;
            margin-top: 4px;
        }
        .btn-sign {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .btn-sign:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        .btn-sign:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .btn-sign .spinner {
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            display: none;
        }
        .btn-sign.loading .spinner {
            display: block;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .alert {
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
            font-size: 14px;
        }
        .alert.show {
            display: block;
        }
        .alert-error {
            background: #ffebee;
            color: #c62828;
            border-left: 4px solid #e53935;
        }
        .alert-success {
            background: #e8f5e9;
            color: #2e7d32;
            border-left: 4px solid #4caf50;
        }
        .alert-info {
            background: #e3f2fd;
            color: #1565c0;
            border-left: 4px solid #2196f3;
        }
        .progress-container {
            margin-top: 20px;
            display: none;
        }
        .progress-container.show {
            display: block;
        }
        .progress-bar {
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
        }
        .progress-text {
            margin-top: 8px;
            font-size: 13px;
            color: #666;
            text-align: center;
        }
        .config-info {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 13px;
        }
        .config-info .item {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .config-info .item:last-child {
            border-bottom: none;
        }
        .config-info .key {
            color: #666;
        }
        .config-info .value {
            color: #333;
            font-weight: 500;
            word-break: break-all;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>APK 签名工具</h1>
            <p>快速为 APK 文件签名，支持多种配置</p>
        </div>
        <div class="content">
            <div class="alert alert-error" id="alertError"></div>
            <div class="alert alert-success" id="alertSuccess"></div>
            <div class="alert alert-info" id="alertInfo"></div>

            <div class="config-info" id="configInfo">
                <div class="item"><span class="key">配置加载中...</span></div>
            </div>

            <form id="signForm">
                <div class="form-group">
                    <label class="required">选择 Android 版本</label>
                    <select id="androidVersion" name="androidVersion" required>
                        <option value="">-- 请选择 Android 版本 --</option>
                    </select>
                </div>

                <div class="form-group">
                    <label class="required">选择签名目标</label>
                    <select id="signTarget" name="signTarget" required>
                        <option value="">-- 请选择签名目标 --</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>签名配置详情</label>
                    <div id="signConfig" style="background:#f5f5f5;padding:12px;border-radius:8px;font-size:13px;color:#666;">
                        选择配置后显示详情
                    </div>
                </div>

                <div class="form-group">
                    <label class="required">上传 APK 文件</label>
                    <div class="file-upload" id="fileUpload">
                        <input type="file" id="apkFile" name="apkFile" accept=".apk">
                        <div class="file-upload-icon">📦</div>
                        <div class="file-upload-text">
                            <strong>点击上传</strong> 或拖拽 APK 文件到此处
                        </div>
                        <div class="file-info" id="fileInfo">
                            <div class="filename" id="fileName"></div>
                            <div class="filesize" id="fileSize"></div>
                        </div>
                    </div>
                </div>

                <div class="progress-container" id="progressContainer">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">准备中...</div>
                </div>

                <button type="submit" class="btn-sign" id="btnSign">
                    <span class="spinner"></span>
                    <span class="btn-text">开始签名</span>
                </button>
            </form>
        </div>
        <div class="footer">
            APK Signer Tool · 局域网签名服务
        </div>
    </div>

    <script>
        let configData = {};
        let selectedFile = null;

        // 显示提示
        function showAlert(type, message) {
            document.querySelectorAll('.alert').forEach(a => a.classList.remove('show'));
            const alert = document.getElementById('alert' + type.charAt(0).toUpperCase() + type.slice(1));
            alert.textContent = message;
            alert.classList.add('show');
            setTimeout(() => alert.classList.remove('show'), 5000);
        }

        // 格式化文件大小
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
        }

        // 加载配置
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                if (!response.ok) throw new Error('获取配置失败');
                configData = await response.json();

                // 更新配置信息
                document.getElementById('configInfo').innerHTML = Object.entries(configData).map(([key, value]) =>
                    '<div class="item"><span class="key">' + key + '</span><span class="value">' + value + '</span></div>'
                ).join('');

                // 填充下拉框
                const androidSelect = document.getElementById('androidVersion');
                configData.androidVersions.forEach(version => {
                    const option = document.createElement('option');
                    option.value = version;
                    option.textContent = version;
                    androidSelect.appendChild(option);
                });

                const targetSelect = document.getElementById('signTarget');
                Object.keys(configData.signTargets).forEach(target => {
                    const option = document.createElement('option');
                    option.value = target;
                    option.textContent = target;
                    targetSelect.appendChild(option);
                });

                showAlert('info', '配置加载成功');
            } catch (error) {
                showAlert('error', '加载配置失败: ' + error.message);
            }
        }

        // 更新签名配置显示
        function updateSignConfig() {
            const target = document.getElementById('signTarget').value;
            const androidVersion = document.getElementById('androidVersion').value;

            if (!target || !androidVersion) {
                document.getElementById('signConfig').innerHTML = '请先选择 Android 版本和签名目标';
                return;
            }

            const config = configData.signTargets[target];
            if (config && config[androidVersion]) {
                const c = config[androidVersion];
                document.getElementById('signConfig').innerHTML = `
                    <div style="margin-bottom:8px;"><strong>目标:</strong> ${target}</div>
                    <div style="margin-bottom:8px;"><strong>Android版本:</strong> ${androidVersion}</div>
                    <div><strong>签名文件:</strong></div>
                    <div style="margin-left:10px;word-break:break-all;">x509: ${c.platform_x509 || '未配置'}</div>
                    <div style="margin-left:10px;word-break:break-all;">pk8: ${c.platform_pk8 || '未配置'}</div>
                `;
            } else {
                document.getElementById('signConfig').innerHTML = '<span style="color:#e74c3c;">该组合没有对应的签名配置</span>';
            }
        }

        // 文件上传处理
        const fileUpload = document.getElementById('fileUpload');
        const apkFileInput = document.getElementById('apkFile');

        fileUpload.addEventListener('click', () => apkFileInput.click());

        fileUpload.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUpload.classList.add('dragover');
        });

        fileUpload.addEventListener('dragleave', () => {
            fileUpload.classList.remove('dragover');
        });

        fileUpload.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUpload.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });

        apkFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });

        function handleFile(file) {
            if (!file.name.toLowerCase().endsWith('.apk')) {
                showAlert('error', '请选择 APK 文件！');
                return;
            }
            selectedFile = file;
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('fileSize').textContent = formatFileSize(file.size);
            document.getElementById('fileInfo').classList.add('show');
        }

        // 更新进度
        function updateProgress(percent, text) {
            document.getElementById('progressFill').style.width = percent + '%';
            document.getElementById('progressText').textContent = text;
        }

        // 提交签名
        document.getElementById('signForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const androidVersion = document.getElementById('androidVersion').value;
            const signTarget = document.getElementById('signTarget').value;

            if (!androidVersion || !signTarget) {
                showAlert('error', '请选择 Android 版本和签名目标');
                return;
            }

            if (!selectedFile) {
                showAlert('error', '请上传 APK 文件');
                return;
            }

            const btn = document.getElementById('btnSign');
            const progressContainer = document.getElementById('progressContainer');

            btn.disabled = true;
            btn.classList.add('loading');
            btn.querySelector('.btn-text').textContent = '签名中...';
            progressContainer.classList.add('show');
            updateProgress(10, '正在上传文件...');

            const formData = new FormData();
            formData.append('apkFile', selectedFile);
            formData.append('androidVersion', androidVersion);
            formData.append('signTarget', signTarget);

            try {
                updateProgress(30, '服务器正在处理...');

                const response = await fetch('/api/sign', {
                    method: 'POST',
                    body: formData
                });

                updateProgress(80, '处理完成，准备下载...');

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.message || '签名失败');
                }

                // 获取文件名
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'signed.apk';
                if (contentDisposition) {
                    const match = contentDisposition.match(/filename[^;=\\n]*=((['"]).*?\\2|[^;\\n]*)/);
                    if (match) filename = match[1].replace(/['"]/g, '');
                }

                // 下载文件
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();

                updateProgress(100, '签名完成！');
                showAlert('success', 'APK 签名成功！文件已自动下载。');

                setTimeout(() => {
                    progressContainer.classList.remove('show');
                }, 2000);

            } catch (error) {
                showAlert('error', '签名失败: ' + error.message);
                progressContainer.classList.remove('show');
            } finally {
                btn.disabled = false;
                btn.classList.remove('loading');
                btn.querySelector('.btn-text').textContent = '开始签名';
            }
        });

        // 事件监听
        document.getElementById('androidVersion').addEventListener('change', updateSignConfig);
        document.getElementById('signTarget').addEventListener('change', updateSignConfig);

        // 初始化
        loadConfig();
    </script>
</body>
</html>'''

def find_apksigner():
    """
    查找 apksigner 工具
    返回 (命令前缀, jar路径) 或 单个命令字符串
    """
    import glob

    print(f"[DEBUG] 脚本目录: {SCRIPT_DIR}")
    print(f"[DEBUG] 操作系统: {os.name} ({'Windows' if os.name == 'nt' else 'Unix'})")

    # 1. 直接在 PATH 中查找 apksigner 命令
    if shutil.which('apksigner'):
        print("[DEBUG] 在 PATH 中找到 apksigner")
        return 'apksigner'
    if os.name == 'nt':
        for ext in ['', '.bat', '.cmd', '.exe']:
            path = shutil.which('apksigner' + ext)
            if path:
                print(f"[DEBUG] 在 PATH 中找到 apksigner{ext}: {path}")
                return 'apksigner' + ext

    # 2. 查找脚本同目录下的 build-tools
    script_build_tools = os.path.join(SCRIPT_DIR, 'build-tools')
    print(f"[DEBUG] 查找 build-tools: {script_build_tools}")

    if os.path.isdir(script_build_tools):
        print(f"[DEBUG] build-tools 目录存在，版本: {os.listdir(script_build_tools)}")
        # 遍历 build-tools 下的每个版本目录
        for version_dir in os.listdir(script_build_tools):
            version_path = os.path.join(script_build_tools, version_dir)
            print(f"[DEBUG] 检查版本目录: {version_path}")
            if os.path.isdir(version_path):
                # Windows: 优先用 java -jar (原生 apksigner 是 Linux 二进制，Windows 无法直接运行)
                if os.name == 'nt':
                    # 检查 java 是否可用
                    java_path = shutil.which('java')
                    print(f"[DEBUG] java 路径: {java_path}")
                    jar_path = os.path.join(version_path, 'lib', 'apksigner.jar')
                    print(f"[DEBUG] 检查 JAR: {jar_path}, 存在: {os.path.exists(jar_path)}")
                    if java_path and os.path.exists(jar_path):
                        print(f"[DEBUG] 使用 java -jar: {jar_path}")
                        return ('java -jar', jar_path)
                    # 再尝试找 .bat 或 .cmd
                    for name in ['apksigner.bat', 'apksigner.cmd', 'apksigner.exe', 'apksigner']:
                        apksigner_path = os.path.join(version_path, name)
                        print(f"[DEBUG] 检查文件: {apksigner_path}, 存在: {os.path.exists(apksigner_path)}")
                        if os.path.exists(apksigner_path):
                            print(f"[DEBUG] 找到 apksigner: {apksigner_path}")
                            return apksigner_path
                else:
                    # Linux/Mac: 查找 apksigner
                    apksigner_path = os.path.join(version_path, 'apksigner')
                    if os.path.exists(apksigner_path):
                        print(f"[DEBUG] 找到 apksigner: {apksigner_path}")
                        return apksigner_path
    else:
        print(f"[DEBUG] build-tools 目录不存在")

    # 3. 常见系统路径
    common_paths = []
    if os.name == 'nt':
        common_paths.extend([
            os.path.expanduser('~\\Android\\Sdk\\build-tools\\*\\apksigner.bat'),
            os.path.expanduser('~\\Android\\Sdk\\build-tools\\*\\apksigner.cmd'),
            'C:\\Android\\build-tools\\*\\apksigner.bat',
        ])
    else:
        common_paths.extend([
            '/usr/bin/apksigner',
            '/usr/local/bin/apksigner',
            os.path.expanduser('~/Android/Sdk/build-tools/*/apksigner'),
            '/opt/android-sdk/build-tools/*/apksigner'
        ])

    print(f"[DEBUG] 检查常见路径: {common_paths}")
    for p in common_paths:
        if '*' in p or '?' in p:
            matches = glob.glob(p)
            print(f"[DEBUG] glob {p}: {matches}")
            if matches:
                return matches[-1]
        elif os.path.exists(p):
            print(f"[DEBUG] 找到: {p}")
            return p

    print("[DEBUG] 未找到 apksigner")
    return None

def sign_apk(apk_path, x509_path, pk8_path, output_path):
    """
    使用 apksigner 对 APK 进行签名
    """
    print(f"[DEBUG] 签名请求:")
    print(f"  APK: {apk_path}")
    print(f"  x509: {x509_path}")
    print(f"  pk8: {pk8_path}")
    print(f"  output: {output_path}")

    apksigner = find_apksigner()
    if not apksigner:
        raise Exception("未找到 apksigner，请将 build-tools 复制到脚本目录下")

    print(f"[DEBUG] 使用 apksigner: {apksigner}")

    # 如果返回的是 (前缀, jar路径) 元组，说明需要用 java -jar 运行
    if isinstance(apksigner, tuple):
        cmd_prefix, jar_path = apksigner
        cmd = f'{cmd_prefix} "{jar_path}" sign --key "{pk8_path}" --cert "{x509_path}" --out "{output_path}" --v2-signing-enabled true --v3-signing-enabled true "{apk_path}"'
        print(f"[DEBUG] 执行命令: {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    else:
        cmd = [
            apksigner,
            'sign',
            '--key', pk8_path,
            '--cert', x509_path,
            '--out', output_path,
            '--v2-signing-enabled', 'true',
            '--v3-signing-enabled', 'true',
            apk_path
        ]
        print(f"[DEBUG] 执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

    print(f"[DEBUG] 返回码: {result.returncode}")
    print(f"[DEBUG] stdout: {result.stdout}")
    print(f"[DEBUG] stderr: {result.stderr}")

    if result.returncode != 0:
        error_msg = result.stderr if result.stderr else result.stdout
        raise Exception(f"签名失败: {error_msg}")
    return True

def get_available_signing_tools():
    """检测可用的签名工具"""
    tools = []

    # 检查 apksigner (使用完整查找逻辑)
    apksigner = find_apksigner()
    if apksigner:
        tools.append('apksigner')

    # 检查 jarsigner
    if shutil.which('jarsigner'):
        tools.append('jarsigner')

    return tools

class APKHandler(SimpleHTTPRequestHandler):
    """处理APK签名请求"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=TEMP_DIR, **kwargs)

    def send_error_response(self, code, message):
        """发送错误响应（支持中文）"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        import json
        response = json.dumps({'error': message}, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))

    def do_GET(self):
        """处理GET请求"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(get_template_html().encode('utf-8'))
        elif self.path == '/api/config':
            self.handle_config()
        else:
            super().do_GET()

    def handle_config(self):
        """返回配置信息"""
        try:
            config = load_config()
            response = {
                'androidVersions': list(set(item['androidVersion'] for item in config.get('targets', []))),
                'signTargets': {}
            }

            for item in config.get('targets', []):
                target = item['signTarget']
                android_version = item['androidVersion']
                if target not in response['signTargets']:
                    response['signTargets'][target] = {}
                response['signTargets'][target][android_version] = {
                    'platform_x509': item.get('platform_x509', ''),
                    'platform_pk8': item.get('platform_pk8', '')
                }

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))

    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/sign':
            self.handle_sign()
        else:
            self.send_error_response(404, 'API not found')

    def handle_sign(self):
        """处理签名请求"""
        print(f"[DEBUG] 收到签名请求")
        try:
            # 解析multipart数据
            content_type = self.headers.get('Content-Type', '')
            print(f"[DEBUG] Content-Type: {content_type}")
            if 'multipart/form-data' not in content_type:
                self.send_error_response(400, '需要 multipart/form-data')
                return

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            print(f"[DEBUG] Content-Length: {content_length}")
            body = self.rfile.read(content_length)
            print(f"[DEBUG] 读取到 {len(body)} 字节")

            # 解析表单数据
            boundary = content_type.split('boundary=')[1] if 'boundary=' in content_type else None
            if not boundary:
                self.send_error_response(400, '无法解析表单边界')
                return

            # 去除可能的引号
            boundary = boundary.strip('"\'')
            print(f"[DEBUG] Boundary: {boundary}")

            # 手动解析 multipart
            import re

            # 分割各部分
            boundary_bytes = ('--' + boundary).encode()
            parts = body.split(boundary_bytes)

            print(f"[DEBUG] 分割为 {len(parts)} 个部分")

            form_data = {}
            apk_data = None

            for part in parts:
                if not part or part.strip() in (b'', b'--', b'--\r\n'):
                    continue

                # 分离 header 和 content
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    continue

                header_part = part[:header_end]
                content_part = part[header_end + 4:]

                # 解析 header
                headers = {}
                for line in header_part.decode('utf-8', errors='ignore').split('\r\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        headers[key.strip().lower()] = value.strip()

                content_disposition = headers.get('content-disposition', '')
                if not content_disposition:
                    continue

                # 提取 name 和 filename
                name_match = re.search(r'name="([^"]+)"', content_disposition)
                filename_match = re.search(r'filename="([^"]+)"', content_disposition)

                if not name_match:
                    continue

                name = name_match.group(1)
                filename = filename_match.group(1) if filename_match else None

                print(f"[DEBUG] 字段: name={name}, filename={filename}")

                if name == 'apkFile' and filename:
                    # 去除末尾的 \r\n--
                    if content_part.endswith(b'\r\n'):
                        content_part = content_part[:-2]
                    apk_data = content_part
                    print(f"[DEBUG] APK文件: {filename}, 大小: {len(apk_data) if apk_data else 0}")
                else:
                    # 去除末尾的 \r\n
                    if content_part.endswith(b'\r\n'):
                        content_part = content_part[:-2]
                    try:
                        form_data[name] = content_part.decode('utf-8')
                        print(f"[DEBUG] 文本字段 {name}: {form_data[name][:50]}...")
                    except:
                        pass

            print(f"[DEBUG] form_data: {form_data}")
            print(f"[DEBUG] apk_data 长度: {len(apk_data) if apk_data else 0}")

            android_version = form_data.get('androidVersion', '')
            sign_target = form_data.get('signTarget', '')

            if not android_version or not sign_target:
                print(f"[DEBUG] 缺少参数: androidVersion={android_version}, signTarget={sign_target}")
                self.send_error_response(400, '缺少必要参数')
                return

            if not apk_data:
                print(f"[DEBUG] 没有APK数据")
                self.send_error_response(400, '未找到APK文件')
                return

            # 查找配置
            print(f"[DEBUG] 加载配置查找: {android_version} - {sign_target}")
            config = load_config()
            target_config = None
            for item in config.get('targets', []):
                if item['androidVersion'] == android_version and item['signTarget'] == sign_target:
                    target_config = item
                    break

            if not target_config:
                print(f"[DEBUG] 未找到配置")
                self.send_error_response(400, f'未找到配置: {android_version} - {sign_target}')
                return

            x509_path = target_config.get('platform_x509', '')
            pk8_path = target_config.get('platform_pk8', '')

            if not x509_path or not pk8_path:
                print(f"[DEBUG] 签名路径未配置")
                self.send_error_response(400, '签名配置文件路径未配置')
                return

            # 解析路径（支持相对路径）
            x509_path = resolve_path(x509_path)
            pk8_path = resolve_path(pk8_path)

            print(f"[DEBUG] x509_path: {x509_path}")
            print(f"[DEBUG] pk8_path: {pk8_path}")

            # 验证签名文件存在
            if not os.path.exists(x509_path):
                print(f"[DEBUG] x509文件不存在")
                self.send_error_response(400, f'证书文件不存在: {x509_path}')
                return
            if not os.path.exists(pk8_path):
                print(f"[DEBUG] pk8文件不存在")
                self.send_error_response(400, f'密钥文件不存在: {pk8_path}')
                return

            # 保存上传的APK
            print(f"[DEBUG] 保存APK文件...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            input_apk = os.path.join(TEMP_DIR, f'input_{timestamp}.apk')
            output_apk = os.path.join(TEMP_DIR, f'signed_{timestamp}_{sign_target}.apk')
            print(f"[DEBUG] input_apk: {input_apk}")
            print(f"[DEBUG] output_apk: {output_apk}")

            with open(input_apk, 'wb') as f:
                f.write(apk_data)
            print(f"[DEBUG] APK已保存，大小: {len(apk_data)} bytes")

            # 验证 APK 是否完整
            import zipfile
            try:
                with zipfile.ZipFile(input_apk, 'r') as zf:
                    namelist = zf.namelist()
                    print(f"[DEBUG] APK 包含 {len(namelist)} 个文件")
                    if 'AndroidManifest.xml' not in namelist:
                        print(f"[ERROR] APK 缺少 AndroidManifest.xml")
                        self.send_error_response(400, f'APK 文件不完整或已损坏，缺少 AndroidManifest.xml')
                        os.remove(input_apk)
                        return
                    print(f"[DEBUG] APK 验证通过")
            except zipfile.BadZipFile:
                print(f"[ERROR] APK 不是有效的 ZIP 文件")
                self.send_error_response(400, 'APK 文件已损坏，不是有效的 APK')
                os.remove(input_apk)
                return

            # 执行签名
            print(f"[DEBUG] 开始执行签名...")
            sign_apk(input_apk, x509_path, pk8_path, output_apk)
            print(f"[DEBUG] 签名完成")

            # 读取签名后的APK
            print(f"[DEBUG] 读取签名后的APK: {output_apk}")
            if not os.path.exists(output_apk):
                print(f"[ERROR] 签名输出文件不存在!")
                self.send_error_response(500, '签名失败：输出文件未生成')
                return
            with open(output_apk, 'rb') as f:
                signed_data = f.read()
            print(f"[DEBUG] 签名后APK大小: {len(signed_data)} bytes")

            # 清理临时文件
            try:
                os.remove(input_apk)
                os.remove(output_apk)
            except:
                pass

            # 发送响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            # 如果签名目标包含中文，使用时间戳作为文件名
            import re
            if re.search(r'[一-鿿]', sign_target):
                safe_filename = f'signed_{timestamp}.apk'
            else:
                safe_filename = f'signed_{sign_target}.apk'
            self.send_header('Content-Disposition', f'attachment; filename="{safe_filename}"')
            self.send_header('Content-Length', len(signed_data))
            self.end_headers()
            self.wfile.write(signed_data)

        except Exception as e:
            import traceback
            print(f"[ERROR] 签名过程出错: {e}")
            traceback.print_exc()
            self.send_error_response(500, str(e))

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")

def get_local_ip():
    """获取本机局域网IP"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def resolve_path(path):
    """
    解析文件路径，支持绝对路径和相对于脚本目录的相对路径
    """
    if os.path.isabs(path):
        return path
    # 相对于脚本目录
    return os.path.normpath(os.path.join(SCRIPT_DIR, path))

def find_available_port(start_port, max_attempts=10):
    """查找可用端口"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, port))
            s.close()
            return port
        except OSError:
            continue
    return None

def main():
    print("=" * 50)
    print("       APK 签名工具 Web 服务")
    print("=" * 50)

    # 加载配置
    try:
        config = load_config()
        print(f"\n[OK] 配置文件加载成功: {CONFIG_FILE}")
        print(f"    - Android 版本数: {len(set(t['androidVersion'] for t in config.get('targets', [])))}")
        print(f"    - 签名目标数: {len(set(t['signTarget'] for t in config.get('targets', [])))}")
    except Exception as e:
        print(f"\n[ERROR] 配置加载失败: {e}")
        print(f"    请创建 {CONFIG_FILE} 配置文件")
        sys.exit(1)

    # 检查签名工具
    tools = get_available_signing_tools()
    if tools:
        print(f"[OK] 可用的签名工具: {', '.join(tools)}")
    else:
        print("[WARNING] 未找到 apksigner")
        print()
        print("=" * 50)
        print("  apksigner 配置方法 (二选一)")
        print("=" * 50)
        print()
        print("方法1 - 复制到脚本目录 (推荐):")
        print("  1. 下载 Build Tools:")
        print("    https://developer.android.com/tools/releases/build-tools?hl=zh-cn")
        print("  2. 解压后将 build-tools 文件夹复制到 apk_signer.py 同目录")
        print("     结构如下:")
        print("       apk_signer.py")
        print("       build-tools/")
        print("         34.0.0/")
        print("           apksigner  <-- 会自动找到")
        print("           platform.x509.pem")
        print("           platform.pk8")
        print()
        print("方法2 - 配置环境变量:")
        print("  export PATH=$PATH:~/android-sdk/build-tools/34.0.0/")
        print("=" * 50)

    # 查找可用端口
    port = find_available_port(DEFAULT_PORT, MAX_PORT_ATTEMPTS)
    if port is None:
        print(f"\n[ERROR] 无法找到可用端口 (尝试范围: {DEFAULT_PORT}-{DEFAULT_PORT + MAX_PORT_ATTEMPTS - 1})")
        sys.exit(1)

    if port != DEFAULT_PORT:
        print(f"\n[INFO] 端口 {DEFAULT_PORT} 被占用，使用端口 {port}")

    # 启动服务
    local_ip = get_local_ip()
    server = HTTPServer((HOST, port), APKHandler)

    print(f"\n[OK] 服务已启动")
    print(f"    - 本地访问: http://localhost:{port}")
    print(f"    - 局域网访问: http://{local_ip}:{port}")
    print(f"\n按 Ctrl+C 停止服务")
    print("=" * 50)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[INFO] 正在停止服务...")
        server.shutdown()
        print("[OK] 服务已停止")

if __name__ == '__main__':
    main()
