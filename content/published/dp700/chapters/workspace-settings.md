# Configure Microsoft Fabric workspace settings

<!-- block-id: orientation -->
The exam objective groups Spark, domain, OneLake, and Apache Airflow settings under one heading. This chapter covers all four. The reliable way to reason through them is to identify the administrative scope, the workload or data affected, and the operational consequence before selecting an option.

## Objective coverage

<!-- block-id: objective-coverage -->
| Measured objective | Coverage in this chapter |
| --- | --- |
| Configure Spark workspace settings | Workspace defaults, environment overrides, runtimes, pools, and compute sizing |
| Configure domain workspace settings | Domain assignment, roles, discovery, delegated governance, and default domains |
| Configure OneLake workspace settings | Diagnostics, immutability, default storage tier, and lifecycle policies |
| Configure Apache Airflow workspace settings | Default runtime, starter and custom pools, sizing, autoscaling, and operating constraints |

## Orient yourself: OneLake, workspace, item

<!-- block-id: scope-model -->
[OneLake](https://learn.microsoft.com/en-us/fabric/onelake/onelake-overview) is the single organizational data lake supplied with a Fabric tenant. Workspaces divide that lake into independently administered project or domain containers. A OneLake workspace setting therefore controls storage or diagnostics behavior for that workspace; it does not create another OneLake.

Keep three scopes separate:

| Scope | Typical owner | Examples |
| --- | --- | --- |
| Tenant | Fabric administrator | Whether a capability is allowed or delegated across the organization |
| Workspace | Workspace administrator | OneLake diagnostics, default storage tier, and lifecycle policy |
| Item or data | Item owner or appropriately privileged user | Lakehouse permissions and OneLake security roles |

Changing a workspace setting is not the same as granting access to data. Workspace roles and OneLake security roles belong to the security model; storage-tier and diagnostic settings govern how workspace data is retained, observed, or billed.

## Configure Spark workspace settings

<!-- block-id: spark-settings -->
Fabric supplies managed Spark compute for Data Engineering and Data Science. At workspace scope, the administrator establishes the default compute behavior and decides whether individual environment items may override it. That governance switch is the first exam distinction:

| Workspace choice | Result |
| --- | --- |
| Item-level customization disabled | Environment compute controls are unavailable; Spark jobs use the workspace default pool |
| Item-level customization enabled | Members and contributors can select session-level compute settings inside an environment |

In the portal, the path is **Workspace settings > Data Engineering/Science > Spark settings**. The workspace administrator can select or create a pool and control whether item-level customization is allowed. An environment can then define a runtime, pool, driver sizing, and executor sizing when the workspace policy permits it.

### Separate the Spark configuration layers

<!-- block-id: spark-layers -->
| Layer | Examples | When it applies |
| --- | --- | --- |
| Workspace default | Default pool and permission to customize item compute | Baseline for Spark jobs in the workspace |
| Environment item | Runtime, pool, driver cores/memory, executor cores/memory | Reusable configuration for attached notebooks and Spark job definitions |
| Spark application | Properties set through `spark.conf.set` | Application behavior inside a Spark session, not the environment's compute allocation |

An environment change is not active merely because it was edited. Runtime and library changes must be saved and published. Publishing can fail when the selected runtime is incompatible with configured libraries or compute settings.

### Choose a Spark pool and size compute

<!-- block-id: spark-decisions -->
- Use the workspace default when workloads have similar requirements and centralized consistency matters most.
- Allow environment overrides when distinct workloads need different runtimes or driver/executor resources.
- Choose a starter pool when fast startup and managed defaults fit the workload.
- Choose an approved custom pool when node family, node size, autoscale, or dynamic allocation requirements justify dedicated configuration.
- Size the driver for coordination and planning needs; size executors for distributed processing. More resources are not automatically better if they reduce concurrency or waste capacity.

When an exam question describes every notebook inheriting an unsuitable configuration, start at the workspace default. When only one workload needs different compute, look for an environment-level override—provided the workspace administrator has enabled customization.

## Configure domain workspace settings

<!-- block-id: domain-settings -->
A Fabric domain is a logical business grouping used for organization, discovery, and federated governance. Assigning a workspace to a domain associates every item in that workspace with the domain and adds domain metadata that users can filter in the OneLake catalog.

Domain assignment does **not** grant access to the workspace or its items. Visibility and data access still depend on workspace roles, item permissions, and data security. This is a frequent exam trap: domain membership organizes and governs; it is not an authorization grant.

### Know who can perform each domain action

<!-- block-id: domain-roles -->
| Role | Relevant responsibility |
| --- | --- |
| Fabric administrator | Creates and deletes domains, appoints domain administrators and contributors, and can associate workspaces |
| Domain administrator | Manages the assigned domain, its contributors, workspace associations, presentation, and delegated settings |
| Domain contributor | Assigns a workspace they administer to an authorized domain or changes that assignment |
| Workspace administrator | Must administer the workspace before acting as its domain contributor |

Fabric and domain administrators can assign workspaces centrally. A domain contributor works from the workspace settings and must also hold the workspace Admin role. Subdomains refine the logical hierarchy but inherit the administrators of their parent domain.

### Default domains and delegated governance

<!-- block-id: domain-defaults -->
A default domain targets specified users or security groups. Existing unassigned workspaces administered by those principals are assigned to the default domain, and new workspaces they create are assigned automatically. Existing domain assignments are preserved rather than overwritten by the default-domain mechanism.

Some tenant settings can be delegated to domain administration. That enables a business area to apply domain-specific governance within boundaries established at tenant scope. Delegation does not transfer every Fabric-administrator capability to the domain administrator.

Use these clues in scenario questions:

- **Improve catalog discovery by business area:** assign workspaces to domains.
- **Automatically organize new workspaces for a department:** configure a default domain for the department's users or groups.
- **Let business owners manage an allowed governance setting:** delegate the supported tenant setting to domain scope.
- **Restrict access to domain data:** use workspace, item, or OneLake security—not domain assignment alone.

## Terminology that drives the decision

<!-- block-id: terminology -->
| Term | Working meaning | Why it matters |
| --- | --- | --- |
| Diagnostic destination | A lakehouse that receives OneLake access events as JSON logs | It must satisfy placement and permission prerequisites before diagnostics can be enabled |
| Immutability period | A retention window during which diagnostic files cannot be modified or deleted | It protects evidence, but it also prevents early cleanup |
| Default storage tier | The tier used when a file has no explicitly assigned tier | Changing it can move affected files and generate transaction or retrieval charges |
| Lifecycle policy | The workspace's collection of automated tiering rules | A workspace has one policy, whose rules can target the workspace or path prefixes |
| Access-time tracking | Metadata needed for rules based on the last time a file was accessed | OneLake enables it when a lifecycle rule requires last-access conditions |

## What the OneLake settings control

<!-- block-id: settings-map -->
| Requirement in a scenario | Setting to examine | Important consequence |
| --- | --- | --- |
| Investigate who accessed data, when, and through which route | OneLake diagnostics | Events begin flowing to the chosen lakehouse after enablement; allow for activation latency |
| Protect diagnostic evidence from alteration for a defined period | Diagnostic-log immutability | Files cannot be changed or deleted until their retention period expires |
| Choose the initial tier for files without an explicit tier | Workspace default storage tier | Hot favors access; cooler tiers trade lower storage cost for higher access and transaction costs |
| Move inactive files automatically | Lifecycle management policy | Rules evaluate creation, modification, or access age and run asynchronously |

The settings are related but not interchangeable. Diagnostics produces evidence. Immutability protects that evidence. The default tier supplies a baseline for untiered files. Lifecycle rules change tiers later when their conditions are met.

## Responsibility and prerequisite boundaries

<!-- block-id: responsibility-boundaries -->
A workspace administrator manages these OneLake settings. For diagnostics, the administrator also needs contributor access to the destination lakehouse. Microsoft Learn states that the destination lakehouse must be in the same capacity as the workspaces being monitored. Network protection can narrow the valid destination further.

Before enabling diagnostics, verify:

1. A suitable lakehouse exists for the diagnostic events.
2. Capacity and network placement meet the documented constraints.
3. The configuring principal has both workspace-admin and destination-lakehouse permissions.
4. Retention, privacy, and cleanup ownership are agreed before immutability is applied.

That last check is deliberately operational. Immutability is not a temporary display option: protected files remain noneditable and nondeletable until their individual retention windows expire.

## Choose storage behavior deliberately

<!-- block-id: tier-decision -->
Hot, cool, and cold tiers exchange storage cost for access cost and minimum-retention commitments. The [OneLake storage-tier documentation](https://learn.microsoft.com/en-us/fabric/onelake/onelake-storage-tiers) identifies a 30-day minimum for cool storage and a 90-day minimum for cold storage. Moving or deleting data before the applicable minimum can incur an early-deletion charge.

Use this sequence:

1. Measure how often the data is read and changed.
2. Separate active paths from retention-oriented paths.
3. Estimate storage savings together with retrieval, transaction, and early-deletion costs.
4. Set a default tier only when it is appropriate for files that do not carry an explicit tier.
5. Use path-scoped lifecycle rules when different parts of the workspace have different access patterns.

Do not select the coldest tier merely because it has the lowest storage rate. A frequently queried dataset can cost more overall and perform less predictably when retrieval behavior is ignored.

## Build a lifecycle policy from the evidence

<!-- block-id: lifecycle-rules -->
A workspace has one lifecycle policy containing rules. A rule combines a scope, enabled state, time condition, and tiering action. Conditions can use age since creation, modification, or last access. Rules without a path filter affect all eligible files in the workspace, so a broad rule deserves explicit review.

Example decision—not a production prescription:

```json
{
  "rules": [
    {
      "name": "cool-stable-diagnostic-exports",
      "enabled": true,
      "scope": "Files/DiagnosticExports/",
      "condition": "daysAfterModificationGreaterThan: 30",
      "action": "tierToCool"
    }
  ]
}
```

The example expresses intent in a readable form. When implementing a policy, use the current portal or API schema from Microsoft Learn rather than treating this study representation as an importable payload.

Lifecycle changes are asynchronous. Microsoft Learn notes that new rules can take up to 24 hours to take effect and that policies attempt to run daily. An exam scenario that requires an immediate, one-time tier change is therefore different from a scenario asking for ongoing automated management.

## Portal and API views describe the same workspace state

<!-- block-id: portal-api -->
In the portal, lifecycle management is under **Workspace settings > OneLake > Lifecycle management**. The Fabric REST API can also retrieve workspace OneLake settings:

```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/onelake/settings
```

The caller must have the Admin workspace role and an appropriate delegated scope such as `OneLake.Read.All` or `OneLake.ReadWrite.All`. A response can report diagnostics status, diagnostic-log immutability, and lifecycle state, including the default tier. Reading settings does not itself enable or modify them.

## Configure Apache Airflow workspace settings

<!-- block-id: airflow-settings -->
Fabric Apache Airflow jobs use a workspace default runtime chosen under **Workspace settings > Data Factory > Apache Airflow Runtime Settings**. The main decision is whether to use the managed starter pool or create a custom pool.

| Characteristic | Starter pool | Custom pool |
| --- | --- | --- |
| Intended fit | Development and workloads that benefit from managed defaults | Production or workloads that need explicit sizing and capacity behavior |
| Startup behavior | Designed for immediate availability | A stopped pool can take time to resume |
| Uptime behavior | Deprovisions after inactivity | Remains available until manually paused |
| Configuration | Fixed managed configuration | Compute-node size, extra nodes, and autoscaling can be configured |
| Operational burden | Lower | Higher; the team owns sizing and uptime decisions |

If item-level compute customization is disabled, Airflow environments use the workspace starter pool. When a custom pool is justified, the workspace administrator chooses its name, compute-node size, autoscale behavior, and extra nodes. Extra nodes increase concurrent DAG worker capacity; they are a concurrency decision, not a substitute for fixing an inefficient DAG.

### Translate workload evidence into Airflow settings

<!-- block-id: airflow-decisions -->
Use a starter pool when the workload is intermittent, development-oriented, and tolerant of the managed configuration. Consider a custom pool when production scheduling needs predictable availability, nondefault sizing, autoscaling, or more concurrent workers.

A useful decision sequence is:

1. Measure concurrent DAG runs, task duration, and scheduling delay.
2. Separate startup-delay problems from insufficient worker-concurrency problems.
3. Choose node size for task requirements and extra nodes for justified concurrency.
4. Enable autoscaling when demand varies enough to outweigh the added operational complexity.
5. Define who pauses, resumes, monitors, and revises the pool.

Current Microsoft Learn documentation states that Fabric Apache Airflow jobs do not support private networks or virtual networks. Treat that as a time-sensitive product limitation and recheck the authoritative source when designing a secured deployment.

## Exam distinctions

<!-- block-id: exam-distinctions -->
- **Diagnostics versus monitoring:** diagnostics records OneLake data-access events. It is not a replacement for every workload-specific execution or performance log.
- **Immutability versus retention cleanup:** immutability prevents change during a fixed window; a separate cleanup process is still needed after the window expires.
- **Default tier versus lifecycle rule:** the default applies when no explicit tier is set; a rule evaluates conditions and changes eligible files over time.
- **Workspace setting versus data permission:** OneLake storage settings do not grant a user access to a lakehouse, table, row, or folder.
- **Workspace admin versus Fabric admin:** the workspace administrator manages the workspace policy; tenant-wide enablement and delegation remain tenant concerns.
- **Spark workspace default versus environment compute:** the workspace establishes the baseline and whether overrides are allowed; an environment holds reusable workload-specific configuration.
- **Environment compute versus `spark.conf`:** driver and executor resources belong to environment compute; `spark.conf` controls application properties inside a session.
- **Domain assignment versus authorization:** a domain organizes metadata and delegated governance; it does not grant access to workspace items or data.
- **Default domain versus forced reassignment:** a default domain assigns eligible unassigned and newly created workspaces; it preserves an existing assignment.
- **Airflow starter versus custom pool:** the starter pool minimizes administration; a custom pool adds control over sizing, autoscaling, concurrency, and uptime.

## Active recall

<!-- block-id: active-recall -->
1. Every Spark job in a workspace inherits an unsuitable pool. Which configuration layer should you examine first?
2. One notebook needs a different runtime and executor size. What must the workspace administrator allow before an environment can solve the problem?
3. Why is changing `spark.conf` not equivalent to changing environment compute?
4. A sales workspace should appear under Sales in the OneLake catalog. Which feature applies, and why does it not grant sales users access?
5. How does a default domain treat a workspace that already belongs to another domain?
6. A compliance team needs access events retained in a tamper-resistant form for 180 days. Which two OneLake capabilities work together, and what cleanup decision remains?
7. A workspace contains frequently queried curated tables and rarely accessed historical exports. Why is one workspace-wide default tier insufficient as the complete design?
8. What permissions and placement constraints must be checked before selecting a diagnostic lakehouse?
9. A question asks for a tier change to happen immediately. Why should you hesitate before choosing lifecycle management?
10. An Airflow team reports slow scheduling during concurrent production DAG runs. Which evidence distinguishes a node-sizing problem from a worker-concurrency problem?

## Sources and provenance

<!-- block-id: official-sources -->
This original study chapter was verified against the official Microsoft Learn pages linked below, retrieved September 1, 2026 (Pacific time). The Git-backed source registry records the retrieval timestamp and SHA-256 content hash for each page.
