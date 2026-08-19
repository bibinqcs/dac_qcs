# Complete Year-End Closing Entry - Usage Guide

## Overview

This script generates a Journal Entry that zeros out **ALL accounts** (Balance Sheet + Profit & Loss) as of August 31, 2024 for Dubai Autism Center, enabling auditors to create fresh opening entries for fiscal year 2024-2025.

## Location

Script: [apps/dac_qcs/dac_qcs/utils/complete_year_end_closing.py](apps/dac_qcs/dac_qcs/utils/complete_year_end_closing.py)

## Prerequisites

1. **Backup**: Create a full backup before proceeding
   ```bash
   bench --site [your-site-name] backup --with-files
   ```

2. **Verify Fiscal Year**: Confirm fiscal year 2023-2024 exists and ends on 2024-08-31

3. **Check Permissions**: Ensure you have Journal Entry creation and submission rights

## Step-by-Step Usage

### Step 1: Open Bench Console

```bash
cd /home/azureuser/frappe-bench
bench --site [your-site-name] console
```

Replace `[your-site-name]` with your actual site name.

### Step 2: Generate Closing Entry (DRY RUN)

```python
from dac_qcs.utils.complete_year_end_closing import generate_complete_closing_entry

# Generate the closing entry (NOT saved yet)
je = generate_complete_closing_entry(
    company="Dubai Autism Center",
    closing_date="2024-08-31",
    fiscal_year="2023-2024"
)

# Review summary
print(f"\n=== CLOSING ENTRY SUMMARY ===")
print(f"Number of account rows: {len(je.accounts)}")
print(f"Total Debit: {je.total_debit:.2f}")
print(f"Total Credit: {je.total_credit:.2f}")
print(f"Difference: {flt(je.total_debit - je.total_credit):.2f}")
print(f"Posting Date: {je.posting_date}")
print(f"Fiscal Year: {je.fiscal_year}")
```

**Expected Output**:
- Message: "Found X account balances to close"
- Message: "Success: Entry is balanced. Total Debits = Total Credits = X"
- Message: "Closing entry created with X rows. Please review before saving."

### Step 3: Export for Detailed Review (Optional)

```python
import json
from frappe.utils import flt

# Export to JSON file for review
with open('/tmp/closing_entry_preview.json', 'w') as f:
    json.dump(je.as_dict(), f, indent=2, default=str)

print("\nClosing entry exported to: /tmp/closing_entry_preview.json")

# Print first 10 rows as sample
print("\n=== SAMPLE ACCOUNT ENTRIES (First 10) ===")
for i, row in enumerate(je.accounts[:10]):
    print(f"{i+1}. {row.account} | Debit: {row.debit:.2f} | Credit: {row.credit:.2f}")
    if row.party:
        print(f"   Party: {row.party_type} - {row.party}")
    if row.cost_center:
        print(f"   Cost Center: {row.cost_center}")
```

### Step 4: Get Trial Balance Before Closing

```python
from dac_qcs.utils.complete_year_end_closing import get_trial_balance_summary

# Get summary before closing
summary_before = get_trial_balance_summary("Dubai Autism Center", "2024-08-31")
```

This shows you the current state of accounts before closing.

### Step 5: Review Checklist

Before proceeding, verify:

- [ ] Number of rows matches expected accounts
- [ ] Total debits equal total credits (difference should be 0.00 or very close)
- [ ] Party balances are preserved (customer/supplier details visible in entries)
- [ ] Cost centers are captured where applicable
- [ ] No suspicious zero-balance accounts included
- [ ] Posting date is correct: 2024-08-31
- [ ] Fiscal year is correct: 2023-2024

### Step 6: Save the Journal Entry

Once satisfied with the preview:

```python
# Save the entry (creates draft Journal Entry in system)
je.insert()
print(f"\n✓ Journal Entry created: {je.name}")
print(f"  Status: Draft (not submitted)")
print(f"  You can now review it in the ERPNext UI")
```

### Step 7: Manual Review in ERPNext UI

