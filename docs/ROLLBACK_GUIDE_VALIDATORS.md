# Rollback Guide - Validator Chain

## Quick Rollback (1 Command)

```bash
# Disable validators globally
export ENABLE_VALIDATORS=false

# Restart backend
# (method depends on your deployment)
```

## Detailed Rollback Steps

### 1. Environment Variables

Set these environment variables to disable validators:

```bash
ENABLE_VALIDATORS=false
ENABLE_TONE_ALIGN=false  # Optional: also disable tone alignment
```

### 2. Restart Backend

**Local:**
```bash
# Stop current process (Ctrl+C)
# Restart
python start_backend.py
# or
uvicorn backend.api.main:app --reload
```

**Docker:**
```bash
docker-compose restart backend
```

**Railway/Render:**
- Update environment variables in dashboard
- Redeploy or restart service

### 3. Verify Rollback

**Check API:**
```bash
# Should work without validation
curl -X POST http://localhost:8000/api/chat/rag \
  -H "Content-Type: application/json" \
  -d '{"message": "Test"}'
```

**Check Logs:**
- No validation-related logs should appear
- No "Validation failed" messages

## Partial Rollback

### Disable Specific Validators

You can't disable individual validators via env vars yet, but you can modify `backend/api/main.py`:

```python
# Comment out specific validators
chain = ValidatorChain([
    CitationRequired(),
    # EvidenceOverlap(threshold=0.08),  # Disabled
    NumericUnitsBasic(),
    # EthicsAdapter(guard_callable=None),  # Disabled
])
```

### Disable Only Validation (Keep Identity/Tone)

```python
# In backend/api/main.py, comment out validation block:
# if enable_validators:
#     ... validation code ...
```

## Rollback Verification Checklist

- [ ] `ENABLE_VALIDATORS=false` set
- [ ] Backend restarted
- [ ] API calls work without validation errors
- [ ] No validation metrics being recorded
- [ ] Dashboard "Validation" page shows "No validation data"
- [ ] Logs show no validation-related errors

## Troubleshooting

### Issue: Still seeing validation errors after rollback

**Solution:**
1. Check environment variables are actually set:
   ```bash
   echo $ENABLE_VALIDATORS
   ```
2. Clear Python cache:
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} +
   ```
3. Restart backend completely (not just reload)

### Issue: API still returns 422 errors

**Solution:**
- Check if `ENABLE_VALIDATORS` is actually `false` (not `False` or `FALSE`)
- Verify backend process has restarted
- Check logs for validation code execution

### Issue: Dashboard still shows validation metrics

**Solution:**
- Metrics are in-memory, will clear on restart
- Or call `GET /api/validators/metrics` to verify it returns empty data

## Full Code Rollback (Nuclear Option)

If environment variables don't work, you can revert code changes:

```bash
# Revert main.py changes
git checkout HEAD -- backend/api/main.py

# Remove validator modules (optional, not required)
# They won't be used if ENABLE_VALIDATORS=false
```

## Prevention

To avoid needing rollback:

1. **Test locally first** with `ENABLE_VALIDATORS=true`
2. **Monitor metrics** in dashboard before enabling in production
3. **Start with low thresholds** (e.g., `VALIDATOR_EVIDENCE_THRESHOLD=0.01`)
4. **Gradually increase** thresholds as confidence builds

## Support

If rollback doesn't work:
1. Check logs: `backend/api/main.py` line 172-246
2. Verify imports are not failing
3. Check Python version compatibility (3.12+)
4. Open issue with logs and environment details

