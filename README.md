# APK 签名工具

基于 Python 的局域网 APK 签名 Web 服务。

## 功能特点

- 🎨 美观的 Web 界面
- 📱 支持选择 Android 版本和签名目标
- 📦 支持 APK 文件上传和拖拽
- ✅ 签名成功后自动下载
- 🔄 实时进度显示
- ⚠️ 完善的错误提示

## 文件说明

```
apk_signer.py    # 主程序
config.json      # 签名配置
README.md        # 说明文档
```

## 配置说明

编辑 `config.json` 文件：

```json
{
  "targets": [
    {
      "androidVersion": "Android 10 (API 29)",
      "signTarget": "版本A",
      "platform_x509": "/path/to/platform.x509.pem",
      "platform_pk8": "/path/to/platform.pk8"
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| androidVersion | Android 版本标识 |
| signTarget | 签名目标名称（如版本A、版本B） |
| platform_x509 | 证书文件 (.x509.pem) 路径 |
| platform_pk8 | 密钥文件 (.pk8) 路径 |

## 使用方法

### 1. 安装依赖

确保已安装 Android SDK Build Tools（包含 apksigner）：

```bash
# Ubuntu/Debian
sudo apt install android-sdk-build-tools

# 或设置 ANDROID_HOME 环境变量
export ANDROID_HOME=/path/to/android-sdk
export PATH=$PATH:$ANDROID_HOME/build-tools/latest/
```

### 2. 配置签名文件

编辑 `config.json`，填入正确的签名文件路径。

### 3. 启动服务

```bash
python3 apk_signer.py
```

### 4. 访问网页

- 本地访问：`http://localhost:8080`
- 局域网访问：`http://<你的IP>:8080`

### 5. 使用流程

1. 选择 Android 版本
2. 选择签名目标
3. 上传 APK 文件（或拖拽）
4. 点击「开始签名」
5. 签名成功后自动下载签名后的 APK

## 界面预览

```
┌─────────────────────────────────┐
│         APK 签名工具            │
│   快速为 APK 文件签名...        │
├─────────────────────────────────┤
│  配置信息                       │
│  ┌───────────────────────────┐  │
│  │ androidVersion: Android 10│  │
│  │ signTarget: 版本A         │  │
│  └───────────────────────────┘  │
│                                 │
│  [Android 版本 ▼]              │
│  [签名目标 ▼]                  │
│                                 │
│  ┌───────────────────────────┐  │
│  │     📦 点击上传APK文件     │  │
│  └───────────────────────────┘  │
│                                 │
│  [       开始签名       ]       │
└─────────────────────────────────┘
```

## Android SDK Build Tools 配置

### 下载地址

访问build-tools：https://developer.android.com/tools/releases/build-tools?hl=zh-cn

访问command-line-tools：https://developer.android.com/studio?hl=zh-cn#command-line-tools-only

下载对应版本的 Build Tools（如 34.0.0）

### 方法一：复制到脚本目录 (推荐)

解压后将 `build-tools` 文件夹复制到 `apk_signer.py` 同目录：

```
apk-sign/
├── apk_signer.py
├── config.json
├── build-tools/
│   └── 34.0.0/
│       ├── apksigner          ← 自动找到
│       ├── platform.x509.pem   ← 签名文件
│       └── platform.pk8        ← 签名文件
```

签名文件路径配置（相对路径）：
```json
{
  "targets": [
    {
      "androidVersion": "Android 10",
      "signTarget": "版本A",
      "platform_x509": "build-tools/34.0.0/platform.x509.pem",
      "platform_pk8": "build-tools/34.0.0/platform.pk8"
    }
  ]
}
```

### 方法二：设置环境变量

```bash
export PATH=$PATH:~/android-sdk/build-tools/34.0.0/
```

### 方法三：使用绝对路径

```json
{
  "platform_x509": "/home/user/android-sdk/build-tools/34.0.0/platform.x509.pem",
  "platform_pk8": "/home/user/android-sdk/build-tools/34.0.0/platform.pk8"
}
```

## 注意事项

- 签名文件路径支持绝对路径和相对路径
- 相对路径基于脚本所在目录解析
- 签名工具需要 `apksigner`（Android SDK Build Tools 内置）
- 临时文件会在签名后自动清理
- 服务启动后会持续运行，直到按 Ctrl+C 停止
