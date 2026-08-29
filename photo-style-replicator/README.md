# Photo Style Replicator (test project)

This is the vertical test project for the `emanager` workflow. It accepts a reference image and a
target image, writes an explainable JSON analysis, emits a Photoshop JSX adjustment script, and can
execute that script through the local `Photoshop.Application` COM interface.

```text
python photo_style_replicator.py reference.jpg target.jpg \
  --report analysis.json --output styled.jpg
```

Use `--no-photoshop` to inspect the report and JSX without touching Photoshop. The tool estimates
global tone, palette, saturation, temperature, and likely adjustment techniques. It cannot recover
the exact layer history of a flattened image, so the output is an approximation that requires review.
