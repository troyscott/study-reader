# Configure security and governance

<!-- block-id: orientation -->
Fabric security is layered. Start with identity, then determine the required scope—workspace, item, or data—and grant the least privilege at that scope. Governance features such as sensitivity labels and endorsement describe and manage data; they do not silently replace authorization.

## Objective coverage

| Measured objective | Core idea |
| --- | --- |
| Implement workspace-level access controls | Roles grant broad capabilities across a collaboration boundary |
| Implement item-level access controls | Sharing and item permissions narrow access without workspace membership |
| Implement row-level, column-level, object-level, and folder/file-level access controls | Data-plane policies constrain what an identity can see or do |
| Implement dynamic data masking | Query results are obscured for principals without unmask privilege |
| Apply sensitivity labels to items | Purview classifications travel through supported inheritance and export paths |
| Endorse items | Promotion, certification, and master-data badges communicate trust |
| Implement and use Microsoft Fabric audit logs | Microsoft Purview audit records activities for investigation and compliance |
| Configure and implement OneLake security | Roles secure OneLake folders and tables independently of broad workspace roles |

## Implement workspace-level access controls

Workspace roles are Admin, Member, Contributor, and Viewer. They apply broadly to items in the workspace and include authoring or administration capabilities according to role. Use security groups rather than many individual assignments, and reserve Admin for principals that truly manage the workspace.

| Need | Starting point |
| --- | --- |
| Manage access and workspace configuration | Admin |
| Collaborate and manage content without full workspace administration | Member |
| Create and modify content | Contributor |
| Consume workspace content | Viewer, then verify data-plane behavior |

A role assignment is not the same as a data permission. Fabric evaluates control-plane and data-plane paths, and item types can enforce additional SQL, semantic-model, or OneLake rules. Test the actual access route the user will employ.

## Implement item-level access controls

Item sharing grants access to a specific item without placing the recipient in the entire workspace. Use it when a consumer needs a lakehouse, warehouse, report, or other supported item but should not discover or modify unrelated content. Item owners can manage permissions through the item, while workspace roles may already confer broader rights.

The least-privilege order is useful: first ask whether data can be served through a curated report or model; next consider item sharing; use a workspace role only when collaboration across the workspace is intended. Revoke stale direct shares and prefer groups for durable ownership.

## Implement row-level, column-level, object-level, and folder/file-level access controls

These controls protect different dimensions:

| Control | Restricts | Typical implementation |
| --- | --- | --- |
| Row-level security (RLS) | Which records a principal sees | Predicate/filter based on identity or role |
| Column-level security (CLS) | Which columns can be selected | Grant or deny column permissions |
| Object-level security (OLS) | Whether an object is visible or accessible | Permissions on tables, views, models, or schemas |
| Folder/file-level access | Which OneLake paths can be read or written | OneLake security roles with path/table permissions |

RLS and CLS are enforcement, while a view is an interface. A view that omits a sensitive column is helpful, but protect the base object so an alternate query path cannot bypass the intended boundary. Evaluate SQL endpoints, Spark, Direct Lake, shortcuts, and OneLake APIs because enforcement support can differ by route.

Example RLS pattern in a warehouse:

```sql
CREATE FUNCTION Security.fn_region(@RegionCode char(2))
RETURNS TABLE WITH SCHEMABINDING AS
RETURN SELECT 1 AS allowed
WHERE @RegionCode = CAST(SESSION_CONTEXT(N'region') AS char(2));

CREATE SECURITY POLICY Security.RegionPolicy
ADD FILTER PREDICATE Security.fn_region(RegionCode) ON Sales.OrderFact
WITH (STATE = ON);
```

The exact identity mapping must be designed and tested; the predicate alone does not establish a trustworthy user-to-region assignment.

## Implement dynamic data masking

Dynamic data masking (DDM) changes query results for users without the `UNMASK` privilege; it does not change stored values. Fabric Warehouse supports default, email, random, and custom-string masks as documented for supported data types.

```sql
ALTER TABLE dbo.Customer
ALTER COLUMN Email varchar(320) MASKED WITH (FUNCTION = 'email()');
```

DDM reduces accidental exposure in ordinary queries. It is not encryption and is not a strong boundary against a user who can infer values through repeated predicates or joins. Combine it with RLS, CLS, object permissions, and least privilege.

## Apply sensitivity labels to items

Sensitivity labels come from Microsoft Purview Information Protection. A tenant administrator enables their use, and labels must be published to the relevant users. Depending on supported item and path, Fabric can apply defaults, require labels, inherit labels downstream, and carry them into supported exports.

