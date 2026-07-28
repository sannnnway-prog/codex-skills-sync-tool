# Codex Skills 同步面板

这是给团队共享 Codex Skills 的本地按钮面板。它支持 Windows 和 macOS，用 GitHub CLI 把团队 skills 在 GitHub 和本地 Codex 之间手动同步。

## 同步范围

面板包含三类仓库：

- SEO 优化 Skills：`sannnnway-prog/seo-optimization-skills`
- Blog 创作 Skills：`sannnnway-prog/blog-creation-skills`
- SEO 页面工厂 Skills：`sannnnway-prog/seo-page-factory`
- 多语言 Skills：`sannnnway-prog/multilingual-content-skills`

可以全选，也可以按项目或单个 skill 勾选后同步。

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
- 把本地上传到 GitHub：把本地 `~/.codex/skills` 的修改上传到对应仓库。上传前会检查远端是否被同事更新过，发现同一文件两边都改了会停止。

## 如果本地和 GitHub 都有更新

先说结论：

- 先下载 GitHub 最新版：不会无声丢失你的本地修改，因为面板会先备份本地旧版本；但工作目录会被 GitHub 最新版覆盖。
- 先上传本地修改：不会直接覆盖同事已经上传的同一文件；面板发现同一文件远端也变了，会停止上传。
- 如果你和同事改的是不同文件：面板会只上传你本地改过的文件，不会覆盖同事更新过但你没改的文件。
- 如果你和同事改的是同一个文件：需要合并。推荐先下载，让面板备份你的本地版本，再对比备份和最新版，合并后再上传。

备份目录：

```text
~/.codex/skill-sync/backups
```

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
