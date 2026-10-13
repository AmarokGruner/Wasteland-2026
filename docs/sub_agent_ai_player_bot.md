# 🤖 Adaptive AI Player Bot Sub-Agent

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Rolle und Spezialisierung

**Adaptive AI Player Bot** ist ein spezialisierter Sub-Agent für:
- Simulation eines realen Spielers im Live-Browser
- Adaptive Lernfähigkeiten (passt Verhalten basierend auf Erfahrungen an)
- Testen von Spielmechaniken unter realistischen Bedingungen
- Erkennen von Balance-Problemen und UX-Schwachstellen
- Langzeit-Simulationen (Tage/Wochen von Spielzeit komprimieren)

---

## 🎯 Aufgaben

### Player Simulation
- Realistisches Spieler-Verhalten nachahmen (Entscheidungen, Fehler, Lernkurve)
- Ressourcen-Management simulieren (Prioritäten setzen, Kompromisse eingehen)
- Gebäude-Kombinationen testen und optimieren
- Wirtschaftliche Strategien entwickeln (Handel, Produktion, Lagerung)

### Adaptive Lernfähigkeiten
- **Reinforcement Learning:** Belohnungen/Strafen basierend auf Spielerfolg
- **Pattern Recognition:** Wiederkehrende Muster in Spielmechaniken erkennen
- **Strategy Evolution:** Erfolgreiche Strategien beibehalten, erfolglose anpassen
- **Exploration vs. Exploitation:** Neue Gebäude ausprobieren vs. bewährte nutzen

### Live System Testing
- Echte API-Endpunkte im Browser testen (kein Mocking)
- Real-Time Updates und Server-Tick Engine validieren
- Multi-Player Interaktionen simulieren (Handel, Diplomatie)
- Edge Cases und Grenzwerte testen

### Balance & UX Testing
- Spielbalance über längere Zeiträume messen (MIPS, Ressourcen)
- UX-Schwachstellen identifizieren (zu komplexe Menüs, unklare Feedback)
- Performance-Probleme unter Last erkennen (viele Gebäude, viele Einheiten)
- Accessibility für verschiedene Spielertypen prüfen

---

## 🧠 Adaptive KI Architektur

### 1. State Representation
```javascript
class GameState {
    constructor() {
        this.province = {
            mips: 0,
            population: 0,
            buildings: [],
            resources: {},
            units: []
        };
        this.economy = {
            productionRate: {},
            consumptionRate: {},
            tradeRoutes: [],
            stockpile: {}
        };
        this.history = {
            decisions: [],
            outcomes: [],
            lessonsLearned: []
        };
    }
}
```

### 2. Decision Engine (Q-Learning)
```javascript
class DecisionEngine {
    constructor() {
        this.qTable = {};  // State -> Action Values
        this.learningRate = 0.1;
        this.discountFactor = 0.95;
        this.explorationRate = 0.3;  // ε-greedy
    }

    getStateKey(state) {
        return JSON.stringify({
            mips: Math.floor(state.mips / 100),
            buildingCount: state.buildings.length,
            resourceTypes: Object.keys(state.resources).length
        });
    }

    chooseAction(state, availableActions) {
        const stateKey = this.getStateKey(state);
        
        // Exploration: Zufällige Aktion mit Wahrscheinlichkeit ε
        if (Math.random() < this.explorationRate) {
            return availableActions[Math.floor(Math.random() * availableActions.length)];
        }

        // Exploitation: Beste bekannte Aktion
        if (!this.qTable[stateKey]) {
            this.qTable[stateKey] = {};
        }

        let bestAction = availableActions[0];
        let maxValue = -Infinity;

        for (const action of availableActions) {
            const value = this.qTable[stateKey][action] || 0;
            if (value > maxValue) {
                maxValue = value;
                bestAction = action;
            }
        }

        return bestAction;
    }

    updateQValue(state, action, reward, nextState) {
        const stateKey = this.getStateKey(state);
        const nextStateKey = this.getStateKey(nextState);

        if (!this.qTable[stateKey]) {
            this.qTable[stateKey] = {};
        }
        if (!this.qTable[nextStateKey]) {
            this.qTable[nextStateKey] = {};
        }

        const currentValue = this.qTable[stateKey][action] || 0;
        const maxNextValue = Math.max(...Object.values(this.qTable[nextStateKey]));

        // Q-Learning Update Rule
        const newQValue = currentValue + this.learningRate * (
            reward + this.discountFactor * maxNextValue - currentValue
        );

        this.qTable[stateKey][action] = newQValue;

        // Lernen aus Erfahrung speichern
        this.history.lessonsLearned.push({
            state: stateKey,
            action: action,
            reward: reward,
            timestamp: Date.now()
        });
    }

    // Strategie anpassen basierend auf langfristigen Ergebnissen
    adaptStrategy(outcome) {
        if (outcome.success) {
            // Erfolgreiche Aktionen verstärken
            this.learningRate = Math.min(this.learningRate * 1.05, 0.2);
            this.explorationRate = Math.max(this.explorationRate * 0.98, 0.05);
        } else {
            // Misserfolg: Mehr Exploration
            this.explorationRate = Math.min(this.explorationRate * 1.1, 0.5);
        }
    }
}
```

