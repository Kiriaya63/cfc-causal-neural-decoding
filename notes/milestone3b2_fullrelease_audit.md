# M3-B2 audit record

All 27 sessions were attempted. Coverage/causal totals describe pipeline-valid sessions only; NA is unassessed, never zero. Raw unit counts and channel provenance are independently read for all 27. Durations summed across release sessions are not unique animal-time: same-date Dino ACC/mPFC releases may overlap. Neuron identities are not matched across sessions.

Preflight: 27/27 PASS. Pipeline-valid: 24/27. {"PASS": 0, "WARN": 24, "FAIL": 3}

Frozen processing modules unchanged (SHA256 snapshot supplied). Checksum 34/34 match is user-reported; this audit checks extracted required files.

Official caveats retained from the previously source-verified mapping notes, with original spreadsheet row citations. No filtering, spectra, normalization, representation changes, split or model training.

Full audit executed; unresolved failures require human protocol decisions. Milestone 3 is not declared complete; M4 not started.


# M3-B2 结果解读（2026-09-15）

## 结论与统计口径

27/27 preflight PASS；27 个 session 均尝试同一冻结 pipeline，结果为 24 WARN、3 FAIL、0 PASS。
这里的“已审计”包括留下失败证据，并不等于 common pipeline 成功。
三个失败 session 的 label coverage、OOB、conflict 未完成，保持 NA；不能把它们当作零。

全部 27 个 raw SStable 文件中的 unit 数为 min/median/max = 10/36/113，且 numgoodcells 与 cell 数一致。
24 个通过完整 pipeline 的 session 对应范围为 10/34/113。
有效监督比例在这 24 个中为 10.3658% / 47.6581% / 89.3295%（min/median/max）。
24 个 session 的 analysis duration 总和 413639.304 s，监督秒数 193612 s。
同日 Dino ACC/mPFC releases 可能覆盖同一实际记录时间，这些求和是 release 条目总量，不能当作独立动物观察时长。

## 未解决结构问题

- Dino_061914_ACC 和 Dino_061914_mPFC：RecordingFileIntervals 第 4 行（从 1 开始）都是 `[10149.85,10149.85]`，违反 stop > start。两份 EEG 都为 6219440250 bytes，142 channels × 2 bytes = 284 bytes/frame，余数 142 bytes；即使移除零长度行，帧完整性仍未通过。不能自动删除该行、截断文件或补齐帧。
- 20140526_277um：metadata/XML acquisition rate 均为 1250 Hz；stable spike timestamps 的网格检查失败，unit 1 最大误差为 0.5 tick。Open-ended resolution 本身成功，analysis support 是 `[0,13572.36)`，失败发生在后续 spike validation。没有改变采样率或重新量化 spike 时间。

这两类失败均要求独立人工协议决定。完整原始值、其他 unit 的网格例子与复现入口见 structural_issues.md 和 session_details.json。

## Time support 与 labels

Open-ended provenance 出现在 JennBuzsaki22 的三个 session：20140526_277um、20140527_421um、20140528_565um。
三者都成功用物理 LFP 定义有限 support；第一个随后 spike 校验失败。
有限来源的 duration mismatch 是 BWRat18_020513、BWRat20_101513、Bogey_012615；三个 open-ended session 还保留 Inf-vs-finite 的显式 mismatch。
BWRat20_101513 metadata end 23347.5 s，GoodSleep/LFP/analysis end 23012 s，是此前 BWRat18 已见的模式。
在可验证的支持范围中，未发现 metadata 短于 LFP、GoodSleep 短于 LFP、非零 analysis origin 或 disconnected analysis support。

24 个成功 session 的 core-target OOB=0；辅助 OOB=2166（MA 1091、WakeInterruption 1075）。
没有新 WAKE/NREM/REM 核心标签组合；新增的是 Splinter_020515 的 `WAKE+SLEEP+MA`，`[5392,5413)` 共 21 s。
该 session 也有已见的 `WAKE+SLEEP+NREM`，`[5414,5455)` 共 41 s；所有冲突均保持 IGNORE。
所有类型合计冲突 3113 s。BWRat19_032413 没有有效 REM；其余 23 个完整可审计 session 含三种核心类别。失败的 3 个不作类别完整性结论。

## 同一动物的不同 session 是否更相似？

只能给出维度相关的描述，不能笼统回答“更相似”：

- 脑区相对一致：多 session animals 中，BWRat17/19/20/21、JennBuzsaki22、Splinter、Rizzo 的 selected LFP anatomy 各自一致；Dino 跨 ACC/mPFC。
- Unit 数并不稳定：BWRat20 为 22–66，Rizzo 为 26–93，Dino 为 16–113；未跨 session 匹配 neuron identities。
- 标签覆盖也并不稳定：BWRat21 的有效监督比例为 10.37%–80.33%；BWRat19 为 44.98%–71.27%，其中一天无有效 REM。
- BWRat17 比较一致：有效监督为 57.45%–60.06%；这不能推广为所有动物的性质。
- Dino 的 8 份 release 中 2 份失败；Jenn 的 3 份中 1 份失败。它们的 label 变异汇总只基于分别 6/2 份成功 session。

## Anatomy 与官方 caveats

Selected LFP anatomy（27 个 raw metadata/anatomy）为 ACC 6、MotorCtx 3、mPFC 14、OFC 4。
Theta 为 dhipp 3、dHipp 4、piriformL3 1、MotorCtx 2、ACC 3、mPFC 5、OFC 4，另有 5 个空 anatomy 标签。
空标签见 BWRat21_121113、Dino_061914_ACC、Dino_061914_mPFC、Dino_062014_ACC、Dino_062014_mPFC；channel number 仍存在。保留大小写及缺失值，没有换通道。
全部 ChannelAnatomy region labels 还包含 CeA。相较代表集没有新 region 名称。
先前官方表摘要把 Templeton 标为 OFC，而此 session 自身 ChannelAnatomy 的 selected LFP 为 mPFC、theta 为 dhipp；两份 provenance 均保留，未据此推断统一脑区。

- Ketamine session BWRat21_121613 的有效监督最低（10.37%），IGNORE 最高（89.63%），broad unlabeled 为 19139 s。说明该 session 对 coverage 审计重要，不能从这些数字推断 ketamine 导致缺失。
- BWRat21_121813 的 saline caveat 保留，有效监督为 80.33%。未进行药理组间统计比较。
- BWRat20_101513 的 ketamine-between-epochs caveat 同时伴随 duration mismatch 与 492 条辅助 OOB。
- Dino_072114_mPFC 的“few units”与 raw stable units=18 一致；“almost no assemblies”未在本阶段验证。
- Templeton stable units=10，为 release 最低；unstable units/high-frequency noise 未做独立验证。本阶段不进行稳定性或频谱分析。
- Rizzo_022615 的 additional unstable units 与 BWRat21_121113 的 later instability 仅保留为官方 caveat，不声称从当前 stable-unit counts 验证了时间稳定性。

## 阶段结论

全 release audit 的执行和交付已完成，但不能宣布全部 27 sessions 协议兼容，也不能据此宣布 Milestone 3 最终 PASS。
当前不进入 M4。下一步是人工审阅三个 FAIL 的证据并决定是否需要新的、适用于数据集的协议；本轮未修改冻结处理模块。
