# 飞书文案交付标准 v2026.09.17

固定列：A编号、B标题、C正文、D标签、E审核状态、F参考稿编号、G原文标题、H原文链接、I改写备注、J完整文案（复制用）。不同业务可按用户明确要求调整。

表头：#173B4D深蓝底，#FFFFFF白字，加粗，13px，顶部对齐，36px行高。
数据：13px、顶部对齐、自动换行，参考行高330px（长文按需要调整，不截断存储的内容）。
A—J列宽px：60、240、400、240、90、90、240、160、230、400。
已确认状态浅绿#DCF3E5；待审核浅黄#FFF2CC；待修改可用浅红#FCE4D6。只为状态格着色，不借颜色假定审批通过。

完整文案 = 标题 + 两个换行 + 正文 +（标签非空时两个换行 + 标签）。不加“标题：”“正文：”等干扰复制的前缀。
第2行公式：`=B2&CHAR(10)&CHAR(10)&C2&IF(D2="","",CHAR(10)&CHAR(10)&D2)`。
J列不要设为文本格式导致公式不执行。复制的是计算结果；若客户端粘贴出现外层引号，建议进入单元格复制文本或使用纯文本导出。

## 脚本输入
JSON顶层为数组，每篇包含：`number,title,body,tags,status,source_code,source_title,source_url,remark`。
number为稳定字符串，保留前导零；title/body为非空字符串；tags可为空；status为待审核/已确认/待修改。已确认必须另带非空`approval_evidence`说明确认范围/来源。来源字段缺失留空，不补造。

```text
python scripts/prepare_delivery.py drafts.json 新输出目录 --expected 50 --sheet-name 文案
```

输出delivery.json（含完整复制结果）、sheets.json（前九列的typed payload）、formulas.json（J列公式）、styles.json（十列样式）。适配已有表时读取实际行号，不机械使用从第2行开始的默认公式。标准空表可以按生成位置直接使用。

飞书CLI可用时以stdin传JSON，避免shell转义和长参数。先读目标，再写sheets/styles与J列公式；写后按delivery.json全量比较。没有在线工具时只能交付本地文件并说明未上传，不能伪报成功。
