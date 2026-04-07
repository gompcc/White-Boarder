# Lessons Learned

## 2026-04-06: Never delete user session data during testing
- **Mistake**: Ran `rm -rf sessions/` to clean up after route verification tests, destroying the user's real session outputs.
- **Rule**: Never delete the `sessions/` directory contents. Use a separate temp directory for test data, or clean up only test-created sessions by name.
- **Pattern**: Before any `rm -rf`, check if real user data exists in the target.
