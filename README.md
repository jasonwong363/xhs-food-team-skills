# 餐饮小红书 Skill 团队组合包

用于从客户资料出发，批量筛选对标笔记，按事实最小改写，再整理图片并按文配图。换客户只换资料，无需重做 Skill。

## 包含4个 Skill

| 顺序 | Skill | 工作内容 |
|---|---|---|
| 1 | xhs-food-content-positioning | 菜单、评价和门店资料整理为有依据的文案基准 |
| 2 | xhs-benchmark-pool-screening | 从100—200条或更多导出记录中筛选同品类对标 |
| 3 | xhs-note-minimal-rewrite | 对已选原稿做必要替换，保留语气，核对菜品，标题默认≤20字 |
| 4 | xhs-food-image-planning | 全量整理原图，按已确认正文选3—5张配图 |

不包含已弃用的看图原创和旧版流程总入口。也不包含自动采集工具、飞书连接器或自动发布功能。

## 安装

先安装 Git、Node.js/npm，并确保当前 Git 身份有本私有仓库读取权限。项目成员可以在自己的工作项目目录执行：

```bash
npx -y skills add jasonwong363/xhs-food-team-skills --all
```

需要所有项目可用时使用：

```bash
npx -y skills add jasonwong363/xhs-food-team-skills -g --all
```

出现权限错误时，由仓库管理员将你加入协作者，或先使用团队分发的ZIP。ZIP解压后也可执行 `npx -y skills add ./xhs-food-team-skills --all`。如目录重名，先检查版本，不覆盖团队已有修改。

重新开启客户端会话后，检查能否看到上表4个名称。无需安装本包制作时使用的 dbs-skill-maker。

脚本可选依赖：Python 3.10+、Pillow、openpyxl。只有执行本地图片或表格脚本才需要：

```bash
python -m pip install -r requirements.txt
```

完整上手流程、复制即用的提示词、分工与验收见 [团队使用说明](团队使用说明.md)。

## 最短使用示例

```text
请使用 $xhs-benchmark-pool-screening。
客户基准：客户A/客户文案基准.md
参考数据：客户A/参考笔记/
筛选最近半年同品类图文，先判断菜品匹配，再比较互动。
输出推荐、备用、淘汰理由和原始链接，先不要改写。
```

## 数据与验证范围

本仓库仅包含方法、通用模板与脚本。客户评价、照片、导出原文、账号凭证由团队放在各自客户目录，不提交到仓库。

互动仅代表导出快照，不能证明自然流量或到店转化。菜名相近不等于同一道菜；图片不能证明具体品种或在售状态。图像判断需支持看图的 Agent，脚本只负责清单、复制与校验。

发布检查记录见 [验证说明](验证说明.md)。
