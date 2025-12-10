# ILP Constraints for Automated Employee Assignment

## Mathematical Formulation

### Decision Variables

```
x[i][j] ∈ {0, 1}

where:
  i = employee index (1 to E)
  j = shift index (1 to S)
  x[i][j] = 1 if employee i is assigned to shift j, 0 otherwise
```

---

## Complete Constraint Set

### **HARD CONSTRAINTS** (Must Always Be Satisfied)

These constraints ensure feasibility - assignments must satisfy all hard constraints or they're invalid.

---

#### **1. Capacity Constraints**
*Each shift must be staffed to required capacity*

```
For each shift j:
  Σ(i=1 to E) x[i][j] = capacity[j]

Meaning: 
  - Sum of all employees assigned to shift j must equal the capacity needed
  - e.g., if shift needs 5 people, exactly 5 must be assigned
```

**Why:**
- Core requirement: shifts must have right staffing level
- Too few: understaffed shift, poor service
- Too many: waste money

**Example:**
```
Shift "Wedding" has capacity 6
So: x[emp1][wedding] + x[emp2][wedding] + ... + x[emp6][wedding] = 6
```

---

#### **2. No Overlapping Shifts**
*An employee cannot work two shifts at the same time*

```
For each employee i and each pair of overlapping shifts (j, k):
  x[i][j] + x[i][k] ≤ 1

where overlapping(j, k) means:
  start[j] < end[k] AND start[k] < end[j]

Meaning:
  - Employee cannot be assigned to both j and k if they overlap in time
```

