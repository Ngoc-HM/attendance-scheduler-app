# liquid_glass_renderer compatibility layer

`liquid_glass_bar` depends on an Impeller-only renderer that does not support
Windows or web. This local package preserves the renderer API used by the bar
and provides a cross-platform glass fallback with backdrop blur, saturation,
directional specular highlights, and subtle chromatic edge dispersion.
