# CfC 因果神经解码项目总体研究规划 v2.0
## 长期 Roadmap：严格因果、多模态、跨动物连续时间神经解码

**项目名称：** 基于闭式连续时间网络（CfC）的严格因果睡眠状态神经解码  
**核心数据集：** CRCNS fcx-1（27 sessions / 11 animals）  
**外部验证：** 实验室 Intan 数据  
**当前项目状态：** Milestone 1–3 已完成并冻结；下一阶段为 Milestone 4  
**文档定位：** 长期总体研究路线图。仅在研究主线发生实质变化时更新版本，不随每个 Milestone 的日常推进频繁改版。

---

# 1. 项目最终科学问题

本项目不以“CfC 首次用于睡眠分期”为主要创新，而围绕一个更强、长期稳定的科学问题展开：

> **在严格因果、跨动物、多模态神经解码中，continuous-time inductive bias 什么时候真正有价值？**

项目希望逐层回答：

\[
	ext{Can it decode?}
ightarrow
	ext{Can it generalize?}
ightarrow
	ext{When does continuous time help?}
ightarrow
	ext{Does the learned dynamics mean anything?}
\]

具体包括：

- 常规 sleep-state decoding；
- 跨动物泛化；
- state-transition forecasting；
- irregular / missing / asynchronous observation；
- variable neural population；
- multimodal fusion；
- inference efficiency；
- external-domain generalization。

CfC 不是预设赢家。项目允许以下结果：

- CfC 在普通分类中与 LSTM / TCN 持平；
- CfC 只在 transition forecasting、irregular observation robustness 或 latency 上体现优势；
- CfC 没有明显优势，也如实报告。

严谨 benchmark、跨动物评估、可复现性和冻结后的外部验证，本身就是项目价值的重要组成部分。

---

# 2. 两条研究轨道

## Track A：必须完成的严谨 benchmark

Track A 是论文的主干和保底闭环。

必须完成：

1. 全 release 数据审计；
2. 严格 causal data protocol；
3. representation protocol；
4. animal-level evaluation；
5. CfC 与经典 / 现代 causal baselines 公平比较；
6. LFP-only / spikes-only / fusion ablation；
7. state classification；
8. transition forecasting；
9. irregular / missing observation stress test；
10. efficiency / latency benchmark；
11. frozen Intan external validation；
12. 完整 reproducibility report 与可复现 pipeline。

即使没有新的算法创新，只要 Track A 完整，也应形成一篇扎实的方法 / 计算神经科学论文。

## Track B：提高论文上限的方法创新

Track B 探索：

- variable-neuron representation；
- asynchronous multimodal continuous-time decoding；
- event-time-aware neural representation；
- permutation-invariant neural population encoder；
- continuous-time latent dynamics；
- learned timescales / physiology connection；
- cross-dataset transfer；
- 如有必要，发展 neural-specific continuous-time architecture。

原则：

> **Track B 失败不能拖垮 Track A；Track B 成功则显著提高论文上限。**

---

# 3. Milestone 1–3：数据与因果协议层

这三阶段已经完成，后续仅作为冻结基础，不因模型表现回改。

## Milestone 1 — Single-session alignment  
**状态：PASS / FROZEN**

解决：

> 不同神经模态能否在统一时间轴上可靠读取和对齐？

完成：

- metadata / XML / anatomy 读取；
- LFP 只读加载；
- stable spikes 读取；
- sleep annotations 读取；
- unified time support；
- multimodal sanity checks；
- explicit OOB diagnostics；
- integration tests。

冻结原则：

- raw data read-only；
- provenance 与 derived support 分离；
- 异常显式记录，不静默修补。

---

## Milestone 2 — Strict causal sample construction  
**状态：PASS / FROZEN**

解决：

> 什么才算一个没有未来泄漏的训练样本？

核心定义：

\[
X_t=[t-W,t)
\]

\[
y_t=	ext{state on }[t-1,t)
\]

冻结：

- 1 s target grid；
- half-open interval `[start, stop)`；
- strict WAKE / NREM / REM / IGNORE；
- 5 / 10 / 30 s past-only context；
- spike binning；
- LFP lazy loading；
- causality tests；
- no normalization / filtering / spectral features。

