# Runtime benchmark v2 Random Control Expected Labels

Scope: label only `random_3sat_control` rows in the selected runtime manifest.
A label is written only when trusted plain Glucose and CaDiCaL agree on SAT/UNSAT.
No neural model, adapter, selector, or gate is trained or changed.

- labeled manifest: `runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv`

## Summary

| agreement_status | agreed_expected_result | rows | base_instances |
| --- | --- | --- | --- |
| agreed | SATISFIABLE | 15 | 5 |
| agreed | UNSATISFIABLE | 6 | 2 |

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
| random_3sat_control_v35_c149_seed1911 | base | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | c918b2de22b8fd3a8eefdd632b3099b2da2830d4490f693c54d4e322c345d739 | plain_glucose_cadical_sha256:c918b2de22b8fd3a |
| random_3sat_control_v35_c149_seed1911_perm1730 | perm_seed1730 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | b525cf8187cc92934851204cdb0ff77944cd3c7de81aa3236435d276894f0285 | plain_glucose_cadical_sha256:b525cf8187cc9293 |
| random_3sat_control_v35_c149_seed1911_perm1731 | perm_seed1731 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | c1bcf71ea2326f30df7a0f5475b1aae0c574792d772bfaa8d0289b754462880a | plain_glucose_cadical_sha256:c1bcf71ea2326f30 |
| random_3sat_control_v60_c180_seed1912 | base | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | d6e944588194d4decc856256ef6dc2aef1de52c50069d9d7a405855a026bdedd | plain_glucose_cadical_sha256:d6e944588194d4de |
| random_3sat_control_v60_c180_seed1912_perm1730 | perm_seed1730 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | a4f18eeaa627ae245c38af94fdcb7095260ce05f7e37222ce71e51b61e7923da | plain_glucose_cadical_sha256:a4f18eeaa627ae24 |
| random_3sat_control_v60_c180_seed1912_perm1731 | perm_seed1731 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | 57168594f5f12a2223694b0a1bcc560328b690683fd4ba1bec0f8eeda0b9d9d5 | plain_glucose_cadical_sha256:57168594f5f12a22 |
| random_3sat_control_v80_c340_seed1913 | base | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | 8dfcda18e8eb03e8dbfa10883fdbe6eca3da66059e4e05b61e282e3b2aac2a1b | plain_glucose_cadical_sha256:8dfcda18e8eb03e8 |
| random_3sat_control_v80_c340_seed1913_perm1730 | perm_seed1730 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | fe56fa7fc6ac3b820c4a12b571d5dd9be845d88663f3e963d7ddc83653e047a1 | plain_glucose_cadical_sha256:fe56fa7fc6ac3b82 |
| random_3sat_control_v80_c340_seed1913_perm1731 | perm_seed1731 | SATISFIABLE | SATISFIABLE | agreed | SATISFIABLE | 74a26efebf498573a3979e8bcb43f9d51b207d9f668d541cbdde856b124cf25a | plain_glucose_cadical_sha256:74a26efebf498573 |
| random_3sat_control_v100_c600_seed1914 | base | UNSATISFIABLE | UNSATISFIABLE | agreed | UNSATISFIABLE | 0d2de417380892ea519f503a4fc6861b5005e2201e5ab5fcd9871b3b063c3d5a | plain_glucose_cadical_sha256:0d2de417380892ea |
| random_3sat_control_v100_c600_seed1914_perm1730 | perm_seed1730 | UNSATISFIABLE | UNSATISFIABLE | agreed | UNSATISFIABLE | ef7212614f14b3461039857c9a0fea88c460e9edcad92512da4e1109dbe0bad1 | plain_glucose_cadical_sha256:ef7212614f14b346 |
| random_3sat_control_v100_c600_seed1914_perm1731 | perm_seed1731 | UNSATISFIABLE | UNSATISFIABLE | agreed | UNSATISFIABLE | b775cb1cc3fea9b55d3ab5e288ae97573dc2883f2330918c22addef7def5ce36 | plain_glucose_cadical_sha256:b775cb1cc3fea9b5 |
