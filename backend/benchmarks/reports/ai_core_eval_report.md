# AI Core Evaluation Report

Dataset size: 40 examples

Language split:
- vi: 20
- zh: 20

## Metrics

| system | accuracy | macro_f1 | valence_mae | energy_mae | stress_mae |
| --- | ---: | ---: | ---: | ---: | ---: |
| legacy | 0.9 | 0.881 | 0.095 | 0.049 | 0.044 |
| ai_core | 0.175 | 0.108 | 0.209 | 0.173 | 0.132 |

## AI Core Provider Breakdown

- vi_model: 20
- zh_model: 20
- fallback_model: 0
- heuristic_fallback: 0

## Representative Legacy Errors
| id | language | gold | pred | route | provider | text |
| --- | --- | --- | --- | --- | --- | --- |
| vi-15 | vi | anxiety | joy | heuristic_fallback | legacy_heuristic | Mình vui nhưng cũng lo lắng về bước tiếp theo. |
| zh-05 | zh | relief | neutral | heuristic_fallback | legacy_heuristic | 事情结束后我松了一口气。 |
| zh-13 | zh | exhaustion | neutral | heuristic_fallback | legacy_heuristic | 我太累了，像被掏空了一样。 |
| zh-15 | zh | anxiety | joy | heuristic_fallback | legacy_heuristic | 我开心，但也担心下一步怎么办。 |

## Representative AI Core Errors
| id | language | gold | pred | route | provider | text |
| --- | --- | --- | --- | --- | --- | --- |
| vi-02 | vi | gratitude | joy | vi_model | visolex/phobert-emotion | Mình biết ơn vì gia đình đã luôn ở bên. |
| vi-03 | vi | pride | joy | vi_model | visolex/phobert-emotion | Mình thấy tự hào vì đã vượt qua được tuần khó này. |
| vi-04 | vi | calm | joy | vi_model | visolex/phobert-emotion | Tối nay mình khá bình yên và dễ thở hơn. |
| vi-05 | vi | relief | joy | vi_model | visolex/phobert-emotion | Xong deadline rồi nên mình nhẹ nhõm hơn nhiều. |
| vi-06 | vi | hope | joy | vi_model | visolex/phobert-emotion | Dù khó nhưng mình vẫn còn hy vọng mọi thứ sẽ khá hơn. |
| vi-08 | vi | loneliness | sadness | vi_model | visolex/phobert-emotion | Mình thấy rất cô đơn và không ai hiểu mình. |

