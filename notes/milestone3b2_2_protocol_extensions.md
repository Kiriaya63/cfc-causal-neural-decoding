# M3-B2.2 — 已批准的通用 structural extensions

人工授权：本轮用户明确批准 A/B/C 三项 dataset-wide 扩展。实现不依赖 session/animal ID；raw data 只读。

## A. Empty half-open provenance

有限 `[a,a)` 作为空集保留在 raw metadata / raw GoodSleep 数组中。derived union 不纳入空行，记录 `zero_duration_provenance` WARN 和原行索引。原始 start 次序仍须非递减；非空行之间仍禁止重叠。全空集合不能形成 analysis support。反向区间、非法非有限端点、错误 shape 继续失败。

## B. Maximal complete-frame prefix

`N = file_size // (n_channels × 2)`；`r = file_size % (n_channels × 2)`。EEG dtype 固定 little-endian int16，通道数为正整数，采样率 finite positive，完整前缀时长 finite positive。

- `r=0`：延续原行为。
- `0<r<frame_width`：从合法 BasicMetaData / GoodSleep 的非空区间取得官方终点（每个来源取整体最大 stop，不能把内部片段端点当成 recording end）。至少一个来源给出 finite end 且与 `N/fs` 相差不超过 `1/fs` 才接受。若两个来源均符合，优先记录 metadata 来源；原始两套 provenance 仍完整保留。
- 两来源都只有 open end、有限 end 不一致或几何无效：FAIL。

接受时仅以 read-only memmap 暴露 `(N,n_channels)` 完整前缀；尾部不解释、不补齐、不写回。记录 `complete_frame_prefix_with_incomplete_tail` WARN；结构化输出包括原始 bytes、frame width、N、尾部 bytes、prefix end、官方 end、来源和有符号差 `official_end-prefix_end`。

时间支持仍为 `I_LFP ∩ I_metadata_constraint ∩ I_GoodSleep_constraint`。`lfp_has_complete_timepoints` 表示有效数据视图中的 frames 完整；raw suffix 是否存在由 frame diagnostics 单独记录。文件格式无法独立证明内部从未错位，接受规则依据此次批准的官方 endpoint consistency guard。

## C. Event timestamp clock

稳定 spike 的 finite、非负、逐 unit 非递减、实数数值向量表示及既有 support 检查仍保留。数值不进行 rounding、重新量化或时钟换算。`bin_stable_spikes` 未修改，仍以 raw seconds 的 `searchsorted(side='left')` 计算 `[start,stop)`。

声明网格残差为 `abs(t*declared_hz-rint(t*declared_hz))`。超过 `1e-6` tick 记录 `declared_grid_mismatch` WARN，不作为 causal correctness 的 fatal 条件。声明 acquisition rate 原样保留。

观察时钟仅为 QC：在 `{1250,2500,5000,10000,20000,declared_hz}` 候选中，以同一 `1e-6` tick 容差检验全部 spikes；`observed_event_clock_hz` 返回最低完全符合的被测频率，无匹配或无事件返回 null。这不能证明原始硬件时钟，也不参与 support/归箱。兼容参数 `validate_acquisition_grid` 保留，但网格诊断总是输出且不再抛出网格不一致异常。

## 冻结项与验证

WAKE/NREM/REM 字段映射、conflict→IGNORE、OOB 不监督、broad Sleep 不等于 NREM、`X_t=[t-W,t)`、`y_t=[t-1,t)` 和 W=5/10/30 全部保持。

新增 synthetic regression tests 覆盖空集、错误端点/次序、完整帧旧行为、受约束尾部、缺失官方 finite end、只读文件、声明时钟不一致、任意有序秒数、bitwise timestamp preservation 和半开边界。原 32 个测试保留；全 release 的报告引用与哈希 fixture 切换至本次新快照，这是批准后的协议版本更新，旧快照保留在 `reports/milestone3b2/`。

本次完整重跑使用同一 audit runner，输出 `reports/milestone3b2_2/`；此前 M3-B2 与 M3-B2.1 报告保留作为历史证据。全量原始文件 size/mtime 和小于 100 MB 的非 EEG 文件 SHA256 做前后对照；未对所有 EEG 重新计算全文件 checksum。

## 最终验证

- preflight 27/27 PASS，27 sessions / 11 animals 公共 pipeline 完成，0 PASS / 27 WARN / 0 FAIL。
- 原 32 + 新增 12 = 44/44 tests PASS，0 skipped；测试日志 `reports/milestone3b2_2/test_results.txt`。
- 原先成功的 24 个 session 的关键统计完全不变；五个 label/causal/binning 模块保持原 SHA256。
- 523 个 raw 文件前后核对未发现变化；raw timestamps 和 metadata 值没有被修补。
- 无未解决 structural issue；技术上满足 M3 冻结条件。M4 未开始，等待用户复核后的阶段指令。
