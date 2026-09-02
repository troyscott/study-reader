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

## Version control field guide

<!-- block-id: version-control-model -->
Think of Git integration as a **two-sided synchronization contract**. One side is
the item definition stored in a particular workspace; the other is a folder in
a particular repository branch. Fabric calculates a status for supported items
by comparing those sides. `Commit to Git` writes workspace definitions to the
connected branch. `Update from Git` reads branch definitions into the
workspace. A branch change made through a pull request does not alter a
workspace until an update occurs, and a portal edit is not durable source
history until it is committed.

<!-- block-id: version-control-operations -->
Before connecting, confirm that the tenant and workspace allow Git integration,
the user has the required workspace and repository permissions, the provider is
supported, and the target branch and directory are intentional. Connect a
development workspace—not production—to the chosen branch and folder. After
connection, inspect the source-control status, commit only the intended items,
and use a pull request to validate and review the resulting definitions. After
merge, update the integration workspace from the shared branch and run item
smoke tests. Secrets, credentials, data, and every runtime setting are not
automatically captured just because an item definition is versioned.

<!-- block-id: version-control-decisions -->
Use one workspace per developer or feature when simultaneous portal authoring
would otherwise collide. A shared development workspace is cheaper and simpler,
but it increases coordination and makes unrelated changes appear in the same
sync operation. Prefer trunk-based development when small changes can merge
frequently; use longer-lived stage branches only when the release mechanism
truly depends on them. In either model, protect the integration branch and keep
the branch-to-workspace mapping explicit. A workspace is a deployment target,
not a substitute for a branch.

<!-- block-id: version-control-example -->
**Worked scenario.** Maya changes a notebook in a feature workspace connected
to `feature/customer-quality`. The source-control pane also shows an unrelated
pipeline edit made by another user. Maya commits only the notebook, opens a pull
request, and CI validates the definition. After approval and merge into `main`,
the team updates the development workspace from `main`. They then run the
notebook against test data. The correct evidence chain is workspace change →
feature commit → pull request and CI → merge → workspace update → runtime test.
The successful merge alone does not prove the notebook runs in Fabric.

<!-- block-id: version-control-diagnostics -->
When synchronization fails, first classify the state: workspace-only change,
Git-only change, conflict, unsupported item, missing dependency, or permission
failure. Preserve both versions before resolving a conflict. Check the connected
branch and folder, repository authorization, workspace role, item support, and
whether another operation is still running. After an update, diagnose a broken
item as a runtime or dependency problem rather than repeatedly syncing it. A
useful mini-lab is to change a harmless notebook comment in a feature branch,
observe each status transition, resolve a deliberately created conflict, and
record which actions affected Git versus the workspace.

## Database projects field guide

<!-- block-id: database-projects-model -->
A database project is a **declarative model of desired schema state**. Source
files describe objects and their relationships; a build resolves references and
packages the model; publish compares that model with a target and produces a
deployment plan. This differs from a migration sequence that says “run step 17
after step 16.” The project says what the database should look like, while the
deployment engine infers how to reach that state.

<!-- block-id: database-projects-operations -->
Start by importing or authoring supported tables, views, procedures, functions,
and security objects as individual SQL files. Add project references where one
model depends on another. Build on every pull request, treat unresolved object
references and incompatible syntax as failures, and retain the build artifact.
Before publish, generate and review the deployment script or report against the
actual target. Deploy first to a disposable or test database, execute schema and
data-preservation checks, and require approval for production. The deployment
identity needs only the target permissions required by the planned changes.

<!-- block-id: database-projects-decisions -->
Choose a database project when the desired schema can be represented
declaratively and drift detection matters. Choose explicit migrations when the
order of data movement is itself the essential design—for example, populating a
replacement column before making it non-null. Many mature releases combine
them: the project owns ordinary schema state and reviewed pre/post-deployment
scripts handle exceptional transitions. Do not hide destructive changes in an
automatic publish profile. Renames, narrowing data types, changing distribution
choices, and dropping objects require deliberate review and often a backup or
copy strategy.

