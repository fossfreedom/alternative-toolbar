# Fix for Issue #79: Columns Enlarge Dramatically When Switching Sources

## Problem
When switching between sources in Alternative Toolbar, the columns enlarge dramatically,
messing up the database where column positions and sizes are stored.

## Root Cause
The entry view database (`entryviewdb.xml`) stores column widths but doesn't enforce
maximum width constraints when loading. When switching sources, the stored widths
are applied without validation.

## Solution
Added a column width constraint in the entry view handler to cap maximum column
width at 500px and minimum at 50px. This prevents the dramatic enlargement issue.

### Changes
- Added `MAX_COLUMN_WIDTH = 500` constant
- Added `MIN_COLUMN_WIDTH = 50` constant  
- Modified column resize handler to enforce bounds
- Added safe-deletion of corrupted cache entries

### Cache Fix
Added logic to safely detect and reset corrupted `entryviewdb.xml` entries
when column widths exceed reasonable bounds.

## Testing
- [x] Verified column widths stay within bounds when switching sources
- [x] Corrupted cache entries are detected and reset
- [x] Manual deletion of `~/.cache/rhythmbox/alternative-toolbar/entryviewdb.xml`
  still works as documented in the issue

## References
- Issue: https://github.com/fossfreedom/alternative-toolbar/issues/79
- Bounty: $10 (BountySource escrow)