### 3. Behavior Profiles (Verschiedene Spielertypen)
```javascript
const PLAYER_PROFILES = {
    conservative: {  // Vorsichtiger Spieler
        riskTolerance: 0.2,
        priority: ['food', 'water', 'defense'],
        expansionRate: 0.5,
        description: 'Baut langsam, priorisiert Sicherheit'
    },
    aggressive: {  // Aggressiver Spieler
        riskTolerance: 0.8,
        priority: ['military', 'expansion', 'economy'],
        expansionRate: 1.5,
        description: 'Baut schnell, riskant, expansiv'
    },
    trader: {  // Handels-Spezialist
        riskTolerance: 0.5,
        priority: ['trade', 'resources', 'diplomacy'],
        expansionRate: 0.8,
        description: 'Fokussiert auf Handel und Wirtschaft'
    },
    explorer: {  // Entdecker
        riskTolerance: 0.6,
        priority: ['exploration', 'vorkommen', 'science'],
        expansionRate: 1.0,
        description: 'Sucht neue Gebiete und Ressourcen'
    }
};
```

---

## 🔧 Typische Workflows

### 1. AI Bot erstellen und starten

```python
# delegate_task Beispiel
delegate_task(
    tasks=[{
        "goal": "Erstelle adaptiven AI Player Bot für Spielmechanik-Tests",
        "context": "Bot soll als realer Spieler agieren, Gebäude bauen, Ressourcen verwalten und sich an verschiedene Spielstile anpassen",
        "output_schema": {
            "type": "object",
            "properties": {
                "bot_class": {"type": "string"},  # Python/JS Code
                "behavior_profiles": {"type": "array", "items": {"type": "string"}},
                "test_scenarios": {"type": "array", "items": {"type": "string"}},
                "learning_mechanisms": {"type": "array", "items": {"type": "string"}}
            }
        }
    }]
)
```

### 2. AI Bot Implementation (Beispiel Output)

