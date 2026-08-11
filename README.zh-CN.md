# StickerNestMac

StickerNestMac 是一个本地运行的 macOS 异形贴纸排版研究工具，目标是在打印纸张上进行轮廓感知排版，同时保持切割间距、可读方向和边界安全。

> 当前状态：早期开源版本。本仓库是经过隐私清理的源码发布；生产数据、二维码映射、内部操作日志和第三方人物素材均未公开。

## 主要能力

- 导入透明背景素材并按真实轮廓排版。
- SwiftUI 原生界面配合 Python/OpenCV 求解器。
- 检查越界、重叠、阅读方向和实际切割间距。
- 对外部求解进程设置内存保护和强制终止机制。
- 全程本地处理，不包含网络请求或遥测代码。

默认求解配置面向约 420 × 594 mm 的纸张。正式生产前仍须进行真实打印和切割校准。

## 环境与构建

需要 Apple Silicon Mac、macOS 14+、Xcode Command Line Tools、Python 3.11+。

```bash
xcode-select --install
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
zsh build.zsh
STICKERNEST_PYTHON="$PWD/.venv/bin/python3" open "build/异形贴纸排版.app"
```

如需使用自定义 PSD 模板，可在启动前设置 `STICKERNEST_TEMPLATE_PSD=/模板文件的绝对路径/template.psd`。

## 测试

```bash
for test_file in Tools/test_*.py; do
  python3 "$test_file" || exit 1
done
```

## 隐私与素材

仓库不包含人物图片、客户素材、生产二维码、真实磁盘路径、私有基准历史或从生产数据生成的策略 JSON。公开构建只复制白名单内的两个运行时 Python 脚本，不会整体复制 `Resources/`。可选的本地学习结果保存在用户的 Application Support 目录中，不进入 Git。贡献者只能提交有权公开再分发的代码、数据和素材。

详细说明见英文 [README](README.md)、[贡献指南](CONTRIBUTING.md) 与 [安全政策](SECURITY.md)。

## 许可证

MIT © 2026 kgdtpv-netizen。
