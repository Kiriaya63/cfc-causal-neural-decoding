# CfC 因果神经解码项目总体研究规划
## 面向 Work 执行与个人复盘的统一版本

**项目名称：** 基于闭式连续时间网络（CfC）的严格因果睡眠状态神经解码  
**当前阶段：** M3-B2.2 三项通用协议扩展已人工批准并实现；全 release 重跑 27/27 preflight PASS、27 WARN / 0 FAIL、11 animals 统一 pipeline 完成，44/44 tests PASS（原 32 + 新增 12）。技术完成标准已满足，等待最终冻结复核，M4 尚未开始。  
**核心数据：** CRCNS fcx-1；后续使用实验室 Intan 数据进行冻结模型后的独立外部验证  
**文档用途：** 作为 Work 的长期执行边界、本人阶段复盘依据，以及后续论文结构的统一路线图。

---

# 1. 项目核心科学问题

本项目不把目标定义为“把 CfC 用在睡眠分类上”，而是尝试回答：

> **连续时间归纳偏置，是否能在严格因果的神经解码中带来可解释、可泛化的优势？这些优势是否主要出现在状态转换、不规则观测、多模态神经信号和低延迟推理等场景？**

因此，CfC 不是唯一主角，也不是预设赢家。项目需要在统一、严格、无未来信息泄漏的框架下，与传统和现代序列模型公平比较。

核心原则：

- 不预设 CfC 一定在分类准确率上获胜；
- 允许结果是“CfC 只在转换预测、缺失数据鲁棒性或推理效率上更好”；
- 如果 CfC 没有明显优势，也应如实报告；
- 方法学严谨性、可复现性、跨动物泛化和外部验证，本身就是项目价值的重要组成部分。

---

# 2. 当前已经完成的工作

## Milestone 1：单 session 数据读取与对齐

已完成 `BWRat17_121712` 的 metadata、LFP、stable spikes、sleep-state annotations 读取与统一时间轴验证，并生成 multimodal sanity-check figures 与 integration tests。

关键结果：

- 公共有效时间范围：`0–6059.4 s`
- LFP sampling rate：`1250 Hz`
- original acquisition rate：`20000 Hz`
- stable units：`50`
- 已识别 2 条越界 annotation：
  - `MATimePairFormat [8145,8155]`
  - `WakeInterruptionTimePairFormat [6801,6890]`
- 异常被显式报告，不静默修补。

**Milestone 1：PASS**

## Milestone 2：严格因果、模型就绪的数据样本层

已完成：

- 1 秒基础时间网格；
- half-open `[start, stop)` 约定；
- strict WAKE / NREM / REM / IGNORE 标签策略；
- past-only causal samples；
- configurable `5/10/30 s` context；
- spike count matrix；
- LFP lazy loading；
- 不 normalization、不滤波、不做未来统计；
- causality tests；
- single causal sample figure；
- label coverage figure。

`BWRat17_121712` 标签覆盖：

- WAKE：2426 s
- NREM：952 s
- REM：103 s
- IGNORE：2578 s
- 完整 1 秒 bins：6059
- conflict：0
- out-of-bounds annotations：2
- 6059–6059.4 s 尾段不构成完整 target bin；
- 尾段 7 个 spikes 被显式报告。

关键因果定义：

\[
X_t=[t-W,t)
\]

\[
y_t=\text{state on }[t-1,t)
\]

例如：

- decision time：2431 s
- input：`[2401,2431)`
- target：`[2430,2431) -> WAKE`
- `[2431,2432)` 为 broad SLEEP 但存在 fine-state gap，因此为 `IGNORE`

Milestone 1 + 2 共 11 个 tests 已通过。

**Milestone 2：PASS**

---

# 3. 后续总体路线：双轨推进

## Track A：必须完成的严谨 benchmark

目标：即使没有非常惊艳的新发现，也能形成一篇完整、可信、可复现的方法/计算神经科学论文。

必须完成：

1. 多 session / 多动物统一 QC；
2. 跨动物划分；
3. 严格 causal preprocessing；
4. 统一 baseline；
5. CfC 与 LSTM / TCN / 现代 SSM 公平比较；
6. LFP-only / spikes-only / fusion ablation；
7. 状态分类；
8. 状态转换预测；
9. efficiency benchmark；
10. 冻结模型后的 Intan 外部验证；
11. 完整开源 pipeline 与 reproducibility report。

## Track B：冲击更高水平的科学发现 / 方法创新

重点探索：

1. irregular sampling / missing observation benchmark；
2. asynchronous LFP + spikes 连续时间建模；
3. 不同动物不同 neuron 数量下的统一神经群体表示；
4. CfC hidden dynamics / learned time constants 的生理解释；
5. state-transition 前的潜在动力学预兆；
6. 多数据集、跨脑区迁移；
7. 如有必要，发展新的 neural-specific continuous-time architecture。

