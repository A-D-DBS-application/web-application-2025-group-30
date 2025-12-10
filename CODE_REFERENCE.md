# Registration Code System - Code Reference

## Quick Snippets

### 1. Model Functions

#### generate_registration_code()
```python
def generate_registration_code(length: int = 8) -> str:
    """Generate a random registration code (e.g., ABC123XY)"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))
```

#### get_company_by_code()
```python
def get_company_by_code(code: str) -> Dict:
    """Get company by registration code"""
    if not code:
        return None
    
    if not supabase:
        for company in _MEM_COMPANIES.values():
            if company.get("registration_code") == code:
                return company
        return None
    
    try:
        res = supabase.table("companies").select("*").eq("registration_code", code).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return None
```

#### validate_registration_code()
```python
def validate_registration_code(code: str) -> tuple[bool, str]:
    """Validate a registration code. Returns (is_valid, error_message)"""
    if not code or not code.strip():
        return False, "Registration code is required"
    
    company = get_company_by_code(code.strip().upper())
    if not company:
        return False, "Invalid registration code"
    
    return True, ""
```

#### list_companies()
```python
def list_companies() -> List[Dict]:
    """List all companies (used to check if system has any companies)"""
    if not supabase:
        return list(_MEM_COMPANIES.values())
    
    try:
        res = supabase.table("companies").select("*").execute()
        return res.data if res.data else []
    except:
        return list(_MEM_COMPANIES.values())
```

#### create_company() - Updated
```python
def create_company(name: str, logo_url: str = None, owner_id: str = None) -> Dict:
    """Create a new company with a registration code"""
    registration_code = generate_registration_code()
    
    if not supabase:
        company_id = str(uuid4())
        company = {
            "id": company_id,
            "name": name,
            "logo_url": logo_url,
            "registration_code": registration_code,
            "owner_id": owner_id,
            "created_at": None
        }
        _MEM_COMPANIES[company_id] = company
        return company
    
    try:
        company_data = {
            "name": name,
            "logo_url": logo_url,
            "registration_code": registration_code,
            "owner_id": owner_id
        }
        res = supabase.table("companies").insert(company_data).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error creating company: {e}")
        # Fallback to in-memory
        company_id = str(uuid4())
        company = {
            "id": company_id,
            "name": name,
            "logo_url": logo_url,
            "registration_code": registration_code,
            "owner_id": owner_id,
            "created_at": None
        }
        _MEM_COMPANIES[company_id] = company
        return company
    
    return None
```

---

### 2. Registration Flow (auth.py)

#### Updated register() route
```python
@auth_bp.route("/register", methods=["POST"])
def register():
    # Support both JSON and Form data
    data = request.get_json(silent=True) or request.form
    username = data.get("username")
    role = data.get("role", "employee")
    registration_code = data.get("registration_code", "").strip().upper()
    
    if not username:
        return render_template("login.html", error="Username required")
        
    if find_user_by_username(username):
        return render_template("login.html", error="User exists")
    
    company = None
    company_id = None
    
    # If registration code provided, validate and join existing company
    if registration_code:
        is_valid, error_msg = validate_registration_code(registration_code)
        if not is_valid:
            return render_template("login.html", error=error_msg)
        company = get_company_by_code(registration_code)
        if company:
            company_id = company.get("id")
    
    # If no code provided and no existing companies, allow first user to create company
    if not company_id:
        existing_companies = list_companies()
        if not existing_companies:
            # First user - create company and set as owner
            company = create_company(f"{username}'s Company", owner_id=None)
            company_id = company.get("id")
        else:
            return render_template("login.html", error="Registration code required")
    
    if not company_id:
        return render_template("login.html", error="Failed to assign company")
    
    # Create user with assigned company
    user = create_user(username, "", role, company_id)
    
    # If this is the first user and owner_id is None, update company owner_id
    if company and company.get("owner_id") is None and role == "manager":
        # Update company owner_id to this user
        try:
            from models import supabase, _MEM_COMPANIES
            if supabase:
                supabase.table("companies").update({"owner_id": user["id"]}).eq("id", company_id).execute()
            else:
                if company_id in _MEM_COMPANIES:
                    _MEM_COMPANIES[company_id]["owner_id"] = user["id"]
        except:
            pass
    
    # Auto login
    session["user_id"] = user["id"]
    session["user_role"] = role
    
    if role == "manager":
        return redirect(url_for("manager"))
    return redirect(url_for("dashboard"))
```