**Why:**
- Physically impossible to be in two places
- Legal requirement (can't double-book)
- Prevents chaos

**Example:**
```
Shift A: 9am-1pm
Shift B: 12pm-4pm
These overlap, so: x[emp1][A] + x[emp1][B] ≤ 1
(Employee can be in only one)
```

---

#### **3. Minimum Break Time Between Shifts**
*Employee needs adequate rest between consecutive shifts*

```
For each employee i and each pair of shifts j, k where end[j] < start[k]:
  If (start[k] - end[j]) < min_break_hours:
    x[i][j] + x[i][k] ≤ 1

where min_break_hours = 8 (configurable)

Meaning:
  - If break between shifts is less than 8 hours, don't assign same person to both
```

**Why:**
- Employee health/safety (fatigue)
- Legal requirements (labor laws)
- Prevents burnout
- Better work quality

**Example:**
```
Shift A: 9am-5pm (8 hours)
Shift B: 11pm-7am (8 hours, next day)

Break = 6 hours (too short, need 8)
So: x[emp1][A] + x[emp1][B] ≤ 1
(Can't assign to both)
```

---

#### **4. Maximum Hours Per Day**
*Employee cannot work excessive hours in a single day*

```
For each employee i and each day d:
  Σ(j: shift j on day d) duration[j] * x[i][j] ≤ max_hours_per_day

where max_hours_per_day = 12 (configurable)

Meaning:
  - Total hours worked by employee on any single day ≤ 12 hours
```

**Why:**
- Labor law compliance (max working hours)
- Employee health
- Prevents scheduling mistakes

**Example:**
```
Employee works:
  - Shift A: 9am-1pm (4 hours)
  - Shift B: 2pm-8pm (6 hours)
  
Total = 10 hours (OK, < 12)

But if also assigned Shift C: 8pm-10pm (2 hours)
Total = 12 hours (exactly at limit, can't add more that day)
```

---

#### **5. Availability Window Constraints**
*Only assign employees during times they said they're available*

```
For each employee i and shift j:
  If shift j is NOT within any availability window of employee i:
    x[i][j] = 0

where availability window = [available_start, available_end]

Meaning:
  - If employee didn't indicate availability for shift time, can't assign them
  - Forced constraint (binary variable set to 0)
```

**Why:**
- Respect employee preferences/constraints
- Account for personal appointments, school, etc.
- Improves morale (assignments respect their stated needs)
- Reduces no-shows

**Example:**
```
Employee Alice says: "Available Mon-Wed 9am-6pm only"

Shift: Thursday 2pm-6pm
→ x[alice][thursday_shift] = 0 (forced to not assign)
```

---

#### **6. Skill Requirements**
*Only assign employees with required skills for shift type*

```
For each shift j requiring skill set S[j]:
  For each employee i WITHOUT skill s in S[j]:
    x[i][j] = 0

where skill requirement is specific to shift type:
  - Wedding coordinator shift: needs "wedding" skill
  - Setup shift: needs "setup" skill
  - Basic shift: no specific skill needed

Meaning:
  - Can only assign skilled employees to specialized shifts
```

**Why:**
- Quality assurance (right people for the job)
- Customer satisfaction
- Prevents training disasters
- Liability (wrong person could cause problems)

**Example:**
```
Shift: "Wedding Coordinator" (requires skill="wedding_experience")

Employee Bob: skills = ["setup", "basic"] (no wedding experience)
→ x[bob][wedding_shift] = 0 (can't assign)

Employee Carol: skills = ["wedding_experience", "setup"]
→ x[carol][wedding_shift] can be 1 (eligible)
```

---

#### **7. Employee Single Assignment Per Shift**
*Cannot assign same employee twice to same shift*

```
For each shift j:
  x[i][j] ≤ 1  for each employee i

(This is implicit in binary constraint, but explicit for clarity)

Meaning:
  - Employee either is or isn't assigned to a shift (not 1.5 times)
```

**Why:**
- Logical requirement (obvious)
- Prevents double-counting

---

### **SOFT CONSTRAINTS** (Try to Optimize, Not Required)

These are incorporated into the objective function with weights. If a soft constraint must be broken to satisfy hard constraints, it's OK.

---

#### **S1. Workload Fairness**
*Distribute hours evenly across employees*

```
Objective contribution:
  - Minimize: Σ(i) (hours[i] - avg_hours)²
  
  OR simpler: Maximize fairness_score = 1 - (max_hours - min_hours) / (2 * avg_hours)

Weight: 0.25 (important for morale)
```

**Why:**
- Prevents overworking some, underutilizing others
- Better retention
- Team morale
- Legal compliance (appearance of fairness)

**Example:**
```
Employee A: 40 hours assigned (from previous solution)
Employee B: 40 hours assigned
Employee C: 5 hours assigned

This is UNFAIR. Algorithm prefers assigning new shifts to C.
```

---

#### **S2. Availability Preference Matching**
*Prioritize shifts within employee's preferred availability windows*

```
Objective contribution:
  For each assignment x[i][j]:
    - If shift j is within employee i's availability: +1 point
    - If shift j is outside availability: -2 points (discouraged but allowed)

Weight: 0.30 (high importance - respects preferences)
```

**Why:**
- Improves morale (respects preferences)
- Reduces no-shows (people prefer their preferred times)
- Shows respect for personal life

**Example:**
```
Employee prefers: Mon-Wed 9am-6pm

Assigned shift: Monday 2pm (preferred) → +1
Assigned shift: Thursday 6pm (not preferred) → -2
```

---

#### **S3. Reliability/No-Show Risk**
*Prioritize assigning reliable employees (low no-show risk)*

```
Objective contribution:
  For each assignment x[i][j]:
    score = (1 - no_show_probability[i])
    
    where no_show_probability[i] ∈ [0.0, 1.0]
    
    Add to objective: score * x[i][j]

Weight: 0.25 (important for operational success)
```

**Why:**
- Prevents cancellations (biggest operational problem)
- Objective data for decisions
- Ensures coverage

**Example:**
```
Employee A: no-show rate 5% (reliable) → score = 0.95
Employee B: no-show rate 25% (unreliable) → score = 0.75

Algorithm prefers assigning A over B (if other factors equal)
```

---

#### **S4. Skill Match Quality**
*Prefer assigning employees who have extensive experience with shift type*

```
Objective contribution:
  For each assignment x[i][j]:
    skill_match_score = experience_level[i][shift_type[j]]
    
    where experience_level ∈ [0.0, 1.0]
    0.0 = no experience (but maybe not required)
    1.0 = expert
    
    Add to objective: skill_match_score * x[i][j]

Weight: 0.15 (prefer experienced, but not mandatory)
```

**Why:**
- Better quality/efficiency
- Reduces training needs
- Improves confidence

**Example:**
```
Shift: Wedding event

Employee A: 20 wedding shifts done, expert → score = 1.0
Employee B: 0 wedding shifts, but capable → score = 0.3
Employee C: 2 wedding shifts, learning → score = 0.5

Algorithm prefers A, then C, then B
(But could still use B if fairness/availability dictates)
```

---

#### **S5. Preference for Clustering/Grouping**
*Prefer assigning same employee to consecutive or nearby shifts (location-aware)*

```
Objective contribution:
  For each pair of shifts (j, k) assigned to same employee i:
    If distance(location[j], location[k]) < 5km
    OR shifts are consecutive (end[j] = start[k]):
      +1 point (bonus for clustering)

Weight: 0.05 (nice-to-have, not critical)
```

**Why:**
- Reduces travel time/costs
- Better for employee (less driving)
- Environmental benefit

**Example:**
```
Venue A: Location X
Venue B: Location X (5km away)

If assigning same person to both → +1 bonus
(Prefer this over assigning different people)
```

---

### Summary: Constraint Categories

| Category | Type | Hard/Soft | Impact |
|----------|------|-----------|--------|
| **Capacity** | Shift must have exact staffing | Hard | Critical |
| **No Overlaps** | Can't be in 2 places | Hard | Critical |
| **Break Time** | 8h min between shifts | Hard | Critical |
| **Max Hours/Day** | ≤12 hours/day limit | Hard | Critical |
| **Availability** | Respect preferences | Hard | Critical |
| **Skills Required** | Right people for job | Hard | Critical |
| **Fairness** | Even hour distribution | Soft | Morale |
| **Availability Match** | Prefer stated windows | Soft | Retention |
| **Reliability** | Prefer low no-show risk | Soft | Operations |
| **Skill Quality** | Prefer experienced | Soft | Quality |
| **Clustering** | Group nearby shifts | Soft | Cost |

---

## Objective Function

```
Maximize:
  Z = (0.25 * fairness_score) 
    + (0.30 * availability_match_score)
    + (0.25 * reliability_score)
    + (0.15 * skill_match_score)
    + (0.05 * clustering_score)

Subject to:
  [All Hard Constraints Above]
  [All Soft Constraints Above]
  x[i][j] ∈ {0, 1}
```

---

## Implementation Strategy

### **Option 1: Pure Greedy + Backtracking** (Recommended for MVP)
```
- Solve hard constraints only
- Use soft constraints to guide decisions (scoring)
- Fast (<100ms), good results (80-90% optimal)
- No external libraries
```

### **Option 2: Integer Linear Programming** (If you want exact)
```
- Use PuLP library (easy, open source)
- Solves hard AND soft constraints optimally
- Slower (but <5 seconds for 50 employees)
- More complex setup
```

### **Option 3: Genetic Algorithm** (Middle ground)
```
- Population-based search
- Respects hard constraints
- Optimizes soft constraints
- Good results (85-95% optimal)
- 2-5 seconds runtime
- No external libraries
```

---

## Recommended Implementation for Your Product

**Start with Option 1 (Greedy + Hard Constraints):**

1. **Sorting Phase**
   - Sort shifts by difficulty (capacity, skill requirement)
   - Sort employees by fairness score (those with fewer hours first)

2. **Assignment Phase**
   - For each shift (in difficulty order):
     - Find all eligible employees (pass hard constraints)
     - Rank by soft constraints
     - Assign top N

3. **Validation Phase**
   - Double-check all hard constraints satisfied
   - If not, try next candidate
   - If none work, mark shift as understaffed

4. **Result**
   - Fast (<50ms)
   - Respects all hard constraints
   - Optimizes soft constraints reasonably well
   - No external libraries

---

## Code Structure Preview

```python
def solve_assignment_ilp(employees, shifts, constraints, weights):
    """
    Solve employee assignment using constraint satisfaction
    
    Hard Constraints (must satisfy):
    1. Capacity[shift] = required employees
    2. No overlapping shifts per employee
    3. Min 8-hour breaks between shifts
    4. Max 12 hours per employee per day
    5. Availability windows must contain shift time
    6. Employee must have required skills
    
    Soft Constraints (optimize):
    1. Fairness: even hour distribution (weight=0.25)
    2. Availability match: prefer stated windows (weight=0.30)
    3. Reliability: prefer low no-show risk (weight=0.25)
    4. Skill quality: prefer experienced (weight=0.15)
    5. Clustering: group nearby shifts (weight=0.05)
    """
    
    assignments = {}
    
    # Phase 1: Sort
    shifts_sorted = sort_by_difficulty(shifts)
    
    # Phase 2: Assign
    for shift in shifts_sorted:
        needed = shift['capacity']
        
        candidates = []
        for emp in employees:
            # Check HARD constraints
            if not passes_hard_constraints(emp, shift, assignments):
                continue
            
            # Score SOFT constraints
            score = calculate_soft_constraint_score(
                emp, shift, assignments, weights
            )
            
            candidates.append((emp, score))
        
        # Sort by score and assign top N
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        for i in range(min(needed, len(candidates))):
            emp_id = candidates[i][0]['id']
            assignments[shift['id']] = assignments.get(shift['id'], [])
            assignments[shift['id']].append(emp_id)
    
    return assignments

def passes_hard_constraints(employee, shift, current_assignments):
    """
    Check all 6 hard constraints:
    1. Capacity - checked globally
    2. No overlaps - check this employee's other shifts
    3. Min break time - check gaps between shifts
    4. Max hours/day - sum this shift + others that day
    5. Availability - shift time in any availability window?
    6. Skills - employee has all required skills?
    """
    
    # 1. Capacity handled by assignment phase
    
    # 2. No overlaps
    for other_shift_id in current_assignments.get(employee['id'], []):
        if overlaps(shift, other_shift_id):
            return False
    
    # 3. Min break time
    for other_shift_id in current_assignments.get(employee['id'], []):
        if insufficient_break(shift, other_shift_id):
            return False
    
    # 4. Max hours/day
    daily_hours = sum_hours_for_day(employee, shift, current_assignments)
    if daily_hours > 12:
        return False
    
    # 5. Availability
    if not in_availability_window(employee, shift):
        return False
    
    # 6. Skills
    if not has_required_skills(employee, shift):
        return False
    
    return True

def calculate_soft_constraint_score(employee, shift, assignments, weights):
    """
    Score based on soft constraints:
    - S1: Fairness (0.25 weight)
    - S2: Availability match (0.30)
    - S3: Reliability (0.25)
    - S4: Skill quality (0.15)
    - S5: Clustering (0.05)
    """
    
    score = 0
    
    # S1: Fairness
    fairness_score = calculate_fairness_score(employee, shift, assignments)
    score += fairness_score * weights.get('fairness', 0.25)
    
    # S2: Availability match
    availability_score = calculate_availability_match(employee, shift)
    score += availability_score * weights.get('availability', 0.30)
    
    # S3: Reliability
    reliability_score = calculate_reliability_score(employee)
    score += reliability_score * weights.get('reliability', 0.25)
    
    # S4: Skill quality
    skill_score = calculate_skill_quality(employee, shift)
    score += skill_score * weights.get('skill_quality', 0.15)
    
    # S5: Clustering
    clustering_score = calculate_clustering_bonus(employee, shift, assignments)
    score += clustering_score * weights.get('clustering', 0.05)
    
    return score
```

---

## Summary: Constraints You'll Implement

### Hard Constraints (Non-Negotiable)
1. ✅ Exact capacity per shift
2. ✅ No overlapping shifts
3. ✅ Minimum 8-hour breaks
4. ✅ Maximum 12 hours/day
5. ✅ Availability windows (force zeros)
6. ✅ Skill requirements (force zeros)

### Soft Constraints (Optimize)
1. ✅ Fairness (workload balance)
2. ✅ Availability preferences (respect stated times)
3. ✅ Reliability (prefer low no-show risk)
4. ✅ Skill quality (prefer experienced)
5. ✅ Clustering (group nearby shifts)

**Total Constraints: 11 (6 hard, 5 soft)**

This is a **realistic, implementable set** that covers all major scheduling concerns without being overly complex.