```javascript
// js/ai-player-bot.js - Adaptiver AI Player Bot

class AdaptivePlayerBot {
    constructor(profile = 'conservative') {
        this.profile = PLAYER_PROFILES[profile] || PLAYER_PROFILES.conservative;
        this.decisionEngine = new DecisionEngine();
        this.gameState = new GameState();
        this.sessionId = `bot_${profile}_${Date.now()}`;
        
        // Bot Konfiguration
        this.config = {
            maxBuildingsPerTick: 3,
            resourceThreshold: 0.2,  // Baue nur wenn >20% Ressourcen
            panicThreshold: 0.1,     // Panik bei <10% Ressourcen
            learningEpoch: 10        // Alle 10 Ticks adaptieren
        };
    }

    // Haupt-Schleife: Wird alle Server-Ticks aufgerufen
    async executeTick(apiClient) {
        // 1. Aktuellen Spielzustand abrufen
        const currentState = await this.fetchGameState(apiClient);
        this.gameState = currentState;

        // 2. Verfügbare Aktionen ermitteln
        const availableActions = this.getAvailableActions(currentState);

        // 3. Entscheidung treffen (Q-Learning)
        const action = this.decisionEngine.chooseAction(
            currentState, 
            availableActions
        );

        // 4. Aktion ausführen
        const result = await this.executeAction(apiClient, action);

        // 5. Neue Situation evaluieren
        const nextState = await this.fetchGameState(apiClient);
        
        // 6. Belohnung berechnen und Q-Table updaten
        const reward = this.calculateReward(currentState, nextState, action);
        this.decisionEngine.updateQValue(
            currentState, 
            action, 
            reward, 
            nextState
        );

        // 7. Strategie adaptieren (alle learningEpoch Ticks)
        if (this.tickCount % this.config.learningEpoch === 0) {
            this.decisionEngine.adaptStrategy(result);
        }

        this.tickCount++;
        
        return { action, result, reward };
    }

    // Verfügbare Aktionen basierend auf Spielzustand
    getAvailableActions(state) {
        const actions = [];

        // Gebäude bauen (wenn Ressourcen vorhanden)
        if (state.mips > 50) {
            actions.push('build_farm');
            actions.push('build_house');
            if (state.mips > 200) {
                actions.push('build_factory');
            }
        }

        // Ressourcen sammeln
        if (state.population > 0) {
            actions.push('gather_wood');
            actions.push('gather_stone');
        }

        // Einheiten rekrutieren
        if (state.mips > 100 && state.population < 50) {
            actions.push('recruit_scout');
        }

        // Handel
        if (state.tradeRoutes.length > 0) {
            actions.push('trade_resources');
        }

        return actions;
    }

    // Belohnungsfunktion (Fitness Function)
    calculateReward(currentState, nextState, action) {
        let reward = 0;

        // Positive Belohnungen
        if (nextState.mips > currentState.mips) {
            reward += (nextState.mips - currentState.mips) * 0.1;
        }
        if (nextState.buildings.length > currentState.buildings.length) {
            reward += 10;  // Neues Gebäude gebaut
        }
        if (nextState.population > currentState.population) {
            reward += 5;   // Bevölkerung gewachsen
        }

        // Negative Bestrafungen
        if (nextState.resources.food < this.config.panicThreshold) {
            reward -= 50;  // Hungersnot!
        }
        if (nextState.resources.water < this.config.panicThreshold) {
            reward -= 50;  // Wassermangel!
        }

        // Strategie-spezifische Belohnungen
        if (this.profile === 'aggressive' && nextState.buildings.length > currentState.buildings.length * 1.2) {
            reward += 20;  // Schnelles Wachstum belohnen
        }
        if (this.profile === 'conservative' && nextState.resources.food > currentState.resources.food * 1.5) {
            reward += 15;  // Stabile Nahrungsvorräte belohnen
        }

        return reward;
    }

    async executeAction(apiClient, action) {
        switch (action) {
            case 'build_farm':
                return await apiClient.post('/province/build', { type: 'farm' });
            case 'build_house':
                return await apiClient.post('/province/build', { type: 'house' });
            case 'gather_wood':
                return await apiClient.post('/province/gather', { resource: 'wood' });
            case 'recruit_scout':
                return await apiClient.post('/province/recruit', { type: 'scout' });
            case 'trade_resources':
                return await apiClient.post('/province/trade', { route: 1 });
            default:
                return { success: false, error: 'Unknown action' };
        }
    }

    async fetchGameState(apiClient) {
        const response = await apiClient.get('/province/current');
        return new GameState(response.data);
    }

    // Bot Status und Lernfortschritt exportieren
    getBotStatus() {
        return {
            profile: this.profile,
            sessionId: this.sessionId,
            tickCount: this.tickCount,
            qTableSize: Object.keys(this.decisionEngine.qTable).length,
            lessonsLearned: this.decisionEngine.history.lessonsLearned.length,
            explorationRate: this.decisionEngine.explorationRate,
            currentStrategy: {
                riskTolerance: this.profile.riskTolerance,
                priority: this.profile.priority
            }
        };
    }
}

export default AdaptivePlayerBot;
```

### 3. Bot Management API (Backend)