Do not equate a label with universal access control. Labels classify content and can invoke protection in documented cases, but access control is unsupported in other routes and cross-tenant scenarios. Verify the current item and export-path matrix.

## Endorse items

Endorsement helps users identify trustworthy assets:

| Badge | Meaning | Who can apply it |
| --- | --- | --- |
| Promoted | Owner believes the item is ready for reuse | A user with write permission |
| Certified | Authorized reviewer confirms organizational quality standards | Administratively designated certifiers |
| Master data | Data item is an authoritative organizational source | Administratively designated reviewers |

Endorsement improves discovery and trust signaling. It does not grant permission, encrypt data, or prove that every downstream use is correct.

## Implement and use Microsoft Fabric audit logs

Fabric user activities are available through Microsoft Purview Audit. Search by time, user, operation, workload, or item context; export results for a documented investigation when needed. Audit records answer *who performed which recorded action and when*. Diagnostic and workload logs answer different operational questions.

Establish retention, reviewer roles, alerting criteria, and an evidence-handling procedure before an incident. A missing result can reflect retention, licensing, ingestion delay, filter choice, or an activity not represented by the searched operation—not necessarily proof that nothing happened.

## Configure and implement OneLake security

OneLake security roles provide data access for selected tables or folders. A role can include members and define read or read/write permissions at paths, allowing data access without broad workspace authoring rights. Plan roles around job functions and stable groups.

Evaluate access as a path:

1. Does the principal have access to the Fabric item or relevant endpoint?
2. Which workspace or item permission applies?
3. Which OneLake security role and path applies?
4. Is a downstream engine enforcing another policy?
5. Does a shortcut introduce source credentials or source-side security?

Test with representative users, including denied cases. Administrators and item owners can have elevated rights that make their tests misleading.

## Build an access decision from the outside in

<!-- block-id: workspace-access-model -->
Workspace roles define a broad collaboration boundary. **Admin** manages the
workspace and access; **Member** collaborates broadly and can manage many
workspace capabilities; **Contributor** creates and changes content; **Viewer**
primarily consumes. Admin, Member, and Contributor are elevated identities for
OneLake because their workspace rights include write access. A narrow OneLake
read role therefore cannot be used to reduce the data rights already granted by
one of those broader workspace roles.

<!-- block-id: workspace-access-operations -->
Inventory people, service principals, and groups; assign each to a job function;
and grant the lowest workspace role that permits the required collaboration.
Prefer Microsoft Entra security groups so joiner, mover, and leaver changes occur
in one identity system. Separate administration from content development, keep
at least two governed owners, and review assignments periodically. Validate with
a user who has no overlapping group membership. For services, document the
identity, credential owner, rotation method, allowed workspace, and exact jobs.

<!-- block-id: workspace-access-decisions -->
Choose a workspace role only when the identity needs capabilities across the
workspace. Do not grant Contributor merely to let a consumer query one table;
use item and data permissions. Conversely, repeated direct shares across most
items are a signal that the person may genuinely belong in the workspace. The
failure mode to avoid is **permission accumulation**: a user receives narrow
access directly but also inherits broad access through a workspace group, so a
test of the narrow policy appears ineffective.

<!-- block-id: workspace-access-example -->
**Scenario.** Data engineers belong to a Contributor group, the platform team
uses a small Admin group, and report consumers are not workspace members. A
contractor who needs one lakehouse is shared that item and assigned a narrow
OneLake role. Test the contractor, a Contributor, and an unassigned account.
The contractor should not discover unrelated workspace items; the Contributor
will still have broad OneLake rights. This three-identity test is more
informative than testing only as the workspace owner.

<!-- block-id: workspace-access-diagnostics -->
When access is unexpectedly allowed, enumerate every workspace role and group,
direct item permission, OneLake role, SQL grant, semantic-model role, and cached
session. When access is denied, check the same layers in order plus tenant
settings and endpoint-specific prerequisites. Remove ambiguity by using a fresh
test identity and a private browser session. Record both positive and negative
tests; “the administrator could open it” is not evidence of least privilege.

## Item permissions and the data plane

<!-- block-id: item-access-model -->
Item permissions answer “may this identity interact with this item?” but not
always “may it read every underlying row through every engine?” `Read` commonly
exposes item metadata. Additional permissions such as `ReadData` or `ReadAll`
govern documented compute or OneLake routes for supported items. A report,
semantic model, SQL endpoint, and lakehouse can therefore participate in one
experience while enforcing different permissions.

