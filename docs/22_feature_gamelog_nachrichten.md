# Feature: Gamelog, Benachrichtigungen & Spieler-Nachrichten

## Source (FAQ 2.4)
- Gamelog: important events on map, player-specific + system messages
- Configurable: which message types to show, how many entries
- Member feature: search by player name or keyword
- Player-to-player messaging: direct messages between players

## Data Models
```python
GameLogEntry: id, event_type, province_id, player_id, message(str),
              visibility("player"/"all"/"admin"), created_at, is_system(bool)

# Event types: PROVINCE_COLONIZED, WAR_DECLARED, REVOLT, HUNGER_IN_XH,
#              BUILDING_BUILT, DEPOSIT_FOUND, ROUTE_ARRIVED, COMBAT_OUTCOME, ...

PlayerMessage: id, sender_id, recipient_id, subject(str), body(str),
               read(bool), sent_at, deleted_sender(bool), deleted_recipient(bool)

PlayerNotificationSettings: player_id, show_war(bool), show_trade(bool),
                             show_system(bool), max_entries(int)
```

## Core Logic
```
LOG EVENT (called from all feature modules):
  GameLogEntry.create(
    event_type=..., province_id=..., player_id=...,
    message=build_message(event_type, payload),
    visibility=determine_visibility(event_type)
  )

VISIBILITY RULES:
  player events (own province): visibility="player"
  diplomacy/war: visibility="all"
  system (cleanup, reset): visibility="admin"

NOTIFICATION FILTER:
  GET /gamelog → filter by PlayerNotificationSettings
  default: last 50 entries, all types

SEARCH (all players):
  full-text search on message field
  filter by player_id, event_type, date range

PLAYER MESSAGE:
  send: create PlayerMessage
  read: set read=True, trigger in-game notification badge
  delete: set deleted_sender/recipient=True (soft delete)
  reply: new message with subject "Re: {original.subject}"
```

## Endpoints
```
GET  /gamelog?type=&player=&limit=50 → filtered log entries
GET  /gamelog/search?q={term} → full-text search
POST /player/{id}/notification-settings → update filter prefs

POST /messages/send {"recipient_id":int, "subject":str, "body":str}
GET  /messages/inbox → unread + recent messages
GET  /messages/{id} → full message + mark as read
DELETE /messages/{id} → soft delete
GET  /messages/unread-count → badge count for UI
```

## Validation
- Message body max 2000 chars
- Cannot message self
- Deleted messages hidden from both sides only when both mark deleted
- GameLog max_entries configurable 10-500, default 50
