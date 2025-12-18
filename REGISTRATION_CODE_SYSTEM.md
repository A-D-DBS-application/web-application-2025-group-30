# Registration Code System - Implementation Guide

## Overview
The Personnel Scheduler now implements a secure registration code system that prevents unauthorized access to companies and enables structured company hierarchies with employee invitations.

## Key Components

### 1. Database Schema Changes
```sql
-- Added to companies table:
- registration_code TEXT UNIQUE NOT NULL (e.g., "ABC123XY")
- owner_id UUID REFERENCES public.users(id) (FK to first manager)
```

### 2. Backend Functions (models.py)

#### `generate_registration_code(length: int = 8) -> str`
- Generates random 8-character codes (uppercase letters + digits)
- Example output: "ABC123XY", "WXYZ9876"
- Characters used: A-Z, 0-9

#### `get_company_by_code(code: str) -> Dict`
- Retrieves company record by registration code
- Returns company object or None
- Supports both Supabase DB and in-memory fallback

#### `validate_registration_code(code: str) -> tuple[bool, str]`
- Validates that a registration code exists
- Returns: `(is_valid: bool, error_message: str)`
- Examples:
  - `(True, "")` - Valid code
  - `(False, "Registration code is required")` - Empty code
  - `(False, "Invalid registration code")` - Code not found

#### `list_companies() -> List[Dict]`
- Lists all companies in the system
- Used to determine if first user can create company
- Returns empty list if no companies exist

#### `create_company(name: str, logo_url: str = None, owner_id: str = None) -> Dict`
- **Updated**: Now auto-generates `registration_code`
- Accepts optional `owner_id` parameter
- Stores owner_id to establish company hierarchy
- Returns company object with code

### 3. Registration Flow (controllers/auth.py)

#### New Registration Workflow:

**Scenario A: First User (No Companies Exist)**
1. User registers WITHOUT code
2. System checks if any companies exist
3. If none: Auto-creates new company, sets user as owner
4. User is assigned to company automatically
5. Company registration code auto-generated

**Scenario B: Employee Joining Existing Company**
1. Employee receives registration code from manager
2. Employee enters code during registration
3. System validates code
4. If valid: User is assigned to that company
5. If invalid: Shows error "Invalid registration code"

**Scenario C: Manager Inviting New Manager**
1. Existing manager needs to share company code
2. New manager enters same code during registration
3. System joins new manager to same company
4. Both managers can see all company data

**Scenario D: Invalid Code with Existing Companies**
1. New user tries to register without code
2. System finds existing companies
3. Registration rejected: "Registration code required"
4. User must get code from company manager

### 4. User Interface Updates

#### Login/Registration Form (login.html)
```html
<!-- New field added -->
<label for="regCode">Company Registration Code <span>(Optional for first user)</span></label>
<input type="text" id="regCode" name="registration_code" 
       placeholder="e.g., ABC123XY" style="text-transform: uppercase;" />
```
- Optional for first user (creates new company)
- Required for subsequent users if companies exist
- Auto-converts to uppercase
- Placeholder shows example code format

#### Manager Dashboard (manager.html)
```html
<!-- New "Invite Employees" Card -->
<div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
  <h3>Invite Employees</h3>
  <p>Share this code with new team members to join your company:</p>
  <div style="font-size: 1.2rem; font-weight: bold; font-family: monospace;">
    {{ company_code }}
  </div>
  <p>Employees can use this code during registration to join your company.</p>
</div>
```
- Displays company's registration code
- Positioned in sidebar for easy access
- Purple gradient styling for visibility
- Copy-friendly monospace font for code

### 5. Company Hierarchy

```
Company (with unique registration_code and owner_id)
├── Owner/Admin Manager (first manager, sets owner_id)
├── Additional Managers (join with code)
└── Employees (join with code)
```

**Ownership Rules:**
- First manager to register in a company becomes owner
- Only owner can change company settings (future feature)
- Multiple managers can manage events together
- Employees can only view/interact with own assignments

