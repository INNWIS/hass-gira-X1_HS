# hass-gira-X1_HS
Unofficial Home Assistant custom integration for the Gira X1, Gira HomeServer and Gira FacilityServer. It uses the Gira IoT REST API v2 to automatically discover all functions in your Gira Project Assistant (GPA) project and exposes them as Home Assistant entities: lights, covers, climate, switches, scenes, sensors, numbers and audio. State changes are pushed in near real time via callbacks, with automatic fallback to polling.

