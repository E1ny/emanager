# Emanager

Emanager is a global Codex skill plugin for building other plugins through an evidence-first
five-stage workflow:

1. Plugin Spike Builder
2. Interaction Runtime Design
3. Plugin Dive Planner
4. Plugin Builder
5. Plugin Checker

The workflow keeps durable progress in `.plugin-manager/state.json`. The companion
`scripts/plugin_manager.py` command records requirements, tasks, findings, gates, and independent
host verification.

The plugin intentionally keeps real host interaction inside the final checker stage. Development
reviews use fresh contexts and every delivery claim requires evidence.
