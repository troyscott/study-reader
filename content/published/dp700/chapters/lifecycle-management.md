# Implement lifecycle management in Fabric

<!-- block-id: orientation -->
Lifecycle management answers three different questions: **How do we review changes? How do we represent database code? How do we promote tested content?** Git integration, database projects, and deployment pipelines cooperate, but none replaces the others.

## Objective coverage

| Measured objective | What to master |
| --- | --- |
| Configure version control | Workspace-to-branch connection, sync direction, branches, commits, conflicts, and supported items |
| Implement database projects | Declarative schema, build validation, publish artifacts, and state-based deployment |
| Create and configure deployment pipelines | Dev/test/prod stages, workspace assignment, comparison, deployment rules, and promotion |

## Configure version control

Fabric Git integration connects a workspace to a branch and folder in Azure DevOps or GitHub. The workspace is a live collaboration surface; the repository is the durable, reviewable representation. A **commit to Git** exports supported workspace changes to the branch. An **update from Git** applies branch changes to the workspace. Neither direction is automatic simply because the connection exists.

Use a development workspace for authoring. Protect the integration branch with pull requests and automated validation. Before syncing, inspect the change list: an update can change or delete live workspace items, while a commit can record unintended portal edits.

| Situation | Best action |
| --- | --- |
| Developer needs isolation | Work on a feature branch and, where supported, a dedicated workspace |
| Workspace and branch both changed | Compare, resolve the conflict deliberately, then synchronize |
| Secret or environment-specific value | Keep it out of source; use supported parameters, rules, or variable libraries |
| Item is not supported by Git integration | Use an API or deployment tool and document that separate release path |

Git records definitions, not all external dependencies or data. Connections, credentials, gateway bindings, permissions, and some item properties can require post-deployment configuration. A successful Git sync therefore proves definition synchronization—not production readiness.

## Implement database projects

A SQL database project stores the intended database schema as code: tables, views, procedures, functions, roles, and other supported objects. Its build checks whether those declarations form a coherent model and produces a deployable artifact such as a DACPAC. Publishing compares the model with a target database and generates a change plan.

```sql
CREATE TABLE dbo.Customer (
    CustomerKey bigint NOT NULL,
    CustomerName varchar(200) NOT NULL,
    RegionCode char(2) NULL,
    CONSTRAINT PK_Customer PRIMARY KEY (CustomerKey)
);
```

The important distinction is **state based versus migration based**. A database project declares the desired end state; the deployment engine calculates changes. A migration script declares ordered steps. Review generated plans carefully, especially when a rename could be interpreted as drop-and-create or when a type change could lose data.

A robust flow builds the project in CI, checks naming and static-analysis rules, creates the deployment artifact, tests it against a disposable database, and requires human approval before production. Database projects cover database objects; they do not version Fabric workspaces or orchestrate the release of every Fabric item.

## Create and configure deployment pipelines

Fabric deployment pipelines promote supported items through ordered stages commonly named Development, Test, and Production. Assign a workspace to each stage, compare adjacent stages, select content, configure supported deployment rules, and deploy forward. Pairing recognizes corresponding items across stages; it does not mean every dependency is automatically rebound.

| Stage | Purpose | Evidence before promotion |
| --- | --- | --- |
| Development | Integrate approved source changes | Build and content validation pass |
| Test | Exercise realistic configuration and data cases | Functional, permission, refresh, and performance checks pass |
| Production | Serve governed consumers | Approval, rollback plan, and post-deployment checks exist |

Deployment rules can vary supported data-source or parameter values by stage. They are not a secret store and do not grant target permissions. After deployment, verify connections, credentials, schedules, gateway mappings, item bindings, and access separately.

### Put the three mechanisms together

1. Author in a development workspace connected to a feature branch.
2. Commit definitions, open a pull request, and run validation.
3. Merge to the integration branch and update the development workspace.
4. Promote approved items through test and production deployment stages.
5. Run post-deployment configuration and smoke tests, then retain the evidence.

This separation creates traceability: Git answers *what changed and who reviewed it*; a database project validates a SQL schema model; a deployment pipeline answers *what was promoted between Fabric environments*.

## Exam distinctions

- Git integration synchronizes a workspace and branch; it is not a Dev/Test/Prod promotion engine.
- Deployment pipelines promote supported Fabric items; they are not general-purpose Git repositories.
- Database projects model database schema; they do not capture data or every server-level setting.
- A deployment that reports success can still have broken credentials, bindings, permissions, or schedules.
- Never assume all Fabric item types support identical Git and deployment behavior; check the current supported-item matrix.

## Active recall

1. Which direction does **Update from Git** move definitions?
2. Why should a generated database deployment plan be reviewed before publishing?
3. What is the difference between a deployment rule and a secret store?
4. A production item deploys but cannot reach its source. Which lifecycle boundary was missed?
5. When would you choose an isolated feature branch and workspace?

## Authoritative sources

- [Introduction to CI/CD in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/cicd/cicd-overview)
- [CI/CD workflow options in Fabric](https://learn.microsoft.com/en-us/fabric/cicd/manage-deployment)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
