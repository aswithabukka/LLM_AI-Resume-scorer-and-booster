# 📊 ATS Scoring System Explained

## Overview

ATS-Tailor calculates a **0-100 score** that predicts how well your resume matches a job description. The score is based on 5 weighted components that ATS systems typically evaluate.

---

## 🎯 Score Formula

```
ATS Score = (Coverage × 0.35) + (Explicitness × 0.25) + (Role Alignment × 0.15) 
            + (Keywords × 0.15) + (Writing Quality × 0.10)
```

**Total weights = 1.0 (100%)**

---

## 📈 Component Breakdown

### 1. **Coverage (35% weight)** - Most Important

**What it measures**: Percentage of must-have skills from the JD that are present in your resume.

**How it's calculated**:
```python
coverage = (present_skills + weak_skills) / total_must_have_skills
```

**Scoring logic**:
- Uses semantic similarity (embeddings) to match requirements to resume bullets
- **Present** (similarity ≥ 0.75): Skill is clearly demonstrated
- **Weak** (0.50 ≤ similarity < 0.75): Skill is mentioned but not explicit
- **Missing** (similarity < 0.50): Skill not found

**Example**:
- JD requires: Python, SQL, AWS, Machine Learning, A/B Testing (5 skills)
- Resume has: Python (present), SQL (present), AWS (weak), ML (present), A/B Testing (missing)
- Coverage = (3 present + 1 weak) / 5 = **80%**

**Why it matters**: ATS systems prioritize candidates who have the required skills.

---

### 2. **Explicitness (25% weight)** - Very Important

**What it measures**: Percentage of must-have skills that are **explicitly named** in your resume (not just implied).

**How it's calculated**:
```python
explicitness = exact_skill_matches / total_must_have_skills
```

**Scoring logic**:
- Checks if skill name appears verbatim in resume text
- Case-insensitive matching
- Includes aliases (e.g., "pytorch" matches "PyTorch")

**Example**:
- JD requires: Python, SQL, AWS, Machine Learning, A/B Testing (5 skills)
- Resume explicitly mentions: "Python", "SQL", "Machine Learning" (3 skills)
- Explicitness = 3 / 5 = **60%**

**Why it matters**: ATS keyword matching looks for exact terms. If you say "statistical experimentation" instead of "A/B testing", ATS may miss it.

---

### 3. **Role Alignment (15% weight)** - Moderately Important

**What it measures**: How well your current/target job title matches the JD title.

**How it's calculated**:
```python
# Extract key role words from both titles
jd_roles = ["data scientist", "machine learning", "senior"]
resume_roles = ["data analyst", "machine learning"]

# Calculate overlap
alignment = len(jd_roles ∩ resume_roles) / len(jd_roles)
```

**Scoring logic**:
- Extracts role keywords (scientist, engineer, analyst, senior, lead, etc.)
- Compares overlap between JD title and your most recent title
- Exact match = 100%, No overlap = 0%

**Example**:
- JD title: "Senior Data Scientist"
- Resume title: "Data Scientist"
- Common keywords: ["data scientist"] (1 out of 2)
- Role Alignment = 1 / 2 = **50%**

**Why it matters**: ATS often filters by job title first. A "Data Analyst" applying for "Data Scientist" may score lower.

---

### 4. **Keywords (15% weight)** - Moderately Important

**What it measures**: Density of technical keywords (tools, platforms, technologies) from the JD in your resume.

**How it's calculated**:
```python
# Extract all technical keywords from JD
jd_keywords = {"Python", "AWS", "Docker", "Kubernetes", "Spark"}

# Count how many appear in resume
matches = 0
for keyword in jd_keywords:
    if keyword.lower() in resume_text.lower():
        matches += 1

keyword_score = matches / len(jd_keywords)
```

**Scoring logic**:
- Checks both Skills section and bullet points
- Case-insensitive matching
- Includes variations (e.g., "K8s" matches "Kubernetes")

**Example**:
- JD mentions: Python, AWS, Docker, Kubernetes, Spark (5 keywords)
- Resume mentions: Python, AWS, Docker (3 keywords)
- Keywords = 3 / 5 = **60%**

**Why it matters**: ATS systems scan for specific technologies. More keyword matches = higher relevance.

---

### 5. **Writing Quality (10% weight)** - Least Important

**What it measures**: Quality of resume bullet points based on best practices.

**How it's calculated**:
```python
for each bullet:
    score = 0
    
    # Check 1: Length (≤28 words ideal)
    if word_count <= 28:
        score += 0.33
    
    # Check 2: Starts with action verb
    if first_word in action_verbs:
        score += 0.33
    
    # Check 3: Contains numbers/metrics
    if has_numbers(bullet):
        score += 0.34
    
writing_quality = average(all_bullet_scores)
```

**Scoring criteria**:
- **Length**: Bullets should be concise (≤28 words)
- **Action verbs**: Start with strong verbs (Built, Led, Improved, etc.)
- **Quantification**: Include metrics (%, $, time, scale)

**Example bullet scoring**:
- ✅ "Built Python ETL pipeline processing 10M records/day, reducing runtime by 40%" 
  - Length: 11 words ✓
  - Action verb: "Built" ✓
  - Metrics: "10M", "40%" ✓
  - **Score: 100%**

- ⚠️ "Responsible for data analysis and reporting"
  - Length: 6 words ✓
  - Action verb: None ✗
  - Metrics: None ✗
  - **Score: 33%**

**Why it matters**: Well-written bullets are easier for ATS to parse and more impressive to human reviewers.

---

## 🎯 Score Interpretation