严格处理：

- `WAKE <- WakeTimePairFormat`
- `NREM <- SWSPacketTimePairFormat`
- `REM <- REMTimePairFormat`
- conflict → IGNORE
- OOB → unsupervised
- broad Sleep ≠ NREM
- fine-state gap → IGNORE
- incomplete target tail → IGNORE

---

## Milestone 3 — Full-release dataset audit  
**状态：PASS / FROZEN**

解决：

> 这套规则能否不依赖 animal/session-specific hack 覆盖整个 fcx-1？

最终：

\[
27/27\ 	ext{sessions}
\]

\[
11\ 	ext{animals}
\]

\[
27\ 	ext{WARN},\quad 0\ 	ext{FAIL}
\]

\[
44/44\ 	ext{tests PASS}
\]

关键数据事实：

- stable units：10–113；
- supervision coverage 差异显著；
- selected LFP anatomy 横跨 ACC / MotorCtx / mPFC / OFC；
- session 间 neuron identity 不可直接对应；
- core-target OOB = 0；
- annotation conflict 全部严格 mask；
- open-ended provenance、empty interval、partial frame、event-clock discrepancy 均已形成通用协议；
- 不存在 session-specific / animal-specific processing branch；
- raw data 未修改。

从 Milestone 4 开始，不允许因为模型性能改变：

- time support；
- strict labels；
- invalid mask；
- OOB / conflict handling；
- causal window definition；
- spike timestamp semantics；
- raw-data preservation rules。

---

# 4. Milestone 4 — Representation & causal preprocessing

核心问题：

> **已经合法、严格因果的数据，应该以什么形式提供给模型？**

本阶段不回答“哪个模型最好”，只冻结输入表示。

## Spike representation

至少保留两条路线。

### Track A：simple robust representation

候选：

- population firing rate；
- population count；
- shank / region aggregation；
- basic population statistics。

目的：

- 稳定；
- 跨动物天然兼容；
- 低实现风险；
- 提供可靠 benchmark baseline。

### Track B：variable-neuron representation

候选形式：

\[
z_i=f_	heta(x_i)
\]

\[
z_{\mathrm{pop}}
=
\operatorname{Pool}\{z_1,\ldots,z_N\}
\]

要求：

- 支持 variable \(N\)；
- 不假设 neuron identity 跨 session 对齐；
- 优先 permutation-invariant；
- 可考虑 mean / sum pooling、DeepSets、attention pooling、set encoder。

M4 不预设 Track B 必须成为最终主方法；是否升级为论文主线，由后续实验决定。

## LFP representation

至少保留两条路线：

### Route A：minimally processed causal waveform

- 尽量保留时序结构；
- causal downsampling；
- causal learned encoder；
- 不先强制压成传统睡眠特征。

### Route B：causal physiological features

可研究：

- delta；
- theta；
- sigma / spindle-related；
- broadband；
- anatomically appropriate ripple-related features。

严格禁止：

- `filtfilt`
- zero-phase filtering
- centered moving average
- centered Welch
- centered STFT / spectrogram
- 任何利用未来样本构造当前 feature 的操作

## Decision grid 与 observation grid

必须区分：

\[
	ext{decision grid}

eq
	ext{observation grid}
\]

当前 target decision grid 可维持 1 Hz，但 observation 不必压成 1 Hz。

候选 observation rate 可以是：

- 10 Hz；
- 20 Hz；
- 50 Hz；
- 其他经验证的 causal rate；
- spikes 未来可保留 event timing。

M4 不应默认：

\[
1	ext{ s}ightarrow1	ext{ input vector}
\]

否则会过早削弱 continuous-time story。

## Multimodal input contract

最终应定义统一接口，包括：

- value；
- timestamp / \(\Delta t\)；
- modality identity；
- mask；
- neuron-set information；
- causal validity。

传统模型可使用规则化版本：

\[
X_{	ext{regular}}
\]

连续时间模型可使用：

\[
X_{	ext{continuous}}
\]

但必须遵守：