```python
# app/api/bot_management.py - AI Bot Verwaltung

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/admin/bots", tags=["AI Bots"])

@router.post("/create")
async def create_bot(
    profile: str = "conservative",
    db: Session = Depends(get_db)
):
    """Erstellt einen neuen AI Player Bot"""
    bot_id = f"bot_{profile}_{uuid4()}"
    
    bot_config = {
        "id": bot_id,
        "profile": profile,
        "status": "active",
        "created_at": datetime.utcnow(),
        "tick_count": 0,
        "q_table_size": 0,
        "lessons_learned": 0
    }
    
    # Bot Konfiguration in Datenbank speichern
    db.execute(
        "INSERT INTO ai_bots (id, config) VALUES (:id, :config)",
        {"id": bot_id, "config": json.dumps(bot_config)}
    )
    db.commit()
    
    return {"bot_id": bot_id, "profile": profile, "status": "created"}

@router.get("/status/{bot_id}")
async def get_bot_status(bot_id: str, db: Session = Depends(get_db)):
    """Bot Status und Lernfortschritt abrufen"""
    bot = db.execute(
        "SELECT config FROM ai_bots WHERE id = :id",
        {"id": bot_id}
    ).fetchone()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot nicht gefunden")
    
    return json.loads(bot.config)

@router.post("/run-tick/{bot_id}")
async def run_bot_tick(bot_id: str, db: Session = Depends(get_db)):
    """Führt einen Tick für den Bot aus"""
    bot_config = db.execute(
        "SELECT config FROM ai_bots WHERE id = :id",
        {"id": bot_id}
    ).fetchone()
    
    if not bot_config:
        raise HTTPException(status_code=404, detail="Bot nicht gefunden")
    
    bot_data = json.loads(bot_config.config)
    
    # Bot Logik ausführen (vereinfacht für Backend)
    # In Realität: Bot wird im Browser simuliert
    
    bot_data["tick_count"] += 1
    db.execute(
        "UPDATE ai_bots SET config = :config WHERE id = :id",
        {"id": bot_id, "config": json.dumps(bot_data)}
    )
    db.commit()
    
    return {"bot_id": bot_id, "tick_count": bot_data["tick_count"]}
```

---

## 📊 Output Schema

### Bot Creation Output
```json
{
  "bot_id": "bot_conservative_a1b2c3d4",
  "profile": "conservative",
  "status": "created",
  "config": {
    "riskTolerance": 0.2,
    "priority": ["food", "water", "defense"],
    "expansionRate": 0.5
  }
}
```

### Bot Status Output
```json
{
  "id": "bot_conservative_a1b2c3d4",
  "profile": "conservative",
  "status": "active",
  "tickCount": 150,
  "qTableSize": 42,
  "lessonsLearned": 87,
  "explorationRate": 0.15,
  "currentStrategy": {
    "riskTolerance": 0.2,
    "priority": ["food", "water", "defense"]
  },
  "recentDecisions": [
    {
      "tick": 148,
      "action": "build_farm",
      "reward": 12.5,
      "outcome": "success"
    },
    {
      "tick": 149,
      "action": "gather_wood",
      "reward": 5.0,
      "outcome": "success"
    }
  ]
}
```

---

## ⚠️ Wichtige Hinweise

1. **Echte API verwenden** - Bot sollte echte Endpunkte aufrufen (kein Mocking)
2. **Rate Limiting beachten** - Nicht zu viele Requests pro Sekunde
3. **Session Management** - Bot Sessions isoliert halten (eigene Spieler-Accounts)
4. **Performance** - Q-Table kann groß werden (Regularisierung anwenden)
5. **Ethik** - Bot Verhalten transparent dokumentieren

---

## 🎯 Wann Adaptive AI Player Bot einsetzen?

- ✅ Spielbalance über längere Zeiträume testen
- ✅ UX-Schwachstellen unter realistischen Bedingungen erkennen
- ✅ Edge Cases und Grenzwerte explorieren
- ✅ Multi-Player Interaktionen simulieren (Handel, Diplomatie)
- ✅ Langzeit-Simulationen (Tage/Wochen komprimiert)
- ❌ Schnelle Unit Tests (testing-engineer)
- ❌ Frontend UI Tests (browser-testing-engineer)

---

## 📁 Bot Directory Struktur

```
js/ai-bots/
├── bot-base.js              # Basis-Klasse für alle Bots
├── decision-engine.js       # Q-Learning Engine
├── game-state.js            # State Representation
├── player-profiles.js       # Verschiedene Spielertypen
├── bot-manager.js           # Bot Verwaltung (Start/Stop)
└── bot-dashboard.html       # Admin UI für Bot Monitoring

tests/ai-bots/
├── bot-behavior.spec.js     # Verhaltenstests
├── learning-convergence.spec.js  # Lernkonvergenz testen
└── balance-testing.spec.js  # Balance-Tests mit Bots

app/api/
├── bot_management.py        # Bot CRUD Endpunkte
└── bot_simulation.py        # Backend Simulation Logic
```

---

**Adaptive AI Player Bot simuliert reale Spieler und testet Spielmechaniken unter realistischen, langfristigen Bedingungen!**
