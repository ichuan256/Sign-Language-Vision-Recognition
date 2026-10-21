# 工具

本项目自带的外部工具，放在工作区内，不依赖系统安装。

## losslesscut/ — LosslessCut 3.70.1（便携版）

- 用途：对 `video/`、`训练视频/` 里的原片做**无损**剪切（直接复制码流，不重新编码），
  适合按时间边界粗剪手语视频、核对片段起止点、导出片段前先试切。
- 启动：双击 `工具\launch-losslesscut.cmd`，或直接把视频文件拖到该脚本上。
- 也可以带参数调用，打开指定文件：

  ```powershell
  .\工具\launch-losslesscut.cmd .\video\BV1Hs411E7aP_p01.mp4
  ```

- 剪切方案可存成 `xxx-proj.llc` 项目文件（与视频同目录、同文件名 + `-proj.llc`），
  再次打开视频时会自动加载。`video/` 里已有 `BV1Hs411E7aP_p01-proj.llc` 这类文件。
- 自带 FFmpeg/FFprobe，不需要另装：
  - `工具\losslesscut\resources\ffmpeg.exe`
  - `工具\losslesscut\resources\ffprobe.exe`
  - 版本：ffmpeg n8.1.3（2026-10-18 构建）

### 来源与版本

从本机 WinGet 安装的同一版本 3.70.1 完整复制而来（原路径
`%LOCALAPPDATA%\Microsoft\WinGet\Packages\ch.LosslessCut_Microsoft.Winget.Source_8wekyb3d8bbwe`），
复制后已从新路径独立启动验证通过。官方仓库：<https://github.com/mifi/lossless-cut>（GPL-3.0）。

### 注意

- 整个 `losslesscut/` 目录约 630 MB，已加入 `.gitignore`，不进入版本库。
  换机器时重新复制一份即可，不要提交。
- 配置仍写在 `%APPDATA%\losslesscut\config.json`，与本便携目录无关；删掉本目录不会丢配置。
- 这个便携副本不会自动跟随 WinGet 升级；需要新版时重新复制一次即可。