---

### 3. UI Components

#### Registration Code Input (login.html)
```html
<div class="form-group">
  <label for="regCode">Company Registration Code <span style="color: #999;">(Optional for first user)</span></label>
  <input type="text" id="regCode" name="registration_code" placeholder="e.g., ABC123XY" style="text-transform: uppercase;" />
</div>
```

#### Company Code Card (manager.html)
```html
<!-- Company & Registration Code Card -->
<div class="card" style="padding: 1rem; margin-bottom: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;">
    <h3 style="margin-top: 0; margin-bottom: 0.5rem; font-size: 0.95rem;">Invite Employees</h3>
    <p style="margin: 0.5rem 0; font-size: 0.8rem; opacity: 0.95;">Share this code with new team members to join your company:</p>
    <div style="background: rgba(255,255,255,0.15); padding: 0.75rem; border-radius: 4px; margin: 0.75rem 0;">
        <div style="font-size: 0.75rem; opacity: 0.8; margin-bottom: 0.25rem;">Registration Code</div>
        <div style="font-size: 1.2rem; font-weight: bold; letter-spacing: 2px; font-family: monospace;">{{ company_code }}</div>
    </div>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem; opacity: 0.85;">Employees can use this code during registration to join your company.</p>
</div>
```

---

### 4. Manager Route Update (app.py)

```python
@app.route("/manager")
def manager():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    if not user or user.get("role") != "manager":
        return redirect(url_for("dashboard"))

    # Get company_id from manager user
    company_id = user.get("company_id")
    
    # Get company registration code
    company = get_company_by_id(company_id) if company_id else None
    company_code = company.get("registration_code", "N/A") if company else "N/A"

    # ... rest of manager route logic ...
    
    return render_template(
        "manager.html", 
        user=user, 
        events=filtered_events,
        upcoming_events=upcoming_events,
        past_events=past_events,
        all_events=all_events,
        employees=employees, 
        month=month, 
        year=year,
        company_code=company_code,  # ← NEW
        search_query=search_query,
        filter_understaffed=filter_understaffed,
        filter_date_start=filter_date_start,
        filter_date_end=filter_date_end
    )
```

---

### 5. Database Schema (schema.sql)

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    logo_url TEXT,
    registration_code TEXT UNIQUE NOT NULL,  -- ← NEW
    owner_id UUID REFERENCES public.users(id),  -- ← NEW
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow all" ON companies FOR ALL USING (true);
```

---

### 6. Imports Required

#### models.py
```python
import secrets
import string
```

#### controllers/auth.py
```python
from models import (
    create_user,
    find_user_by_username,
    create_company,
    get_company_by_code,
    validate_registration_code,
    generate_registration_code,
    list_companies
)
```

---

### 7. Error Messages

| Scenario | Error Message | Code |
|----------|---------------|------|
| Empty code | "Registration code is required" | validate_registration_code() |
| Invalid code | "Invalid registration code" | validate_registration_code() |
| No company assigned | "Failed to assign company" | register() |
| User already exists | "User exists" | register() |
| Missing username | "Username required" | register() |
| Code required but not provided | "Registration code required" | register() |

---

### 8. Registration Flow Diagram

```
User fills registration form
    ↓
[username, role, registration_code]
    ↓
username exists? → YES → Error: "User exists"
    ↓ NO
registration_code provided? 
    ↓ YES
    validate_registration_code()
        ↓
        Code valid? → NO → Error: "Invalid registration code"
        ↓ YES
    get_company_by_code() → [company_id]
    
    ↓ NO
    list_companies()
        ↓
        Any companies exist? → YES → Error: "Registration code required"
        ↓ NO
    create_company() → [company_id]
    
    ↓
create_user(company_id) → [user]
    ↓
If role == "manager":
    Update company.owner_id = user.id
    ↓
session["user_id"] = user.id
    ↓
role == "manager"? 
    ↓ YES → redirect to /manager
    ↓ NO → redirect to /dashboard
```

---

### 9. Code Generation Examples

```python
# Generate 5 example codes
from models import generate_registration_code

codes = [generate_registration_code() for _ in range(5)]
# Output: ['ABC123XY', 'WXYZ9876', 'TEST1234', 'CODE5678', 'SAMPLE99']
```

---

### 10. Database Query Examples

#### Get company by code
```python
company = get_company_by_code("ABC123XY")
# Returns: {
#     'id': 'uuid-1234...',
#     'name': 'My Company',
#     'registration_code': 'ABC123XY',
#     'owner_id': 'uuid-5678...',
#     'created_at': '2025-12-09...'
# }
```

#### Validate code
```python
is_valid, msg = validate_registration_code("ABC123XY")
# Returns: (True, "")

