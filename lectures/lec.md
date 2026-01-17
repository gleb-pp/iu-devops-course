You are a senior DevOps educator and technical content designer.

Your task is to generate **lecture slides in Markdown** for an online lecture.

## Lecture Title
**DevOps Introduction: From Chaos to Flow**

## Audience
- ~150 online students
- Beginner to early-intermediate level
- Technical background, minimal DevOps knowledge

## Output Format (STRICT)

- Use **Markdown**
- Each slide MUST start with:

```markdown
---
slide_id: DEVOPS_L1_SXX
title: "Slide Title"
---
```

Where `SXX` is a zero-padded slide number (S01, S02, ...).

* Content must be concise (slide-ready, not speaker notes)
* Use bullet points
* Use diagrams where appropriate

---

## Diagram Rules

* Use **Mermaid diagrams** wherever a process, flow, or system is described
* Mermaid diagrams MUST be valid
* Prefer:

  * flowchart
  * sequenceDiagram
  * graph LR
* Every major section should include at least one diagram

---

## Quiz Placeholder Slides (VERY IMPORTANT)

You must include **BLANK QUIZ SLIDES** with NO content except a title.

Use EXACT slide titles below so they match the quiz app:

* `QUIZ — DEVOPS_L1_PRE`
* `QUIZ — DEVOPS_L1_MID`
* `QUIZ — DEVOPS_L1_POST`

Example quiz slide:

```markdown
---
slide_id: DEVOPS_L1_S05
title: "QUIZ — DEVOPS_L1_PRE"
---
```

No bullets. No text. No diagrams.

---

## Lecture Structure

### Section 0 — Introduction & Warm-up

* Why this course exists
* What DevOps helps solve
* Learning outcomes

➡ Insert PRE quiz slide after this section

---

### Section 1 — The Problem Before DevOps

* Dev vs Ops silos
* Manual releases
* Fear and blame
* "Works on my machine"

Include:

* Before/After diagram
* Failure flow

---

### Section 2 — What DevOps Really Is

* One clear definition
* What DevOps is NOT
* Three Ways of DevOps

Include:

* Principles diagram

---

### Section 3 — DevOps as a Game (Simulation)

* Startup scenario
* Release failure
* Infra drift
* Secret leak
* No observability

Each problem → DevOps solution

Include:

* Flow or decision diagrams

➡ Insert MID quiz slide after this section

---

### Section 4 — DevOps Lifecycle & Course Map

* DevOps infinity loop
* Mapping course modules to lifecycle

Include:

* Lifecycle diagram
* Table slide

---

### Section 5 — DevOps in Real Life

* Day-to-day work
* Roles
* Collaboration
* Career trajectory

---

### Section 6 — Reflection & Impact

* Key takeaways
* Mindset shift
* Learning progress

➡ Insert POST quiz slide before the final slide

---

### Final Slide — What Comes Next

* Next lecture teaser
* Motivation
* Confidence boost

---

## Style Rules

* Use emojis sparingly for structure (🎯 🧩 🔁)
* No long paragraphs
* No speaker notes
* Slide count target: **35–45**
* Keep content vendor-neutral

Generate the full slide deck now.
