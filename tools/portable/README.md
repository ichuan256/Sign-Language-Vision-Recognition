# 便携工具入口

当前目录的 `launch-losslesscut.cmd` 使用同目录
`losslesscut/LosslessCut.exe`。2026-10-25 已统一本机便携工具位置，
120 个文件与迁移前工具文件集合逐一核对，完整目录约 631 MiB；没有启动 GUI。

从仓库根调用：

```powershell
.\tools\portable\launch-losslesscut.cmd <视频文件>
```

便携二进制目录已加入 `.gitignore`。旧 `工具/losslesscut/resources`
中部分资源被占用，已复制并校验到新位置；旧残余保留且忽略 Git，未强杀进程或删除文件。
当前 ffmpeg/ffprobe 从新 `losslesscut/resources/` 发现。
迁移记录见 [素材整理执行记录](../../analysis/materials/20261025_organization/执行记录.md)。
