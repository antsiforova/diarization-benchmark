# Sequestered Data Methodology

## My Implementation: Scripted Conversations

### Overview

I recorded conversations between 2 people following given scenarios. The recordings were then automatically annotated and manually verified to produce perfect ground truth.

### Complete Pipeline

```
1. Script/Scenario → 2. Live Recording → 3. Auto-Annotation → 4. Manual Verification → 5. Ground Truth
```

### Step 1: Scenario Design

**Key Steps:**
- Create realistic conversation scenarios (team meetings, interviews, casual discussions)
- Define speaker roles but no exact scripts
- Aim for 10-15 minute conversations
- Encourage natural overlaps and turn-taking

**Example scenario:**
> "Product planning meeting: 3 people discussing feature priorities. Person A is project manager, B is designer, C is engineer. Discuss 3 features, with natural disagreements and clarifications."

### Step 2: Recording Setup

**Equipment:**
- Single microphone (simulates real-world conditions)
- Quiet room with some ambient sound (realistic)

**Recording process:**
- Positioned mic centrally
- Brief test recording to check levels
- Recorded full conversation (10-15 minutes)
- Saved as WAV files

**Participants:**
- Friends and colleagues who volunteered
- Different voice types (gender, accent, pitch)
- Natural conversation style, not reading scripts

### Step 3: Automatic Annotation

I used **Precision-2** model (via pyannote.ai API) to generate initial annotations.

This produces RTTM format:
```
SPEAKER conversation_01 1 0.0 3.5 <NA> <NA> spk0 <NA> <NA>
SPEAKER conversation_01 1 3.5 2.1 <NA> <NA> spk1 <NA> <NA>
```

### Step 4: Manual Verification

**Process:**
1. Listen to recording while viewing Precision-2 annotations
2. Correct speaker boundaries (start/end times)
3. Fix speaker label mistakes
4. Mark overlapping speech regions
5. Verify against recording metadata (who spoke when)


### Step 5: Final Ground Truth

After manual verification, I have:
- Perfect speaker labels
- Accurate time boundaries
- All overlaps marked correctly
- Validated RTTM format

**Example final RTTM:**
```
SPEAKER conv_01 1 0.000 3.245 <NA> <NA> spk0 <NA> <NA>
SPEAKER conv_01 1 3.245 1.980 <NA> <NA> spk1 <NA> <NA>
SPEAKER conv_01 1 4.100 0.850 <NA> <NA> spk0 <NA> <NA>
SPEAKER conv_01 1 4.800 2.100 <NA> <NA> spk1 <NA> <NA>
```

### Current Dataset

This is a small demonstration dataset to show the methodology in practice.

**Statistics:**
- 6 conversations
- ~20 seconds each (short samples for demo purposes)
- 2 speakers per conversation
- ~2 minutes total audio
- All manually verified following the process above

**File locations:**
```
data/sequestered/
  recordings/
    audio/           # WAV files
      conversation_01.wav
      conversation_02.wav
      ...
    annotation/      # Ground truth RTTM
      conversation_01.rttm
      conversation_02.rttm
      ...
```

## Other Approaches to Sequestered Data

For production systems, there are different ways to collect evaluation data:

**Recording Options:**
- **Internal volunteers** (company employees) - easiest consent, known participants
- **External participants** (with explicit consent) - more diverse, but requires clear agreements

**Annotation Options:**
- **Model + manual verification** (what I used) - use existing diarization model, then manually correct its output
- **Professional labelers** - hire annotation services for high volume
