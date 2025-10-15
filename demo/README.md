(see repo demo README)

## Quick self-hosted example (curl)

If you run a local Mistral-like server (example: http://localhost:8080), you can test with curl:

```bash
# replace YOUR_API_KEY if required, or omit Authorization if not needed
curl -sS -X POST http://localhost:8080/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model":"mistral-large","input":"Hello from curl","max_tokens":64}' | jq .

Expected: JSON response with outputs or choices. Our adapter normalizes those shapes.
