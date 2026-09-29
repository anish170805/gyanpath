# Master Instructions: Project Report Format

## Source basis
These instructions are extracted from the uploaded vocational training project report and preserve its **overall organization, numbering pattern, section order, table conventions, figure conventions, and writing structure**.

## Project-folder rule
Create and maintain the report work inside one dedicated project folder:

```text
<PROJECT_ROOT>/
├── report/
│   ├── 00_MASTER_REPORT_RULES.md
│   ├── 01_COVER_PAGE.md
│   ├── 02_DECLARATION.md
│   ├── 03_ACKNOWLEDGEMENT.md
│   ├── 04_ABSTRACT.md
│   ├── 05_INDEX.md
│   ├── 06_TABLE_OF_CONTENTS.md
│   ├── 07_LIST_OF_FIGURES.md
│   ├── 08_LIST_OF_TABLES.md
│   ├── 09_CHAPTER_1_INTRODUCTION.md
│   ├── 10_CHAPTER_2_LITERATURE_REVIEW.md
│   ├── 11_CHAPTER_3_PROBLEM_STATEMENT.md
│   ├── 12_CHAPTER_4_METHODOLOGY.md
│   ├── 13_CHAPTER_5_RESULTS_AND_DISCUSSION.md
│   ├── 14_CHAPTER_6_FUTURE_SCOPE.md
│   ├── 15_CHAPTER_7_CONCLUSION.md
│   ├── 16_REFERENCES.md
│   └── 17_BIBLIOGRAPHY.md
├── assets/
│   ├── figures/
│   ├── screenshots/
│   ├── diagrams/
│   └── tables/
└── project-source/
```

**Instruction for every section:** inspect and use `<PROJECT_ROOT>/project-source/` as the source of truth for actual project facts. Do not invent features, modules, technologies, metrics, screenshots, results, or architecture. If information is missing, leave a clearly marked placeholder rather than fabricating it.

## Exact structural pattern
1. Cover Page
2. Declaration
3. Acknowledgement
4. Abstract
5. Index
6. Table of Contents
7. List of Figures
8. List of Tables
9. Chapter 1: Introduction
10. Chapter 2: Literature Review
11. Chapter 3: Problem Statement
12. Chapter 4: Methodology
13. Chapter 5: Results and Discussion
14. Chapter 6: Future Scope
15. Chapter 7: Conclusion
16. References
17. Bibliography

## Numbering rules
- Chapter title: `CHAPTER N` on one line, chapter name on the next line.
- Main chapter sections: `N.1`, `N.2`, `N.3`, ...
- Nested sections: `N.1.1`, `N.1.2`, ...
- Figures: `Figure 4.1`, `Figure 4.2`, `Figure 5.1`, etc.
- Tables: `Table 2.1`, `Table 4.1`, `Table 5.1`, etc.
- Restart figure/table numbering by chapter.

## Page-number rules
- Front matter uses roman numerals in the sample structure.
- Main chapters use Arabic page numbers.
- Page numbers must be updated only after the final document is assembled.
- In draft Markdown, use `{PAGE_NO}` or leave the page-number field as `TBD`.

## Figure and image rule
Whenever a section needs a diagram, screenshot, chart, graph, UI image, ER diagram, DFD, architecture diagram, or deployment diagram, **reserve space instead of writing fake image descriptions as if an image already exists**.

Use this exact placeholder pattern:

```md
<!-- IMAGE SPACE START -->
[INSERT IMAGE HERE]
Asset path: `assets/<category>/<filename>`
Suggested caption: `Figure N.M: <Exact Title>`
<!-- IMAGE SPACE END -->
```

Place the caption immediately below the image in the final report.

## Table rule
Use tables only where the report format calls for structured comparison, schema, requirements, test cases, or measured results.

For every table:
1. Assign a chapter-based table number.
2. Give a concise title.
3. Keep column names factual and consistent.
4. Use actual project data from `<PROJECT_ROOT>/project-source/`.
5. Do not fill rows with invented values.
6. Update the List of Tables after finalizing.

Generic format:

| Column 1 | Column 2 | Column 3 |
|---|---|---|
| Actual value | Actual value | Actual value |

## Writing rule
Follow the source report's style:
- Start major sections with a short contextual explanation.
- Follow with subheadings.
- Use paragraphs for explanation.
- Use bullets for features, responsibilities, advantages, limitations, requirements, and lists.
- Use numbered steps for workflows, phases, and processes.
- End major chapters with a `Summary` section where the sample report does so.
- Keep the writing project-specific.

## Word-processing note
The uploaded report does not expose one perfectly reliable global Word style specification through all paragraphs. Preserve the **structural format exactly** and use the institution's required font/margins if separately provided. If no separate formatting guideline exists, keep the final DOCX visually consistent throughout rather than pretending the sample establishes a single exact font/spacing rule.

## Extracted document style metadata
{
  "Normal": {
    "font": null,
    "size_pt": null,
    "bold": null,
    "italic": null,
    "alignment": "None",
    "space_before_pt": null,
    "space_after_pt": null,
    "line_spacing": null
  },
  "Heading 1": {
    "font": null,
    "size_pt": 20.0,
    "bold": null,
    "italic": null,
    "alignment": "None",
    "space_before_pt": 18.0,
    "space_after_pt": 4.0,
    "line_spacing": null
  },
  "Heading 2": {
    "font": null,
    "size_pt": 16.0,
    "bold": null,
    "italic": null,
    "alignment": "None",
    "space_before_pt": 8.0,
    "space_after_pt": 4.0,
    "line_spacing": null
  },
  "Heading 3": {
    "font": null,
    "size_pt": 14.0,
    "bold": null,
    "italic": null,
    "alignment": "None",
    "space_before_pt": 8.0,
    "space_after_pt": 4.0,
    "line_spacing": null
  },
  "Title": {
    "font": null,
    "size_pt": 28.0,
    "bold": null,
    "italic": null,
    "alignment": "None",
    "space_before_pt": null,
    "space_after_pt": 4.0,
    "line_spacing": 1.0
  }
}
