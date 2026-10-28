# Development Checklist

> **IMPORTANT**: Use this checklist before finishing each development session.

## Before finishing each development session:

- [ ] Update `PROJECT_PROGRESS.md`
- [ ] Record files changed
- [ ] Record functionality added
- [ ] Record tests performed
- [ ] Record known issues
- [ ] Record next task

## Before committing code:

- [ ] Ensure frontend builds without errors (`npm run build`)
- [ ] Ensure backend starts without crashes (`uvicorn app.main:app`)
- [ ] Verify `/health` endpoint returns `{"status": "healthy"}`
- [ ] Verify `/docs` Swagger UI loads correctly
- [ ] Check that mock modules (Disease, Yield, Irrigation, Weather, Assistant) still work
- [ ] Check English/Hindi language toggle still works

## After integrating a new model:

- [ ] Run `python scripts/check_models.py`
- [ ] Test the corresponding API endpoint via Swagger
- [ ] Test the frontend form → API → result flow
- [ ] Update the ML Model Status table in `PROJECT_PROGRESS.md`
- [ ] Update the Change Log section
