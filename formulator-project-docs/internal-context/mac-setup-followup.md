---
cursor:
  subagentId: "bc-b1f5b1a0-2045-5d68-bfb4-d6f8ac9cb2c6"
---

# Follow-up: Mac setup still blocked from this cloud run

## Attempts

| Agent | `usePrivateWorker` | `privateWorkerId` | Result |
|-------|--------------------|-------------------|--------|
| [Setup ~/develop/republic-formulas](bc-8d182330-3baf-56e8-8967-f41635449bf8) | false | null | Cloud Linux; wrote [mac-setup-blocker.md](mac-setup-blocker.md) |
| [Mac checkout + drive tiers](bc-ce87d349-7f81-5891-916f-5df3010dd45d) | false | null | Same — Task ignored `usePrivateWorker` / `privateWorkerId` / `workerId` |

This parent run itself: `usePrivateWorker=false`, `privateWorkerId=null` ([Implement formula evolve plan](bc-b1f5b1a0-2045-5d68-bfb4-d6f8ac9cb2c6)).

## Contrast (worked)

Desktop-launched Mac agents on worker `3f4cb657-9337-5ac6-9965-ed5753ed8745` (`~/develop/republic_ner_matching @ RiksMacBook`): e.g. survey / S4 sample — `usePrivateWorker=true`.

## What’s needed

Coordinator (or user from Desktop) must spawn the checkout checklist **on that private worker**. Task-from-cloud cannot place onto RiksMacBook with the current Task schema.

Checklist remains in [mac-setup-blocker.md](mac-setup-blocker.md).
