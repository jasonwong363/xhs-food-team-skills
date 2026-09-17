# 筛选记录与核对页契约

先运行 prepare_pool.py 得到原始池，再逐篇阅读候选正文，填写 review.json。程序只检查证据结构，不代替语义判断；不可批量填“已读”冒充精读。

review.json 顶层：`mode` 为 `strict`（严格最小改写）或 `adaptive`（保留结构适配），`decisions` 为数组。每项示例（脱敏虚构）：

```json
{
  "mode": "adaptive",
  "decisions": [{
    "id": "example-id",
    "source_ref": "example.xlsx/Sheet1/2",
    "decision": "selected",
    "read_status": "full",
    "body_status": "complete",
    "subject": "单店正餐",
    "dishes": ["鱼头泡饼"],
    "structure": ["逛街开头", "菜品段", "饭后散步"],
    "evidence": "鱼头泡饼",
    "reason": "正文以单店正餐和蘸汤吃法为主，与客户产品对应",
    "limits": ["原店步行时间不能迁移"],
    "adaptation": "adaptive",
    "rewrite_plan": "保留三段顺序，按客户证据替换另一道菜的描述",
    "family": "逛街后正餐",
    "reconsidered_from": "",
    "reconsideration_reason": ""
  }]
}
```

- decision：selected / backup / observe / reject / pending。未填写决定的原始记录为初筛待读，不冒称精读。
- read_status：full / initial；body_status：complete / missing / truncated / tags_only。
- adaptation：strict / adaptive / title_only / unusable。strict模式只能入选strict；adaptive模式允许strict或adaptive。
- selected必须有完整非标签正文、完整阅读记录、有效发布时间（半年内）、来源ID和链接、点赞量、正文主角、主要菜品、段落结构、真实原文摘录、理由、不可迁移清单、改写方案、标题家族。
- 空limits数组表示逐项检查后未发现，不可漏字段。互动缺失保留null，不能填0；收藏/评论/分享缺失在页面显示未知。
- 同一ID多快照通过source_ref选取完整的一份，不拼最大值。原始所有行仍保留在审计JSON与CSV。
- 撤回淘汰或备用决定时填写reconsidered_from、reconsideration_reason；模式改变不是自动入选。
- 缺正文只能待补或标题备用，不补写原文。评估原文标题中的具体承诺，不能把只有窗景/酒店才成立的稿视作纯菜品替换。

运行：
```text
python scripts/build_review.py pool.json review.json 新输出目录
```

输出固定为00-对标筛选核对.html、selected.csv、audit.csv、audit.json。核对页包含全文、数据、来源、适配理由、参考结构、不可迁移项、搜索和分类筛选；无需网络加载依赖。所有记录守恒、入选按独立ID计数。审核人仍须检查实际分析是否与原文相符。
