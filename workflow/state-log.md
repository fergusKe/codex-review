# Workflow State Log

本檔由 Transition CLI append。

## 2026-08-30T16:16:53+08:00
- Actor: machine-verified
- Action: set-mode
- Change: none
- From: DISCOVERY
- To: DISCOVERY
- Git SHA: 772703c5bee36a51990d8c293df13a0bd545e754
- State hash: 239bd4f9be8cbf5aba824ba14542110cf5b9e1761a58c28e2fe686504cd3fb2d
- Reason: Project mode=GREENFIELD

## 2026-08-30T16:16:54+08:00
- Actor: machine-verified
- Action: start-change
- Change: review-round-runner
- From: DISCOVERY
- To: SPECIFICATION
- Git SHA: e5fbe64a1c7d65e4ad0665f71f776076c92ca1b9
- State hash: 2632123a01a5c6e77db22b6ad553925a08db7a35d96cc6c7eaebf52f3a8a004b
- Reason: Active change bound

## 2026-08-30T16:16:56+08:00
- Actor: machine-verified
- Action: submit-for-review
- Change: review-round-runner
- From: SPECIFICATION
- To: SPEC_REVIEW
- Git SHA: 5f1b58e3afca7133af624c53e01e2a78dbdae575
- State hash: 9e337ab4174931eeb980efd17bff6cfce2631f548ad44759c6b7e3933460d896
- Reason: Required OpenSpec artifacts exist

## 2026-08-30T16:18:20+08:00
- Actor: ai-or-human
- Action: revert-to-spec
- Change: review-round-runner
- From: SPEC_REVIEW
- To: SPECIFICATION
- Git SHA: 31c93b4869659267fcdcf15b3de6c7d5fcf21f3b
- State hash: 6d1cd1810f945a6e0361ecf21ad55f9e8c0a867badeb7a9b6b5ade7eba3b03bf
- Reason: profile 的 Test database strategy 在送審時仍為 UNKNOWN，approve-spec 拒絕；退回 SPECIFICATION 定案

## 2026-08-30T16:18:21+08:00
- Actor: machine-verified
- Action: submit-for-review
- Change: review-round-runner
- From: SPECIFICATION
- To: SPEC_REVIEW
- Git SHA: f0381bf5fa302143f00415dffe463b5fee25fe22
- State hash: 1763b1e0bc0309aa5372e4c95654da0a77f689e082ba08e1ab0cc55406ce1f6e
- Reason: Required OpenSpec artifacts exist

## 2026-08-30T16:21:52+08:00
- Actor: fergus
- Action: approve-spec
- Change: review-round-runner
- From: SPEC_REVIEW
- To: TEST_DESIGN
- Git SHA: 84eba9596df3ee2ed95cc601bf78043d985dc3e0
- State hash: 5762d16e7d62bacac845c40eadb3d9d6f3cb0e77062bb2f13368542d0ab4bdad
- Reason: Human approved specification; profile digest 6d11e609f2d26f11; spec digest 4fd34056c652246c

## 2026-08-30T16:54:16+08:00
- Actor: fergus
- Action: approve-tests
- Change: review-round-runner
- From: TEST_DESIGN
- To: TEST_DESIGN
- Git SHA: 909c72f00dd261890e8668f81761f13b1a58721d
- State hash: c052c1f4f515293fde3125cebf4d3ed854a847303b938ecf86484576053ca944
- Reason: Human approved test design; digest 5a1bbbd328589698

## 2026-08-30T16:55:05+08:00
- Actor: machine-verified
- Action: start-engineering
- Change: review-round-runner
- From: TEST_DESIGN
- To: ENGINEERING
- Git SHA: b76a6dfee7ac001e8cb9b93a79102fb70419dbd0
- State hash: 456010d88bc7601839a36e8e71a163d837b1295ede98400d13fb5fb94e504c0c
- Reason: Approval prerequisites satisfied; profile digest re-verified