<!-- block-id: item-access-operations -->
Start at the consumer experience and trace backward: report → semantic model →
SQL endpoint or OneLake table → source or shortcut target. Grant the report or
item permission first, then only the downstream data permission the intended
route requires. Use Manage permissions to inspect direct grants and reshare
rights. Avoid granting build, write, or reshare unless the user must create new
content or delegate access. Re-test after removing a grant because tokens and
sessions can temporarily obscure the result.

<!-- block-id: item-access-decisions -->
Use a curated report when consumers need answers, item sharing when they need a
specific reusable item, and workspace membership when they participate in the
workspace lifecycle. Granting `ReadAll` for OneLake access is materially
different from granting basic `Read` metadata access. Direct Lake also requires
careful reasoning about which identity and fallback path performs the query.
Never infer the data plane solely from whether the item appears in navigation.

<!-- block-id: item-access-example -->
**Worked access trace.** Lee can open a report but receives an error when
connecting directly to the lakehouse SQL endpoint. That can be correct: the
report path may be authorized through its semantic model while direct SQL data
access was never granted. If the requirement is report consumption only, do not
“fix” the result with Contributor. If direct analysis is required, grant the
documented endpoint permission and test a permitted and forbidden table.

<!-- block-id: item-access-diagnostics -->
Classify the failing action precisely: discover item, open item, query SQL,
read OneLake, build a semantic model, write data, or reshare. Each action points
to a different permission. Examine group expansion and inherited workspace
roles before adding another direct grant. A mini-lab should create a matrix of
three users by four actions and predict each outcome before testing it.

## Data-level controls

<!-- block-id: data-access-model -->
Object or folder security chooses the tables, schemas, or paths a role can
reach. Column security removes selected attributes. Row security applies a
predicate to records. These controls can be combined, but OneLake roles use a
**grant model**: a restrictive role does not deny access obtained from another
role or permission path. Engine-native SQL or semantic-model security may have
different authoring and enforcement surfaces, so identify the query route in
every design.

<!-- block-id: data-access-operations -->
Define access from a business policy, not from the current folder layout. Create
roles for stable functions, grant only required tables or folders, then apply
row and column rules where supported. Use immutable business keys and a governed
identity-to-scope mapping for dynamic row filtering. Validate Spark, SQL,
Direct Lake, and OneLake API paths that are actually in scope. Test nulls,
multiple group memberships, new rows, schema changes, and an identity that
should see nothing.

<!-- block-id: data-access-decisions -->
Prefer object or folder grants when whole datasets differ by audience. Use CLS
when a column must not be visible, RLS when records differ by user context, and
a curated view when a stable consumer contract or derived logic is needed.
Masking is not a substitute for removing a sensitive column. Avoid elaborate
per-user roles; group-driven roles and mapping tables scale better and are
auditable. Check current feature support before assuming the same rule is
enforced by every Fabric engine.

<!-- block-id: data-access-example -->
**Worked policy.** Regional analysts may read `Sales.OrderFact` only for their
region and must not see `Customer.Email`; finance may read all regions and the
email column. Create separate group-based roles, apply the region predicate to
the analyst role and exclude or restrict Email, then test an analyst in two
regions, finance, and an unassigned user. Adding an analyst to Contributor would
invalidate the intended OneLake restriction and should be caught by the test.

<!-- block-id: data-access-diagnostics -->
If a filter appears bypassed, look for broad workspace write, another granting
role, ownership, a different engine, or a cached result. If a query fails,
distinguish inability to reach the item from denial at table, column, or row
evaluation. Use a minimal query against one known object and progressively add
columns and predicates. Preserve the identity, endpoint, query, expected rows,
actual rows, and effective memberships as security-test evidence.

## Masking, classification, trust, and evidence

<!-- block-id: masking-comprehensive -->
Dynamic data masking is a presentation control evaluated at query time for
principals without `UNMASK`. Configure a supported mask on the target column,
grant ordinary query access to a test role, and compare results with and without
`UNMASK`. Choose a mask that reduces accidental exposure without misleading
users about the data type. Because values remain unchanged and inference can be
possible, use encryption, RLS, CLS, or denied object access for true
confidentiality boundaries. Troubleshoot by checking the querying principal,
`UNMASK` grants, object permissions, endpoint, and supported type.