| Score Range | Interpretation | Action |
|-------------|----------------|--------|
| **80-100** | Excellent match | Apply with confidence |
| **60-79** | Good match | Apply top suggestions |
| **40-59** | Moderate gaps | Significant tailoring needed |
| **0-39** | Poor match | Major mismatch or wrong role |

---

## 🔧 How to Improve Your Score

### **To improve Coverage (+35% impact)**:
1. Add missing must-have skills to your bullets
2. Rewrite bullets to demonstrate required skills
3. Add relevant projects that showcase skills

### **To improve Explicitness (+25% impact)**:
1. Use exact skill names from JD
2. Add skills to your Skills section
3. Replace vague terms with specific ones
   - ❌ "cloud platforms" → ✅ "AWS, GCP"
   - ❌ "data analysis" → ✅ "Python, Pandas, SQL"

### **To improve Role Alignment (+15% impact)**:
1. Update your title to match target role
2. Add target role keywords to summary
3. Emphasize relevant experience

### **To improve Keywords (+15% impact)**:
1. Mention specific tools/technologies
2. Use industry-standard terms
3. Include frameworks, platforms, methodologies

### **To improve Writing Quality (+10% impact)**:
1. Start bullets with action verbs
2. Add quantified metrics
3. Keep bullets concise (≤28 words)

---

## 📊 Example Calculation

**Job Description**: Senior Data Scientist
- Must-have skills: Python, SQL, Machine Learning, A/B Testing, AWS (5 skills)
- Keywords: Pandas, Scikit-learn, Docker, Airflow (4 keywords)
- Title: "Senior Data Scientist"

**Your Resume**:
- Skills present: Python (present), SQL (present), ML (present), A/B Testing (weak), AWS (missing)
- Explicit mentions: Python, SQL, Machine Learning (3 skills)
- Keywords found: Pandas, Scikit-learn (2 keywords)
- Your title: "Data Scientist"
- Bullet quality: 75% average

**Score Calculation**:
```
Coverage = (3 present + 1 weak) / 5 = 0.80
Explicitness = 3 / 5 = 0.60
Role Alignment = 1 / 2 = 0.50  (missing "Senior")
Keywords = 2 / 4 = 0.50
Writing Quality = 0.75

ATS Score = (0.80 × 0.35) + (0.60 × 0.25) + (0.50 × 0.15) + (0.50 × 0.15) + (0.75 × 0.10)
          = 0.28 + 0.15 + 0.075 + 0.075 + 0.075
          = 0.655
          = 66/100
```

**Interpretation**: Good match with room for improvement. Apply top suggestions to reach 75-80.

---

## 🔬 Technical Details

### **Semantic Similarity (for Coverage)**

Uses **BGE-large-en-v1.5** embeddings:
- State-of-the-art sentence transformer
- 1024-dimensional vectors
- Cosine similarity for matching
- FAISS for fast retrieval

**Thresholds** (configurable in `config.yaml`):
- `tau_high = 0.75`: Present threshold
- `tau_low = 0.50`: Weak threshold

### **Skills Taxonomy**

150+ canonical skills across 11 categories:
- Programming languages
- ML frameworks
- Data tools
- Cloud platforms
- Databases
- MLOps
- LLM tools
- NLP/CV
- Visualization
- Statistics
- Soft skills

Located in: `data/skills_taxonomy.json`

### **Action Verbs Library**

Categorized by type:
- Leadership: Led, Directed, Managed
- Creation: Built, Developed, Designed
- Improvement: Optimized, Enhanced, Streamlined
- Analysis: Analyzed, Evaluated, Investigated
- Automation: Automated, Scripted, Orchestrated
- Data Science: Modeled, Predicted, Trained

Located in: `data/action_verbs.json`

---

## ⚙️ Customization

### **Adjust Weights** (in `config.yaml`):

```yaml
scoring:
  coverage_weight: 0.35      # Increase if skills are most important
  explicitness_weight: 0.25  # Increase for keyword-heavy ATS
  role_alignment_weight: 0.15
  keywords_weight: 0.15
  writing_quality_weight: 0.10
```

**Note**: Weights must sum to 1.0

### **Adjust Thresholds** (in `config.yaml`):

```yaml
matching:
  tau_high: 0.75  # Higher = stricter "present" status
  tau_low: 0.50   # Higher = stricter "weak" status
```

**Effect**:
- Higher thresholds = fewer false positives, more conservative
- Lower thresholds = more lenient, may catch more skills

---

## ❓ FAQ

**Q: Is the score guaranteed to match real ATS systems?**
A: No. Each ATS (Workday, Greenhouse, Lever) has different algorithms. Our score is an estimate based on common factors.

**Q: Why is my score low even though I have the skills?**
A: You may not be using explicit keywords. Say "Python" instead of "programming languages", "A/B testing" instead of "experimentation".

**Q: Can I change the weights?**
A: Yes! Edit `config.yaml` to prioritize different components. For example, if applying to keyword-heavy ATS, increase `explicitness_weight`.

**Q: What's a good score?**
A: 70+ is good, 80+ is excellent. Below 60 means significant gaps.

**Q: Does the score predict interview success?**
A: No. It only predicts ATS screening success. Interview success depends on many other factors.

---

## 🎯 Summary

**The ATS score is a weighted combination of**:
1. **Coverage (35%)** - Do you have the required skills?
2. **Explicitness (25%)** - Are skills explicitly named?
3. **Role Alignment (15%)** - Does your title match?
4. **Keywords (15%)** - Are technical terms present?
5. **Writing Quality (10%)** - Are bullets well-written?

**Use the score as a guide**, not absolute truth. Always review suggestions and apply what makes sense for your actual experience.

**Goal**: Get your score to 75-85 for best results. Above 85 may be over-optimized.
