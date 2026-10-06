# Tester Phase 2B Final Error Log

| Date | Phase | Finding | Severity | Disposition |
|---|---|---|---|---|
| 2026-10-07 | 2B | S08 strict endpoint agreement = 95.8333%, below strict 99%, while practical corroboration = 97.9167% within 1% and max relative error = 2.8037% | Medium | Keep S08 non-canonical; practical gate accepted only for corroboration |
| 2026-10-07 | 2B | S08 selected rows had no usable spot values | Medium | Record source_field_unavailable; never fabricate spot |
| 2026-10-07 | 2B | S31 dynamic ATM files do not yield exact contract keys | Medium | Keep S31 NOT_COMPARABLE/research-only |
| 2026-10-07 | 2B | US Treasury endpoint in source manifest returned HTTP 404 | Medium | Correct or replace before US-rate features are admitted |