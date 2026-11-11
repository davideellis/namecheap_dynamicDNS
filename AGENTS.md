# AGENTS.md

## Homelab docs (source of truth)

The whole homelab is documented in the private repo `davideellis/homelab_docs_massiveweb`
(checked out next to this one at `../homelab_docs_massiveweb`). **Any change you make to the homelab
through this repo — new/changed service, container, port, vhost, DNS record, VM, script, timer, credential
location, backup or alert — must also be reflected there in the same session**: update the relevant
`docs/` pages, add a `CHANGELOG.md` line, run `scripts/collect-inventory.sh <host>` if it is visible on a host,
then commit and push. Its `AGENTS.md` has the full checklist.
