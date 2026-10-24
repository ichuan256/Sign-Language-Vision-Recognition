# 便携工具入口

当前目录保留 `launch-losslesscut.cmd`。启动器要求同目录存在
`losslesscut/LosslessCut.exe`；该二进制目录目前不在工作区，不能把旧说明当成已安装状态。

本地具备该目录后，可从仓库根调用：

```powershell
.\tools\portable\launch-losslesscut.cmd <视频文件>
```

便携二进制目录已加入 `.gitignore`。本轮只迁移启动入口，未安装程序、启动 GUI
或修改用户工具配置。
