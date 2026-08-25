# 离线背单词

基于 [DictionaryData](https://github.com/LinXueyuanStdio/DictionaryData) 的跨平台离线背单词应用。

- **技术栈**：Python (FastAPI) + Vue 3 + SQLite + PyWebView
- **平台**：macOS、麒麟 V10（x86_64）
- **特点**：完全离线，适合内网环境

## 学习模式

闪卡复习 · 英→中 · 中→英 · 键盘拼写 · 浏览词表 · 错词本

## 环境准备

```bash
# Python 依赖
pip3 install -r requirements.txt

# 前端依赖
npm install

# 词库（约 240MB）
npm run db:download
```

## 开发运行

开两个终端：

```bash
# 终端 1：Python API
npm run dev:api

# 终端 2：Vue 前端
npm run dev
```

或一条命令（后台启动 API）：

```bash
npm run dev:all
```

## 桌面应用

```bash
npm run build
npm start
```

`npm start` 会启动 Python 后端并用 PyWebView 打开桌面窗口。

## 一键打包安装包

打包前请确保词库已下载：`npm run db:download`

打包需要 **Python 3.9+** 及依赖（脚本会自动选择可用解释器，也可手动指定 `PYTHON=/usr/bin/python3`）。

### macOS（.dmg）

在本机执行：

```bash
npm run pack:mac
```

产物：

- `release/EnWord.app` — 应用程序
- `release/EnWord-0.1.0-mac.dmg` — 安装镜像

安装：打开 DMG，将 **EnWord** 拖入「应用程序」文件夹。首次打开若提示未验证开发者，请右键 → 打开。

### 麒麟 V10 / Linux（.deb，x86_64）

**方式 A：在 Mac 上通过 Docker 打包（推荐）**

需要安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。会在 `linux/amd64` 容器里构建，产物适用于麒麟 V10 x86：

```bash
npm run pack:kylin:docker
```

首次构建镜像较慢；Apple 芯片 Mac 会通过 QEMU 模拟 x86，请耐心等待。

**方式 B：在麒麟 / Ubuntu 本机打包**

```bash
npm run pack:kylin
```

产物：

- `release/en-word_0.1.0_amd64.deb`

安装：

```bash
sudo dpkg -i release/en-word_0.1.0_amd64.deb
sudo apt -f install   # 如有依赖缺失
```

安装后从应用菜单启动「离线背单词」，或终端运行 `en-word`。

> PyInstaller 无法从 Mac 直接交叉编译 Linux 程序，因此纯本地打包必须在 Linux 上进行；Mac 上请用 Docker 方案。

**方式 C：GitHub Actions 自动打包**

推送到 `main` / `master` 后，会在 `ubuntu-latest` 上自动构建 `.deb`，可在 Actions 页面的 **Artifacts** 下载：

- 工作流：`.github/workflows/build-kylin-deb.yml`
- 推送标签 `v*`（如 `v0.1.0`）时，还会自动创建 GitHub Release 并附上 `.deb`

```bash
git tag v0.1.0
git push origin v0.1.0
```

> 学习进度保存在 `~/.en-word/dictionary.db`（首次启动从内置词库复制，约 240MB）。

## 测试

```bash
npm run test:backend
npm run test:features
```

## 麒麟 V10 依赖

```bash
sudo apt install python3 python3-pip python3-venv \
  python3-gi python3-gi-cairo gir1.2-webkit2-4.1 \
  libwebkit2gtk-4.1-0 libgtk-3-0
pip3 install -r requirements.txt
```

## 目录结构

```
en/
├── backend/          # Python FastAPI 后端
├── src/              # Vue 前端
├── scripts/          # 词库导入与测试
├── data/             # dictionary.db（生成）
└── requirements.txt
```
