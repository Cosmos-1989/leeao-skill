# Retrieval Workflow

## 快速路径

1. 先读 `knowledge/quickstart.md` 判断主题。
2. 再读对应 `knowledge/topics/*.md`。
3. 如需核对出处，读 `docs/dev/leeao-source-map.md`。
4. 用 `rg` 在 `../leeao-upstream/` 中搜索关键词。
5. 只打开高相关作品的局部段落。

## 搜索建议

常用命令示例：

```sh
rg -n "胡适|自由主义|播种者" ../leeao-upstream
rg -n "蒋介石|国民党|白色恐怖" ../leeao-upstream
rg -n "传统|独白|狂叛|文章" ../leeao-upstream
```

## 读取粒度

- 先看作品目录和小标题。
- 再读目标章节开头和结论部分。
- 只在需要引证时读取上下文。
- 如果文本很长，优先用 `rg -n` 定位关键词，不要整本扫读。

## 证据分层

- 一手自述：自传、回忆录、日记、书信。
- 一手论述：杂文、史论、人物研究、节目文本。
- 二手评价：百家论李敖、序言、他人文章。
- 上游整理说明：README、SUMMARY、wjm_tcy 说明。

## 使用边界

上游材料是格式化合集，不等于权威校勘本。涉及严肃出处时，应把它作为本地检索入口，而不是最终版本学结论。
