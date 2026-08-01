# Perseus Vault Demo

Public browser demo for the Perseus Vault memory loop.

- `app.py` — narrow stdlib HTTP wrapper around the real Vault binary
- `index.html` — responsive demo UI and visual system
- `Dockerfile` — runtime image definition
- `docker-compose.yml` — ownership-preserving Portainer deployment definition

The public demo uses browser-scoped session isolation and is not production data.

Live service: https://vault-demo.perseus.observer/

## Portainer deployment

The canonical deployment is an editable Portainer stack sourced from this
repository's `docker-compose.yml`. It deliberately preserves the existing
runtime contract:

- service/container: `perseus-vault-demo`
- external network: `media-net`
- external data volume: `perseus-vault-demo-data:/data`
- public origin port: `8092`
- restart policy: `unless-stopped`

`LEDGER_ORG` and `LEDGER_API_KEY` are intentionally not committed; configure
them as protected Portainer environment values only if the optional scoped
evidence inspection is enabled. The wrapper returns only a sanitized receipt
summary and never sends raw Ledger events or the key to the browser.
