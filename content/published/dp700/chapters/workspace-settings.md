# Configure Microsoft Fabric workspace settings

<!-- block-id: orientation -->
The exam objective groups Spark, domain, OneLake, and Apache Airflow settings under one heading. This chapter concentrates on **OneLake workspace settings** as the representative case. The reliable way to reason through these settings is to identify the administrative scope, the data affected, and the operational consequence before selecting an option.

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

## Exam distinctions

<!-- block-id: exam-distinctions -->
- **Diagnostics versus monitoring:** diagnostics records OneLake data-access events. It is not a replacement for every workload-specific execution or performance log.
- **Immutability versus retention cleanup:** immutability prevents change during a fixed window; a separate cleanup process is still needed after the window expires.
- **Default tier versus lifecycle rule:** the default applies when no explicit tier is set; a rule evaluates conditions and changes eligible files over time.
- **Workspace setting versus data permission:** OneLake storage settings do not grant a user access to a lakehouse, table, row, or folder.
- **Workspace admin versus Fabric admin:** the workspace administrator manages the workspace policy; tenant-wide enablement and delegation remain tenant concerns.

## Active recall

<!-- block-id: active-recall -->
1. A compliance team needs access events retained in a tamper-resistant form for 180 days. Which two OneLake capabilities work together, and what cleanup decision remains?
2. A workspace contains frequently queried curated tables and rarely accessed historical exports. Why is one workspace-wide default tier insufficient as the complete design?
3. What permissions and placement constraints must be checked before selecting a diagnostic lakehouse?
4. Why might a last-access lifecycle rule change workspace metadata behavior?
5. A question asks for a tier change to happen immediately. Why should you hesitate before choosing lifecycle management?

## Sources and provenance

<!-- block-id: official-sources -->
This original study chapter was verified against the official Microsoft Learn pages linked below, retrieved September 1, 2026 (Pacific time). The Git-backed source registry records the retrieval timestamp and SHA-256 content hash for each page.
