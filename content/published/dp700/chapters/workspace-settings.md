# Configure Microsoft Fabric workspace settings

<!-- block-id: orientation -->
Workspace settings are control points. They shape how a team uses compute, organizes ownership, reaches shared data, and schedules orchestration. For the exam, focus on **who controls a setting, what scope it affects, and what operational consequence follows**.

## Start with the boundary

<!-- block-id: boundary-model -->
A workspace is a collaboration and security boundary, but not every behavior is controlled at workspace scope. Some defaults inherit from capacity or tenant administration. Before changing a setting, identify the governing scope and whether the workspace administrator can override it.

| Setting family | Primary concern | Exam question to ask |
| --- | --- | --- |
| Spark | Compute defaults and runtime behavior | Does this change the workspace default or only one session? |
| Domain | Business ownership and discovery | Is the workspace assigned to the correct data domain? |
| OneLake | How data is exposed and accessed | Does the change affect access, discoverability, or data movement? |
| Apache Airflow | Managed orchestration configuration | Who owns connections, schedules, and operational monitoring? |

## A practical decision sequence

<!-- block-id: decision-sequence -->
1. Identify the required outcome: performance, governance, access, or orchestration.
2. Locate the narrowest administrative scope that owns the behavior.
3. Check inheritance and override rules before changing a default.
4. Validate the effect with a representative workload rather than assuming the setting is isolated.
5. Record the operational owner and a rollback path.

## Exam distinction

<!-- block-id: exam-distinction -->
Do not treat all workspace settings as interchangeable toggles. Spark settings primarily influence compute behavior; domain assignment communicates business organization; OneLake settings influence the shared data plane; and Apache Airflow settings support managed workflow orchestration. A scenario usually gives clues about **scope**, **owner**, and **effect**.

## Active recall

<!-- block-id: active-recall -->
- Which settings would you examine first when every notebook in a workspace starts with an unsuitable Spark default?
- Why is assigning a workspace to a domain different from granting access to the workspace?
- What evidence would you collect before changing a setting that may affect multiple workloads?

## Source

<!-- block-id: official-source -->
Use the [official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700) as the authoritative skills outline. This chapter is original study-oriented writing and will be expanded with setting-specific Microsoft Learn sources in the content-authoring milestone.
