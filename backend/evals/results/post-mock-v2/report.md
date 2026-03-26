# Response Quality Evaluation Report

- Run name: `post-mock-v2`
- Dataset: `/mnt/c/Users/admin/Desktop/Project/Emotion/backend/evals/response_quality_cases.json`
- Provider: `mock`
- Generated at: `2026-03-24T08:18:18.053071+00:00`

## Summary

- Total cases: 36
- Successful cases: 36
- Failed cases: 0
- Average ai_response word count: 10.42

## Heuristic Flags

- `missing_expected_question`: 3
- `unexpected_question`: 2

## Repeated Openings

- `that seems to`: 11
- `that sounds like`: 4
- `it sounds a`: 3

## Repeated Questions

- `what feels hardest to say out`: 8
- `what feels heaviest right now`: 5

## Flagged Cases

### sadness-02 (self_sadness)

- Input: I felt low all evening after that conversation.
- Output: That seems to be sitting with you.
- Issues: missing_expected_question
- Review focus: Stay evidence-bounded and emotionally natural.

### sadness-03 (self_sadness)

- Input: I miss my dad a lot tonight.
- Output: Missing someone can feel especially close at night. What feels hardest to say out loud?
- Issues: unexpected_question
- Review focus: Warmth without therapy tone.

### ambiguous-01 (ambiguous_emotion_ownership)

- Input: Things have felt tense at home lately.
- Output: That seems to be sitting with you.
- Issues: missing_expected_question
- Review focus: Ambiguous ownership should stay ambiguous.

### ambiguous-02 (ambiguous_emotion_ownership)

- Input: We both seemed off after dinner.
- Output: That seems to have stayed with you.
- Issues: missing_expected_question
- Review focus: This should not over-claim.

### frustration-03 (frustration_not_heard)

- Input: They kept interrupting me and now I'm just annoyed.
- Output: That would wear on you. What feels hardest to say out loud?
- Issues: unexpected_question
- Review focus: Short frustration handling.


## Baseline Comparison

- Changed cases: 22
### greeting-03 (greeting_opening)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: I'm glad you checked in.
- Word count delta: -18
- Issue delta: -2

### neutral-01 (neutral_checkin)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: A quieter day still counts.
- Word count delta: -18
- Issue delta: -2

### neutral-02 (neutral_checkin)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: A quieter day still counts.
- Word count delta: -18
- Issue delta: -2

### sadness-02 (self_sadness)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to be sitting with you.
- Word count delta: -16
- Issue delta: 1

### sadness-03 (self_sadness)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: Missing someone can feel especially close at night. What feels hardest to say out loud?
- Word count delta: -8
- Issue delta: -1

### stress-03 (self_stress_overload)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you. What feels hardest to say out loud?
- Word count delta: -9
- Issue delta: 0

### guilt-01 (guilt_regret)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you. What feels hardest to say out loud?
- Word count delta: -9
- Issue delta: 0

### guilt-02 (guilt_regret)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to be lingering with you.
- Word count delta: -16
- Issue delta: -2

### guilt-03 (guilt_regret)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you. What feels hardest to say out loud?
- Word count delta: -9
- Issue delta: 0

### relief-02 (positive_relief_gratitude)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: It sounds a little lighter today.
- Word count delta: -17
- Issue delta: -2

### ambiguous-01 (ambiguous_emotion_ownership)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to be sitting with you.
- Word count delta: -16
- Issue delta: 0

### ambiguous-02 (ambiguous_emotion_ownership)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you.
- Word count delta: -16
- Issue delta: 0

### ambiguous-03 (ambiguous_emotion_ownership)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you. What feels hardest to say out loud?
- Word count delta: -9
- Issue delta: 0

### deadline-02 (work_pressure_deadline)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you. What feels hardest to say out loud?
- Word count delta: -9
- Issue delta: 0

### energy-01 (low_energy_emptiness)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That sounds flat and draining.
- Word count delta: -18
- Issue delta: -2

### energy-02 (low_energy_emptiness)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you.
- Word count delta: -16
- Issue delta: -2

### energy-03 (low_energy_emptiness)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That sounds flat and draining.
- Word count delta: -18
- Issue delta: -2

### frustration-01 (frustration_not_heard)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you. What feels hardest to say out loud?
- Word count delta: -9
- Issue delta: 0

### frustration-03 (frustration_not_heard)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That would wear on you. What feels hardest to say out loud?
- Word count delta: -11
- Issue delta: -1

### recovery-01 (mixed_recovery_improvement)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: It sounds a little lighter today.
- Word count delta: -17
- Issue delta: -2
