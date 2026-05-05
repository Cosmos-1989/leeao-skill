# TOOLS

本工程主要服务于李敖文本材料的本地检索、风格蒸馏与分析型写作。

## 默认工具偏好

- 先读本工程的轻量入口，再回到上游原文。
- 搜索文件优先使用 `rg`。
- 不为了“更像”而扫描大量无关材料。
- 需要核对书名、篇名、节目集数、年代和原话时，必须查 `../leeao-upstream/`。

## 推荐读取路径

1. `skills/leeao/SKILL.md`
2. `prompts/persona.md`
3. `prompts/literary_style.md`
4. `prompts/analysis_framework.md`
5. `prompts/response_policy.md`
6. `prompts/retrieval_workflow.md`
7. `knowledge/quickstart.md`
8. 对应 `knowledge/topics/*.md`
9. `docs/dev/leeao-source-map.md`
10. 高相关 `../leeao-upstream/<类别>/<作品>.md`

## 上游材料定位

上游材料在：

`../leeao-upstream/`

它来自用户指定仓库：

`https://github.com/whatot/leeao`

上游说明称该仓库由 whatot 对 wjm_tcy 编著的“大李敖全集”做格式化和 mdbook 化，whatot 并非原著者。

## 何时运行脚本

只有在以下情况才建议新增或运行维护脚本：

- 用户明确要求重建索引、切块或同步上游。
- 需要把全集拆成更小 chunk 供检索使用。
- 需要批量提取标题、目录、作品元数据或 fact 候选。

## 不推荐的行为

- 不要把李敖等同于“会骂人”的语气包。
- 不要伪造原话、书名、节目集数或人物关系。
- 不要把争议性、性别相关或政治攻击性表达无条件复刻到新语境。
- 不要把上游全集全文复制到本工程蒸馏层。
