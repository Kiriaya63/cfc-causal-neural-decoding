# fcx-1 official animal-session mapping

## Evidence and reconciliation

Primary evidence is `WatsonSleepHomestasis2016Table.xlsx`, worksheet `SleepOverview`. Animal header rows group the recording rows below them, and column L supplies a matching source path. The official release `filelist.txt` supplies archive basenames and compressed sizes. All 27 source session names match release basenames exactly; the set difference in both directions is empty. The local data-description PDF independently states 11 animals and 27 recording sessions.

Result: **11 animals, 27 sessions, 27 confirmed mappings, 0 probable mappings, 0 unknown mappings**. There is no naming ambiguity. `20140526_277um`, `20140527_421um`, and `20140528_565um` are confirmed as animal `JennBuzsaki22` by the official table rather than by filename inference.

## Complete mapping

| Animal | Source session name | Release session name | XLSX row | Confidence | Local | Audited | Archive size |
|---|---|---|---:|---|---:|---:|---:|
| BWRat17 | BWRat17_121712 | BWRat17_121712 | 4 | confirmed | yes | yes | 892.8 MB |
| BWRat17 | BWRat17_121912 | BWRat17_121912 | 5 | confirmed | no | no | 970.7 MB |
| BWRat18 | BWRat18_020513 | BWRat18_020513 | 8 | confirmed | yes | yes | 1.8 GB |
| BWRat19 | BWRat19_032413 | BWRat19_032413 | 11 | confirmed | no | no | 1.3 GB |
| BWRat19 | BWRat19_032513 | BWRat19_032513 | 12 | confirmed | yes | yes | 1.0 GB |
| BWRat20 | BWRat20_101013 | BWRat20_101013 | 15 | confirmed | yes | yes | 1.7 GB |
| BWRat20 | BWRat20_101513 | BWRat20_101513 | 16 | confirmed | no | no | 3.5 GB |
| BWRat21 | BWRat21_121113 | BWRat21_121113 | 19 | confirmed | no | no | 2.5 GB |
| BWRat21 | BWRat21_121613 | BWRat21_121613 | 20 | confirmed | no | no | 2.4 GB |
| BWRat21 | BWRat21_121813 | BWRat21_121813 | 21 | confirmed | no | no | 2.4 GB |
| Dino | Dino_061814_mPFC | Dino_061814_mPFC | 24 | confirmed | no | no | 5.0 GB |
| Dino | Dino_061914_ACC | Dino_061914_ACC | 25 | confirmed | no | no | 4.3 GB |
| Dino | Dino_061914_mPFC | Dino_061914_mPFC | 26 | confirmed | no | no | 4.4 GB |
| Dino | Dino_062014_ACC | Dino_062014_ACC | 27 | confirmed | no | no | 5.6 GB |
| Dino | Dino_062014_mPFC | Dino_062014_mPFC | 28 | confirmed | no | no | 5.7 GB |
| Dino | Dino_072114_mPFC | Dino_072114_mPFC | 29 | confirmed | no | no | 2.0 GB |
| Dino | Dino_072314_mPFC | Dino_072314_mPFC | 30 | confirmed | no | no | 2.6 GB |
| Dino | Dino_072414_mPFC | Dino_072414_mPFC | 31 | confirmed | no | no | 3.4 GB |
| JennBuzsaki22 | 20140526_277um | 20140526_277um | 34 | confirmed | no | no | 2.6 GB |
| JennBuzsaki22 | 20140527_421um | 20140527_421um | 35 | confirmed | no | no | 3.3 GB |
| JennBuzsaki22 | 20140528_565um | 20140528_565um | 36 | confirmed | no | no | 2.3 GB |
| Bogey | Bogey_012615 | Bogey_012615 | 39 | confirmed | no | no | 3.9 GB |
| Splinter | Splinter_020515 | Splinter_020515 | 42 | confirmed | no | no | 2.9 GB |
| Splinter | Splinter_020915 | Splinter_020915 | 43 | confirmed | yes | yes | 2.5 GB |
| Rizzo | Rizzo_022615 | Rizzo_022615 | 46 | confirmed | no | no | 5.5 GB |
| Rizzo | Rizzo_022715 | Rizzo_022715 | 47 | confirmed | no | no | 3.6 GB |
| Templeton | Templeton_032415 | Templeton_032415 | 50 | confirmed | no | no | 3.4 GB |

## Animal-level release summary

| Animal | Sessions | Official session IDs | Current coverage |
|---|---:|---|---|
| BWRat17 | 2 | BWRat17_121712; BWRat17_121912 | BWRat17_121712 audited |
| BWRat18 | 1 | BWRat18_020513 | audited |
| BWRat19 | 2 | BWRat19_032413; BWRat19_032513 | BWRat19_032513 audited |
| BWRat20 | 2 | BWRat20_101013; BWRat20_101513 | BWRat20_101013 audited |
| BWRat21 | 3 | BWRat21_121113; BWRat21_121613; BWRat21_121813 | uncovered |
| Dino | 8 | Dino_061814_mPFC; Dino_061914_ACC; Dino_061914_mPFC; Dino_062014_ACC; Dino_062014_mPFC; Dino_072114_mPFC; Dino_072314_mPFC; Dino_072414_mPFC | uncovered |
| JennBuzsaki22 | 3 | 20140526_277um; 20140527_421um; 20140528_565um | uncovered |
| Bogey | 1 | Bogey_012615 | uncovered |
| Splinter | 2 | Splinter_020515; Splinter_020915 | Splinter_020915 audited |
| Rizzo | 2 | Rizzo_022615; Rizzo_022715 | uncovered |
| Templeton | 1 | Templeton_032415 | uncovered |

Current animal coverage is 5/11: BWRat17, BWRat18, BWRat19, BWRat20, and Splinter. The six uncovered animals are BWRat21, Dino, JennBuzsaki22, Bogey, Rizzo, and Templeton.

## Recommended M3-B1 download batch

| Animal | Recommended session | Archive size | Reason |
|---|---|---:|---|
| JennBuzsaki22 | 20140528_565um | 2.3 GB | Smallest of three; adds mPFC+dHipp configuration. |
| Bogey | Bogey_012615 | 3.9 GB | Only released Bogey session; mPFC. |
| BWRat21 | BWRat21_121613 | 2.4 GB | Smallest of three; official table identifies ketamine, which must remain explicit in audit interpretation. |
| Dino | Dino_072114_mPFC | 2.0 GB | Smallest of eight; official table notes few units and almost no assemblies. |
| Rizzo | Rizzo_022715 | 3.6 GB | Smaller of two; OFC. |
| Templeton | Templeton_032415 | 3.4 GB | Only released session; official table warns of unstable units and high-frequency noise. |

This batch adds all six uncovered animals with six archives. Exact total: **19,257,746,171 bytes = 17.94 GiB (about 19.26 decimal GB)**. Summing the release list's individually rounded display sizes gives approximately 17.6 GB.

The recommendation follows minimum archive size within each uncovered animal. It does not imply later scientific inclusion. BWRat21_121613, Dino_072114_mPFC, and Templeton_032415 carry explicit official caveats that should be preserved during M3-B1 QC.

## Mapping ambiguity

None in the 27-session release. The official XLSX source name and release basename match exactly for every session. `Splinter_020515` and `Splinter_020915` are two separate confirmed sessions from the same animal.
