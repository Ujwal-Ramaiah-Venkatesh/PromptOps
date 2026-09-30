# Spelling Correction Guide for PromptOps Videos
## Ensure ZERO Spelling Mistakes in Generated Videos

---

## ✅ CRITICAL: SPELL OUT ALL NUMBERS AS WORDS

Google Vids may misinterpret numbers. Always provide both formats:

### CORRECT Format:
```
Text: "1,000+ Cloud Resources"
Pronunciation: "One thousand plus Cloud Resources"
Display: 1,000+ Cloud Resources
```

### WRONG Format:
```
Text: "1000+ Cloud Resources" ❌ (may render as "Thousand")
```

---

## 📝 CORRECTED TEXT FOR ALL CLIPS

### CLIP 1 TEXT:
**Text 1:**
- Display: **"1,000+ Cloud Resources"**
- Spell Check: ✅ Correct
- Alternative: "One Thousand Plus Cloud Resources"

**Text 2:**
- Display: **"3 Clouds, One View Needed"**
- Spell Check: ✅ Correct
- Alternative: "Three Clouds, One View Needed"

---

### CLIP 2 TEXT:
**Text 1:**
- Display: **"80% Time on Incidents"**
- Spell Check: ✅ Correct
- Alternative: "Eighty Percent Time on Incidents"

**Text 2:**
- Display: **"Less Time for Innovation"**
- Spell Check: ✅ Correct

---

### CLIP 3 TEXT:
**Text 1:**
- Display: **"$5,600 Per Minute"**
- Sub: **"DOWNTIME COST"**
- Spell Check: ✅ Correct
- Alternative Main: "Five Thousand Six Hundred Dollars Per Minute"
- Alternative Sub: "Downtime Cost"

**Text 2:**
- Display: **"35-40% Optimization"**
- Sub: **"OPPORTUNITY"**
- Spell Check: ✅ Correct
- Alternative Main: "Thirty-Five to Forty Percent Optimization"
- Alternative Sub: "Opportunity"

---

### CLIP 4 TEXT:
**Text 1:**
- Display: **"$2.4M Potential Savings"**
- Spell Check: ✅ Correct
- Alternative: "Two Point Four Million Dollars Potential Savings"

**Text 2:**
- Display: **"70% From Config Gaps"**
- Spell Check: ✅ Correct
- Alternative: "Seventy Percent From Configuration Gaps"

---

### CLIP 5 TEXT:
**Text 1:**
- Display: **"6:00 PM: Normal Traffic"**
- Spell Check: ✅ Correct
- Alternative: "Six PM: Normal Traffic"

**Text 2:**
- Display: **"6:30 PM: 10X SPIKE"**
- Sub: **"SYSTEMS STRAIN"**
- Spell Check: ✅ Correct (but check "10X")
- Alternative Main: "Six Thirty PM: Ten Times Spike"
- Alternative Sub: "Systems Strain"

---

### CLIP 6 TEXT:
**Text 1:**
- Display: **"2.5 Hours = $840K"**
- Sub: **"IMPACT"**
- Spell Check: ✅ Correct
- Alternative Main: "Two and Half Hours Equals Eight Hundred Forty Thousand Dollars"
- Alternative Sub: "Impact"

**Text 2:**
- Display: **"Better Coordination"**
- Sub: **"NEEDED"**
- Spell Check: ✅ Correct

**Text 3:**
- Display: **"Proactive Approach"**
- Sub: **"POSSIBLE"**
- Spell Check: ✅ Correct

---

### HERO ENTRY TEXT:
**Main Text:**
- Display: **"THE ULTIMATE SOLUTION"**
- Spell Check: ✅ Correct

**Subtitle:**
- Display: **"One Platform. All Clouds. Complete Control."**
- Spell Check: ✅ Correct
- Check periods: Each period must be included exactly

---

## 🔍 COMMON SPELLING MISTAKES TO AVOID

### 1. TECHNICAL TERMS:
❌ "Infastructure" → ✅ **"Infrastructure"**
❌ "Confguration" → ✅ **"Configuration"**
❌ "Opimization" → ✅ **"Optimization"**
❌ "Coordinaton" → ✅ **"Coordination"**
❌ "Obvservability" → ✅ **"Observability"**

### 2. NUMBERS & SYMBOLS:
❌ "5600" → ✅ **"5,600"** (include comma)
❌ "2.4 Million" → ✅ **"2.4M"** OR **"$2.4M"** (include $)
❌ "840K" → ✅ **"$840K"** (include $)
❌ "10x" → ✅ **"10X"** (capital X)

### 3. ABBREVIATIONS:
❌ "Pm" → ✅ **"PM"** (capital)
❌ "Am" → ✅ **"AM"** (capital)
❌ "K" (for thousand) → ✅ **"K"** (always capital)
❌ "M" (for million) → ✅ **"M"** (always capital)

### 4. PUNCTUATION:
❌ "Cloud Resources" → ✅ **"Cloud Resources"** (check no extra spaces)
❌ "One Platform All Clouds" → ✅ **"One Platform. All Clouds."** (include periods)
❌ "6:00PM" → ✅ **"6:00 PM"** (space before PM)