1. Navigate to: **Accounting > Journal Entry > [je.name]**
2. Review all account entries carefully
3. Verify totals balance
4. Check party details
5. Verify cost center allocations

**If you need to make changes**:
- You can edit the Journal Entry in the UI
- Or cancel and regenerate using Step 2

### Step 8: Submit the Journal Entry

**Option A: Via Console**
```python
# Submit the entry
je.submit()
print(f"\n✓ Journal Entry {je.name} submitted successfully!")
print(f"  All GL Entries have been created")
```

**Option B: Via UI**
- Open the Journal Entry
- Click "Submit" button

### Step 9: Validate All Accounts Are Zeroed

```python
from dac_qcs.utils.complete_year_end_closing import validate_accounts_are_zeroed

# Validate closure
remaining = validate_accounts_are_zeroed("Dubai Autism Center", je.name)

if not remaining:
    print("\n✓ SUCCESS: All accounts have been zeroed!")
else:
    print(f"\n✗ WARNING: {len(remaining)} accounts still have balances")
    for bal in remaining:
        print(f"  - {bal.account}: {bal.balance:.2f}")
```

**Expected Output**: "Success! All accounts have been zeroed for Dubai Autism Center as of 2024-08-31."

### Step 10: Get Trial Balance After Closing

```python
# Get summary after closing
summary_after = get_trial_balance_summary("Dubai Autism Center", "2024-08-31")

# Should show:
# Accounts with balances: 0
# Total Debit Balances: 0.00
# Total Credit Balances: 0.00
```

### Step 11: Post-Closing Actions

#### A. Set Accounts Freezing Date

**Via UI**:
1. Go to: **Accounting > Setup > Accounts Settings**
2. Set **"Accounts Frozen Upto"** = `2024-08-31`
3. Set **"Frozen Accounts Modifier"** role (e.g., "Accounts Manager")
4. Save

**Via Console**:
```python
settings = frappe.get_doc("Accounts Settings")
settings.acc_frozen_upto = "2024-08-31"
settings.frozen_accounts_modifier = "Accounts Manager"
settings.save()
print("\n✓ Accounts frozen up to 2024-08-31")
```

#### B. Create Backup

```bash
# Exit the console first (Ctrl+D)
bench --site [your-site-name] backup --with-files
```

#### C. Generate Reports for Auditors

Generate these reports from ERPNext:

1. **Trial Balance as of 31-Aug-2024** (before closing)
   - Go to: Reports > Trial Balance
   - Set date: 2024-08-31
   - Uncheck "Include Closing Entry" (if option available)
   - Export to Excel/PDF

2. **Trial Balance as of 31-Aug-2024** (after closing)
   - Same report, should show all zeros

3. **General Ledger Report** (full fiscal year)
   - Go to: Reports > General Ledger
   - From: Fiscal year start date
   - To: 2024-08-31
   - Export to Excel/PDF

4. **The Closing Journal Entry**
   - Open Journal Entry: [je.name]
   - Print or Export to PDF

## Complete Example Script

Here's a complete script you can copy-paste into the console:

```python
from dac_qcs.utils.complete_year_end_closing import (
    generate_complete_closing_entry,
    validate_accounts_are_zeroed,
    get_trial_balance_summary
)
from frappe.utils import flt
import json

print("\n" + "="*60)
print("COMPLETE YEAR-END CLOSING - DUBAI AUTISM CENTER")
print("Closing Date: 2024-08-31 | Fiscal Year: 2023-2024")
print("="*60)

# Step 1: Get trial balance before
print("\n[1/5] Getting trial balance BEFORE closing...")
summary_before = get_trial_balance_summary("Dubai Autism Center", "2024-08-31")

# Step 2: Generate closing entry
print("\n[2/5] Generating closing entry...")
je = generate_complete_closing_entry(
    company="Dubai Autism Center",
    closing_date="2024-08-31",
    fiscal_year="2023-2024"
)

# Step 3: Review summary
print(f"\n[3/5] Review Summary:")
print(f"  Rows: {len(je.accounts)}")
print(f"  Total Debit: {je.total_debit:.2f}")
print(f"  Total Credit: {je.total_credit:.2f}")
print(f"  Difference: {flt(je.total_debit - je.total_credit):.2f}")

# Step 4: Export preview
with open('/tmp/closing_entry_preview.json', 'w') as f:
    json.dump(je.as_dict(), f, indent=2, default=str)
print(f"\n  Exported to: /tmp/closing_entry_preview.json")

# Step 5: Pause for manual review
print("\n[4/5] MANUAL REVIEW REQUIRED")
print("  Please review the summary above and the exported JSON file.")
print("\n  To continue, run:")
print(f"    je.insert()  # Save as draft")
print(f"    je.submit()  # Submit the entry")
print("\n  To validate after submission, run:")
print(f"    from dac_qcs.utils.complete_year_end_closing import validate_accounts_are_zeroed")
print(f"    validate_accounts_are_zeroed('Dubai Autism Center', je.name)")

print("\n" + "="*60)
```