<!-- block-id: sensitivity-comprehensive -->
Sensitivity labels classify an item according to organizational information
protection policy. Prerequisites include tenant configuration, labels published
to the author, and a supported item or propagation path. Choose a label based on
the data's policy classification, not the item's popularity. Apply it, verify
the displayed label and any documented downstream inheritance or export
behavior, and test the relevant route. A label can persist as governance
metadata or invoke supported protection, but it is not evidence that workspace,
item, and data permissions are correct. If a label is unavailable, inspect
Purview publication, licensing, tenant settings, user scope, and item support.

<!-- block-id: endorsement-comprehensive -->
Endorsement describes organizational trust. Owners can promote suitable items;
authorized reviewers certify items or designate master data according to the
organization's governance process. Define criteria—owner, documentation,
quality checks, freshness, security review, and support contact—before applying
a badge. Review it when those facts change. Certification does not grant access
or guarantee that a consumer's interpretation is valid. If endorsement options
are missing, verify write permission, tenant configuration, and designated
certifier status.

<!-- block-id: audit-comprehensive -->
Fabric audit evidence is searched through Microsoft Purview Audit. Establish
the investigation question and time zone, then query an appropriate time range,
users, operations, and workload context. Preserve exported results with the
query criteria and investigation record. Audit is for recorded user and admin
activity; Monitoring hub and workload logs explain operational executions.
Account for retention, licensing, ingestion delay, operation naming, and clock
boundaries before concluding an event is absent. As a mini-lab, perform a
benign item-share change, wait for ingestion, locate its audit record, and
compare what the audit event tells you with what the item's current permission
page tells you.

<!-- block-id: onelake-security-comprehensive -->
OneLake security roles grant supported table and folder access within a data
item. The author needs the documented Fabric Write or Reshare capability, and
role members should be stable groups where possible. Create the role, choose
Read or ReadWrite as required, select data objects, apply optional row or column
filters, assign members, and test through the intended engine. Default roles can
map documented item or workspace permissions to data access. Because grants are
additive, always inspect other roles and broad workspace rights when a user sees
too much. For a shortcut, evaluate both the OneLake reference and the remote
source identity or credential path.

<!-- block-id: security-exam-distinctions -->
For exam scenarios, separate four verbs: **authorize** with workspace, item, and
data permissions; **obscure returned values** with masking; **classify** with a
sensitivity label; **signal trust** with endorsement. Then distinguish audit
evidence from operational monitoring. A request for “one table only” points
away from Contributor and toward item plus OneLake data permissions. A request
to hide rows by region points to RLS, not a label or mask.

<!-- block-id: security-recall-lab -->
**Recall and mini-lab.** Why can a Contributor bypass the intent of a narrow
OneLake read role? What additional capability does a user need when `Read`
allows item discovery but not direct data access? Contrast CLS with DDM in one
sentence. Explain why Certified and Confidential answer different questions.
Finally, design a five-row access matrix for an administrator, engineer,
analyst, report-only consumer, and unassigned user; include at least one denied
test for workspace, item, SQL, and OneLake access.

## Exam distinctions

- Workspace roles are broad collaboration grants; item permissions are narrower.
- RLS filters rows; CLS restricts columns; OLS restricts objects; OneLake roles restrict tables or paths.
- DDM changes displayed results, not stored data, and is not encryption.
- Sensitivity labels classify and can protect supported flows; endorsement signals trust.
- Audit logs, OneLake diagnostics, and workload execution logs have different purposes.
- A OneLake shortcut can expose a reference while source-side security and credentials still matter.

## Active recall

1. Why is Viewer not a universal statement about every data access path?
2. When is item sharing preferable to workspace membership?
3. Which control hides a column entirely, and which only masks its returned value?
4. What is the difference between Certified and a sensitivity label?
5. Which identities should be used for negative access tests?
6. Where would you investigate a recorded item-deletion activity?

## Authoritative sources

- [Fabric permission model](https://learn.microsoft.com/en-us/fabric/security/permission-model)
- [OneLake data access control model](https://learn.microsoft.com/en-us/fabric/onelake/security/data-access-control-model)
- [Dynamic data masking in Fabric Data Warehouse](https://learn.microsoft.com/en-us/fabric/data-warehouse/dynamic-data-masking)
- [Information protection in Fabric](https://learn.microsoft.com/en-us/fabric/governance/information-protection)
- [Endorsement overview](https://learn.microsoft.com/en-us/fabric/governance/endorsement-overview)
- [Track user activities in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/admin/track-user-activities)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