Track B 失败不能拖垮 Track A；Track B 成功则显著提高论文上限。

---

# 4. Milestone 3：多 session 泛化与数据集审计

## M3-B2 全 release audit（2026-09-15，执行完成，等待人工决定）

- 用户确认全部数据外部下载/checksum/extraction 完成（34/34 match）；实际 27 个 session、11 个 animals 均通过必需文件只读 preflight。
- 27 个 session 均尝试同一冻结 M3-B1.1 pipeline，24 WARN、3 FAIL；未改动任何 `src/data` 处理模块，保留 SHA256 记录。
- Dino_061914_ACC 与 Dino_061914_mPFC 都有 metadata 第 4 行 `[10149.85,10149.85]`；EEG 文件 6219440250 bytes / 284 bytes-frame 各余 142 bytes，另有帧不完整问题。没有删行、截断或补帧。
- 20140526_277um 的 open-end 已合法解析到 `[0,13572.36)`，但 metadata/XML 声明的 1250 Hz acquisition grid 与 stable spikes 不一致（unit 1 最大 0.5 tick），保持 FAIL；没有调整采样率或 timestamps。
- 全 27 个 raw stable unit count min/median/max=10/36/113；24 个通过全链路的 validated counts 为 10/34/113。24 个成功 session 的 valid supervision min/median/max=10.3658%/47.6581%/89.3295%；analysis duration 合计 413639.304 s，监督秒数 193612 s（release 条目求和，非独立动物时长）。
- 可审计的 24 个 core OOB=0，auxiliary OOB=2166（MA 1091、WakeInterruption 1075）。BWRat19_032413 缺少有效 REM。新辅助组合 Splinter_020515 WAKE+SLEEP+MA `[5392,5413)` 21 s 保持 IGNORE，未出现新的核心标签冲突组合。
- 三个 Jenn sessions 都有 open-ended provenance；有限 duration mismatch 在 BWRat18_020513、BWRat20_101513、Bogey_012615。五份 session 的 theta channel 有编号但 anatomy 空白。官方 caveats 均保留，不自动排除。
- 多 session 动物的 selected LFP anatomy 通常一致，Dino 跨 ACC/mPFC；unit/coverage 同动物内仍可强烈变化。详细 within-animal 描述、官方 caveat 对照与统计口径见 `notes/milestone3b2_interpretation.md`。
- 全部 27 个原 tests 保留通过，新增 5 个 full-release invariant tests，32/32 PASS；失败的科学数据案例保留 FAIL，测试验证其有可复现证据。
- 输出在 `reports/milestone3b2/`；`reports/milestone3b/full_release_inventory.csv` 已区分 downloaded/extracted/preflight_passed/audited/qc_status，三个 FAIL 也是已审计，不再误标 missing。
- M3-B2 执行完成，但不宣布 Milestone 3 最终 PASS。下一步仅由用户决定如何处理零长度 provenance、半帧 EEG 和 spike acquisition-grid 不一致；本轮未修改冻结协议，不进入 M4。

## M3-B2.1 structural-failure diagnosis（2026-09-15，只读诊断完成）

- 两个 Dino FAIL 的 raw `RecordingFileIntervals` 均含 `[10149.85,10149.85)`；按半开集合这是 empty interval。仅在数学上忽略其 union 贡献后，其余四行严格首尾相接并连续覆盖 `[0,17519.55)`，但没有实施删行或解析规则。
- 两个 EEG 均为 6,219,440,250 bytes，142 channels、int16、284 bytes/frame；最大完整前缀含 21,899,437 frames，余 142 bytes，按 1250 Hz 得 17,519.5496 s。余数物理上位于最大完整前缀之后；flat int16 无内部 frame marker，故不能仅凭文件长度证明此前绝无插入/删除，但没有发现中间错帧的正证据。
- 27-session 只读扫描确认：仅这两个 session 有 `start == stop` row，也仅这两个有非零 EEG frame remainder；未发现 `stop < start`，未发现 remainder 达到 frame width。
- `20140526_277um` 的 62 units / 2,214,209 spikes 全部 finite、非负、逐 unit 非递减，0 条超出 `[0,13572.36)` support，逐 unit duplicate 为 0。1250 Hz 上仅 137,189 条在容差内（93.8042% off-grid），20 kHz 上 2,214,209/2,214,209 在容差内，最大误差 2.98e-8 tick。
- 相邻 `20140527_421um` 与 `20140528_565um` 的 XML/MAT acquisition rate 都是 20 kHz，三天 spike timestamp 的最低被测全覆盖网格均为 20 kHz；`20140526` 唯独 XML/MAT 声明 1250 Hz，但事件时钟仍与 20 kHz 一致。
- 现有 half-open causal binning 只用排序后的 raw seconds 与 `searchsorted`，数学上不依赖 `spike_time × acquisition_rate` 为整数；grid check 当前属于完整性诊断与被编码成 fatal guard 的历史假设，不是 bin assignment 的必要条件。未修改该 guard。
- 可供人工决定的最小 dataset-wide 候选扩展有三项且彼此独立：empty row 对 derived union 的零贡献、最大完整 frame 前缀、declared acquisition clock 与 observed event clock 分离。均未实施，三个 FAIL/WARN 状态保持原样。
- 证据输出见 `reports/milestone3b2_1/`；`src/data` 15 个冻结模块 SHA256 仍与 M3-B2 snapshot 15/15 一致，未重跑 27-session audit，不进入 M4。