> **不同模型可以使用不同接口形式，但必须获得相同信息量。**

禁止：

- CfC 获得更精细 spike timing，而 LSTM 只看到粗 population count；
- 某模型获得更长 history；
- 某模型得到 future-derived features。

## Normalization 边界

M4 只冻结 normalization 的数学规则，不 fit 正式统计量。

原因：

\[
	ext{normalization statistics}
\]

必须来自 future training animals。

M4 只决定：

- 哪些变量需要 normalization；
- normalization 数学形式；
- 哪些统计量必须 train-only fit；
- scaler 如何保存；
- external Intan 如何应用 frozen scaler。

真正 fit mean/std 等统计量放到 M5。

## M4 完成标准

M4 应最终冻结：

- spike representation protocol；
- LFP representation protocol；
- temporal resolution；
- multimodal interface；
- masks / timestamps；
- normalization rule；
- representation-level causality tests；
- no-leakage rules。

不进行正式 CfC benchmark。

---

# 5. Milestone 5 — Evaluation protocol & data split

核心问题：

> **怎样确保不同模型的比较真正公平，并测试的是跨动物泛化？**

本阶段正式冻结：

- animal-level split；
- validation strategy；
- Leave-One-Animal-Out 是否为主协议；
- random seeds；
- train-only normalization；
- class weighting；
- early stopping；
- model selection；
- parameter-budget fairness。

原则：

\[
oxed{	ext{No random time-bin split}}
\]

也不能让同一动物同时出现在 train/test 中造成 identity leakage。

M4 只定义 normalization 方法，M5 才真正 fit scaler statistics。

---

# 6. Milestone 6 — Main state-decoding benchmark

这是第一轮真正的主模型结果。

任务：

\[
	ext{WAKE / NREM / REM causal decoding}
\]

比较：

1. linear / logistic baseline；
2. HMM 或传统 sequential baseline；
3. TCN；
4. LSTM / GRU；
5. CfC；
6. 至少一个现代 causal SSM。

指标：

- Macro-F1；
- Balanced Accuracy；
- Cohen's \(\kappa\)；
- per-class F1；
- confusion matrix；
- multiple seeds mean ± variance。

REM 必须单独报告。

这一阶段回答：

> 在规则、稳定、常规 state decoding 中，不同 temporal inductive biases 的基线位置在哪里？

不是简单问：

> CfC 赢了吗？

---

# 7. Milestone 7 — State-transition forecasting

这是项目最重要的科学增强之一。

目标从：

> 当前是什么状态？

升级到：

> 当前神经动态是否已经预示即将发生的状态转换？

## REM entry

\[
P(\mathrm{REM\ entry\ within}\ H)
\]

## NREM → Wake

\[
P(\mathrm{Wake\ transition\ within}\ H)
\]

候选：

\[
H=5,10,30\ \mathrm{s}
\]

若标签质量允许，可加入：

\[
T_{	ext{next transition}}-t
\]

重点比较：

- steady-state；
- transition-near；
- forecasting horizon；
- calibration；
- false alarm trade-off。

如果 CfC 在普通分类中不占优，但在 transition forecasting 中明显更强，仍是高价值结果。

---

# 8. Milestone 8 — Irregular / missing / asynchronous observation

这是回答：

> **为什么需要 continuous-time model？**

的关键阶段。

构造受控 stress tests：

- 10% missing；
- 20% missing；
- 40% missing；
- irregular timestamps；
- observation gaps；
- asynchronous LFP / spikes；
- variable \(\Delta t\)。

主要看：

\[
	ext{performance degradation vs missingness}
\]

而不是只看绝对准确率。

理想结果可能是：

\[
	ext{regular data: CfC}pprox	ext{LSTM}
\]

但：

\[
	ext{irregular data: CfC degradation slower}
\]

这种结果比“普通分类高 1%”更能支持 continuous-time inductive bias 的科学意义。

---

# 9. Milestone 9 — Multimodal and population ablation

回答：

> **模型真正利用了什么神经信息？**

系统比较：

\[
	ext{LFP only}
\]

\[
	ext{Spikes only}
\]

