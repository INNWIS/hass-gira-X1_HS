# Gira X1 & Homeserver for Home Assistant

Unofficial Home Assistant custom integration for the **Gira X1**, **Gira HomeServer** and **Gira FacilityServer**. It uses the Gira IoT REST API v2 to automatically discover all functions in your Gira Project Assistant (GPA) project and exposes them as Home Assistant entities.

- Lighting (switching, dimming, RGBW, color temperature)
- Shutters and blinds (position and slat angle)
- Climate (heating/cooling, sauna, fan coil)
- Switches, buttons, scenes, sensors, numbers
- Audio / Sonos
- **Push updates** via callbacks (near real time), with automatic fallback to polling

> Tested on Gira X1. HomeServer / FacilityServer support is based on the official API documentation; feedback is welcome.

## Installation via HACS

1. Open HACS → menu (three dots, top right) → **Custom repositories**.
2. Paste the URL of this repository, select category **Integration**, and click **Add**.
3. Search for **Gira X1** in HACS and click **Download**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration → Gira X1**.
6. Enter the IP address, username and password of your X1 (or HomeServer).

## Network

The integration starts a small HTTPS server (default port 51888, self-signed certificate) to which the Gira device pushes state changes. Home Assistant and the Gira device must be able to reach each other (same network/VLAN, no firewall blocking that port). If this does not work, the integration automatically falls back to polling every 10 seconds.

## Troubleshooting

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.gira_x1: debug
```

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by Gira, Giersiepen GmbH & Co. KG.