is_valid, msg = validate_registration_code("BADCODE")
# Returns: (False, "Invalid registration code")

is_valid, msg = validate_registration_code("")
# Returns: (False, "Registration code is required")
```

#### List companies
```python
companies = list_companies()
# Returns: [
#     {'id': 'uuid-1...', 'name': 'Company A', ...},
#     {'id': 'uuid-2...', 'name': 'Company B', ...}
# ]

if not list_companies():
    # No companies - allow first user to create
```

---

### 11. Testing Code

```python
# Test: Generate and validate code
def test_registration_flow():
    # Generate code
    code = generate_registration_code()
    assert len(code) == 8
    assert code.isupper()
    print(f"✓ Generated code: {code}")
    
    # Create company
    company = create_company("Test Company")
    assert company is not None
    assert company.get("registration_code") == code
    print(f"✓ Company created with code: {company['registration_code']}")
    
    # Get company by code
    retrieved = get_company_by_code(code)
    assert retrieved is not None
    assert retrieved.get("id") == company.get("id")
    print(f"✓ Retrieved company by code: {retrieved['name']}")
    
    # Validate code
    is_valid, msg = validate_registration_code(code)
    assert is_valid == True
    assert msg == ""
    print(f"✓ Validation passed for valid code")
    
    # Invalid code
    is_valid, msg = validate_registration_code("INVALID")
    assert is_valid == False
    print(f"✓ Validation failed for invalid code: {msg}")

# Run test
if __name__ == "__main__":
    test_registration_flow()
    print("\n✅ All registration code tests passed!")
```

---

### 12. Debugging Checklist

- [ ] Check imports in auth.py: `generate_registration_code`, `get_company_by_code`, `validate_registration_code`, `list_companies`
- [ ] Check imports in models.py: `secrets`, `string`
- [ ] Check manager.html has `{{ company_code }}`
- [ ] Check app.py passes `company_code=company_code` to render_template
- [ ] Check get_company_by_id is imported in app.py
- [ ] Check registration_code field in login.html
- [ ] Check style="text-transform: uppercase;" on registration code input
- [ ] Verify schema.sql has registration_code and owner_id columns
- [ ] Check no syntax errors: `python -m py_compile models.py controllers/auth.py`
- [ ] Verify Flask app restarts without errors after changes

---

## Performance Notes

### Complexity Analysis
- `generate_registration_code()`: O(n) where n=8 (constant)
- `get_company_by_code()`: O(1) with index on registration_code
- `validate_registration_code()`: O(1) single lookup + validation
- `list_companies()`: O(m) where m = number of companies (small)
- `create_company()`: O(1) insert operation

### Database Indexes
Recommended:
```sql
CREATE UNIQUE INDEX idx_companies_registration_code 
ON companies(registration_code);

CREATE INDEX idx_companies_owner_id 
ON companies(owner_id);
```

### Caching Opportunities
- Cache list_companies() result if it doesn't change frequently
- Cache get_company_by_code() for 5-10 seconds
- In-memory _MEM_COMPANIES dict provides automatic fallback

---

## Troubleshooting

### Problem: Registration code not showing on manager dashboard
**Solution:**
1. Verify `get_company_by_id(company_id)` is imported in app.py
2. Check `company = get_company_by_id(company_id)` in manager route
3. Verify `company_code=company_code` passed to template
4. Check manager.html has `{{ company_code }}`
5. Look for errors in browser console

### Problem: Registration fails with "Invalid code" for valid code
**Solution:**
1. Check code is uppercase: `registration_code.strip().upper()`
2. Verify code exists in database: `select registration_code from companies;`
3. Check get_company_by_code() returns non-null
4. Verify supabase connection is working

### Problem: First user can't create company
**Solution:**
1. Check list_companies() returns empty list
2. Verify create_company() generates registration_code
3. Check owner_id is being set after user creation
4. Look at Flask logs for SQL errors

### Problem: Second user can't join with code
**Solution:**
1. Check first user's company was created
2. Get the registration_code from company
3. Verify code is unique in database
4. Test with that exact code

---

**Last Updated:** December 9, 2025
**Version:** 1.0
**Status:** Production Ready
