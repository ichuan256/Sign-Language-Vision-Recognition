# 电脑协同AV的板端自启层

只启动已冷加载固件的HDMI所有者，并通过固定入口为原PC识别程序提供相机/音频；不含模型训练、板端独立推理或位流下载。用户说明见[视听三栏开机启动](../../../docs/视听三栏开机启动.md)。

`board_gateway.py`为受保护的有限免密入口，参数白名单在访问硬件前验证；`runner.py`只加载固定音频服务；`sign-av-owner.service`在bootpy之后运行。`install_board.py`只安装和enable，不start、不reboot，保存旧配置并核对原固件/boot.py未变。

发布由`project/scripts/package_av_autostart.py`从已验收来源派生：保留采集/显示算法，仅替换受保护的运行目录、保留原Overlay冷加载路径、取消一小时会话上限。安装与证据见`project/analysis/av_autostart_20261101/`，不能从任意目录运行gateway或旧探针接管当前板卡。
