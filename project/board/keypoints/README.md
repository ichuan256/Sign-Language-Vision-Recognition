# 单手关键点 PL 驱动

`hand_runtime.py` 的硬件路径只在 PS 做索引、分块、DDR 复制和输出尺度还原，全部神经网络算子调用
`kp_mac` / `kp_vector`。`DLLBackend` 是显式命名的主机验证后端，不是板端回退。
`run_hand_board.py` 先核对候选 bit/hwh、新 boot ID 和 bootpy 已完成，再以 `download=False` 接管。
核超时直接报错，不切换到 CPU。

当前实际验收见 [整网上板记录](../../analysis/keypoints_pl_20261025/single_hand_board.md)：
PC ROI→PL 单手 21 点已通过，单 ROI 12.28 秒；HDMI 静态叠加已目视确认。该入口尚不是任意视频实时识别。

## 部署与运行

主机工具位于 [scripts/keypoints](../../scripts/keypoints/README.md)。以下路径均为本机当前证据示例，
复跑时须选新输出目录。密码只由临时 `KEYPOINT_BOARD_SUDO_PASSWORD` 环境变量传入，禁止写到文件、命令行参数或日志。
部署默认只准备候选；只有显式 `--apply` 才会备份、替换并冷重启。

```powershell
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/deploy_hand_board.py --build project/_tmp/kp_system_v3 --model project/_tmp/kp_packed_v1 --output project/_tmp/kp_board_deploy_new --apply
# 等待新 boot ID、bootpy exited、成对哈希匹配；绝不运行中下载 bit
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/run_hand_remote.py --deployment project/_tmp/kp_board_deploy_new --reference project/_tmp/kp_packed_v1/probes.npz --output project/_tmp/kp_board_result_new
```

输出 `report.json` 含逐层时间与核调用数，`alignment.json` 含整网对齐和延迟，`output.npy` 含 63 坐标＋presence。
同一 ROI 的重复试验只是数值/时延试验，不增加独立样本数。首次进程初始化耗时与前向耗时分别记录。

## 固件边界与恢复

候选固件保留了旧 W6 HDMI、音频、按键和闲置模块；本轮验收范围只有单手 PL 推理与 HDMI，未宣称音频回归完成。
旧 W6 本地发布文件保持原样，旧演示的固件哈希检查仍可拒绝候选；不要为绕过检查重载 FPGA。
HDMI 验证可用 `--release-manifest project/analysis/keypoints_pl_20261025/single_hand_board.json` 显式接受这份成对哈希，
不会修改全局已接受列表。

部署记录 `project/_tmp/kp_board_deploy_v2/deployment.json` 保存了板端旧 pair 的备份位置。
如需恢复，先核对备份两份哈希，与原 pair 一致后再成对恢复到启动路径并重启一次；
禁止运行中 `Overlay(download=True)`，禁止修改 boot.py 或调用旧 base.bit 脚本。
恢复会中断板端画面，应按 AGENTS.md 的危险操作约定执行。