---

## 🛠️ FIX SPELLING MISTAKES IN GOOGLE VIDS

### If Google Vids Renders Text Incorrectly:

**Option 1: Regenerate with Clearer Instructions**
Add to prompt:
```
CRITICAL TEXT SPELLING:
- "Infrastructure" spelled I-N-F-R-A-S-T-R-U-C-T-U-R-E
- "Configuration" spelled C-O-N-F-I-G-U-R-A-T-I-O-N
- "Optimization" spelled O-P-T-I-M-I-Z-A-T-I-O-N
- Numbers: Use commas (5,600 not 5600)
- Currency: Always include $ symbol
- Time: Include space before AM/PM (6:00 PM not 6:00PM)
```

**Option 2: Fix in Video Editor**
1. Open video in **CapCut** or **DaVinci Resolve**
2. Add **Text Layer** over incorrect text
3. Match font: **Montserrat ExtraBold** or **Arial Black**
4. Match size, color, position exactly
5. Add black outline (5-6px) + drop shadow
6. Export with corrected text

**Option 3: Use Text Overlay Template**
Create pre-designed text overlays in Canva:
1. Design text with correct spelling
2. Export as transparent PNG
3. Import into video editor
4. Place over video at correct timing

---

## 📋 PRE-GENERATION CHECKLIST

Before generating each clip in Google Vids, verify:

**Text Accuracy:**
- [ ] All words spelled correctly
- [ ] Numbers formatted with commas (1,000 not 1000)
- [ ] Currency symbols included ($5,600 not 5600)
- [ ] Percentages include % symbol
- [ ] AM/PM capitalized with space
- [ ] Periods included where needed
- [ ] No extra spaces in text

**Technical Terms:**
- [ ] "Infrastructure" spelled correctly
- [ ] "Configuration" spelled correctly
- [ ] "Optimization" spelled correctly
- [ ] "Coordination" spelled correctly
- [ ] "Proactive" spelled correctly

**Formatting:**
- [ ] All capitals for emphasis words (ULTIMATE, NEEDED, POSSIBLE)
- [ ] Proper capitalization for titles
- [ ] Consistent font specified (Arial Black or Montserrat ExtraBold)

---

## 🔧 ENHANCED PROMPT INSTRUCTIONS FOR SPELLING

### Add This Section to EVERY Clip Prompt:

```
TEXT ACCURACY REQUIREMENTS (CRITICAL):
- Every word must be spelled EXACTLY as written below
- Use spell-check before rendering text
- Double-check all numbers, symbols, and punctuation
- If text is unclear, render as typed character-by-character
- NO automatic text corrections or substitutions
- Font must display all characters clearly with zero blur

VERIFY THESE SPECIFIC WORDS:
✓ Infrastructure (not Infastructure)
✓ Configuration (not Confguration)  
✓ Optimization (not Opimization)
✓ Coordination (not Coordinaton)
✓ Proactive (not Proactive)

VERIFY NUMBER FORMATTING:
✓ Use commas: 1,000+ (not 1000+)
✓ Use commas: 5,600 (not 5600)
✓ Include $: $2.4M (not 2.4M)
✓ Include %: 35-40% (not 35-40)
✓ Space before AM/PM: 6:00 PM (not 6:00PM)
✓ Capital X: 10X (not 10x)
```

---

## ✅ FINAL VERIFICATION STEPS

### After Google Vids Generates Each Clip:

1. **Pause video at each text overlay**
2. **Read text character by character**
3. **Check against this guide**
4. **Look for:**
   - Missing letters
   - Transposed letters (confguration vs configuration)
   - Missing punctuation (commas, periods, symbols)
   - Wrong capitalization
   - Extra spaces
   - Blurry or unclear letters

5. **If ANY spelling error found:**
   - Mark clip as "needs correction"
   - Either regenerate OR fix in video editor
   - DO NOT use clips with spelling errors

---

## 🎯 QUALITY STANDARD

**ZERO TOLERANCE for spelling mistakes.**

Every text element must be:
- ✅ 100% spelled correctly
- ✅ Properly formatted
- ✅ Crystal clear (readable)
- ✅ Professional appearance

**Remember:** One spelling mistake = unprofessional = regenerate or fix!

---

## 📞 TROUBLESHOOTING COMMON ISSUES

**Issue:** "Infastructure" appears instead of "Infrastructure"
**Fix:** Add to prompt: "Infrastructure spelled I-N-F-R-A-S-T-R-U-C-T-U-R-E"

**Issue:** "$5600" appears without comma
**Fix:** Add to prompt: "Currency formatted as $5,600 with comma separator"

**Issue:** "6:00PM" appears without space
**Fix:** Add to prompt: "Time formatted as 6:00 PM with space before PM"

**Issue:** Text is blurry/unclear
**Fix:** Add to prompt: "Text must be crystal clear, sharp edges, no blur, anti-aliased"

**Issue:** Wrong font used
**Fix:** Add to prompt: "MUST use Arial Black OR Montserrat ExtraBold, no substitutions"

---

**🎯 GOAL: PERFECT SPELLING IN EVERY SINGLE FRAME! 🎯**
