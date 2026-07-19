# C-305 deterministic Python fixture

This generated Git repository is intentionally small. `fixture_math.py` implements the accepted
baseline behavior, `tests/test_fixture_math.py` verifies that baseline, and
`tests/known_failure.py` describes the intentionally missing negative-number behavior.

The known failure is a real, bounded repair target: change `classify_number(-1)` to return
`"negative"` without regressing the existing positive and zero cases. No network, credentials,
external services, or non-standard Python packages are required.
