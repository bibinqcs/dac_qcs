# Quick Start Guide - Year-End Closing Entry

## TL;DR - Quick Commands

```bash
# 1. Backup first!
bench --site [your-site] backup --with-files

# 2. Open console
bench --site [your-site] console

# 3. In Python console:
from dac_qcs.utils.complete_year_end_closing import generate_complete_closing_entry, validate_accounts_are_zeroed

# 4. Generate (preview only)
je = generate_complete_closing_entry("Dubai Autism Center", "2024-08-31", "2023-2024")

# 5. Review
print(f"Rows: {len(je.accounts)} | Debit: {je.total_debit:.2f} | Credit: {je.total_credit:.2f}")

# 6. Save & Submit
je.insert()
je.submit()

# 7. Validate
validate_accounts_are_zeroed("Dubai Autism Center", je.name)
```

## One-Line Complete Script

For experienced users, copy-paste this into bench console:

```python
from dac_qcs.utils.complete_year_end_closing import *; je = generate_complete_closing_entry("Dubai Autism Center", "2024-08-31", "2023-2024"); print(f"\nRows: {len(je.accounts)} | Debit: {je.total_debit:.2f} | Credit: {je.total_credit:.2f} | Review and run: je.insert(); je.submit()")
```

## What This Does

1. Queries ALL account balances as of 2024-08-31
2. Creates a Journal Entry that reverses every balance
3. Result: All accounts show zero balance after submission
4. Auditors can then create fresh opening entries

## Important Notes

- **BACKUP FIRST** - Always create backup before running
- **REVIEW BEFORE SUBMIT** - The entry is created as draft, review it carefully
- **REVERSIBLE** - Can be cancelled if needed: `je.cancel()`
- **SELF-BALANCING** - Total debits automatically equal total credits

## Files Created

1. [complete_year_end_closing.py](complete_year_end_closing.py) - Main script
2. [CLOSING_ENTRY_USAGE.md](CLOSING_ENTRY_USAGE.md) - Detailed documentation
3. [QUICK_START.md](QUICK_START.md) - This file

## Questions?

See [CLOSING_ENTRY_USAGE.md](CLOSING_ENTRY_USAGE.md) for complete documentation.
