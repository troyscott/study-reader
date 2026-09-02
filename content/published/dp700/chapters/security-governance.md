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
