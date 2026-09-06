# Sovereign Security

- Model and embedding endpoints must be local when sovereign mode is enabled.
- External endpoint rejection is audited as a `security_blocked` event.
- Model and embedding audit records contain metadata, not prompts, responses, or document contents.
- Generated Python runs in a disposable Docker container with no network, limited resources, no application secrets, and a read-only input mount.
- File and artifact tools are confined to approved local workspaces.
- High-risk actions require human approval.
- The security dashboard reports application-enforced policy and measured audit events; it does not claim to be an OS firewall or packet monitor.

## Verify

```powershell
python -m unittest tests.test_phase6 -v
docker compose exec sovereign-ai tesseract --version
docker compose exec sovereign-ai pdfinfo -v
```
