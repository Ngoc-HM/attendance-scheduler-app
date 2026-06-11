# liquid_glass_renderer compatibility layer

`liquid_glass_bar` depends on an Impeller-only renderer that does not support
Windows or web. This local package preserves the renderer API used by the bar
and provides a cross-platform blur fallback without shader assets.