## M3-B2.2 approved protocol extensions（2026-09-15）

- 用户已批准三项 dataset-wide 扩展：finite `[a,a)` 作为 empty set 保留 raw row 并记录 WARN；不足一帧尾部仅在可信 finite official endpoint 距完整前缀终点不超过一个 LFP sample 时使用 read-only complete prefix；declared spike-grid 不一致作为 WARN，raw timestamps 与 declared acquisition rate 均不变。无 session/animal processing branch。
- 新版本对全 27 sessions / 11 animals 重新运行统一审计：preflight 27/27 PASS；最终 0 PASS、27 WARN、0 FAIL。此前三个 FAIL 均完整处理，未解决 structural issue 为 0。
- 两个 Dino support 均为 `[0,17519.5496)`：原 EEG 6,219,440,250 bytes，frame width 284，完整 frames 21,899,437，尾部 142 bytes，官方 end 17519.55，相差 0.0004 s。空 metadata row 原样保留。
- Dino ACC：52 units，WAKE/NREM/REM/IGNORE=630/1665/299/14925 s，监督率 14.8068%；Dino mPFC：60 units，630/1597/296/14996 s，监督率 14.4015%。两者 core OOB/conflict 均为 0；5/10/30 s 样本数分别均为 2594、2523。
- Jenn 首日 `20140526_277um`：declared acquisition=1250 Hz，最低被测全匹配 event grid=20000 Hz，原 2,214,209 spikes 完全保留。62 units，WAKE/NREM/REM/IGNORE=2141/2754/181/8496 s，监督率 37.4005%；core OOB/conflict=0，5/10/30 s 样本均为 5076。
- 全 release stable units min/median/max=10/36/113；valid supervision fraction min/median/max=10.3658%/44.3762%/89.3295%。core-target OOB=0，auxiliary OOB=2224（MA 1118、WakeInterruption 1106）；BWRat19_032413 仍缺少有效 REM。
- 6 种 conflict 共 3113 s，全部保持 IGNORE；此次恢复三个 session 没有新增 conflict。27 session analysis duration 求和 462250.7632 s，监督时间求和 203805 s；同日 Dino ACC/mPFC 可共享时间，不能视作独立动物记录时长。
- 原 24 个成功 session 的 support、labels、coverage、OOB、conflicts、units、5/10/30 s 样本数逐项一致；label/causal/spike binning 五个模块与旧 SHA256 一致。523 个 raw 文件前后 size/mtime 检查一致，并对小于 100 MB 的非 EEG 文件核对 SHA256；没有重算全部 EEG checksum。
- 新输出在 `reports/milestone3b2_2/`，旧 M3-B2 与 M3-B2.1 报告保留。inventory 更新为全部已审计 WARN；协议细节见 `notes/milestone3b2_2_protocol_extensions.md`。M4 尚未执行。
- 完整测试最终 44/44 PASS（99.510 s，0 skipped）：原 32 项保留，新增 12 项结构测试。全 27 sessions 的 support、target mask、5/10/30 s past-only invariants 和无身份分支检查均通过。M3 已具备正式冻结条件；待用户复核后可进入 M4 representation/protocol design，本轮不执行 M4。

## M3-A 验收与 M3-B 范围（2026-09-14）

