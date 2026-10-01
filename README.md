# 李敖.Skill · v2.0

面向中文原创写作、改写、拟题与原文检索的非官方 skill。新版重点蒸馏文学作品与后期论辩：用细节、词义翻转、语势和有限让步形成文气，不把古雅词汇或刻薄警句当作风格配额。

## 本次升级

- 20 张带行号、短定位词和使用边界的证据卡，来自 11 个正文/合集文件的选段。
- 按命题作文、抒情散文、小说、书信和后期论辩分流，不用一个配方写所有文章。
- 修正作者身份、引文说话者、小说与史实、选集时间与成文时间的混淆。
- 增加可复跑的来源校验、检索工具与人工作文校准。脚本不判定文章是否“像李敖”。

本轮做的是选段精读，不是逐篇读完全集；20 张卡片是编辑性提炼，不是人物事实认证。详见 [审查与升级记录](docs/dev/v2-review.md)。

## 使用

已有本工程时，从 [skill 入口](skills/leeao/SKILL.md) 按任务读取。可直接要求：

> 使用李敖 skill，写一篇命题作文：……
>
> 保持事实和篇幅，改得有文气，少些随处可用的警句。
>
> 核对这句话是否出自李敖，说明篇章和引文身份。

远程仓库地址沿用 [Cosmos-1989/leeao-skill](https://github.com/Cosmos-1989/leeao-skill)。本地升级并不表示远程仓库已经更新。

```sh
git clone https://github.com/Cosmos-1989/leeao-skill
cd leeao-skill
```

本仓库中的 skill 依赖外层的 `prompts/`、`knowledge/` 等资源，须保留整个工程。它是仓库内入口；单独复制 `skills/leeao/` 不是完整安装。在 Codex、Claude Code 等工具中打开工程或显式指定入口即可，不需要把人格设置为所有问答的默认口吻。

## 原始材料

上游：[whatot/leeao](https://github.com/whatot/leeao)，为第三方整理的 Markdown 合集，不是权威校勘本。本工程不再分发全文。

默认将上游放在本工程旁边，目录名为 `leeao-upstream/`：

```sh
git clone https://github.com/whatot/leeao ../leeao-upstream
git -C ../leeao-upstream checkout c638b71323bf8bdce66a9cbf19c1408202426d73
```

固定提交使行号可复查。已有语料可用 `--upstream` 指定位置，不必另拉一份。没有语料时仍可依据蒸馏规则原创写作，不能声称已核对原话。

## 检索与验证

Python 3.10 及以上，仅用标准库。以下命令在工程根目录运行；从别处运行时使用脚本绝对路径。

```sh
python3 tools/corpus.py search --work 李敖文存 文章 --limit 3
python3 tools/validate_skill.py
python3 -m unittest discover -s tests
python3 tools/validate_skill.py --offline
```

默认验证同时核对原文哈希、行号与定位词；离线验证明确跳过原文内容检查。更新上游须先重核证据卡，再重建 `knowledge/source_manifest.json`，不能仅刷新索引来消除漂移告警。

## 工程入口

- [文学笔法](prompts/literary_style.md)、[后期论辩](prompts/late_argument.md)、[文体选择](prompts/persona.md)
- [证据卡](knowledge/style_evidence.jsonl)、[来源与抽样范围](docs/dev/leeao-source-map.md)
- [人工评估](evals/README.md)、[校准样段](evals/calibration.md)
- [变更记录](CHANGELOG.md)、[检索说明](TOOLS.md)

`facts/leeao/verified.jsonl` 保留旧路径以兼容已有引用，但目前只有语料元信息，没有已核人物生平库。写作是原创借鉴，不冒充李敖本人，不把他对旧事的评价移作今天的事实。
