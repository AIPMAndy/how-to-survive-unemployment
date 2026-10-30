# 发布到 GitHub / GitHub Pages

公开仓库：[AIPMAndy/how-to-survive-unemployment](https://github.com/AIPMAndy/how-to-survive-unemployment)，已于 **2026-10-09** 创建并推送。GitHub Pages 已配置为 `main` 分支根目录：[在线互动指南](https://aipmandy.github.io/how-to-survive-unemployment/)。

本目录是完整的独立开源项目源代码。以下创建步骤供首次发布或 Fork 参考；维护当前仓库只需提交改动后 `git push`，不要重复创建仓库。

## 方式 A：使用 GitHub 网站（最简单）

1. 打开 https://github.com/new 。
2. Owner 选 `AIPMAndy`，Repository name 填 `how-to-survive-unemployment`，选择 **Public**。
3. 不勾选自动创建 README、License 或 .gitignore（这些文件都已提供）；点击 **Create repository**。
4. 在电脑上解压项目 ZIP，进入目录后执行：

```bash
git init -b main
git add .
git commit -m "feat: launch unemployment survival guide"
git remote add origin https://github.com/AIPMAndy/how-to-survive-unemployment.git
git push -u origin main
```

需要提前配置 git 用户信息并完成 GitHub 身份验证。上面的命令不会覆盖其他已有仓库。

## 方式 B：安装 gh CLI 后一条命令

```bash
git init -b main
git add .
git commit -m "feat: launch unemployment survival guide"
gh auth login          # 如果尚未登录
gh repo create AIPMAndy/how-to-survive-unemployment --public --source=. --remote=origin --push
```

## 开通 GitHub Pages

打开新仓库 **Settings → Pages → Build and deployment**，选择 **Deploy from a branch**，branch 选 `main`、folder 选 `/(root)`，保存。站点正常部署后，通常可使用：

`https://aipmandy.github.io/how-to-survive-unemployment/`

本仓库已启用 Pages；后续推送至 `main` 会触发重新部署。项目包含根目录 `index.html` 和 `.nojekyll`，部署状态可在仓库 Actions 中查看。

## 给仓库做开源分发准备

- Repo Description 可填：`失业了咋办？从 N+1、失业金到社保医保、公积金、重新找工作和个人生意。53项行动任务、6份实操SOP、13周现金流、北京上海广州政策，免费开源。`
- Topics：`unemployment`、`career`、`job-search`、`layoff`、`china`、`career-guide`、`open-source`、`personal-finance`。
- **Social preview**：到 Settings → General → Social preview，上传已生成的 `assets/social-preview.png`（1200×630）。
- 仓库 About 中填写成功启用的 Pages 地址。
- 在微信/小红书分享时，用一个具体问题引流，如“在北京失业后，医保怎么接续？”并附对应 Github 源链接。不要购买 Star、刷量或冒充政策权威。

## 发布前建议执行

```bash
python3 build.py
python3 -m unittest discover -s tests -v
node tests/calc.test.js  # 可选，需要Node.js
```

可选浏览器验证需要安装 Playwright 和 Chromium：

```bash
python3 tests/browser_smoke.py
```

如需使用已有 Chromium 浏览器，通过 `CHROMIUM_EXECUTABLE_PATH` 指定可执行文件。发布时已通过桌面与手机视口自动化检查；真实手机仍可手动核验城市分流、补偿试算、任务勾选、13周现金表导出，以及打开《前72小时》的HTML文档。

参考 [GitHub传播和维护清单](LAUNCH.md)。
