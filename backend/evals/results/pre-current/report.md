# Response Quality Evaluation Report

- Run name: `pre-current`
- Dataset: `/mnt/c/Users/admin/Desktop/Project/Emotion/backend/evals/response_quality_cases.json`
- Provider: `gemini`
- Generated at: `2026-03-24T08:05:53.567185+00:00`

## Summary

- Total cases: 36
- Successful cases: 0
- Failed cases: 36
- Average ai_response word count: 0.0

## Heuristic Flags

- `pipeline_error:ProviderExecutionError`: 36

## Repeated Openings

- No repeated openings crossed the threshold.

## Repeated Questions

- No repeated question stems crossed the threshold.

## Flagged Cases

### greeting-01 (greeting_opening)

- Input: Hello
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Greeting should feel natural, brief, and welcoming.

### greeting-02 (greeting_opening)

- Input: Hey
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Warmth without over-assembly.

### greeting-03 (greeting_opening)

- Input: I just wanted to check in.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Opening should be short and steady.

### neutral-01 (neutral_checkin)

- Input: Today was pretty ordinary.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Neutral inputs should not feel over-processed.

### neutral-02 (neutral_checkin)

- Input: Nothing big happened today, just a normal day.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Neutral tone should remain calm and simple.

### sadness-01 (self_sadness)

- Input: I feel so sad now because I didn't finish the deadline on time.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Should feel supportive, grounded, and not stitched together.

### sadness-02 (self_sadness)

- Input: I felt low all evening after that conversation.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Stay evidence-bounded and emotionally natural.

### sadness-03 (self_sadness)

- Input: I miss my dad a lot tonight.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Warmth without therapy tone.

### stress-01 (self_stress_overload)

- Input: I can't keep up with all this pressure anymore.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Pressure support should feel direct and human.

### stress-02 (self_stress_overload)

- Input: Everything keeps piling up and I feel behind.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Catch over-assembly and template drift.

### stress-03 (self_stress_overload)

- Input: My head feels like too many tabs are open at once.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Should sound companion-like, not report-like.

### guilt-01 (guilt_regret)

- Input: I snapped at my sister and I keep replaying it.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Gentle validation without lecture.

### guilt-02 (guilt_regret)

- Input: I should have answered that message earlier.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Small regret should not become dramatic.

### guilt-03 (guilt_regret)

- Input: I keep thinking about what I said and wishing I could take it back.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Natural remorse handling.

### relief-01 (positive_relief_gratitude)

- Input: Finally, I finished my deadline.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Positive relief should feel like release, not treatment.

### relief-02 (positive_relief_gratitude)

- Input: Today felt lighter than yesterday.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Mixed recovery should preserve the lighter tone.

### relief-03 (positive_relief_gratitude)

- Input: My friend helped me today and I feel really grateful.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Gratitude should remain warm and uncluttered.

### other-01 (other_person_concern)

- Input: My friend Minh seems sad now.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Self-vs-other correctness is critical here.

### other-02 (other_person_concern)

- Input: My crush looks upset today.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Concern and uncertainty should both be visible.

### other-03 (other_person_concern)

- Input: My sister seems really stressed lately.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Relationship concern should stay relational.

### other-04 (other_person_concern)

- Input: My coworker has looked overwhelmed all week.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Concern can be present without overpersonalizing.

### ambiguous-01 (ambiguous_emotion_ownership)

- Input: Things have felt tense at home lately.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Ambiguous ownership should stay ambiguous.

### ambiguous-02 (ambiguous_emotion_ownership)

- Input: We both seemed off after dinner.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: This should not over-claim.

### ambiguous-03 (ambiguous_emotion_ownership)

- Input: It was a weird conversation and now everything feels heavy.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Evidence-bounded restraint matters here.

### deadline-01 (work_pressure_deadline)

- Input: I didn't finish the project on time and now I feel behind.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Deadline pressure should be grounded and concise.

### deadline-02 (work_pressure_deadline)

- Input: My inbox keeps growing and I can't catch up.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Supportive pressure handling without canned coaching.

### deadline-03 (work_pressure_deadline)

- Input: I'm behind again and the deadline is tomorrow.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Urgency without panic.

### energy-01 (low_energy_emptiness)

- Input: I feel empty today.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Low-energy moments should not feel overwritten.

### energy-02 (low_energy_emptiness)

- Input: I got out of bed, but that's about all I had in me.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Should feel quiet and humane.

### energy-03 (low_energy_emptiness)

- Input: Everything feels flat lately.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Tone should match the low-energy input.

### frustration-01 (frustration_not_heard)

- Input: I tried to explain myself and nobody really listened.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Frustration should feel seen without narrative invention.

### frustration-02 (frustration_not_heard)

- Input: I feel talked over every time I bring this up.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Supportive and plainspoken.

### frustration-03 (frustration_not_heard)

- Input: They kept interrupting me and now I'm just annoyed.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Short frustration handling.

### recovery-01 (mixed_recovery_improvement)

- Input: Yesterday was rough, but today feels a little easier.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Mixed recovery should sound hopeful but grounded.

### recovery-02 (mixed_recovery_improvement)

- Input: I'm still tired, but not as stuck as before.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Nuance matters.

### recovery-03 (mixed_recovery_improvement)

- Input: I cried earlier, but now I feel calmer.
- Output: None
- Issues: pipeline_error:ProviderExecutionError
- Review focus: Human, not clinical.
