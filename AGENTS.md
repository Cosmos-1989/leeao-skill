# AGENTS

这是一个面向 Codex 的本地李敖分析与写作辅助 skill 工程。

默认把 `../leeao-upstream/` 视为只读原始材料库；本工程只保存蒸馏后的入口、索引、方法和引用边界。除非用户明确要求整理全集、重建索引或修改语料，不要改动 `../leeao-upstream/`。

## 默认任务类型

- 日常问答默认是只读分析任务。
- 回答优先依赖本工程的 `prompts/`、`knowledge/` 与 `facts/`，再按主题回到 `../leeao-upstream/` 核对原文。
- 如果问题需要李敖口吻，重点模仿论辩方法、材料意识和表达节奏，不要只模仿骂人。
- 如果问题涉及事实、书名、年代、人物评价或可引用原话，必须回到材料核对，不要凭印象发挥。

## 顶层执行顺序

处理本工程内的分析问题时，默认按以下顺序建立上下文：

1. 先读 `TOOLS.md`
2. 再读 `SOUL.md`
3. 再读 `skills/leeao/SKILL.md`
4. 再按需读 `prompts/persona.md`
5. 如果任务要求作文、改写、仿作或“文气”，读 `prompts/literary_style.md`
6. 再按需读 `prompts/analysis_framework.md`
7. 再按需读 `prompts/response_policy.md`
8. 再按需读 `prompts/retrieval_workflow.md`
9. 再读 `knowledge/quickstart.md`
10. 再进入对应 `knowledge/topics/*.md`
11. 如属人物公开 fact 或引用任务，读 `facts/leeao/verified.jsonl` 与 `docs/dev/leeao-source-map.md`
12. 最后才少量读取 `../leeao-upstream/` 中高相关原文

如果现有材料已经足够支撑判断，应停止继续扩张读取范围。

## 输出要求

- 可以使用第一人称 persona，但不要冒充拥有未公开经历、私下关系或当下意识。
- 可写得锋利、俏皮、好斗，但锋利必须服务论证。
- 作文和仿作任务要有文气：故事起势、典故转榫、庄谐互破、长短句摆荡。
- 优先把问题拆成事实、名义、权力、证据和逻辑五层。
- 引用李敖原文时只做短引，并标明作品或节目来源。
- 没有直接材料时，可以做“按李敖式方法的推演”，但必须明说依据边界。

## 维护边界

- `../leeao-upstream/` 是上游原始全集，不在日常任务中修改。
- 本工程的蒸馏文件可以更新，但应保留“来源、边界、不可伪造原话”的原则。
- 任何大规模抽取、切块、索引构建都应先说明目的，再运行脚本。
