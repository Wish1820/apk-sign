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

## 注意事项

- 确保签名文件路径正确且可读
- 签名工具需要 `apksigner`，请安装 Android SDK Build Tools
- 临时文件会在签名后自动清理
- 服务启动后会持续运行，直到按 Ctrl+C 停止
