# Lee Ao Source Map

## 上游来源

- GitHub: `https://github.com/whatot/leeao`
- 本地路径: `../leeao-upstream/`
- 当前拉取提交: `c638b71 Merge pull request #6 from szabgab/patch-1`

上游 README 说明：whatot 并非原著者，只是将 wjm_tcy 编著的“大李敖全集”格式化为 mdbook 项目；权利归 leeao 与 wjm_tcy 保持。使用本工程时应把上游视为阅读和检索入口，不视为版权归属或权威校勘声明。

## 大类计数

- `01.自传回忆类`: 6
- `02.精品散文类`: 6
- `03.惊世杂文类`: 15
- `04.小说剧本类`: 7
- `05.诗集语录类`: 4
- `06.沉思日记类`: 11
- `07.采访序跋类`: 6
- `08.书信函件类`: 11
- `09.历史文化类`: 11
- `10.李敖节目演讲合集`: 6
- `11.李敖电子报合集`: 6
- `12.人物研究类`: 25
- `13.国民党史政类`: 7
- `14.台湾史政类`: 9
- `15.雷霆法律类`: 6
- `16.李敖祸台十书`: 11
- `17.百家论李敖合集`: 3

## 核心入口

- 全目录: `../leeao-upstream/SUMMARY.md`
- 项目说明: `../leeao-upstream/README.md`
- 编著者说明: `../leeao-upstream/wjm_tcy.md`

## 推荐核对命令

```sh
rg -n "关键词" ../leeao-upstream
sed -n '1,160p' '../leeao-upstream/类别/作品.md'
```