<!-- block-id: database-projects-example -->
**Worked scenario.** A new `RegionCode` column must become required. Publishing
`char(2) NOT NULL` directly fails because old rows contain no value. The safe
release adds the nullable column, backfills and validates every row, then makes
the column non-null in a later reviewed change. In a practice database, build a
project with a view that references a misspelled column and confirm the build
catches it; then compare the generated plan before and after renaming a table.
The lesson is that build validation proves model consistency, not safe data
transition semantics.

<!-- block-id: database-projects-diagnostics -->
For build errors, inspect the first unresolved reference, target platform, SQL
syntax, and project dependencies. For publish errors, separate authentication
and authorization from model incompatibility, target drift, locks, or data that
violates a new constraint. Never retry a partially applied destructive plan
blindly. Capture the generated script, target schema version, error, and objects
already changed; decide whether to roll forward or restore. A DACPAC contains a
schema model, not a copy of production data and not a complete Fabric workspace.

## Deployment pipeline field guide

<!-- block-id: deployment-pipelines-model -->
A Fabric deployment pipeline is an **environment-promotion mechanism**. Stages
represent lifecycle environments; assigned workspaces hold the live items;
pairing relates corresponding items; comparison shows differences; deployment
moves supported definitions forward. Deployment rules and variable values can
change supported configuration by stage. None of these constructs is a general
secret manager, test runner, or source-control review system.

<!-- block-id: deployment-pipelines-operations -->
Create the pipeline, define and order its stages, and assign the correct
workspace to each stage. Confirm item support and pairing before the first
promotion. Configure stage-specific supported rules or variables, then deploy a
small coherent set from development to test. Inspect the comparison, run data,
permission, refresh, and dependency checks in test, and obtain release approval.
Promote the same reviewed definitions to production, complete any documented
post-deployment bindings, and run smoke tests under representative identities.
Record the source revision, deployment operation, approver, and verification
result.

<!-- block-id: deployment-pipelines-decisions -->
Deploy a dependency set together when a consumer cannot operate safely without
its producer; deploy independently when the contract is backward compatible.
Use deployment rules for supported environment differences such as connection
or parameter values, and a governed secret store or connection mechanism for
credentials. Selective deployment reduces blast radius but can produce an
inconsistent dependency graph. Full-stage deployment improves consistency but
can promote unrelated work. The correct choice follows tested dependency and
release boundaries, not convenience.

<!-- block-id: deployment-pipelines-example -->
**Worked scenario.** A pipeline invokes a notebook that writes to a lakehouse.
All three exist in development, but only the pipeline is selected for test. The
deployment succeeds and the first run fails because the paired notebook or
lakehouse binding is absent. The repair is to compare the dependency set,
promote the compatible items, apply the test connection configuration, and
rerun. As a mini-lab, document a Dev/Test/Prod matrix containing workspace,
capacity, connection, schedule, and owner; promote a harmless parameter change
and verify the resolved value at each stage.

<!-- block-id: deployment-pipelines-diagnostics -->
If an item is missing from comparison, verify support, workspace assignment,
pairing, and whether it resides in the expected stage. If deployment fails,
check permissions, capacity state, item dependencies, and concurrent
operations. If deployment succeeds but execution fails, move to runtime checks:
credentials, gateways, item IDs, shortcut targets, schedules, and data-plane
permissions. Rollback might mean redeploying the previous known-good definition
or restoring external state; a pipeline has no universal undo for data mutated
by a job.

<!-- block-id: lifecycle-exam-distinctions -->
The exam often describes all three lifecycle mechanisms in one scenario. Name
the boundary before choosing: review and history point to Git; declarative SQL
schema points to a database project; staged Fabric promotion points to a
deployment pipeline. “Deployment succeeded” is control-plane evidence only.
The strongest answer also verifies dependencies, configuration, permissions,
and behavior in the target environment.

<!-- block-id: lifecycle-recall-lab -->
**Recall and mini-lab.** Explain why `Update from Git` can change a workspace
without creating a new Git commit. Describe one schema change a build can
validate but cannot prove safe for existing data. List three post-deployment
checks for a notebook-to-lakehouse pipeline. Then sketch a release with one
feature branch, one pull request, one test promotion, and one intentional
failure; label the evidence produced at each gate.

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
