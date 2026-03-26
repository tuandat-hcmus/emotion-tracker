# Response Quality Evaluation Report

- Run name: `post-recovery`
- Dataset: `/mnt/c/Users/admin/Desktop/Project/Emotion/backend/evals/response_quality_cases.json`
- Provider: `mock`
- Generated at: `2026-03-24T08:11:06.143731+00:00`

## Summary

- Total cases: 3
- Successful cases: 3
- Failed cases: 0
- Average ai_response word count: 12.0

## Heuristic Flags

- `unexpected_question`: 2

## Repeated Openings

- No repeated openings crossed the threshold.

## Repeated Questions

- No repeated question stems crossed the threshold.

## Flagged Cases

### recovery-01 (mixed_recovery_improvement)

- Input: Yesterday was rough, but today feels a little easier.
- Output: It sounds a little lighter today. What feels hardest to say out loud?
- Issues: unexpected_question
- Review focus: Mixed recovery should sound hopeful but grounded.

### recovery-03 (mixed_recovery_improvement)

- Input: I cried earlier, but now I feel calmer.
- Output: It sounds a little steadier right now. What feels hardest to say out loud?
- Issues: unexpected_question
- Review focus: Human, not clinical.


## Baseline Comparison

- Changed cases: 3
### recovery-01 (mixed_recovery_improvement)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: It sounds a little lighter today. What feels hardest to say out loud?
- Word count delta: -10
- Issue delta: -1

### recovery-02 (mixed_recovery_improvement)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: Even a small shift away from stuck can matter.
- Word count delta: -14
- Issue delta: -2

### recovery-03 (mixed_recovery_improvement)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: It sounds a little steadier right now. What feels hardest to say out loud?
- Word count delta: -9
- Issue delta: -1
