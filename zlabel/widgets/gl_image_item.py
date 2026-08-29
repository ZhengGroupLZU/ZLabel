"""OpenGL-backed ImageItem for the ZLabel annotation canvas.

The stock pyqtgraph ImageItem uploads a QImage through QPainter on every
repaint.  This subclass keeps the full ImageItem API (setImage, boundingRect,
levels, ...) but, when the GraphicsView viewport is pyqtgraph's OpenGL widget,
uploads the current display array to a persistent QOpenGLTexture and draws a
textured quad with a small shader.  Pan/zoom then only re-draws the GPU texture
instead of re-running CPU downsample / QImage make on the UI thread.

When the viewport is not OpenGL (offscreen tests, export, software rendering)
it falls back to the normal ImageItem QPainter path.
"""

from __future__ import annotations

import os

import numpy as np
from pyqtgraph import functions as fn
from pyqtgraph.graphicsItems.ImageItem import ImageItem
from pyqtgraph.Qt import OpenGLConstants as GLC
from pyqtgraph.Qt import OpenGLHelpers, QtCore, QtGui, QtOpenGL

__all__ = ["GLImageItem"]


class _GLImageState(QtCore.QObject):
    VERT_SRC_COMPAT = """
        attribute vec2 a_position;
        attribute vec2 a_texcoord;
        varying vec2 v_texcoord;
        uniform mat4 u_mvp;
        void main() {
            v_texcoord = a_texcoord;
            gl_Position = u_mvp * vec4(a_position, 0.0, 1.0);
        }
    """

    FRAG_SRC_COMPAT = """
        #ifdef GL_ES
        precision mediump float;
        #endif
        varying vec2 v_texcoord;
        uniform sampler2D u_texture;
        uniform int u_channels;
        void main() {
            vec4 c = texture2D(u_texture, v_texcoord);
            if (u_channels == 1) {
                gl_FragColor = vec4(c.rrr, 1.0);
            } else if (u_channels == 3) {
                gl_FragColor = vec4(c.rgb, 1.0);
            } else {
                gl_FragColor = c;
            }
        }
    """

    VERT_SRC_140 = """
        #version 140
        in vec2 a_position;
        in vec2 a_texcoord;
        out vec2 v_texcoord;
        uniform mat4 u_mvp;
        void main() {
            v_texcoord = a_texcoord;
            gl_Position = u_mvp * vec4(a_position, 0.0, 1.0);
        }
    """

    FRAG_SRC_140 = """
        #version 140
        in vec2 v_texcoord;
        out vec4 fragColor;
        uniform sampler2D u_texture;
        uniform int u_channels;
        void main() {
            vec4 c = texture(u_texture, v_texcoord);
            if (u_channels == 1) {
                fragColor = vec4(c.rrr, 1.0);
            } else if (u_channels == 3) {
                fragColor = vec4(c.rgb, 1.0);
            } else {
                fragColor = c;
            }
        }
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.context = None
        self.texture = None
        self.vbo = None
        self.m_vao = QtOpenGL.QOpenGLVertexArrayObject(self)
        self.program = None
        self._texture_format = None
        self._vbo_key = None
        self._channels = 4

    def setup(self, context, glwidget):
        if self.context is context:
            return
        if self.context is not None:
            try:
                self.context.aboutToBeDestroyed.disconnect(self.cleanup)
            except RuntimeError:
                pass
            self.cleanup()
        self.context = context
        self.context.aboutToBeDestroyed.connect(self.cleanup)

        is_es = context.isOpenGLES()
        version = context.format().version()
        if (not is_es and version >= (3, 1)) or (is_es and version >= (3, 0)):
            vert = self.VERT_SRC_140
            frag = self.FRAG_SRC_140
        else:
            vert = self.VERT_SRC_COMPAT
            frag = self.FRAG_SRC_COMPAT

        program = QtOpenGL.QOpenGLShaderProgram()
        if not program.addShaderFromSourceCode(QtOpenGL.QOpenGLShader.ShaderTypeBit.Vertex, vert):
            raise RuntimeError(program.log())
        if not program.addShaderFromSourceCode(QtOpenGL.QOpenGLShader.ShaderTypeBit.Fragment, frag):
            raise RuntimeError(program.log())
        program.bindAttributeLocation("a_position", 0)
        program.bindAttributeLocation("a_texcoord", 1)
        if not program.link():
            raise RuntimeError(program.log())
        self.program = program

        self.vbo = QtOpenGL.QOpenGLBuffer(QtOpenGL.QOpenGLBuffer.Type.VertexBuffer)
        self.vbo.create()
        self.m_vao.create()

    def cleanup(self):
        glwidget = self.parent()
        try:
            glwidget.makeCurrent()
            for obj in (self.texture, self.vbo, self.m_vao):
                if obj is not None:
                    try:
                        obj.destroy()
                    except RuntimeError:
                        pass
            if self.program is not None:
                try:
                    self.program.release()
                    self.program.removeAllShaders()
                    self.program.setParent(None)
                    self.program.deleteLater()
                except RuntimeError:
                    pass
        finally:
            try:
                glwidget.doneCurrent()
            except RuntimeError:
                pass
        self.texture = None
        self.vbo = None
        self.m_vao = QtOpenGL.QOpenGLVertexArrayObject(self)
        self.program = None
        self.context = None
        self._texture_format = None
        self._vbo_key = None
        self._channels = 4

    def upload_texture(self, data: np.ndarray, texture_format, pixel_format, channels: int):
        h, w = data.shape[:2]
        if (
            self.texture is None
            or self.texture.width() != w
            or self.texture.height() != h
            or self._texture_format != texture_format
        ):
            if self.texture is not None:
                self.texture.destroy()
            self.texture = QtOpenGL.QOpenGLTexture(QtOpenGL.QOpenGLTexture.Target.Target2D)
            self.texture.setFormat(texture_format)
            self.texture.setSize(w, h)
            self.texture.setAutoMipMapGenerationEnabled(True)
            self.texture.allocateStorage()
            self.texture.setMinMagFilters(
                QtOpenGL.QOpenGLTexture.Filter.LinearMipMapLinear,
                QtOpenGL.QOpenGLTexture.Filter.Linear,
            )
            self.texture.setWrapMode(QtOpenGL.QOpenGLTexture.WrapMode.ClampToEdge)
            self._texture_format = texture_format

        glfn = self.parent().getFunctions()
        # RGB/R8 rows are not always 4-byte aligned (e.g. 2560-long pyramid
        # levels with odd widths); default GL_UNPACK_ALIGNMENT=4 can read past
        # the row and crash the process on some drivers.
        gl_unpack_alignment = 0x0CF5  # GL_UNPACK_ALIGNMENT (missing from pyqtgraph constants)
        glfn.glPixelStorei(gl_unpack_alignment, 1)
        try:
            self.texture.setData(pixel_format, QtOpenGL.QOpenGLTexture.PixelType.UInt8, data)
        finally:
            glfn.glPixelStorei(gl_unpack_alignment, 4)
        self.texture.generateMipMaps()
        self._channels = channels

    def upload_vertices(self, height: int, width: int):
        key = (width, height)
        if self._vbo_key == key:
            return
        vertices = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                width,
                0.0,
                1.0,
                0.0,
                width,
                height,
                1.0,
                1.0,
                0.0,
                height,
                0.0,
                1.0,
            ],
            dtype=np.float32,
        )
        self.vbo.bind()
        self.vbo.allocate(vertices, vertices.nbytes)
        self.vbo.release()
        self._vbo_key = key

    def draw(self, glwidget, mvp) -> None:
        glfn = glwidget.getFunctions()
        program = self.program
        program.bind()
        program.setUniformValue("u_mvp", mvp)
        program.setUniformValue("u_texture", 0)
        program.setUniformValue("u_channels", self._channels)

        self.m_vao.bind()
        self.texture.bind(0)
        self.vbo.bind()
        stride = 4 * 4  # interleaved vec2 position + vec2 texcoord
        program.enableAttributeArray(0)
        program.setAttributeBuffer(0, GLC.GL_FLOAT, 0, 2, stride)
        program.enableAttributeArray(1)
        program.setAttributeBuffer(1, GLC.GL_FLOAT, 2 * 4, 2, stride)

        glfn.glDrawArrays(GLC.GL_TRIANGLE_STRIP, 0, 4)

        program.disableAttributeArray(1)
        program.disableAttributeArray(0)
        self.vbo.release()
        self.texture.release()
        program.release()
        self.m_vao.release()


class GLImageItem(ImageItem):
    """ImageItem with a persistent OpenGL texture fast path for GL viewports."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._gl_state: _GLImageState | None = None
        self._texture_image = None
        self._texture_levels_key = None
        self._texture_lut = None

    def setImage(self, image=None, *args, **kwargs):
        super().setImage(image, *args, **kwargs)
        self._texture_image = None

    def setLevels(self, levels, update: bool = True):
        super().setLevels(levels, update=update)
        self._texture_image = None

    def setLookupTable(self, lut, update: bool = True):
        super().setLookupTable(lut, update=update)
        self._texture_image = None

    def _prepare_texture_data(self) -> tuple[np.ndarray, object, object, int]:
        img = self.image
        levels = self.levels
        lut = self.lut

        def identity_u8() -> bool:
            if img is None or img.dtype != np.uint8 or lut is not None:
                return False
            if levels is None:
                return True
            try:
                return float(levels[0]) == 0.0 and float(levels[1]) == 255.0
            except (TypeError, ValueError, IndexError):
                return False

        if identity_u8():
            data = np.ascontiguousarray(img)
            if img.ndim == 2:
                return data, QtOpenGL.QOpenGLTexture.TextureFormat.R8_UNorm, QtOpenGL.QOpenGLTexture.PixelFormat.Red, 1
            if img.ndim == 3 and img.shape[2] == 3:
                return (
                    data,
                    QtOpenGL.QOpenGLTexture.TextureFormat.RGB8_UNorm,
                    QtOpenGL.QOpenGLTexture.PixelFormat.RGB,
                    3,
                )
            if img.ndim == 3 and img.shape[2] == 4:
                return (
                    data,
                    QtOpenGL.QOpenGLTexture.TextureFormat.RGBA8_UNorm,
                    QtOpenGL.QOpenGLTexture.PixelFormat.RGBA,
                    4,
                )

        rgba, _ = fn.makeRGBA(img, levels=levels, lut=lut)
        return (
            np.ascontiguousarray(rgba),
            QtOpenGL.QOpenGLTexture.TextureFormat.RGBA8_UNorm,
            QtOpenGL.QOpenGLTexture.PixelFormat.RGBA,
            4,
        )

    def _levels_key(self):
        if self.levels is None:
            return None
        try:
            return (float(self.levels[0]), float(self.levels[1]))
        except (TypeError, ValueError, IndexError):
            return self.levels

    def _sync_texture(self, widget) -> None:
        if (
            self._texture_image is self.image
            and self._texture_levels_key == self._levels_key()
            and self._texture_lut is self.lut
        ):
            return

        if self._gl_state is None:
            self._gl_state = _GLImageState(widget)
        self._gl_state.setup(widget.context(), widget)

        data, texture_format, pixel_format, channels = self._prepare_texture_data()
        self._gl_state.upload_texture(data, texture_format, pixel_format, channels)
        h, w = self.image.shape[:2]
        self._gl_state.upload_vertices(h, w)

        self._texture_image = self.image
        self._texture_levels_key = self._levels_key()
        self._texture_lut = self.lut

    def _paintGL(self, painter, widget) -> None:
        painter.beginNativePainting()
        try:
            self._sync_texture(widget)
            proj = QtGui.QMatrix4x4()
            proj.ortho(widget.rect())
            tr = QtGui.QMatrix4x4(self.sceneTransform())
            mvp = proj * tr
            self._gl_state.draw(widget, mvp)
        finally:
            painter.endNativePainting()

    @staticmethod
    def _is_offscreen() -> bool:
        if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
            return True
        app = QtCore.QCoreApplication.instance()
        return app is not None and app.platformName() == "offscreen"

    def paint(self, painter, opt, widget):
        use_gl = isinstance(widget, OpenGLHelpers.GraphicsViewGLWidget) and not self._is_offscreen()
        if use_gl:
            if self.image is None:
                return
            try:
                self._paintGL(painter, widget)
            except Exception:
                # If native GL drawing fails (driver/context issue), fall back to
                # the normal QImage/QPainter path used by stock pyqtgraph.
                super().paint(painter, opt, widget)
            return
        super().paint(painter, opt, widget)
