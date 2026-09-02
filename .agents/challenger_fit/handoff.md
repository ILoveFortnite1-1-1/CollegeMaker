# Handoff Report: Fit Scoring Math, Edge Cases & UI Workflows Evaluation

## 1. Observation

Adversarial stress tests were designed, implemented, and executed across four core dimensions in `tests/test_tier5_adversarial.py`:
- 8-dimension fit scoring algorithm with extreme boundary inputs (all weights 0, single weight 100%, negative weights, budget = $0, SAT = 1600, GPA = 4.0 vs 2.0).
- Missing data normalization and handling when optional metrics are unpopulated.
- Reach / Target / Likely selectivity invariance and categorization transitions.
- Portfolio scale and lifecycle: adding 50 schools, updating custom notes and tags, batch-modifying preference weights, clearing the portfolio, and verifying SQLite database persistence and hygiene.

### Test Execution Command & Summary Output
Command run:
```bash
.venv/bin/pytest tests/test_tier5_adversarial.py -v
```

Results: **29 PASSED, 2 FAILED** out of 31 tests.

### Verbatim Failures Observed

1. **`test_fit_scorer_with_completely_empty_college_metrics`**
```
________________ test_fit_scorer_with_completely_empty_college_metrics _____________
    def test_fit_scorer_with_completely_empty_college_metrics():
        sparse_college = CanonicalCollege(
            id="sparse_999999",
            unitid=999999,
            name="Sparse University",
            location=Location(city="Nowhere", state="XX"),
            undergrad_size=MetricField(value=None),
            admissions=AdmissionsData(acceptance_rate=MetricField(value=None)),
            costs=CostData(
                tuition_in_state=MetricField(value=None),
                tuition_out_of_state=MetricField(value=None),
                net_price_average=MetricField(value=None),
            ),
            outcomes=OutcomesData(
                completion_rate_6yr=MetricField(value=None),
                median_earnings_10yr=MetricField(value=None),
            ),
            popular_programs=[],
        )
        prefs = StudentPreferences(sat_score=1400, budget_max_annual=30000, preferred_majors=["Computer Science"], home_state="CA")
>       analysis = fit_scorer.evaluate_college_fit(sparse_college, prefs)
...
server/services/fit_scorer.py:166: in _score_career
    if earnings >= 115000:
E   TypeError: '>=' not supported between instances of 'NoneType' and 'int'
```

2. **`test_randomized_monte_carlo_probability_bounds`**
```
________________ test_randomized_monte_carlo_probability_bounds ________________
server/services/fit_scorer.py:166: in _score_career
    if earnings >= 115000:
E   TypeError: '>=' not supported between instances of 'NoneType' and 'int'
```

### Exact Code Flaw in `server/services/fit_scorer.py`
In `server/services/fit_scorer.py`, lines 164, 182-183, 201, 220, 239, 287, and 321 use the pattern:
```python
earnings = college.outcomes.median_earnings_10yr.value if college.outcomes.median_earnings_10yr else 70000
```
Because `college.outcomes.median_earnings_10yr` is an instance of `MetricField` (which is a truthy Pydantic model), the ternary expression evaluates to truthy even when its `.value` attribute is `None`. Consequently, `earnings` is assigned `None` rather than the default `70000`. When `if earnings >= 115000:` executes on line 166, Python raises a fatal `TypeError`.

This bug exists across all 7 metric extraction sites in `fit_scorer.py`:
- Line 164: `_score_career` (`median_earnings_10yr.value`)
- Line 182: `_score_roi` (`median_earnings_10yr.value`)
- Line 183: `_score_roi` (`net_price_average.value`)
- Line 201: `_score_academic` (`completion_rate_6yr.value`)
- Line 220: `_score_admissions` (`acceptance_rate.value`)
- Line 239: `_score_experience` (`retention_rate_ft.value`)
- Line 287: `_score_cost` (`net_price_average.value`)
- Line 321: `_classify_category` (`acceptance_rate.value`)

---

## 2. Logic Chain

1. **Pydantic Model Structure**: `CanonicalCollege` models wrap metrics inside `MetricField[T]`. When a metric is unpopulated or missing from a data source, `MetricField.value` is `None`, but the `MetricField` container object is instantiated and truthy (`bool(college.outcomes.median_earnings_10yr) == True`).
2. **Evaluation Logic**: `fit_scorer.py` checks `if college.outcomes.median_earnings_10yr` rather than checking `if college.outcomes.median_earnings_10yr and college.outcomes.median_earnings_10yr.value is not None`.
3. **Failure Propagation**: When any college in the database or search results has missing optional metric fields (e.g. specialized, vocational, or sparsely reported institutions), `evaluate_college_fit()` crashes with `TypeError`.
4. **API Impact**: Adding such a college to the portfolio, viewing its profile fit breakdown, or updating preferences crashes the `/api/portfolio/*` endpoint with a 500 Internal Server Error.
5. **Robust Areas**: 
   - Weight normalization with all 0 weights correctly normalizes to `0.125` each without ZeroDivisionError.
   - Single 100% weights isolate the exact dimension score across all 8 dimensions.
   - Budget edge cases ($0, negative, $1, $10M) are handled without division by zero.
   - Reach/Target/Likely selectivity categorization (<15% acceptance rate always classified as Reach) is verified and stable.
   - Portfolio lifecycle with 50 colleges, note mutations, preference updates with batch recalculation, summary stats, clearance, session isolation, and corrupted SQLite record recovery is fully functional and persisted.

---

## 3. Caveats

- All 52 colleges in `data/colleges_seed.json` have non-null values for primary metrics, which is why standard Tier 1-4 tests on seed data passed while adversarial missing-data tests failed.
- In production, live College Scorecard API queries will encounter sparse institutions with `value=None` across various metrics.
- The missing metric handling should also assign `ConfidenceLevel.ESTIMATED` (or omit the missing dimension from `available_dims` so `weights.normalized(available_dims)` dynamically reallocates weights to reported dimensions) to maintain high data provenance integrity.

---

## 4. Conclusion & Verdict

**Verdict**: **REQUEST_CHANGES**

### Required Action Items for the Implementation Team:
1. **Fix Metric Value Extraction in `server/services/fit_scorer.py`**:
   Introduce a safe helper or explicit check `field.value is not None` before accessing values:
   ```python
   def _get_metric_val(field, default):
       if field is not None and getattr(field, "value", None) is not None:
           return field.value
       return default
   ```
   Apply this across all 8 dimension scoring methods (`_score_career`, `_score_roi`, `_score_academic`, `_score_admissions`, `_score_experience`, `_score_strength`, `_score_location`, `_score_cost`) and `_classify_category`.

2. **Confidence & Dynamic Reweighting on Missing Data**:
   When a dimension uses a fallback/default value due to missing institutional metrics, set `dim.confidence = ConfidenceLevel.ESTIMATED` (or exclude it from `available_dims` to allow `weights.normalized(available_dims)` to redistribute weight exclusively to populated dimensions).

---

## 5. Verification Method

To independently verify the adversarial test suite and reproduce the findings:
```bash
# Run full adversarial suite
.venv/bin/pytest tests/test_tier5_adversarial.py -v

# Run targeted missing-data tests
.venv/bin/pytest tests/test_tier5_adversarial.py -k "empty_college_metrics or monte_carlo" -v
```
Expected output before fix: 2 failed (`TypeError: '>=' not supported between instances of 'NoneType' and 'int'`).
Expected output after fix: 31 passed across all adversarial edge cases.
