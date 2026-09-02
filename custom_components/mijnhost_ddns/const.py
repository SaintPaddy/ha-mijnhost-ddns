"""Constants for the mijn.host DDNS integration."""

from __future__ import annotations

DOMAIN = "mijnhost_ddns"

CONF_DNS_DOMAIN = "dns_domain"
CONF_RECORD_NAME = "record_name"
CONF_TTL = "ttl"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_IP_SOURCE = "ip_source"
CONF_CUSTOM_IP_URL = "custom_ip_url"

DEFAULT_TTL = 300
DEFAULT_UPDATE_INTERVAL_MINUTES = 5
DEFAULT_IP_SOURCE = "mullvad"

API_BASE = "https://mijn.host/api/v2"

IP_SOURCE_CUSTOM = "custom"

# Plain-text IPv4 echo services. Keys are stable ids stored in config entries;
# values are (label, url). URLs are chosen to be IPv4-only where the provider
# offers a dedicated v4 endpoint.
IP_SOURCES: dict[str, tuple[str, str]] = {
    "mullvad": ("Mullvad (Sweden, EU)", "https://am.i.mullvad.net/ip"),
    "ifconfig_co": ("ifconfig.co (Norway, EEA)", "https://ifconfig.co/ip"),
    "ipify": ("ipify (global)", "https://api.ipify.org"),
    "icanhazip": ("icanhazip / Cloudflare (global)", "https://ipv4.icanhazip.com"),
    "identme": ("ident.me (anycast, global)", "https://v4.ident.me"),
}
