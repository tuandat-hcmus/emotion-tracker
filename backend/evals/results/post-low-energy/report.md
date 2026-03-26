# Response Quality Evaluation Report

- Run name: `post-low-energy`
- Dataset: `/mnt/c/Users/admin/Desktop/Project/Emotion/backend/evals/response_quality_cases.json`
- Provider: `mock`
- Generated at: `2026-03-24T08:10:06.394560+00:00`

## Summary

- Total cases: 3
- Successful cases: 3
- Failed cases: 0
- Average ai_response word count: 8.0

## Heuristic Flags

- `unexpected_question`: 1

## Repeated Openings

- No repeated openings crossed the threshold.

## Repeated Questions

- No repeated question stems crossed the threshold.

## Flagged Cases

### energy-02 (low_energy_emptiness)

- Input: I got out of bed, but that's about all I had in me.
- Output: That seems to have stayed with you. What feels hardest to say out loud?
- Issues: unexpected_question
- Review focus: Should feel quiet and humane.


## Baseline Comparison

- Changed cases: 3
### energy-01 (low_energy_emptiness)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That sounds flat and draining.
- Word count delta: -18
- Issue delta: -2

### energy-02 (low_energy_emptiness)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That seems to have stayed with you. What feels hardest to say out loud?
- Word count delta: -9
- Issue delta: -1

### energy-03 (low_energy_emptiness)

- Before: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- After: That sounds flat and draining.
- Word count delta: -18
- Issue delta: -2