### 6. Data Isolation

All queries filter by `company_id`:
```python
list_events(company_id)           # Only company's events
list_users(company_id)            # Only company's users
list_availabilities(company_id)   # Only company's availabilities
get_availability_for_user(user_id, company_id)  # Only if user in company
```

Users from Company A cannot:
- See Company B's events
- See Company B's employees
- Make assignments to Company B's shifts
- Access Company B's availability data

### 7. Security Considerations

**Protection Against:**
1. ✅ Unauthorized company joining (requires valid code)
2. ✅ Data cross-contamination (company_id in every query)
3. ✅ First-user exploit (registration code validates existing companies)
4. ✅ Duplicate codes (unique constraint on registration_code)

**Best Practices:**
- Managers should regularly review team members
- Registration codes can be regenerated per company (future feature)
- Remove employees from company (future feature)
- Audit access logs (future feature)

## Testing Scenarios

### Test 1: First User Creates Company
```
1. No users or companies exist
2. User "manager1" registers as "manager" role
3. Leave registration code field empty
4. System auto-creates company "manager1's Company"
5. User auto-assigned to company
6. Company gets registration code (e.g., "XYZ789AB")
✓ Result: Manager dashboard shows registration code
```

### Test 2: Employee Joins with Valid Code
```
1. Company exists with code "XYZ789AB"
2. User "employee1" registers as "employee" role
3. Enters registration code "XYZ789AB"
4. System validates and assigns to company
5. Employee can see company's events and availabilities
✓ Result: Employee dashboard shows company data
```

### Test 3: Invalid Code Rejected
```
1. Company exists with code "XYZ789AB"
2. User "hacker" tries to register with code "INVALID1"
3. System validates - code not found
4. Registration fails with error: "Invalid registration code"
✓ Result: Error message displayed, registration blocked
```

### Test 4: Multiple Managers in Same Company
```
1. Manager1 creates company with code "ABC123XY"
2. Manager2 registers with same code "ABC123XY"
3. Both assigned to same company
4. Both can create/manage events
✓ Result: Both managers see same events and employees
```

### Test 5: Company Isolation
```
1. Manager1's company: code "COMPANY1"
   - Events: Wedding, Catering, Setup
   - Employees: Alice, Bob
2. Manager2's company: code "COMPANY2"
   - Events: Conference, Meeting
   - Employees: Charlie, Diana
3. Manager1 logs in - sees only: Wedding, Catering, Setup, Alice, Bob
4. Manager2 logs in - sees only: Conference, Meeting, Charlie, Diana
✓ Result: Complete data isolation verified
```

## Implementation Summary

### Files Modified:
1. **backend_flask/schema.sql** - Added registration_code, owner_id fields
2. **backend_flask/models.py** - Added 5 new functions, updated create_company()
3. **backend_flask/controllers/auth.py** - Updated register() flow with code validation
4. **backend_flask/templates/login.html** - Added registration code input
5. **backend_flask/templates/manager.html** - Added company code display card
6. **backend_flask/app.py** - Updated manager route to pass company_code

### Lines of Code:
- models.py: ~50 lines added (3 validation functions + list_companies)
- auth.py: ~30 lines added (code validation + first-user check)
- manager.html: ~15 lines added (new code card)
- app.py: ~5 lines added (company code retrieval)
- login.html: ~5 lines added (code input field)

### Status: ✅ COMPLETE
All components implemented and tested. System ready for production use.

## Future Enhancements

1. **Code Regeneration** - Allow managers to generate new codes
2. **Code Expiration** - Set time limits on invitation codes
3. **Invite Links** - Share personal registration links
4. **Employee Removal** - Remove employees from company
5. **Role Management** - Promote/demote between manager/employee
6. **Audit Logging** - Track all registrations and role changes
7. **SSO Integration** - Single sign-on with registration codes
8. **Multi-code Support** - Different codes for different departments
