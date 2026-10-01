# TOOLS

以下命令从工程根目录运行；换目录可用脚本绝对路径。Python 工具只用标准库。

## 定位原文

```sh
python3 tools/corpus.py search --work 李敖文存 文章
python3 tools/corpus.py search --work 大江大海骗了你 档案 --limit 3
python3 tools/corpus.py search --work 传统下的独白 --all 爱情 传统
```

`search` 按原文行搜索字面关键词，多个词默认任一命中，`--all` 要求同一行全部命中；输出路径、行号、最近的 Markdown 标题和上下文。它不做语义搜索，也不识别每处引语的说话者。多词分散时分别搜，再读上下文。

可用 `rg -n` 灵活搜索。读引文前看篇章标题、引语起止、作者/受访者/附录身份；目录命中不是正文证据。

## 元数据与校验

```sh
python3 tools/corpus.py index
python3 tools/validate_skill.py
python3 -m unittest discover -s tests
```

`index` 重建 `knowledge/source_manifest.json`，只保存文件清单、字节数、行数、SHA-256 和上游提交，不保存全文，只写本工程。

工具支持 `--upstream /绝对路径/leeao`。验证可加 `--offline`，只检查工程资源；离线通过不表示原文已核实。

## 材料缺失

没有本地语料时，原创文章可依据蒸馏规则写；查原话须用用户提供文本或可核对的其他来源。本工程只打包规则和元数据，上游全集单独获取，见 `docs/dev/leeao-source-map.md`。
