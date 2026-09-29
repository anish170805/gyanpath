# CHAPTER 4 — METHODOLOGY

## Heading format

```text
CHAPTER 4
METHODOLOGY
```

## Required section sequence from the source format
1. `4.1 Introduction`
2. `4.2 Development Methodology`
   - `4.2.1 Reasons for Selecting <Methodology>`
   - `4.2.2 <Methodology> Development Phases`
3. `4.3 System Architecture`
   - `4.3.1 High-Level Architecture`
   - layer/component subsections as needed
4. `4.4 System Modules`
5. `4.5 Database Design`
6. `4.6 Entity Relationship Diagram (ER Diagram)`
7. `4.7 Data Flow Diagram (DFD)`
8. `4.8 System Workflow`
9. `4.9 Algorithms`
10. `4.10 Implementation Details`
11. `4.11 Testing Methodology`
12. `4.12 Test Cases`
13. `4.13 Deployment Methodology`
14. `4.14 Performance Considerations`
15. `4.15 Hardware and Software Requirements`
16. `4.16 Advantages of Proposed Methodology`
17. `4.17 Summary`

## 4.2 Development Methodology
State the actual methodology used. Explain:
- what the methodology is,
- why it was selected,
- phases followed,
- project-specific activities in each phase.

Use numbered phases:

```text
Phase 1: Requirement Analysis
Phase 2: System Design
Phase 3: Implementation
Phase 4: Testing
Phase 5: Deployment
```

Adapt only if the actual project followed a different process.

## 4.3 System Architecture
Explain architecture in text first, then reserve image space.

<!-- IMAGE SPACE START -->
[INSERT HIGH-LEVEL SYSTEM ARCHITECTURE HERE]
Asset path: `assets/diagrams/figure_4_1_system_architecture.png`
Suggested caption: `Figure 4.1: High-Level System Architecture`
<!-- IMAGE SPACE END -->

For each major layer/component, create a subsection explaining:
- responsibility,
- inputs,
- outputs,
- technologies used,
- interactions with other components.

## 4.4 System Modules
Create one subsection per actual module.

For every module include:
- purpose,
- major functions,
- input/output or workflow,
- dependencies,
- project-specific logic.

Use numbered workflows where appropriate.

## 4.5 Database Design
Explain the selected database and why it fits the project.

For every major table/collection/schema, use this format:

**<Entity/Collection Name> Schema**

| Field | Data Type | Description |
|---|---|---|
| `<field>` | `<type>` | `<actual meaning>` |

Use one table per important entity/collection. Number them sequentially, e.g. `Table 4.1`, `Table 4.2`.

## 4.6 ER Diagram
Briefly explain the main entities and relationships, then reserve space:

<!-- IMAGE SPACE START -->
[INSERT ER DIAGRAM HERE]
Asset path: `assets/diagrams/figure_4_2_er_diagram.png`
Suggested caption: `Figure 4.2: Entity Relationship Diagram (ER Diagram)`
<!-- IMAGE SPACE END -->

## 4.7 Data Flow Diagram
Include Level 0 and Level 1 only if they accurately represent the project.

<!-- IMAGE SPACE START -->
[INSERT DFD LEVEL 0 HERE]
Asset path: `assets/diagrams/figure_4_3_dfd_level_0.png`
Suggested caption: `Figure 4.3: Data Flow Diagram (Level 0)`
<!-- IMAGE SPACE END -->

<!-- IMAGE SPACE START -->
[INSERT DFD LEVEL 1 HERE]
Asset path: `assets/diagrams/figure_4_4_dfd_level_1.png`
Suggested caption: `Figure 4.4: Data Flow Diagram (Level 1)`
<!-- IMAGE SPACE END -->

## 4.8 System Workflow
Explain the end-to-end workflow in numbered steps. Add a workflow diagram only if useful.

## 4.9 Algorithms
For each major algorithm/process:
- name the algorithm,
- explain purpose,
- list step-by-step logic or pseudocode,
- avoid fake mathematical algorithms if the project uses standard application logic.

## 4.10 Implementation Details
Describe actual implementation by major subsystem. Include API architecture or other architecture only when present.

<!-- IMAGE SPACE START -->
[INSERT API / INTERNAL ARCHITECTURE HERE IF APPLICABLE]
Asset path: `assets/diagrams/figure_4_5_api_architecture.png`
Suggested caption: `Figure 4.5: <Actual Architecture Title>`
<!-- IMAGE SPACE END -->

## 4.11 Testing Methodology
Explain the testing approach and categories actually performed.

## 4.12 Test Cases
Use separate tables by major module when useful.

Required table pattern:

| Test Case ID | Test Description | Input / Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| TC-01 | ... | ... | ... | ... | Pass/Fail |

Do not claim `Pass` without actual evidence.

## 4.13 Deployment Methodology
Explain frontend, backend, database, environment configuration, and deployment flow according to the actual project.

Reserve deployment architecture image space when relevant:

<!-- IMAGE SPACE START -->
[INSERT DEPLOYMENT ARCHITECTURE HERE]
Asset path: `assets/diagrams/figure_4_6_deployment_architecture.png`
Suggested caption: `Figure 4.6: Deployment Architecture`
<!-- IMAGE SPACE END -->

## 4.14 Performance Considerations
Discuss actual performance techniques:
- database optimization,
- API optimization,
- frontend optimization,
- caching/queues/concurrency only if actually used.

## 4.15 Hardware and Software Requirements
Use two structured tables.

**Hardware Requirements**

| Component | Requirement |
|---|---|
| Processor | ... |
| RAM | ... |
| Storage | ... |
| Internet | ... |

**Software Requirements**

| Software / Area | Technology |
|---|---|
| Frontend | ... |
| Backend | ... |
| Database | ... |
| Authentication | ... |
| Development Environment | ... |
| Browser / Runtime | ... |

## 4.16 Advantages of Proposed Methodology
Use numbered advantages, each with a short explanation.

## 4.17 Summary
Summarize methodology, architecture, modules, implementation, testing, deployment, and key benefits.

## Project-folder instruction
Everything in this chapter must be derived from the actual implementation and source files under `<PROJECT_ROOT>/project-source/`. This is the chapter where fabricated architecture is most damaging.