\[
	ext{LFP + Spikes}
\]

以及必要时：

- population baseline vs variable-neuron encoder；
- waveform vs physiological LFP features；
- modality dropout；
- region-dependent effects。

不仅看总体性能，还分析：

- WAKE / NREM / REM；
- transition-near；
- cross-animal；
- irregular observation。

这一阶段决定 Track B 的 variable-neuron 方法是否真正有价值。

---

# 10. Milestone 10 — Continuous-time dynamics & interpretability

只有当前面的 benchmark 结果值得解释时，才重点投入。

研究：

- CfC learned time constants；
- hidden-state trajectories；
- transition-aligned latent states；
- PCA / UMAP；
- state-space geometry；
- latent timescales 与神经生理 feature 的对应。

重点状态转换：

\[
\mathrm{Wake}ightarrow\mathrm{NREM}
\]

\[
\mathrm{NREM}ightarrow\mathrm{REM}
\]

\[
\mathrm{REM}ightarrow\mathrm{Wake}
\]

目标不是简单展示：

> hidden state 能分三类

而是寻找：

> **是否存在跨动物重复出现、与真实状态转换对应的 continuous latent dynamics。**

---

# 11. Milestone 11 — Efficiency & real-time capability

回答：

> continuous-time model 是否不仅有效，而且适合在线神经解码？

比较：

- parameter count；
- training time；
- inference latency；
- throughput；
- peak GPU memory；
- optional FLOPs。

重点结果：

\[
	ext{Performance vs Latency}
\]

\[
	ext{Performance vs Parameter Count}
\]

如果 CfC 不是最高准确率，但：

- performance 接近最优；
- latency 更低；
- 模型更小；
- irregular robustness 更强；

仍然可以形成完整的方法优势。

---

# 12. Milestone 12 — Frozen external validation

最后才进入实验室 Intan。

原则：

\[
oxed{	ext{public development} ightarrow 	ext{freeze} ightarrow 	ext{external test}}
\]

Intan 前必须冻结：

- representation；
- normalization；
- architecture；
- hyperparameters；
- thresholds；
- decision rules。

Intan 结果不好也不能回去重调 fcx-1 主模型。

如果确需 adaptation：

- 必须作为单独 sensitivity / domain adaptation analysis；
- 不能混入主结果。

本阶段真正测试：

> **framework 是否能跨 acquisition system / laboratory / recording domain 泛化？**

---

# 13. Optional extension — Cross-dataset transfer

主线完整以后再考虑：

- hc-11；
- hc-14；
- pfc-2；
- 其他公开 neural recordings。

用途：

- cross-region；
- cross-dataset；
- domain shift；
- transfer learning。

不同数据集的标签体系不完全一致，不应直接粗暴混合训练。

---

# 14. 三个 Decision Gates

## Gate A — M6 后

如果 CfC 普通 decoding 明显更强：

- 强化主模型；
- 进一步研究原因。

如果持平：

- 正常进入 transition / irregular tests。

如果明显落后：

- 检查模型假设是否不适合；
- 不能为了救结果回改 M1–M3 协议。

## Gate B — M8 后

如果 continuous-time 模型在 transition / irregular observation 明显占优：

- Track B 升级为主故事。

如果仍无明显优势：

- 文章重心转向 rigorous benchmark；
- negative / neutral result；
- efficiency；
- external validation。

## Gate C — M9 / M10 后

如果 variable-neuron / asynchronous method 有明确收益：

- 可考虑形成新的方法框架。

否则：

- 保留为 ablation；
- 不强行宣称新 architecture。

---

# 15. 最终论文的三个版本

## Minimum viable paper

包含：

- strict causal benchmark；
- cross-animal split；
- strong baselines；
- CfC；
- multimodal ablation；
- transition forecasting；
- efficiency；
- Intan external validation。

潜在投稿：

- Journal of Neural Engineering
- Neural Networks
- Neuroinformatics
- IEEE JBHI
- Journal of Neuroscience Methods

## Strong paper

再加入：

- irregular observation；
- variable-neuron representation；
- robust multimodal fusion；
- strong transition result；
- frozen external validation。