## AI Core Per-Row Routes
| id | language | gold | pred | route | provider | confidence | text |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| vi-01 | vi | joy | joy | vi_model | visolex/phobert-emotion | 1.0 | Hôm nay mình rất vui vì công việc tiến triển tốt. |
| vi-02 | vi | gratitude | joy | vi_model | visolex/phobert-emotion | 1.0 | Mình biết ơn vì gia đình đã luôn ở bên. |
| vi-03 | vi | pride | joy | vi_model | visolex/phobert-emotion | 1.0 | Mình thấy tự hào vì đã vượt qua được tuần khó này. |
| vi-04 | vi | calm | joy | vi_model | visolex/phobert-emotion | 0.99 | Tối nay mình khá bình yên và dễ thở hơn. |
| vi-05 | vi | relief | joy | vi_model | visolex/phobert-emotion | 0.95 | Xong deadline rồi nên mình nhẹ nhõm hơn nhiều. |
| vi-06 | vi | hope | joy | vi_model | visolex/phobert-emotion | 0.98 | Dù khó nhưng mình vẫn còn hy vọng mọi thứ sẽ khá hơn. |
| vi-07 | vi | sadness | sadness | vi_model | visolex/phobert-emotion | 1.0 | Mình buồn và thất vọng về bản thân hôm nay. |
| vi-08 | vi | loneliness | sadness | vi_model | visolex/phobert-emotion | 1.0 | Mình thấy rất cô đơn và không ai hiểu mình. |
| vi-09 | vi | emptiness | sadness | vi_model | visolex/phobert-emotion | 0.77 | Cả ngày như trống rỗng và hơi tê liệt. |
| vi-10 | vi | anxiety | sadness | vi_model | visolex/phobert-emotion | 0.81 | Mình lo lắng và bất an về kỳ thi sắp tới. |
| vi-11 | vi | overwhelm | sadness | vi_model | visolex/phobert-emotion | 0.67 | Deadline dồn dập làm mình ngộp và quá tải. |
| vi-12 | vi | anger | anger | vi_model | visolex/phobert-emotion | 0.92 | Mình rất bực bội và ức chế vì bị đổ lỗi. |
| vi-13 | vi | exhaustion | sadness | vi_model | visolex/phobert-emotion | 1.0 | Mình mệt, kiệt sức và thiếu ngủ nhiều ngày rồi. |
| vi-14 | vi | hope | joy | vi_model | visolex/phobert-emotion | 0.79 | Mình hơi buồn nhưng vẫn còn hy vọng. |
| vi-15 | vi | anxiety | sadness | vi_model | visolex/phobert-emotion | 0.95 | Mình vui nhưng cũng lo lắng về bước tiếp theo. |
| vi-16 | vi | loneliness | sadness | vi_model | visolex/phobert-emotion | 0.99 | Mình cô đơn và mệt nên chỉ muốn im lặng. |
| vi-17 | vi | neutral | neutral | vi_model | visolex/phobert-emotion | 0.61 | Hôm nay mọi thứ bình thường, không quá tốt cũng không quá tệ. |
| vi-18 | vi | gratitude | joy | vi_model | visolex/phobert-emotion | 0.99 | Mình nhẹ nhõm và biết ơn sau khi nói chuyện với mẹ. |
| vi-19 | vi | overwhelm | joy | vi_model | visolex/phobert-emotion | 0.76 | Mình áp lực nhưng vẫn cố gắng giữ bình tĩnh. |
| vi-20 | vi | hope | joy | vi_model | visolex/phobert-emotion | 0.49 | Mình thấy có chút hy vọng sau một ngày nặng nề. |
| zh-01 | zh | joy | joy | zh_model | Johnson8187/Chinese-Emotion-Small | 0.99 | 今天我很开心，事情进展得不错。 |
| zh-02 | zh | gratitude | joy | zh_model | Johnson8187/Chinese-Emotion-Small | 0.98 | 我很感谢家人一直支持我。 |
| zh-03 | zh | pride | joy | zh_model | Johnson8187/Chinese-Emotion-Small | 0.97 | 我为自己挺过这周感到自豪。 |
| zh-04 | zh | calm | neutral | zh_model | Johnson8187/Chinese-Emotion-Small | 0.98 | 今晚我终于平静了一些。 |
| zh-05 | zh | relief | neutral | zh_model | Johnson8187/Chinese-Emotion-Small | 0.99 | 事情结束后我松了一口气。 |
| zh-06 | zh | hope | neutral | zh_model | Johnson8187/Chinese-Emotion-Small | 0.9 | 虽然很难，但我还是有一点希望。 |
| zh-07 | zh | sadness | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.98 | 我今天很难过，也对自己很失望。 |
| zh-08 | zh | loneliness | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.97 | 我觉得很孤独，没有人真正理解我。 |
| zh-09 | zh | emptiness | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.98 | 整个人都很空虚，好像麻木了。 |
| zh-10 | zh | anxiety | neutral | zh_model | Johnson8187/Chinese-Emotion-Small | 0.89 | 我最近很焦虑，也一直很担心。 |
| zh-11 | zh | overwhelm | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.97 | 压力一下子全压过来，我有点崩溃。 |
| zh-12 | zh | anger | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.98 | 我真的很生气，也很委屈。 |
| zh-13 | zh | exhaustion | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.98 | 我太累了，像被掏空了一样。 |
| zh-14 | zh | hope | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.94 | 我有点难过，但还是保留希望。 |
| zh-15 | zh | anxiety | neutral | zh_model | Johnson8187/Chinese-Emotion-Small | 0.96 | 我开心，但也担心下一步怎么办。 |
| zh-16 | zh | loneliness | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.98 | 我很孤独，也很累，只想安静。 |
| zh-17 | zh | neutral | neutral | zh_model | Johnson8187/Chinese-Emotion-Small | 0.99 | 今天就很普通，没有特别好也没有特别糟。 |
| zh-18 | zh | gratitude | neutral | zh_model | Johnson8187/Chinese-Emotion-Small | 0.63 | 和妈妈聊完后，我既感激又放松。 |
| zh-19 | zh | overwhelm | neutral | zh_model | Johnson8187/Chinese-Emotion-Small | 0.94 | 我压力很大，但还是努力保持冷静。 |
| zh-20 | zh | hope | sadness | zh_model | Johnson8187/Chinese-Emotion-Small | 0.98 | 经历很沉重的一天后，我还有一点希望。 |
