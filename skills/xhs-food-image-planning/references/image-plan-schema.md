# 图片清单结构

## 素材库 catalog-plan.json
根节点数组，每张原图恰好一条：
```json
{"id":"P0001","source":"photos/beef.jpg","category":"dish_closeup","subject":"鲜切牛肉片（部位待核对）","name_status":"描述名","decision":"优选","cover_candidate":true,"similar_group":"牛肉盘正面","reason":"主体清楚、肉纹突出，相似机位代表","old_selected":false,"folder":"01-单品菜品/鲜切牛肉片/优选"}
```
category：dish_closeup、dish_combo、table_spread、preparation、environment、storefront、unconfirmed。
decision：优选、备选、不建议使用、待核对。备选可以是质量合格但近重复的照片。
cover_candidate仅允许优选的dish_closeup，实际主体必须为一道菜；菜名待核对不代表画面质量差。
folder必须为输出内相对目录，禁止绝对路径和..。

运行 `python scripts/materialize_catalog.py catalog-plan.json 输出目录`，输出目录必须不存在。
交付分类图片、图片分类清单.csv/json、00-首图候选、00-分类预览；补00-核对说明.md，说明原图范围、总数、旧精选数、各类数量、不确定项、未执行阶段。候选副本不重复计入原图数。

## 按文分组 selection-plan.json
根节点数组，每组包括id、note_id、note_subject、images。每图含source、order、category、role、subject、match_reason。
首图category=dish_closeup且role=cover；第二张category=table_spread；其他为相关补图。order从1连续，每组3至5张；note_id、note_subject和match_reason不能空。
默认source全局唯一，允许跨组复用时也不能组内重复。materialize_groups.py只负责已获授权的按文分组；不得拿旧随机分组方案绕过正文匹配字段。
