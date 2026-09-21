# Runtime v1 Random Control Expected Labels

Scope: label only `random_3sat_control` rows for the v1.1 protocol hygiene refresh.
A label is written only when trusted plain Glucose and CaDiCaL agree on SAT/UNSAT.
No neural model, adapter, selector, or gate is trained or changed.

- labeled manifest: `/home/sunshixin/chenchao/my_rlaf/runs/analysis/symmetry_runtime_protocol_v1_manifest_labeled.csv`

## Summary

| agreement_status | agreed_expected_result | rows | base_instances |
| --- | --- | --- | --- |
| agreed | SATISFIABLE | 6 | 2 |
| agreed | UNSATISFIABLE | 3 | 1 |

## Per-CNF Provenance

| instance_id | variant | glucose_result | cadical_result | agreement_status | agreed_expected_result | cnf_sha256 | label_provenance_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random_3sat_control_v20_c85_seed1901 | base | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | 496be0f98476fc595181815e21132e87fd958ba35608aa39f827258dd0340da2 | plain_glucose_cadical_sha256:496be0f98476fc59 |
| random_3sat_control_v20_c85_seed1901_perm1730 | perm_seed1730 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | 79568ceb509b90ca8a690d3925ce3f6f49e99c7f1b9319ff175cf70335f0057e | plain_glucose_cadical_sha256:79568ceb509b90ca |
| random_3sat_control_v20_c85_seed1901_perm1731 | perm_seed1731 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | 7eac3ec4988d69e03a77b48d9e18a21a2a7cf8d8109bb9e44dc5b6dcc7d8cb50 | plain_glucose_cadical_sha256:7eac3ec4988d69e0 |
| random_3sat_control_v30_c128_seed1902 | base | UNSATISFIABLE | UNSATISFIABLE | agreed | UNSATISFIABLE | 228ec665bdc13fccf6fac8c0987473d4895ac2010717f70e4c5a6af185bb38e9 | plain_glucose_cadical_sha256:228ec665bdc13fcc |
| random_3sat_control_v30_c128_seed1902_perm1730 | perm_seed1730 | UNSATISFIABLE | UNSATISFIABLE | agreed | UNSATISFIABLE | 62e4e478bdda9967cd50f31c11edc31e906c15bf40f83f0ae0d084993015b515 | plain_glucose_cadical_sha256:62e4e478bdda9967 |
| random_3sat_control_v30_c128_seed1902_perm1731 | perm_seed1731 | UNSATISFIABLE | UNSATISFIABLE | agreed | UNSATISFIABLE | d2a6fe9f76337653db4f7bdc5df47962a6a610798e5defd539918918b434e1d0 | plain_glucose_cadical_sha256:d2a6fe9f76337653 |
| random_3sat_control_v40_c170_seed1903 | base | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | 09761b7b693002593da7552aedd4e1a3b81255a92cccb4e8d2d3d28e5474608c | plain_glucose_cadical_sha256:09761b7b69300259 |
| random_3sat_control_v40_c170_seed1903_perm1730 | perm_seed1730 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | ebd8b596fc0891fcbfc5293357ee6e7e91f5dab36a9f173daaeac4a6bd0c73fc | plain_glucose_cadical_sha256:ebd8b596fc0891fc |
| random_3sat_control_v40_c170_seed1903_perm1731 | perm_seed1731 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | 1ebc85a6fe55cedeba067863c64bfc49f1d615366c857ac4bc638b4b6e0f2a02 | plain_glucose_cadical_sha256:1ebc85a6fe55cede |