用户已验收 5-session pilot 为 M3-A PASS；全量 27 sessions / 11 animals 属于 M3-B，尚未验收。
深度 QC 显示：133 条越界行全部来自 MA/WakeInterruption，核心 Wake/REM/SWSPacket 越界为零。
BWRat18 的冲突为 WAKE+MA [3644,3653) 9 s 与 WAKE+WakeInterruption [3712,3793) 81 s；
Splinter_020915 为 WAKE+WakeInterruption [17349,17424) 75 s 与 WAKE+MA [17432,17443) 11 s。
这些冲突仍按原 strict policy 归为 IGNORE，未修改时间支持、通道选择或 spike representation。
5 只动物均有有效 WAKE/NREM/REM；动物汇总中的 unit counts 为每 session 分布，不能解释为跨天唯一神经元总数。
输出见 `reports/milestone3b/pilot_deep_qc.md`、`animal_qc.csv`、`full_release_inventory.csv`。
只读检查 F:/CfC-Sleep 后仅发现 5 个 session 的压缩包及解压数据；其余 22 个标为 missing_not_audited。
官方清单同时包含 Splinter_020515 与 Splinter_020915；后者是 pilot 使用的 session，前者是全量待审计的另一个 session。
下一步需要补齐缺失 session 的本地路径/数据后，才能完成全量分布与 11-animal 汇总；暂不制定 inclusion/representation/preprocessing policy。

## M3-B 官方 animal-session mapping（2026-09-14，等待人工复核）

- 官方 `WatsonSleepHomestasis2016Table.xlsx` 给出 11 个 animal 分组和 27 个 recording rows；本地 data-description PDF 独立陈述 11 animals / 27 sessions；
- 表内 27 个 `Session Name` 与官方 `filelist.txt` 的 27 个 release basename 集合完全一致，无命名差异；27/27 mappings 均为 confirmed，无 probable/unknown；
- 当前已覆盖 BWRat17、BWRat18、BWRat19、BWRat20、Splinter，共 5/11 animals；未覆盖 BWRat21、Dino、JennBuzsaki22、Bogey、Rizzo、Templeton；
- 建议每个未覆盖动物下载其最小 archive：BWRat21_121613、Dino_072114_mPFC、20140528_565um、Bogey_012615、Rizzo_022715、Templeton_032415；总计 19,257,746,171 bytes（17.94 GiB）；
- BWRat21_121613 为 ketamine session；Dino_072114_mPFC 被官方表标注为 units 较少；Templeton_032415 被标注为 units unstable / high-frequency noise。这些是未来 audit provenance，不构成当前 inclusion 决定；
- 已更新 `reports/milestone3b/full_release_inventory.csv`，保持 5 个已审计与 22 个 `missing_not_audited` 状态；未下载任何数据，未修改 processing pipeline；
- 正式映射、动物汇总与下载候选见 `reports/milestone3b/fcx1_animal_session_map.*`、`fcx1_animal_release_summary.csv`、`m3b1_download_candidates.csv`。

## M3-B1：11-animal representative-session audit（2026-09-14，等待人工复核）

- 用户已在 Work 外部完成 6 个新增 session 的下载、CRCNS archive checksum 验证与解压；本轮代表集采用用户有意选择的 `BWRat21_121813` 与 `Dino_072314_mPFC`，不使用先前下载规划中的替代项；
- 11/11 session 的目录与 metadata、XML、ChannelAnatomy、GoodSleep、WSRestrictedIntervals、SStable、EEG 七类必要文件均通过只读 preflight；
- 冻结 pipeline 在 10/11 session 上完成统一 time support、strict labels 与 5/10/30 s past-only samples；这 10 个均为 WARN、core alignment 与三种 causal window 均有效；
- `20140528_565um` 为 FAIL：官方 `BasicMetaData.RecordingFileIntervals` 与 `GoodSleepInterval.timePairFormat` 都是开区间式 `[0, Inf]`。实际 EEG support 有限且文件完整，但现有有限区间校验在 metadata 阶段停止；未用 last spike / last annotation 推断终点，未增加 JennBuzsaki22/session-specific fallback；
- 10 个可审计 session 的 core-target annotation OOB 为 0；辅助 OOB 共 679 行（MA 279、WakeInterruption 400）。JennBuzsaki22 因 analysis end 未定义，OOB 不作推断；
- 新 conflict type 出现在 Rizzo：`WAKE+SLEEP` 1 s、`WAKE+SLEEP+NREM` 29 s、`WAKE+SLEEP+WakeInterruption` 61 s；仍全部按 strict policy → IGNORE，其中 `[9981,10010)` 是 29 s 的 WAKE/NREM 核心 target 冲突；
- 新 time-support pattern 包括 Bogey 的 metadata/GoodSleep 终点晚于实际 LFP（候选 support 正确截于 LFP，显式 `duration_mismatch`）以及 JennBuzsaki22 的非有限 provenance sentinel；非零 origin、disconnected finite support、malformed intervals 在 10 个可审计 session 中均未出现；
- 10 个可审计 session 的 stable units 为 10–93（median 38）；均含 WAKE/NREM/REM。valid supervision 为 24.701%–89.329%，REM 为 1.700%–15.932%，IGNORE 为 10.671%–75.299%；
- selected LFP anatomy 横跨 ACC、MotorCtx、OFC、mPFC；theta anatomy 还包括 dHipp/dhipp、piriformL3。保留官方原始大小写，不做 representation 决策；Templeton caveat 仅保留为 provenance；
- 原 18 tests 继续通过，并新增 3 个结构性 regression tests；当前 21/21 PASS；
- 输出见 `reports/milestone3b1/fcx1_11animal_session_qc.*`、`fcx1_11animal_summary.*`、`structural_issues.md` 与 `notes/milestone3b1_11animal_audit.md`。M3-B1 已执行完但尚未人工验收；整个 Milestone 3 仍未完成，暂不进入 27-session audit。