## Rollback / Reversal

If you need to reverse the closing entry:

### Method 1: Cancel the Journal Entry

```python
# Via console
je = frappe.get_doc("Journal Entry", "[CLOSING-ENTRY-NAME]")
je.cancel()
print(f"✓ Journal Entry {je.name} cancelled")
```

### Method 2: Create Reverse Entry via UI

1. Open the closing Journal Entry
2. Click **"Make"** > **"Reverse Journal Entry"**
3. Set posting date (e.g., 2024-09-01)
4. Review and submit

Both methods automatically create reversing GL Entries.

## Troubleshooting

### Error: "Closing date must be within fiscal year"

**Solution**: Verify the fiscal year dates:
```python
frappe.db.get_value("Fiscal Year", "2023-2024", ["year_start_date", "year_end_date"])
```

### Error: "Company does not exist"

**Solution**: Check the exact company name:
```python
frappe.db.get_all("Company", fields=["name"])
```

### Warning: "Debits and credits don't balance"

**Cause**: Usually rounding differences in multi-currency scenarios.

**Solution**: If difference is < 1.00, this is acceptable. If larger, investigate individual account balances.

### No accounts found / Entry is empty

**Possible causes**:
1. All accounts already have zero balance
2. Wrong fiscal year specified
3. Wrong company name

**Solution**: Run trial balance query to verify:
```python
get_trial_balance_summary("Dubai Automation Center", "2024-08-31")
```

### Accounts still have balances after closing

**Possible causes**:
1. Transactions posted after the closing entry was generated
2. Specific account types excluded from query

**Solution**: Verify with:
```python
remaining = validate_accounts_are_zeroed("Dubai Autism Center", "[JE-NAME]")
```

## For Auditors: Opening Entry Process

After this closing entry, auditors should:

1. **Review Reports**:
   - Trial Balance as of 31-Aug-2024 (before closing)
   - The closing Journal Entry document
   - General Ledger for fiscal year 2023-2024

2. **Create Opening Entry** (as of 2024-09-01):

   ```python
   # In console
   je_opening = frappe.new_doc("Journal Entry")
   je_opening.company = "Dubai Autism Center"
   je_opening.posting_date = "2024-09-01"
   je_opening.voucher_type = "Opening Entry"
   je_opening.is_opening = "Yes"
   je_opening.fiscal_year = "2024-2025"  # Next fiscal year
   je_opening.user_remark = "Opening balances for fiscal year 2024-2025"

   # Add opening balances for each account
   # (based on Trial Balance before closing)
   # For each account with balance:
   #   If had debit balance: add debit entry
   #   If had credit balance: add credit entry

   je_opening.insert()
   # Review in UI, then submit
   ```

## Support

For issues or questions:
- Review this documentation
- Check the script code: [complete_year_end_closing.py](complete_year_end_closing.py)
- Review the plan: `/home/azureuser/.claude/plans/quirky-floating-wave.md`

## Script Information

- **Author**: Claude Code
- **Date**: 2024
- **Script Location**: `/home/azureuser/frappe-bench/apps/dac_qcs/dac_qcs/utils/complete_year_end_closing.py`
- **License**: MIT
