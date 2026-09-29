# CHAPTER 5 — RESULTS AND DISCUSSION

## Heading format

```text
CHAPTER 5
RESULTS AND DISCUSSION
```

## Required section sequence
1. `5.1 Introduction`
2. `5.2 System Output`
   - Add subsections for actual screens/features.
3. `5.3 Testing Results Analysis`
4. `5.4 Performance Analysis`
5. `5.5 User Activity Analysis`
6. `5.6 Graphical Representation`
7. `5.7 <Distribution / Specific Result Analysis>`
8. `5.8 Discussion`
9. `5.9 Comparison with Existing Systems`
10. `5.10 Summary`

## 5.1 Introduction
Explain what was implemented and what dimensions are being evaluated:
- functionality,
- correctness,
- performance,
- usability,
- effectiveness,
only where actual evidence exists.

## 5.2 System Output
Create one subsection per important actual output/interface.

For each subsection:
1. Explain what the screen/output does.
2. State what input/action leads to it.
3. Reserve screenshot space.
4. State the observed result.

Use:

<!-- IMAGE SPACE START -->
[INSERT SCREENSHOT HERE]
Asset path: `assets/screenshots/<filename>.png`
Suggested caption: `Figure 5.N: <Screen / Output Title>`
<!-- IMAGE SPACE END -->

Do not write a fake screenshot description as evidence.

## 5.3 Testing Results Analysis
Use a table based on real tests:

| Feature / Module | Test Objective | Expected Result | Actual Result | Status |
|---|---|---|---|---|

## 5.4 Performance Analysis
Only include real measurements or defensible observations. Use tables when measured data exists:

| Metric | Scenario | Result | Interpretation |
|---|---|---|---|

## 5.5 User Activity Analysis
Include only if the project has actual activity/usage data. If no real data exists, explicitly omit or mark the section as not evaluated rather than inventing analytics.

## 5.6 Graphical Representation
Reserve space for graphs based on real data.

<!-- IMAGE SPACE START -->
[INSERT GRAPH HERE]
Asset path: `assets/figures/figure_5_1_<name>.png`
Suggested caption: `Figure 5.1: <Graph Title>`
<!-- IMAGE SPACE END -->

## 5.7 Distribution / Specific Result Analysis
Use a chart or distribution only when actual project data exists.

<!-- IMAGE SPACE START -->
[INSERT CHART HERE]
Asset path: `assets/figures/figure_5_2_<name>.png`
Suggested caption: `Figure 5.2: <Chart Title>`
<!-- IMAGE SPACE END -->

## 5.8 Discussion
Interpret results:
- what worked,
- what did not,
- trade-offs,
- limitations,
- relation to objectives.

## 5.9 Comparison with Existing Systems
Use a factual comparison table:

| Feature | Existing System / Approach | Proposed System |
|---|---|---|

Do not exaggerate superiority.

## 5.10 Summary
Summarize outputs, testing, performance, discussion, and comparison.

## Project-folder instruction
Use screenshots from `<PROJECT_ROOT>/assets/screenshots/`, graphs from `<PROJECT_ROOT>/assets/figures/`, and measured results from `<PROJECT_ROOT>/project-source/`.
