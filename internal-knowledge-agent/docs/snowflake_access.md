---
id: it-snowflake-access
title: Snowflake Access Runbook
allowed_groups: it,data-platform
---

# Snowflake Access Runbook

Snowflake access is role-based and must be approved through the internal access-request workflow.

## Standard access

Employees requesting analytics access should specify the business reason, requested Snowflake role, and manager. The Data Platform team confirms that the requested role is appropriate and that required data-training acknowledgements are complete.

## Troubleshooting

If a user previously had access but receives an authentication error:

1. Confirm the user is signing in through company SSO.
2. Check whether the identity account is active.
3. Verify that the Snowflake user and expected role are still assigned.
4. If SSO succeeds but the role is missing, route the ticket to Data Platform for entitlement review.

## Elevated access

Administrative and production roles require Data Platform approval plus Security approval. Elevated credentials must not be shared or embedded in local scripts.