重点争取：

- PLOS Computational Biology
- Cell Reports Methods
- Communications Biology

## High-upside paper

进一步出现：

- asynchronous continuous-time architecture；
- reproducible cross-animal transition dynamics；
- multi-dataset evidence；
- strong real-time demonstration；
- clear external generalization。

才考虑：

- Nature Communications

Nature Neuroscience / Nature Machine Intelligence / Nature Computational Science 暂不作为按当前路线自然完成即可达到的默认预期。

---

# 16. 最终论文叙事

基础版本：

> **We establish a strictly causal, multimodal and cross-animal benchmark for neural-state decoding and systematically test when continuous-time inductive biases become useful for state decoding, transition forecasting, irregular observations and real-time inference.**

Track B 成功后：

> **We develop a variable-population, asynchronous continuous-time neural decoding framework that generalizes across animals without assuming fixed neuron identities or perfectly synchronized observations.**

若 interpretability 结果进一步成立：

> **Continuous-time latent dynamics capture and anticipate physiologically meaningful state transitions across animals and recording domains.**

---

# 17. 主要风险与防线

## 风险 1：CfC 普通分类不优于 baseline

应对：

- transition forecasting；
- irregular sampling；
- efficiency；
- robustness；
- interpretable dynamics。

## 风险 2：variable neurons

应对：

- Track A：population baseline；
- Track B：set encoder + permutation-invariant pooling。

## 风险 3：LFP anatomy 不统一

应对：

- per-session metadata-driven selection；
- anatomy-aware analysis；
- 不写死 channel index。

## 风险 4：sleep annotation 不完美

应对：

- strict labels；
- IGNORE；
- explicit QC；
- 不补标签。

## 风险 5：future leakage

应对：

- past-only windows；
- causal preprocessing；
- future perturbation tests；
- animal-level split；
- train-only normalization；
- leakage audit。

## 风险 6：Intan external validation 较差

应对：

- 不回头调 public benchmark；
- 作为真实 domain shift 结果；
- adaptation 单独分析。

---

# 18. Work 长期执行原则

1. 先读 protocol，再改代码。
2. 不因模型结果不好自动改变科研定义。
3. 涉及科学结论的 protocol change 必须先人工批准。
4. raw data read-only。
5. 每个 Milestone 都必须有：
   - protocol
   - code
   - tests
   - machine-readable report
   - human-readable notes
   - sanity figures
   - completion criteria
6. 所有旧 regression tests 持续通过。
7. 不静默修补异常。
8. 不使用未来信息。
9. 不在 validation / test / external data 上 fit normalization。
10. 所有关键实验保留 config / seed / hash。
11. 不一次跨多个 Milestone。
12. 每阶段完成后暂停，由用户人工复核。
13. WARN 不等于 exclusion。
14. 数据问题与模型问题分离处理。
15. representation 必须对不同模型保持信息公平。

---

# 19. 长期 Milestone 逻辑

\[
oxed{
	ext{M1--3 Data validity}
ightarrow
	ext{M4 Representation}
ightarrow
	ext{M5 Evaluation protocol}
ightarrow
	ext{M6 Main benchmark}
ightarrow
	ext{M7 Transition}
ightarrow
	ext{M8 Irregularity}
ightarrow
	ext{M9 Multimodal mechanism}
ightarrow
	ext{M10 Dynamics}
ightarrow
	ext{M11 Efficiency}
ightarrow
	ext{M12 External validation}
}
\]

这份 Roadmap 正常情况下不因单个 Milestone 完成而改版。

只有发生真正的研究方向变化，例如：

- variable-neuron asynchronous decoder 升级成论文主体；
- continuous-time hypothesis 被系统证伪；
- external validation 改变了核心科学问题；

才值得升级到新的 Roadmap 版本。

---

# 20. 当前状态

**M1–M3：PASS / FROZEN**

下一阶段：

## Milestone 4 — Representation & causal preprocessing

当前不训练正式 CfC，不进行正式 benchmark，不使用 full-dataset normalization。

---

**文档版本：v2.0**  
**更新时间：2026-09-15**
