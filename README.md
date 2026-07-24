# Codex Skills 同步面板

这是给团队共享 Codex Skills 的本地按钮面板。它支持 Windows 和 macOS，把三类业务 skills 在 GitHub 和本地 Codex 之间手动同步：

- SEO 优化 Skills：`sannnnway-prog/seo-optimization-skills`
- Blog 创作 Skills：`sannnnway-prog/blog-creation-skills`
- SEO 页面工厂 Skills：`sannnnway-prog/seo-page-factory`

## 先安装

每台电脑只需要准备两样东西：

1. GitHub CLI：<https://cli.github.com/>
2. Python 3：<https://www.python.org/downloads/>

安装后登录 GitHub：

```bash
gh auth login
```

## 打开面板

Windows：

```text
双击 start-panel-windows.cmd
```

macOS：

```text
第一次可能需要右键 start-panel-mac.command，选择“打开”。
```

打开后会自动启动本地网页面板：

```text
http://127.0.0.1:8765/
```

## 三个按钮

- 状态检查：检查 GitHub CLI 是否登录、本地 Codex Skills 目录是否存在。
- 从 GitHub 更新到本地：把团队最新版 skills 下载到 `~/.codex/skills`，下载前自动备份本地旧版本。
- 把本地上传到 GitHub：把本地 `~/.codex/skills` 的修改上传到对应仓库。上传前会检查远端是否被同事更新过，发现冲突会停止并提示。

## 本地目录

默认同步到：

```text
~/.codex/skills
```

如需指定其他目录，可以设置环境变量：

```bash
CODEX_SKILLS_DIR=/path/to/skills
```

## 备份和日志

面板会把备份和日志放到：

```text
~/.codex/skill-sync
```

## 注意

不要把 API Key、Token、密码、Cookie、客户敏感数据写进 `SKILL.md` 或任何 skill 文件。
