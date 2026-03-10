# Feature: Schnellbau- & Schnellabrissmodus

## Source (FAQ 3.2.9)
- Schnellbaumodus: build same building type repeatedly without full page reload
- Most useful for roads + intersections
- Page does NOT reload between builds (Canvas state preserved)
- Build result opens in external overlay/modal
- Schnellabrissmodus: same concept for demolishing

## Data Models
```python
# No new DB models needed – reuses existing build/demolish endpoints
# Frontend state only:
QuickBuildSession: {
  active: bool,
  template_id: int,
  province_id: int,
  built_fields: [int],   # client-side tracking (no reload)
  failed_fields: [int]
}
```

## Core Logic (Frontend-focused)
```
ACTIVATE SCHNELLBAU:
  POST /province/{id}/quickbuild/activate {"template_id": int}
  → server returns: {session_token, template_name, ap_cost_per_build}
  → frontend: lock template selection, show "EXIT" button

BUILD IN SESSION (per field click):
  POST /province/{id}/build {"template_id": int, "field_id": int, "session": true}
  → response: {success, ap_remaining, field_id}
  → frontend: mark field on canvas (no reload), update AP counter
  → on fail: mark field red, show error overlay (non-blocking)

DEACTIVATE:
  POST /province/{id}/quickbuild/deactivate
  → reload full province state

SCHNELLABRISS (same pattern):
  POST /province/{id}/quickdemolish/activate
  per-click: POST /province/{id}/demolish/{field_id} {"session": true}
  → refund shown in running total overlay
```

## Endpoints
```
POST /province/{id}/quickbuild/activate   {"template_id": int}
POST /province/{id}/quickbuild/deactivate
POST /province/{id}/quickdemolish/activate
POST /province/{id}/quickdemolish/deactivate
# Actual build/demolish reuse existing endpoints with session=true flag
```

## Validation
- Session auto-expires after 30min inactivity
- AP checked per-click; session continues even if AP runs out (fail gracefully)
- Only one active session per province at a time
- Cannot switch template mid-session (must deactivate first)