## 2026-08-30T17:03:29+08:00
- Actor: machine-verified
- Action: verification-pass
- Change: review-round-runner
- From: ENGINEERING
- To: VERIFICATION
- Git SHA: f4f83fe63cac686d19110e1ae4bf94e7e26cea2b
- State hash: d93857a4cdd25148f2ab00eb0838372421c7eb1794793f0778a22870ae73bb5d
- Core evidence: workflow/evidence/review-round-runner/core/20260830T090329817559Z.md
- Core evidence sha256: 91835a912bddd6e569da7fe326c01e6da99e760a5654fd65b5cbe9237d2502da
- Browser evidence sha256: f6efbf0df9bebf2e2c4aa23cd99f36e67e773e2e9e674af5e9aec62a0d38566b
- Reason: Core/browser/API evidence validated

## 2026-08-30T17:04:01+08:00
- Actor: machine-verified
- Action: archive
- Change: review-round-runner
- From: VERIFICATION
- To: ARCHIVE
- Git SHA: dd09c189c45d0f7c5776d60697c445f46693b4a2
- State hash: d41ff2bcb1270717fc709ca772cedfa05c50441bc97ae4e8e44fd5912f8a815f
- Reason: Evidence complete

## 2026-08-30T17:12:11+08:00
- Actor: machine-verified
- Action: start-change
- Change: enable-ci-and-self-use
- From: ARCHIVE
- To: SPECIFICATION
- Git SHA: 4586a0586c04c9e4240b6497942eec26c0658aa4
- State hash: 275bdf3fd370ea283bceb02d5e096e96185740138f7f41ca200ac391c0ce4c06
- Reason: Active change bound

## 2026-08-30T17:12:25+08:00
- Actor: machine-verified
- Action: submit-for-review
- Change: enable-ci-and-self-use
- From: SPECIFICATION
- To: SPEC_REVIEW
- Git SHA: 1892219a2f47f9feee1702a0c9bea25b79da6c56
- State hash: 5974d9c836d1beb12a2b0a55b64e1fbdc89288ddc6cd88aab9b18fe0d7fb8fa8
- Reason: Required OpenSpec artifacts exist

## 2026-08-30T17:26:57+08:00
- Actor: fergus
- Action: approve-spec
- Change: enable-ci-and-self-use
- From: SPEC_REVIEW
- To: TEST_DESIGN
- Git SHA: dd915c535af1a27e6cf1a88eb490102fe035a3a8
- State hash: dbc4185a7d1ccbc2f070950c24a1c14a5ea9c86820a60017f70023c2db9e2ae1
- Reason: Human approved specification; profile digest 6d11e609f2d26f11; spec digest 285b716a51986815

## 2026-08-30T17:31:02+08:00
- Actor: fergus
- Action: approve-tests
- Change: enable-ci-and-self-use
- From: TEST_DESIGN
- To: TEST_DESIGN
- Git SHA: abee3b5624e45c7facab3157a0df9bb443c1035a
- State hash: c251d4d75f97d2e71d884d7221b776586da9ac9a126e2325b727badc13bfc72b
- Reason: Human approved test design; digest bda1404936a2b480

## 2026-08-30T17:31:21+08:00
- Actor: machine-verified
- Action: start-engineering
- Change: enable-ci-and-self-use
- From: TEST_DESIGN
- To: ENGINEERING
- Git SHA: 714db0703ef330092ac56ec13750e2975f453473
- State hash: 493cbaf6953430e8a1c879da76c958711c3b3015d89395f62451c13a21457e2e
- Reason: Approval prerequisites satisfied; profile digest re-verified

## 2026-08-30T17:36:24+08:00
- Actor: ai-or-human
- Action: revert-to-spec
- Change: enable-ci-and-self-use
- From: ENGINEERING
- To: SPECIFICATION
- Git SHA: c5819fa80911ec9829e9de023b40c8eed1040988
- State hash: b26a57a357614e0c5528a6c666146b58d20188f14fe6d0715b8de04d8c553b48
- Reason: T8.3 驗收標準要求 constraint 含本機絕對路徑，導致出貨設定檔不可攜；worktree 與任何非同名 clone 皆會失敗。需改為 repository 範圍判準並新增「不得含絕對路徑」的負向要求。

## 2026-08-30T17:36:53+08:00
- Actor: machine-verified
- Action: submit-for-review
- Change: enable-ci-and-self-use
- From: SPECIFICATION
- To: SPEC_REVIEW
- Git SHA: 03809f19ac5627f79900a2e4287d33d24a1bbd61
- State hash: 0198d54b14d1b09bcb29fbf4097ba6c322c9fe6b8833ceaed476e39dd7bbb3b7
- Reason: Required OpenSpec artifacts exist