## M3-B1.1：dataset-wide open-ended time-support rule（2026-09-14，等待人工复核）

- 通用规则只接受 `finite start + positive-infinity stop`；`+Inf` 表示 official provenance 没有给出 finite upper bound，raw metadata 与 raw GoodSleep interval 均原样保留；
- derived support 明确分层为 raw metadata、raw GoodSleep、verified physical LFP、resolved metadata constraint、resolved GoodSleep constraint、analysis support 与 resolution method；
- `I_analysis = I_LFP ∩ I_metadata_constraint ∩ I_GoodSleep_constraint`。open end 只有在 EEG 存在且非空、channel/sample-rate 合法、int16 frame width 已知、文件大小可被 frame width 整除且 LFP duration finite positive 时才能裁到实际 LFP；
- NaN、`-Inf`、non-finite start、stop ≤ start、malformed/overlapping interval structures 仍 FAIL；last spike、last annotation、core-state interval 或 WakeSleep episode 均不参与 boundary resolution；
- `20140528_565um` 的 raw metadata 与 raw GoodSleep 保持 `[0,+Inf)`，resolved constraints 与 analysis support 均为 `[0,12395.736)`，method 为 `open_end_clipped_to_verified_lfp_support`；
- JennBuzsaki22 现可由公共 pipeline 完整处理：33 stable units、1,183,330 spikes；WAKE/NREM/REM/IGNORE 为 789/2746/523/8337 s，有效监督比例 32.739%；core annotation OOB=0、conflict=0，5/10/30 s causal sample counts 均为 4058；
- 11/11 representative sessions 现在均为 WARN、0 FAIL，全部 core alignment 与 causal invariants 有效；stable-unit min/median/max 更新为 10/36/93；
- 原 21 tests 继续通过，新增 6 个 open-end regression tests，当前 27/27 PASS；实现中没有 session/animal-specific branch；
- 协议记录见 `notes/milestone3b1_1_open_ended_time_support.md`，更新后的 11-animal reports 见 `reports/milestone3b1/`。原 `structural_issues.md` 已移除，因为当前代表集不再存在未解决的 protocol-breaking structural issue；
- M3-B1.1 自动完成但尚未人工验收。按用户边界暂停，不下载或审计剩余 16 sessions，不进入 Milestone 4。

## 目标

回答：

> **Milestone 1/2 的单-session pipeline，是否能在不同动物和不同 session 上不依赖特殊硬编码地复用？**

当前第一轮审计：

- `BWRat17_121712`
- `BWRat18_020513`
- `BWRat19_032513`
- `BWRat20_101013`
- `Splinter_020915`

## 时间支持规则（2026-09-14；M3-B1.1 扩展 open-ended provenance）

- 候选 analysis support 由实际 LFP support、metadata constraint 与 `GoodSleepInterval` constraint 的交集定义；raw official intervals 与 resolved constraints 必须分开保留；
- stable spikes 与主 WAKE/SLEEP annotations 只用于一致性验证，不使用 last spike 或 last annotation 缩短 recording end；
- `BasicMetaData.RecordingFileIntervals` 保留原值作为 provenance，不覆盖、不改写；
- 合法 `[finite start,+Inf)` stop 表示没有 finite official upper bound；只有 verified finite LFP support 可以在 derived constraint 层解析该 open end；
- metadata、LFP、GoodSleep 或候选 analysis support 的时长差异必须以 `duration_mismatch` 显式记录；
- BWRat18_020513 已验证：metadata end 为 `9388.8 s`，实际 LFP 与 GoodSleep end 均为 `7591 s`，因此 analysis end 为 `7591 s` 且 `duration_mismatch=True`；last spike 为 `7590.45115 s`，未参与边界定义；
- 新增 BWRat18 时间支持 regression test 已通过，原 Milestone 1/2 的 `11/11` tests 继续通过；Milestone 3 尚未判定 PASS。

## 主要任务

对每个 session 统一运行：

- metadata loading；
- LFP inspection；
- stable spike loading；
- sleep-state loading；
- common-clock validation；
- strict label timeline；
- spike binning；
- causal-window construction；
- session-level QC。

形成 aggregate QC table，至少记录：

