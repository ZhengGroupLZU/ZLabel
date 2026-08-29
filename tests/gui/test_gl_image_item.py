from __future__ import annotations

import numpy as np
from pyqtgraph.Qt import QtOpenGL

from zlabel.widgets.gl_image_item import GLImageItem


def test_prepare_texture_data_uses_direct_formats():
    """uint8 RGB/gray/RGBA bypass makeRGBA and upload compact textures."""
    item = GLImageItem(axisOrder="row-major")

    rgb = np.zeros((4, 6, 3), dtype=np.uint8)
    item.setImage(rgb, autoLevels=False, levels=(0, 255))
    data, fmt, pixfmt, channels = item._prepare_texture_data()
    assert channels == 3
    assert fmt == QtOpenGL.QOpenGLTexture.TextureFormat.RGB8_UNorm
    assert pixfmt == QtOpenGL.QOpenGLTexture.PixelFormat.RGB
    assert data.flags["C_CONTIGUOUS"]
    assert data.shape == rgb.shape

    gray = np.zeros((4, 6), dtype=np.uint8)
    item.setImage(gray, autoLevels=False, levels=(0, 255))
    _, fmt, pixfmt, channels = item._prepare_texture_data()
    assert channels == 1
    assert fmt == QtOpenGL.QOpenGLTexture.TextureFormat.R8_UNorm
    assert pixfmt == QtOpenGL.QOpenGLTexture.PixelFormat.Red

    rgba = np.zeros((4, 6, 4), dtype=np.uint8)
    item.setImage(rgba, autoLevels=False, levels=(0, 255))
    _, fmt, pixfmt, channels = item._prepare_texture_data()
    assert channels == 4
    assert fmt == QtOpenGL.QOpenGLTexture.TextureFormat.RGBA8_UNorm
    assert pixfmt == QtOpenGL.QOpenGLTexture.PixelFormat.RGBA


def test_set_mipmap_enabled_invalidates_texture():
    item = GLImageItem()
    assert item._mipmap_enabled is True
    item._texture_image = object()  # pretend a texture is already uploaded
    item.set_mipmap_enabled(False)
    assert item._mipmap_enabled is False
    assert item._texture_image is None

    item.set_mipmap_enabled(False)
    assert item._texture_image is None  # no-op does not invalidate again


def test_offscreen_platform_disables_gl_fast_path():
    """Offscreen (CI/test) environments must fall back to the QPainter path."""
    item = GLImageItem()
    assert item._is_offscreen() is True