## 2026-08-30T17:43:34+08:00
- Actor: fergus
- Action: approve-spec
- Change: enable-ci-and-self-use
- From: SPEC_REVIEW
- To: TEST_DESIGN
- Git SHA: abed5ad500f6069d6a09b7822e8d6e8c15fa9218
- State hash: c0087217316b163a55f903653f955a962dbc33590196ae4f8ea886f827d1634b
- Reason: Human approved specification; profile digest 6d11e609f2d26f11; spec digest 3e32533a45eb11ad

## 2026-08-30T17:48:19+08:00
- Actor: fergus
- Action: approve-tests
- Change: enable-ci-and-self-use
- From: TEST_DESIGN
- To: TEST_DESIGN
- Git SHA: b26d64a5327efe4b80409eaaa6fcf7fc05e85de9
- State hash: f101b4a9f458ea23c6ed08b31ac4edfbcdd517a205854160efea3bce04f41143
- Reason: Human approved test design; digest 20235d69abe19808

## 2026-08-30T17:48:33+08:00
- Actor: machine-verified
- Action: start-engineering
- Change: enable-ci-and-self-use
- From: TEST_DESIGN
- To: ENGINEERING
- Git SHA: b290b1831014976b991a5119b4b272cecefbbc4e
- State hash: 5e71f72ce8012a1250be08543ddab6d0ff350bc05afc9c2f8b1d7f7e0117f6d9
- Reason: Approval prerequisites satisfied; profile digest re-verified

## 2026-08-30T17:51:29+08:00
- Actor: machine-verified
- Action: verification-pass
- Change: enable-ci-and-self-use
- From: ENGINEERING
- To: VERIFICATION
- Git SHA: 4201a0081ab97ec1749e365708f404e97299d4f3
- State hash: 10b68cd4ac9962fdf78bdda144a838c007e42e349193ae743f19cbcf3b448b2b
- Core evidence: workflow/evidence/enable-ci-and-self-use/core/20260830T095129453828Z.md
- Core evidence sha256: 2a041864adf5232be6e93edce76b3d8bae8c23f346c87ffa2225af6ccf842444
- Browser evidence sha256: f6efbf0df9bebf2e2c4aa23cd99f36e67e773e2e9e674af5e9aec62a0d38566b
- Reason: Core/browser/API evidence validated

## 2026-08-30T17:52:46+08:00
- Actor: machine-verified
- Action: archive
- Change: enable-ci-and-self-use
- From: VERIFICATION
- To: ARCHIVE
- Git SHA: 50f8e3f1198a7f8fff88fe0732f86b2357b6e018
- State hash: 453af3bba7f310025fccc023fa976abce15822411cccd4c3efe976417a5826e2
- Reason: Evidence complete

## 2026-08-30T18:00:56+08:00
- Actor: machine-verified
- Action: start-change
- Change: pin-core-manifest
- From: ARCHIVE
- To: SPECIFICATION
- Git SHA: e515ca73a644afbd6a3e66f00b0f449beceb16a3
- State hash: a63ec5f13c8756335779bd48da94b17843b5d229bce05b8d15674322a377e877
- Reason: Active change bound

## 2026-08-30T18:01:07+08:00
- Actor: machine-verified
- Action: submit-for-review
- Change: pin-core-manifest
- From: SPECIFICATION
- To: SPEC_REVIEW
- Git SHA: f6ac5e05152ab38b1fe04296c3d6a7a24d420144
- State hash: cfcf5522777442faa6892fe6e72f66683fde31de91f4d59f730e0646bbc56e3d
- Reason: Required OpenSpec artifacts exist

## 2026-08-30T18:02:53+08:00
- Actor: fergus
- Action: approve-spec
- Change: pin-core-manifest
- From: SPEC_REVIEW
- To: TEST_DESIGN
- Git SHA: 9ad516c64129e9fd968a8e542ded25b3151dfd6f
- State hash: f5a0d0d3c9d244254ebfb00f2caaf9d500b4f8d90acfa363badfd992abc41abe
- Reason: Human approved specification; profile digest 6d11e609f2d26f11; spec digest 61a44982fc982946

