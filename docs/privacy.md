# 隐私与分享范围

这个仓库只包含示例文稿、场景配置、绘图代码和通用制作组件。它不需要公众号、邮箱或 GitHub 凭据来生成视频。

## 运行时的数据流

| 环节 | 数据去向 |
|---|---|
| `prepare` 首次生成或口播变更 | 送读文本发往微软 Edge 在线语音服务 |
| 声音复用 | 参数和文本相同且结果存在时，使用本地声音 |
| 字幕与时间轴 | 本机处理词级时间点 |
| 绘图与 FFmpeg 合成 | 本机处理 |
| AI 协助改文稿或代码 | 取决于你使用的 AI 产品和向它提供的内容 |

当前使用的 `edge-tts` 是社区项目。在线语音服务的可用性及规则由服务方决定。本流程不能描述为全离线制作。

## 分享一个新示例

只选择打算分享的文稿、图形、代码与配置。保持素材路径相对于示例目录，不在代码中写入真实账户、私人文档位置、密钥或访问令牌。

构建结果可能包含完整送读文本、声音和时间轴，因此 `build/` 默认不提交。字体和本机环境也不提交。需要分享成片时，单独选择相应成片。

本仓库没有网站统计、遥测或自动发布代码。

## GitHub 提交信息

Git 提交会携带作者名和邮箱。首次提交前，在此仓库设置准备公开的显示名与 GitHub 提供的 `noreply` 邮箱；不要把真实邮箱写进教程示例。

新仓库只接收选定文件，不复制私人工作目录的 `.git`、历史日志、账号配置或其他文稿。`.gitignore` 不会清除已经进入提交历史的内容。

保持私有不会自动清理历史；改成公开后，别人可能保存副本。如果密钥意外公开，应先撤销或轮换密钥，删除文件本身不能消除所有历史副本。

GitHub 官方说明：

- https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address
- https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files
- https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