- recording duration；
- n_channels；
- LFP / acquisition sampling rate；
- recommended LFP channel；
- theta channel；
- available anatomy；
- stable unit count；
- total spike count；
- WAKE/NREM/REM/IGNORE coverage；
- unlabeled / gap / conflict；
- out-of-bounds annotation；
- tail duration / tail spikes；
- core alignment validity；
- causal sample validity；
- PASS / WARN / FAIL。

## 特别关注

### A. stable units 数量是否跨 session 变化

先观察真实分布，再决定未来如何统一 spike representation。Milestone 3 暂不决定 fixed-N、population rate、shank aggregation、neuron encoder + pooling 等方案。

### B. LFP channel / anatomy 是否一致

不假设 ACC 永远是 channel 13，也不假设 dHipp/theta 永远是 channel 65。必须从每个 session 自己的 metadata / XML / anatomy map 中读取。

### C. label quality 是否一致

比较 coverage、gap、conflict、out-of-bounds 与 WAKE-SLEEP episode validity。

## 完成标准

- 至少 5 个 session、多动物统一通过审计；
- 无 session-specific hard-coded processing；
- M1/M2 regression tests 继续 PASS；
- 每个 session 有结构化 QC；
- 有 aggregate QC table；
- 已掌握 stable-unit count、LFP channel、label coverage、annotation quality 的跨 session 差异；
- 所有异常显式报告；
- 形成 `milestone3_dataset_audit.md`。

## 当前实现状态（2026-09-14，等待人工复核）

- manifest 中 5 个 session、5 个动物身份均已发现并完成统一审计；第五个 session 已核实为 `Splinter_020915`；
- 5/5 session 均建立了有效 core alignment，并分别通过 5/10/30 s past-only causal sample 检查；
- 自动 QC 判定为 `PASS=0, WARN=5, FAIL=0`：WARN 表示 pipeline 可运行但仍保留时长、annotation、coverage、conflict 或尾段 finding，不代表核心对齐失败；
- analysis duration 为 `3928.8–23487.5 s`，stable units 为 `22–61`，total spikes 为 `222,046–2,132,698`；
- anatomy 涵盖 ACC、CeA、MotorCtx、OFC、dhipp、piriformL3；recommended LFP/theta channel 及其脑区均随 session 变化；
- 越界 annotation 不只出现在 BWRat17：BWRat17/BWRat18/BWRat19/BWRat20 分别为 2/51/54/26 条；Splinter 为 0 条；
- strict-label conflict 出现在 BWRat18（90 s）与 Splinter（86 s）；
- BWRat18 是本轮唯一 `duration_mismatch` session，按冻结规则使用 `7591 s` analysis end，并保留 metadata `9388.8 s` provenance；
- 已生成 5 份 individual JSON、1 份 aggregate CSV、1 份 aggregate Markdown 和 `notes/milestone3_dataset_audit.md`；
- 原 Milestone 1/2 的 `11/11` tests 继续通过；连同 BWRat18 时间支持与 multi-session audit tests，当前为 `16/16 PASS`；
- 当前只表示实现和自动验证完成；在本人检查报告并接受之前，不将 Milestone 3 标记为最终 PASS。

---

# 5. Milestone 4：正式 causal preprocessing / feature protocol

Milestone 3 结束后，再决定真正的模型输入协议。

## LFP

需要系统比较和决定：

- raw LFP 还是派生特征；
- 是否降采样；
- causal filtering；
- causal bandpower；
- delta / theta / spindle-related features；
- spectrogram-like representation；
- 如何保证滤波和频谱特征绝不使用未来信息。

严格禁止：

- `filtfilt`
- zero-phase filters
- centered rolling windows
- centered Welch
- 利用未来样本构造当前特征

## Spikes

根据 M3 的 stable-unit count 分布决定：

- unit-wise 输入；
- population rate；
- shank-level aggregation；
- neuron encoder + pooling；
- variable-set representation。

## Normalization

只能在未来 training animals / training data 上 fit。禁止 full-session z-score 或用 validation/test 动物统计量参与 scaler fitting。

## 输出

- 冻结的 preprocessing protocol；
- causal feature tests；
- leakage audit；
- feature ablation protocol；
- 明确的输入张量定义。

---

# 6. Milestone 5：跨动物数据划分与基础 baseline

建立真正的 animal-level evaluation protocol。

优先：

\[
\text{Leave-One-Animal-Out}
\]

或根据数据规模使用 animal-level train/val/test 与 repeated animal-level split。禁止随机时间片跨集合。

Baseline 顺序：

1. Logistic Regression / Linear baseline；
2. HMM；
3. TCN；
4. LSTM / GRU；
5. CfC；
6. 至少一个现代 causal SSM，例如 S4 / S5 / Mamba 类模型。