## 2026-08-30T18:12:54+08:00
- Actor: fergus
- Action: approve-tests
- Change: pin-core-manifest
- From: TEST_DESIGN
- To: TEST_DESIGN
- Git SHA: 345e3bf6b1c2ebff9e9c9298775afb5345927416
- State hash: 0eead17197f4647059bc87006924784558bb639c52de787ce00b481321773f86
- Reason: Human approved test design; digest ff2c2d67f154b4b3

## 2026-08-30T18:13:15+08:00
- Actor: machine-verified
- Action: start-engineering
- Change: pin-core-manifest
- From: TEST_DESIGN
- To: ENGINEERING
- Git SHA: 5f194ff09d7e5d9b34d7096d095dd8875a21de74
- State hash: 3eced4407363cb858f5589eba4ca0730bf0979a2a099816799984dd738eca6ae
- Reason: Approval prerequisites satisfied; profile digest re-verified

## 2026-08-30T18:17:56+08:00
- Actor: ai-or-human
- Action: revert-to-spec
- Change: pin-core-manifest
- From: ENGINEERING
- To: SPECIFICATION
- Git SHA: bff4487d19225afb78a5626f87e1f6c1b14850d3
- State hash: 2ff6786468fff9e9e796c29545fa47cda5e1345dc011296fe3f822e293ea1152
- Reason: T12 的做法在淺 clone 上讀 HEAD，導致修正它的那個 commit 永遠無法通過 pre-commit

## 2026-08-30T18:19:16+08:00
- Actor: machine-verified
- Action: submit-for-review
- Change: pin-core-manifest
- From: SPECIFICATION
- To: SPEC_REVIEW
- Git SHA: 8f6fd9e62a57e289fd90ba6ce59e47215eaf6830
- State hash: 471760756c20b1f07f14fb7de3c177df8c269f38ebae5d6e7f7872fa091a9463
- Reason: Required OpenSpec artifacts exist

## 2026-08-30T18:25:29+08:00
- Actor: fergus
- Action: approve-spec
- Change: pin-core-manifest
- From: SPEC_REVIEW
- To: TEST_DESIGN
- Git SHA: beb5e457a442299634b0f71ef1b555660fedd397
- State hash: 15c77c3bba6597beddb8fe66beed2a90dc7abf4593653ee3218c81c1eee157db
- Reason: Human approved specification; profile digest 6d11e609f2d26f11; spec digest e861919569276228

## 2026-08-30T18:25:48+08:00
- Actor: fergus
- Action: approve-tests
- Change: pin-core-manifest
- From: TEST_DESIGN
- To: TEST_DESIGN
- Git SHA: beb5e457a442299634b0f71ef1b555660fedd397
- State hash: ec1fa84002efc4bfcb87c1bf7aa1b1dbbf75f6e72830ab20101751f18cd53b9d
- Reason: Human approved test design; digest 7a37bb71c36733b6

## 2026-08-30T18:26:29+08:00
- Actor: machine-verified
- Action: start-engineering
- Change: pin-core-manifest
- From: TEST_DESIGN
- To: ENGINEERING
- Git SHA: 18394a852b1a98cb00c363a8d0f74277c5ddb98f
- State hash: a99670291f96905fd62eabbe2d1cb178c08f1aa31ff057f2fbcdc7487811c3f0
- Reason: Approval prerequisites satisfied; profile digest re-verified

## 2026-08-30T18:49:36+08:00
- Actor: machine-verified
- Action: verification-pass
- Change: pin-core-manifest
- From: ENGINEERING
- To: VERIFICATION
- Git SHA: 02668abbf7bf3a3f550fbe098bfd147f43f3def7
- State hash: ef24107ed1acd1fa950f22015e1b4c0862944dac9299193112fc6f5ac506d8d3
- Core evidence: workflow/evidence/pin-core-manifest/core/20260830T104936731789Z.md
- Core evidence sha256: a417b1065240e8ba646aec692f266bd1db0ec4120d92e92424c31e562396ba84
- Browser evidence sha256: f6efbf0df9bebf2e2c4aa23cd99f36e67e773e2e9e674af5e9aec62a0d38566b
- Reason: Core/browser/API evidence validated

