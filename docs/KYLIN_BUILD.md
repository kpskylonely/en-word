# Kylin / Linux ARM64 打包说明

## 目标

在 **GitHub Actions** 和 **本地 Docker** 中稳定产出 `arm64` `.deb`，满足：

- 运行在 **麒麟 V10 / Ubuntu 20.04 时代** 的系统（glibc **≤ 2.31**）
- 不依赖 GitHub runner 自带的 Ubuntu 24.04 环境（glibc 2.39）

## 架构（固定，请勿随意改）

```
GitHub ubuntu-24.04-arm runner
        │
        ▼
  Docker (ubuntu:20.04)          ← glibc 2.31 基线
        │
        ├─ indygreg CPython 3.10  ← 可移植 Python，pip wheel 兼容
        ├─ Node.js tarball
        └─ apt: GTK/WebKit/dpkg
        │
        ▼
  scripts/install_linux_build_deps.sh
  scripts/build_kylin.sh
  scripts/verify_glibc.sh        ← 打包后自动校验 GLIBC
        │
        ▼
  release/en-word_*_arm64.deb
```

## 设计原则

| 规则 | 原因 |
|------|------|
| Docker 基镜像只用 **ubuntu:20.04** | 锁定 glibc 2.31 |
| **禁止** PPA / deadsnakes / 源码编译 Python | ARM64 CI 反复 apt/pip 失败 |
| Python 用 **indygreg standalone** | 官方可移植构建，wheel 正常 |
| **禁止** 在 Dockerfile 里 pip install | 依赖变更只改 `requirements-build-linux.txt` |
| 打包后 **verify_glibc.sh** | 防止再次把 2.38 包发给麒麟用户 |

## 命令

```bash
# CI / 推荐
npm run db:download
npm run pack:kylin:docker

# 在麒麟本机
npm run pack:kylin
```

## 故障排查

1. **Docker 镜像构建失败** → 检查 `packaging/docker/Dockerfile.kylin-build` 是否违反上述规则
2. **pip 安装失败** → 改 `requirements-build-linux.txt` 版本，不要改 Dockerfile 加 PPA
3. **麒麟运行 GLIBC 报错** → 看 CI 日志里 `verify_glibc.sh` 是否通过；若 CI 通过但真机失败，降低 `MAX_ALLOWED` 或换更老基镜像