要求：相同输入、相同 split、相同 early stopping 原则、相同 random seeds、尽量公平的参数规模比较，并报告多个 seed 的均值和方差。

指标至少包括：

- Macro-F1
- Balanced Accuracy
- Cohen's kappa
- per-class F1
- confusion matrix

尤其关注 REM，而不是只看总体 accuracy。

---

# 7. Milestone 6：状态转换预测

这是本项目最重要的科学增量之一。

任务包括：

### REM entry prediction

\[
P(\text{REM entry within }H)
\]

### NREM -> Wake prediction

\[
P(\text{Wake transition within }H)
\]

### Time-to-next-transition

如标签质量允许，预测：

\[
T_{\text{next transition}}-t
\]

H 建议：5 s、10 s、30 s。

重点比较 steady-state classification、transition forecasting、transition-near performance。如果 CfC 只在 transition forecasting 上有优势，也属于有价值结论。

---

# 8. Milestone 7：irregular observation / missing-data benchmark

这是验证“为什么需要连续时间模型”的关键实验。

构造可控 stress test：

- 10% observation missing；
- 20% missing；
- 40% missing；
- irregular sampling；
- recording gaps；
- LFP 与 spikes 异步可用；
- variable \(\Delta t\)。

关注：

\[
\text{performance degradation vs missingness}
\]

核心问题：CfC 是否在规则采样时只与 LSTM 持平，但在 irregular observation 下更稳定？如果成立，将形成很有说服力的 continuous-time model justification。

---

# 9. Milestone 8：多模态消融与机制分析

必须做：

\[
\text{LFP only}
\]

\[
\text{Spikes only}
\]

\[
\text{LFP + Spikes}
\]

不能只比较 accuracy，还要研究：

- steady-state 中谁贡献更多；
- transition 前谁提供更多增量；
- fusion 的提升发生在哪里；
- 某些动物/状态是否依赖特定模态。

进一步分析 delta、theta、spindle、population firing、UP/DOWN states，以及在合适脑区中的 ripple。

---

# 10. Milestone 9：CfC dynamics 与可解释性

如果 CfC 主实验结果值得继续深挖，则分析：

- learned time constants；
- hidden-state trajectories；
- transition-aligned hidden dynamics；
- PCA / UMAP / state-space trajectories；
- 与神经生理变量的相关关系。

目标不是简单展示“hidden state 能分三类”，而是尝试回答：

> **模型内部动力学是否与真实睡眠转换中的神经生理时间尺度和状态轨迹对应？**

特别关注 Wake -> NREM、NREM -> REM、REM -> Wake。

---

# 11. Milestone 10：计算效率与实时性

除性能指标外，还要比较：

- 参数量；
- training time；
- inference latency；
- peak GPU memory；
- throughput；
- 可选 FLOPs。

重点展示 Performance vs Latency 与 Performance vs Parameter Count。

如果 CfC 并非最高准确率，但能实现接近最优性能 + 更低 latency + 更小模型 + 更强 irregular-data 鲁棒性，仍然是有价值结论。

---

# 12. Milestone 11：冻结模型后的 Intan 外部验证

原则：

1. preprocessing、architecture、hyperparameters、thresholds、normalization 规则先在 fcx-1 上确定；
2. 冻结后再测试实验室 Intan 数据；
3. 不因 Intan 结果不好而回头重新调主模型；
4. 如确需调整，必须作为单独 sensitivity analysis；
5. 明确报告 domain shift。

最终回答：模型是否能从 public benchmark 泛化到独立实验室数据？

---

# 13. 可选 Milestone 12：跨数据集 / 跨脑区迁移

可考虑：

- hc-11
- hc-14
- pfc-2

用途：跨脑区、跨实验、跨记录体系、domain shift stress test。

注意这些数据的标签体系不完全一致，不应直接混合训练，更适合作为迁移/外部 stress test。

---

# 14. 潜在方法创新方向

## Asynchronous multimodal continuous-time neural decoder

不再要求所有信息都压成规则 1 秒同步 bins，而是保留 spike events 与 LFP observations 的真实时间差和异步性。

## Variable-neuron representation

为解决不同动物不同 neuron 数量：

\[
\text{neuron encoder}
\rightarrow
\text{permutation-invariant pooling}
\rightarrow
\text{continuous-time dynamics}
\]

如果实现成功，项目贡献将从“测试 CfC”升级为“为多模态、异步、变数量神经群体数据设计连续时间神经解码框架”。

---

# 15. 论文最终主张的优先顺序

1. **严格因果 benchmark**
2. **跨动物泛化**
3. **状态转换预测**
4. **LFP / spike / fusion 系统消融**
5. **irregular observation 下的 continuous-time 优势**
6. **效率与实时性**
7. **冻结后的独立 Intan 验证**
8. **hidden dynamics / time constants 的生理解释**
9. **若成功，进一步提出新的 asynchronous multimodal 方法**

