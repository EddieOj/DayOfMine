# 莺中的一天 · 宝宝日记

可爱的 H5 翻页动画，记录傅融（代号莺中）一天的生活。适配手机端，每滑一下播放一段场景动画。

## 技术栈

- **前端**: 纯 HTML + CSS + JS，零依赖，单页应用
- **AI 资产**: 即梦AI (Jimeng AI) API — 文生图 3.1 + 视频首尾帧 3.0
- **后端签名**: Volcengine V4 Signature (volcengine-python-sdk)

## 快速开始

### 1. 安装依赖

```bash
cd DayOfMine
uv sync
```

### 2. 配置 API 凭证

在即梦AI控制台获取你的 AccessKey 和 SecretKey：

```bash
# Windows (cmd)
set VOLC_ACCESSKEY=your_access_key
set VOLC_SECRETKEY=your_secret_key

# 或 PowerShell
$env:VOLC_ACCESSKEY="your_access_key"
$env:VOLC_SECRETKEY="your_secret_key"

# 或 Git Bash
export VOLC_ACCESSKEY="your_access_key"
export VOLC_SECRETKEY="your_secret_key"
```

### 3. 生成 AI 资产

```bash
uv run python scripts/generate_assets.py
```

脚本会依次：
1. 为每个场景生成 1080×1920 图片（文生图）
2. 用图片作为首尾帧生成 5 秒动画视频
3. 下载到 `assets/scenes/` 和 `assets/videos/`
4. 生成 `assets/scene_data.json` 供前端读取

### 4. 打开前端

直接用浏览器打开 `index.html`，或搭建本地服务器：

```bash
# Python 简易服务器
cd DayOfMine
python -m http.server 8080
# 浏览器打开 http://localhost:8080
```

## 场景时间线

| ID | 时间 | 场景 |
|---|---|---|
| sleep | 00:00–08:00 | 🌙 呼呼大睡 |
| wakeup | 08:00–08:30 | ☀️ 起床咯 |
| wash | 08:30–09:00 | 🪥 洗漱 |
| breakfast | 09:00 | 🥟 早餐 |
| login_game | 09:00–09:10 | 🎮 领游戏奖励 |
| study | 09:10–09:40 | 📚 学科一 |
| play | 10:00–12:00 | 🦋 自由玩耍 |
| lunch | 12:00–13:00 | 🍚 午餐 |
| nap | 13:00–14:00 | 😴 午休 |
| afternoon | 14:00–17:00 | 🧋 下午茶追剧 |
| dinner | 17:00–19:00 | 🍜 晚餐 |
| evening | 19:00–21:00 | 📱 睡前娱乐 |
| goodnight | 21:00–24:00 | 🌠 晚安 |

## 设计思路

- **场景融合**: 每个 slide 有自己的渐变色背景 + 浮动装饰元素（星星、泡泡等），避免生硬矩形框
- **视频卡片**: 视频嵌入圆角卡片中，带阴影，像一张「会动的照片」
- **粒子背景**: 全局粒子系统增强氛围，不干扰内容
- **时间轴**: 右侧圆点指示当前进度，点击可跳转
- **日夜循环**: 左上角月亮/太阳图标随场景变化

## 文件结构

```
DayOfMine/
├── index.html              # H5 前端入口
├── ApiKey.txt              # API 密钥 (格式: API Key: <access_key>.<secret_key>)
├── pyproject.toml          # Python 项目配置
├── src/
│   └── api_helper.py       # 即梦AI API 客户端 (V4 签名)
├── scripts/
│   └── generate_assets.py  # 资产生成脚本
└── assets/
    ├── scenes/             # 场景图片 (自动生成)
    ├── videos/             # 场景动画 (自动生成)
    └── scene_data.json     # 前端数据清单 (自动生成)
```
