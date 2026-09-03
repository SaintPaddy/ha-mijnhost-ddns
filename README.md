# mijn.host DDNS for Home Assistant

A Home Assistant custom integration that keeps A records at [mijn.host](https://mijn.host)
pointed at your network's current public IPv4 address — dynamic DNS without any external
updater, cron job, or YAML. Includes API-key expiry warnings, because mijn.host API keys
are not eternal.

## What it does

Every few minutes (configurable) it:

1. Looks up your public IPv4 via a lookup service **you choose** — including
   EU-based options (Mullvad 🇸🇪, ifconfig.co 🇳🇴), global ones (ipify, icanhazip,
   ident.me), or your own custom plain-text echo URL.
2. Reads the current A record via the [mijn.host API](https://mijn.host/api/doc).
3. If they differ, updates the record (PATCH) with your configured TTL. The record
   is created if it does not exist yet.

## Features

- **Full UI configuration** — domain, record, and API key are entered in the
  Home Assistant UI. The key is stored in HA's config entry storage (never in
  `secrets.yaml` or `configuration.yaml`).
- **API-key lifecycle management**:
  - *Reactive*: if mijn.host rejects the key (expired/revoked), HA raises a
    re-authentication prompt — paste the new key, done.
  - *Proactive*: set the key's expiry date in the options and get a **Repairs
    warning**, a problem binary sensor, and a date sensor ahead of time
    (default: 14 days, configurable). Replace a still-working key anytime via
    the entry's **Reconfigure** action.
- **Choice of public-IP lookup service** with EU/sovereign options, or a custom URL.
- **Multiple records**: one config entry manages one record — add the integration
  again for each additional subdomain (also across different domains). Each entry
  has its own device, entities, and options.
- IPv4 validation: a lookup response that isn't a bare IPv4 address is rejected
  (protects against HTML error pages and IPv6 answers ending up in your A record).

## Entities (per managed record)

| Entity | Type | Meaning |
|---|---|---|
| Public IP | sensor | Your current public IPv4 as reported by the lookup service |
| DNS record IP | sensor | What the A record at mijn.host currently holds |
| Managed record | sensor | The FQDN this entry maintains (attributes: domain, TTL) |
| Last checked | sensor (timestamp) | Last successful poll — a stale value means the updater is stuck |
| Last record update | sensor (timestamp) | Last time the record was actually rewritten |
| API key expires | sensor (date) | The expiry date you configured (unknown when unset) |
| Record in sync | binary sensor | On when record matches reality |
| API key expiring soon | binary sensor (problem) | On inside the warning window — automate a notification on this |
| Check & sync now | button | Force an immediate check |

## Installation

### HACS (custom repository)

HACS → Integrations → Custom repositories → add this repository as category
*Integration* → download → restart Home Assistant.

### Manual

Copy `custom_components/mijnhost_ddns/` into `/config/custom_components/` on your
Home Assistant instance and restart HA.

## Configuration

Settings → Devices & Services → Add integration → **mijn.host DDNS**.

| Field | Meaning |
|---|---|
| Domain | The domain as registered at mijn.host, e.g. `example.nl` |
| Record name | The record to manage, e.g. `wg` (or full `wg.example.nl`) |
| API key | Created in the mijn.host control panel under API |

### Options (gear icon on the entry)

| Option | Default | Meaning |
|---|---|---|
| Public IP lookup service | Mullvad (EU) | Or ifconfig.co, ipify, icanhazip, ident.me, custom URL |
| Custom lookup URL | — | Used only with 'Custom'; must return a bare IPv4 over https |
| Record TTL | 300 s | Written with every record update |
| Check interval | 5 min | How often to compare and sync |
| API key expiry date | unset | Enables the expiry warning machinery |
| Warn days before expiry | 14 | When the Repairs warning and problem sensor activate |

### Rotating the API key

1. Create the new key in the mijn.host control panel.
2. Integration entry → ⋮ → **Reconfigure** → paste the new key.
3. Update the expiry date in the options; the warning clears on the next poll.

If the old key expires before you rotate: entities become unavailable, HA shows a
re-authentication prompt, and the record keeps its last value in the meantime.

## Notes

- Only IPv4 (A records) in this version. AAAA support may come later.
- The integration polls; a typical setup (5-minute checks) performs one lookup
  request and one mijn.host API read per cycle, and writes only on change.
- Not affiliated with mijn.host.

## License

MIT