避免主要主张写成：

> “CfC 第一次用于某个睡眠任务，因此新颖。”

更强的主张应是：

> **我们建立了一个严格因果、多模态、跨动物的神经状态解码 benchmark，并系统检验 continuous-time inductive bias 在状态转换、不规则观测和实时推理中的实际价值。**

---

# 16. 投稿层级预期

## 基础完整版本

如果完成 fcx-1 全数据、严格 causal protocol、animal-level evaluation、CfC + 强 baseline、LFP/spike/fusion、transition prediction、efficiency、Intan external validation，但没有明显新算法或强生物学发现：

- Journal of Neural Engineering
- Neuroinformatics
- Journal of Neuroscience Methods
- Neural Networks
- IEEE Journal of Biomedical and Health Informatics

优先考虑 JNE 级别。

## 强化版本

如果同时完成跨动物、transition forecasting、irregular sampling、multimodal mechanism、hidden dynamics、efficiency、frozen external validation、reproducible benchmark：

- **PLOS Computational Biology**
- **Cell Reports Methods**
- **Communications Biology**

这是当前最值得争取的主要目标区间。

## 高风险冲刺版本

如果进一步拥有新的 asynchronous multimodal continuous-time decoder、多动物、多 public dataset、frozen Intan external validation、online/replay real-time demonstration、transition forecasting 明显优势、hidden dynamics 揭示可重复的新神经转换规律：

- **Nature Communications**

Nature Neuroscience / Nature Machine Intelligence / Nature Computational Science 暂不作为“按当前方案完成即可达到”的预期。

---

# 17. 风险与防线

## 风险 1：CfC 普通分类并不优于 baseline

应对：transition prediction、irregular sampling、efficiency、robustness、interpretable dynamics。

## 风险 2：不同 session neuron 数量差异过大

应对：Milestone 3 先观察真实分布，再决定统一 representation。

## 风险 3：不同 session LFP channel 不一致

应对：依赖 metadata/anatomy 自动选择，不写死 channel；无法统一时显式报告。

## 风险 4：sleep annotation 不完美

应对：strict policy + IGNORE + explicit QC，不静默补标签。

## 风险 5：未来信息泄漏

应对：past-only windows、causal preprocessing、future perturbation tests、animal-level split、training-only normalization、leakage audit。

## 风险 6：Intan 外部验证结果不好

不得回头调主模型。将其作为真实 external validation 和 domain shift 结果报告。

---

# 18. Work 的长期执行原则

1. **先读 protocol，再改代码。**
2. 不因为“效果不好看”自动改变科研定义。
3. 遇到影响科学结论的选择，先报告，不自行决定。
4. raw data read-only。
5. 每个 Milestone 都必须有：protocol、code、tests、machine-readable report、human-readable notes、sanity-check figures、completion criteria。
6. 所有已有 regression tests 必须持续通过。
7. 不静默修补异常数据。
8. 不使用未来信息。
9. 不在 test / validation / external data 上 fit normalization。
10. 每个关键实验都留下可复现配置和随机种子。
11. 不一次性跨越多个 Milestone。
12. 每个阶段完成后先停下来，由本人复核，再进入下一阶段。

---

# 19. 当前下一步

当前暂停在：

## Milestone 3-B2.2 — 全 release 协议冻结复核

三项通用扩展已人工批准并实现，全量重跑 27/27 preflight PASS、27 WARN / 0 FAIL、44/44 tests PASS。新报告与旧版 24 个成功 session 的逐项回归对照已完成；当前已具备冻结 M3 和讨论 M4 的条件，等待用户复核及下一阶段指令。

当前暂停边界：**不自行进入 M4，不训练 CfC，不做 filtering、normalization 或正式 train/test split。** 本轮验证回答：

\[
\boxed{\text{现有 causal pipeline 是否能可靠扩展到不同 fcx-1 动物和 session？}}
\]

---

# 20. 项目最终希望形成的论文故事

理想版本不是：

> “我们把 CfC 用到了睡眠分类上。”

而是：

> **We establish a strictly causal, multimodal and cross-animal benchmark for neural-state decoding from LFP and spiking activity, and systematically test when continuous-time inductive biases improve state decoding, transition forecasting, robustness to irregular observations and computational efficiency.**

如果进一步得到可靠的 hidden-dynamics 和 transition-neurophysiology 结果，则提升为：

> **Continuous-time neural dynamics not only decode sleep states, but capture and anticipate physiologically meaningful neural population transitions across animals and recording domains.**

---

**文档状态：研究路线图 v1.0**  
**下一次更新建议：M3-B1.1 人工复核或 full-release audit 决策后。**
