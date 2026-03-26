# Response Quality Evaluation Report

- Run name: `pre-mock`
- Dataset: `/mnt/c/Users/admin/Desktop/Project/Emotion/backend/evals/response_quality_cases.json`
- Provider: `mock`
- Generated at: `2026-03-24T08:05:41.334202+00:00`

## Summary

- Total cases: 36
- Successful cases: 36
- Failed cases: 0
- Average ai_response word count: 18.94

## Heuristic Flags

- `unexpected_question`: 13
- `too_long:23>18`: 9
- `too_long:23>20`: 4
- `too_long:23>22`: 2

## Repeated Openings

- `that sounds heavy`: 22
- `that sounds like`: 4

## Repeated Questions

- `what feels hardest to say out`: 22
- `what feels heaviest right now`: 5

## Flagged Cases

### greeting-03 (greeting_opening)

- Input: I just wanted to check in.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Opening should be short and steady.

### neutral-01 (neutral_checkin)

- Input: Today was pretty ordinary.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Neutral inputs should not feel over-processed.

### neutral-02 (neutral_checkin)

- Input: Nothing big happened today, just a normal day.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>20, unexpected_question
- Review focus: Neutral tone should remain calm and simple.

### sadness-03 (self_sadness)

- Input: I miss my dad a lot tonight.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>20, unexpected_question
- Review focus: Warmth without therapy tone.

### guilt-02 (guilt_regret)

- Input: I should have answered that message earlier.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Small regret should not become dramatic.

### relief-02 (positive_relief_gratitude)

- Input: Today felt lighter than yesterday.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Mixed recovery should preserve the lighter tone.

### ambiguous-01 (ambiguous_emotion_ownership)

- Input: Things have felt tense at home lately.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>22
- Review focus: Ambiguous ownership should stay ambiguous.

### ambiguous-02 (ambiguous_emotion_ownership)

- Input: We both seemed off after dinner.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>22
- Review focus: This should not over-claim.

### energy-01 (low_energy_emptiness)

- Input: I feel empty today.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Low-energy moments should not feel overwritten.

### energy-02 (low_energy_emptiness)

- Input: I got out of bed, but that's about all I had in me.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>20, unexpected_question
- Review focus: Should feel quiet and humane.

### energy-03 (low_energy_emptiness)

- Input: Everything feels flat lately.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Tone should match the low-energy input.

### frustration-03 (frustration_not_heard)

- Input: They kept interrupting me and now I'm just annoyed.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>20, unexpected_question
- Review focus: Short frustration handling.

### recovery-01 (mixed_recovery_improvement)

- Input: Yesterday was rough, but today feels a little easier.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Mixed recovery should sound hopeful but grounded.

### recovery-02 (mixed_recovery_improvement)

- Input: I'm still tired, but not as stuck as before.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Nuance matters.

### recovery-03 (mixed_recovery_improvement)

- Input: I cried earlier, but now I feel calmer.
- Output: That sounds heavy, and you do not have to sort all of it out right now. What feels hardest to say out loud?
- Issues: too_long:23>18, unexpected_question
- Review focus: Human, not clinical.
