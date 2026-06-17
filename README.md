# Hume AI — Speech Prosody Dataset

Interactive map: https://www.hume.ai/explore/speech-prosody-model

## What this is

A dataset of ~8,000 short speech clips labelled with emotion scores, collected via Amazon Mechanical Turk and published by Alan Cowen, Dacher Keltner et al. (Hume AI / UC Berkeley).

Each clip is a neutral sentence spoken with a specific emotional prosody (tone, rhythm, timbre). MTurk raters listened and selected which emotions they heard; the scores are the proportion of raters who chose each emotion. Only emotions that passed a significance threshold are stored per clip — the rest are absent from that entry.

The dataset was originally published with 2,519 clips (Cowen et al., 2019). The version on the Hume AI website contains **7,988 clips**.

## How it was collected

1. **Recording:** 100 actors from 5 cultures produced speech samples. They spoke lexically identical sentences (same words every time) while being induced into a target emotional state — so any emotional signal is purely prosodic.
2. **Rating:** US and Indian participants on MTurk rated each clip on 48 emotion categories and several affective scales (valence, arousal, etc.).
3. **Analysis:** Semantic space methods (PPCA across cultures) identified 12+ preserved dimensions of emotional prosody. Results visualized as a 2D t-SNE map.

## Files

```
metadata.json          — full dataset, one object per clip (7,988 entries)
labels.csv             — same data in CSV format
audio/                 — MP3 files, named to match the File field
download_progress.csv  — download tracking (url, filename, status)
scrape_and_download.py — script used to extract + download everything
```

## Data format

Each entry has:

| Field | Type | Description |
|-------|------|-------------|
| `File` | string | Original S3 URL of the MP3 |
| `X` | int | t-SNE x coordinate on the 2D emotion map |
| `Y` | int | t-SNE y coordinate on the 2D emotion map |
| `Color` | hex string | Dot color on the map (encodes dominant emotion cluster) |
| *(emotion name)* | float 0–1 | Proportion of raters who attributed that emotion |

Only emotions above a significance threshold are included per clip. The full set of 46 possible emotion labels: Admiration, Adoration, Aesthetic_Appreciation, Amusement, Anger, Anxiety, Awe, Awkwardness, Boredom, Calmness, Concentration, Confusion, Contemplation, Contempt, Contentment, Craving, Desire, Determination, Disappointment, Disgust, Distress, Doubt, Ecstasy, Embarrassment, Empathic_Pain, Entrancement, Envy, Excitement, Fear, Guilt, Horror, Interest, Joy, Love, Nostalgia, Pain, Pride, Realization, Relief, Romance, Sadness, Satisfaction, Shame, Sympathy, Tiredness, Triumph.

## Samples

**Clip with high anger + blended aesthetics** (`dia973_utt12.mp3`):
```json
{
  "File": "https://mturkrecord.s3.amazonaws.com/targpros/dia973_utt12.mp3",
  "X": 270, "Y": 151, "Color": "#964E82",
  "Anger": 0.715, "Aesthetic_Appreciation": 0.538, "Calmness": 0.48,
  "Admiration": 0.326, "Adoration": 0.339, "Doubt": 0.353,
  "Distress": 0.247, "Joy": 0.251, "Disgust": 0.216
}
```

**Clip dominated by anxiety** (`dia590_utt7.mp3`):
```json
{
  "File": "https://mturkrecord.s3.amazonaws.com/targpros/dia590_utt7.mp3",
  "X": 331, "Y": 512, "Color": "#906376",
  "Anxiety": 0.59, "Contemplation": 0.393, "Awkwardness": 0.362,
  "Determination": 0.225, "Interest": 0.207, "Adoration": 0.252
}
```

## Papers

- **nihms-1518869.pdf** — Cowen et al. (2019). *The primacy of categories in the recognition of 12 emotions in speech prosody across two cultures.* Nature Human Behaviour. The original study behind this dataset.
- **1-s2.0-S136466132030276X-main.pdf** — Cowen & Keltner (2021). *Semantic Space Theory: A Computational Approach to Emotion.* Trends in Cognitive Sciences. The theoretical framework.
- **23Keltner-BasicEmotions.pdf** — Keltner, Brooks & Cowen (2023). *Semantic Space Theory: Data-Driven Insights Into Basic Emotions.* Current Directions in Psychological Science.
- **Deep-learning-reveals-what-vocal-bursts-express-in-different-cultures.pdf** — Brooks et al. (2022). *Deep learning reveals what vocal bursts express in different cultures.* Nature Human Behaviour. Related dataset (non-linguistic vocalizations, same lab).
