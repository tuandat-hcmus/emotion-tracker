# Vietnamese AI Core Demo

Generated from the live Vietnamese AI core demo service path.

## Work stress / deadline

**Input**: Mấy hôm nay deadline dồn liên tục, đầu mình lúc nào cũng căng và cứ sợ làm không kịp. Mình thấy khó thở nhẹ mỗi khi mở laptop.

**Provider path used**: `vi_canonical_emotion`

**Normalized emotion output**

```json
{
  "primary_emotion": "overwhelm",
  "secondary_emotions": [
    "anger",
    "anxiety"
  ],
  "emotion_label": "căng",
  "valence_score": -0.5,
  "energy_score": 0.77,
  "stress_score": 0.84,
  "confidence": 0.81,
  "provider_name": "vi_canonical_emotion",
  "response_mode": "grounding_soft"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "Áp lực đang dồn lên bạn khá nhiều quanh chuyện công việc/học tập. Mình không nghĩ bạn cần ép mình phải ổn ngay bây giờ, chỉ cần chậm lại một nhịp cũng đã là đủ.",
  "gentle_suggestion": "Nếu thấy hợp, thử thả vai xuống và hít ra chậm hơn một nhịp.",
  "safety_note": null
}
```

## Loneliness / left behind

**Input**: Dạo này nhìn bạn bè ai cũng có nhịp sống riêng, còn mình cứ thấy lạc lõng và hơi bị bỏ lại phía sau. Mình không biết nên tâm sự với ai.

**Provider path used**: `vi_canonical_emotion`

**Normalized emotion output**

```json
{
  "primary_emotion": "loneliness",
  "secondary_emotions": [
    "neutral",
    "sadness"
  ],
  "emotion_label": "cô đơn",
  "valence_score": -0.51,
  "energy_score": 0.21,
  "stress_score": 0.41,
  "confidence": 0.67,
  "provider_name": "vi_canonical_emotion",
  "response_mode": "low_energy_comfort"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "Từ điều bạn chia sẻ, mình đoán là bạn đã ôm cảm giác lạc lõng này khá lâu quanh chuyện cô đơn. Chỉ riêng việc bạn nói ra nó lúc này cũng đã là một cách tự dịu mình rất tử tế.",
  "gentle_suggestion": "Nếu được, cho mình một khoảng nghỉ thật ngắn mà không ép phải làm thêm gì ngay.",
  "safety_note": null
}
```

## Relief / gratitude

**Input**: Hôm nay mình nhận được một lời động viên đúng lúc và tự nhiên thấy nhẹ cả người. Mình rất biết ơn vì ít nhất mọi thứ không còn nặng như mấy hôm trước.

**Provider path used**: `vi_canonical_emotion`

**Normalized emotion output**

```json
{
  "primary_emotion": "gratitude",
  "secondary_emotions": [
    "joy",
    "neutral"
  ],
  "emotion_label": "biết ơn",
  "valence_score": 0.7,
  "energy_score": 0.39,
  "stress_score": 0.1,
  "confidence": 0.96,
  "provider_name": "vi_canonical_emotion",
  "response_mode": "celebratory_warm"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "Mình nghe khá rõ sự biết ơn và nhẹ lại quanh chuyện biết ơn/thành tựu. Có vẻ bạn đang chạm vào một điều thật sự nâng đỡ mình, và cảm giác đó đáng được giữ lại thêm một chút.",
  "gentle_suggestion": "Nếu muốn, bạn có thể giữ lại một chi tiết nhỏ đang làm hôm nay dễ thở hơn.",
  "safety_note": null
}
```

## Low energy / exhausted mood

**Input**: Mình không hẳn buồn dữ dội, chỉ là mệt và cạn pin. Làm gì cũng thấy chậm, đầu óc hơi trống và mình chỉ muốn nằm im một lúc.

**Provider path used**: `vi_canonical_emotion`

**Normalized emotion output**

```json
{
  "primary_emotion": "loneliness",
  "secondary_emotions": [
    "sadness",
    "neutral"
  ],
  "emotion_label": "cô đơn",
  "valence_score": -0.52,
  "energy_score": 0.21,
  "stress_score": 0.41,
  "confidence": 0.58,
  "provider_name": "vi_canonical_emotion",
  "response_mode": "low_energy_comfort"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "Từ điều bạn chia sẻ, mình đoán là năng lượng của bạn đang xuống khá thấp quanh chuyện sức khỏe. Mình muốn ghi nhận sự mệt đó mà không bắt bạn phải gượng lên ngay.",
  "gentle_suggestion": "Nếu được, cho mình một khoảng nghỉ thật ngắn mà không ép phải làm thêm gì ngay.",
  "safety_note": null
}
```

## Mixed emotion / nervous but hopeful

**Input**: Mai mình bắt đầu một việc mới nên vừa hồi hộp vừa có chút hy vọng. Mình sợ mình không đủ tốt, nhưng cũng thật lòng muốn thử tử tế với bản thân hơn.

**Provider path used**: `vi_canonical_emotion+visolex/phobert-emotion`

**Normalized emotion output**

```json
{
  "primary_emotion": "sadness",
  "secondary_emotions": [
    "loneliness",
    "anxiety"
  ],
  "emotion_label": "nặng nề",
  "valence_score": -0.46,
  "energy_score": 0.34,
  "stress_score": 0.47,
  "confidence": 0.89,
  "provider_name": "vi_canonical_emotion+visolex/phobert-emotion",
  "response_mode": "validating_gentle"
}
```

**Supportive sharing output**

```json
{
  "empathetic_response": "Có một phần nặng và căng trong điều bạn vừa kể quanh chuyện đời sống hằng ngày. Phản ứng đó không hề quá đáng, nó cho thấy chuyện này thật sự chạm vào bạn.",
  "gentle_suggestion": "Nếu thấy hợp, lùi lại một nhịp trước khi phải quyết định hay phản hồi điều gì tiếp theo.",
  "safety_note": null
}
```
