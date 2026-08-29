# Emanager

Emanager is a Codex plugin workflow for turning a plugin idea into an installable, host-verified
delivery. It uses five stages, provenance-aware requirements, vertical tasks, independent reviews,
and resumable evidence.

## Repository layout

- `plugins/emanager/`: the installable Codex plugin
- `marketplace.json`: a local marketplace catalog for the plugin
- `photo-style-replicator/`: the vertical test project used to verify the workflow with Photoshop

## Install locally

From this repository's parent directory:

```text
codex plugin marketplace add ./emanager-open-source
codex plugin add emanager@emanager-open-source
```

For the standard personal marketplace, install from the plugin source with the normal Codex plugin
commands. Start a new task after installation so the skill is loaded into a fresh context.

## Versioning

The plugin manifest in `plugins/emanager/.codex-plugin/plugin.json` is the version source of truth.
Use semantic versions for releases and keep changes in Git history.

## License

MIT. See `LICENSE`.
