import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'

// ── SimpleHeat ───────────────────────────────────────────────────────────
// A tiny JavaScript library for drawing heatmaps with Canvas
// (c) 2014, Vladimir Agafonkin
class SimpleHeat {
  _canvas: HTMLCanvasElement
  _ctx: CanvasRenderingContext2D
  _width: number
  _height: number
  _max: number = 1
  _data: [number, number, number][] = []
  _circle?: HTMLCanvasElement
  _r: number = 0
  _grad?: Uint8ClampedArray

  defaultRadius = 25
  defaultGradient: Record<number, string> = {
    0.4: 'blue',
    0.6: 'cyan',
    0.7: 'lime',
    0.8: 'yellow',
    1.0: 'red'
  }

  constructor(canvas: HTMLCanvasElement) {
    this._canvas = canvas
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Could not get 2D context')
    this._ctx = ctx
    this._width = canvas.width
    this._height = canvas.height
    this.clear()
  }

  data(data: [number, number, number][]) {
    this._data = data
    return this
  }

  max(max: number) {
    this._max = max
    return this
  }

  add(point: [number, number, number]) {
    this._data.push(point)
    return this
  }

  clear() {
    this._data = []
    return this
  }

  radius(r: number, blur = 15) {
    const circle = (this._circle = document.createElement('canvas'))
    const ctx = circle.getContext('2d')
    if (!ctx) return this

    const r2 = (this._r = r + blur)
    circle.width = circle.height = r2 * 2

    ctx.shadowOffsetX = ctx.shadowOffsetY = 200
    ctx.shadowBlur = blur
    ctx.shadowColor = 'black'

    ctx.beginPath()
    ctx.arc(r2 - 200, r2 - 200, r, 0, Math.PI * 2, true)
    ctx.closePath()
    ctx.fill()

    return this
  }

  gradient(grad: Record<number, string>) {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return this

    canvas.width = 1
    canvas.height = 256

    const gradient = ctx.createLinearGradient(0, 0, 0, 256)
    for (const i in grad) {
      gradient.addColorStop(parseFloat(i), grad[i])
    }

    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, 1, 256)

    this._grad = ctx.getImageData(0, 0, 1, 256).data

    return this
  }

  draw(minOpacity?: number) {
    if (!this._circle) this.radius(this.defaultRadius)
    if (!this._grad) this.gradient(this.defaultGradient)

    const ctx = this._ctx
    ctx.clearRect(0, 0, this._width, this._height)

    for (let i = 0, len = this._data.length; i < len; i++) {
      const p = this._data[i]
      ctx.globalAlpha = Math.max(p[2] / this._max, minOpacity || 0.05)
      ctx.drawImage(this._circle!, p[0] - this._r, p[1] - this._r)
    }

    const colored = ctx.getImageData(0, 0, this._width, this._height)
    this._colorize(colored.data, this._grad!)
    ctx.putImageData(colored, 0, 0)

    return this
  }

  _colorize(pixels: Uint8ClampedArray, gradient: Uint8ClampedArray) {
    for (let i = 3, len = pixels.length; i < len; i += 4) {
      const alpha = pixels[i] * 4
      if (alpha) {
        pixels[i - 3] = gradient[alpha]
        pixels[i - 2] = gradient[alpha + 1]
        pixels[i - 1] = gradient[alpha + 2]
      }
    }
  }
}

// ── HeatLayer ────────────────────────────────────────────────────────────
// Leaflet.heat, a tiny and fast heatmap plugin for Leaflet
// (c) 2014, Vladimir Agafonkin
const LeafletHeatLayer = (L.Layer ? L.Layer : (L as any).Class).extend({
  initialize: function (latlngs: any[], options: any) {
    this._latlngs = latlngs
    L.setOptions(this, options)
  },

  setLatLngs: function (latlngs: any[]) {
    this._latlngs = latlngs
    return this.redraw()
  },

  addLatLng: function (latlng: any) {
    this._latlngs.push(latlng)
    return this.redraw()
  },

  setOptions: function (options: any) {
    L.setOptions(this, options)
    if (this._heat) {
      this._updateOptions()
    }
    return this.redraw()
  },

  redraw: function () {
    if (this._heat && !this._frame && !this._map._animating) {
      this._frame = L.Util.requestAnimFrame(this._redraw, this)
    }
    return this
  },

  onAdd: function (map: any) {
    this._map = map

    if (!this._canvas) {
      this._initCanvas()
    }

    if (this.options.pane) {
      this.getPane().appendChild(this._canvas)
    } else {
      map._panes.overlayPane.appendChild(this._canvas)
    }

    map.on('moveend', this._reset, this)

    if (map.options.zoomAnimation && L.Browser.any3d) {
      map.on('zoomanim', this._animateZoom, this)
    }

    this._reset()
  },

  onRemove: function (map: any) {
    if (this.options.pane) {
      this.getPane().removeChild(this._canvas)
    } else {
      map.getPanes().overlayPane.removeChild(this._canvas)
    }

    map.off('moveend', this._reset, this)

    if (map.options.zoomAnimation) {
      map.off('zoomanim', this._animateZoom, this)
    }
  },

  addTo: function (map: any) {
    map.addLayer(this)
    return this
  },

  _initCanvas: function () {
    const canvas = (this._canvas = L.DomUtil.create(
      'canvas',
      'leaflet-heatmap-layer leaflet-layer'
    ))

    const originProp = L.DomUtil.testProp([
      'transformOrigin',
      'WebkitTransformOrigin',
      'msTransformOrigin'
    ])
    if (originProp && typeof originProp === 'string') {
      canvas.style[originProp as any] = '50% 50%'
    }

    const size = this._map.getSize()
    canvas.width = size.x
    canvas.height = size.y

    const animated = this._map.options.zoomAnimation && L.Browser.any3d
    L.DomUtil.addClass(canvas, 'leaflet-zoom-' + (animated ? 'animated' : 'hide'))

    this._heat = new SimpleHeat(canvas)
    this._updateOptions()
  },

  _updateOptions: function () {
    this._heat.radius(
      this.options.radius || this._heat.defaultRadius,
      this.options.blur
    )

    if (this.options.gradient) {
      this._heat.gradient(this.options.gradient)
    }
    if (this.options.max) {
      this._heat.max(this.options.max)
    }
  },

  _reset: function () {
    const topLeft = this._map.containerPointToLayerPoint([0, 0])
    L.DomUtil.setPosition(this._canvas, topLeft)

    const size = this._map.getSize()

    if (this._heat._width !== size.x) {
      this._canvas.width = this._heat._width = size.x
    }
    if (this._heat._height !== size.y) {
      this._canvas.height = this._heat._height = size.y
    }

    this._redraw()
  },

  _redraw: function () {
    if (!this._map) return
    const r = this._heat._r
    const size = this._map.getSize()
    const bounds = new L.Bounds(L.point([-r, -r]), size.add([r, r]))

    const max = this.options.max === undefined ? 1 : this.options.max
    const maxZoom =
      this.options.maxZoom === undefined
        ? this._map.getMaxZoom()
        : this.options.maxZoom
    const v =
      1 / Math.pow(2, Math.max(0, Math.min(maxZoom - this._map.getZoom(), 12)))
    const cellSize = r / 2
    const grid: any[] = []
    const panePos = this._map._getMapPanePos()
    const offsetX = panePos.x % cellSize
    const offsetY = panePos.y % cellSize

    for (let i = 0, len = this._latlngs.length; i < len; i++) {
      const latlng = this._latlngs[i]
      const point = this._map.latLngToContainerPoint(latlng)
      if (bounds.contains(point)) {
        const xCell = Math.floor((point.x - offsetX) / cellSize) + 2
        const yCell = Math.floor((point.y - offsetY) / cellSize) + 2

        const alt =
          latlng.alt !== undefined
            ? latlng.alt
            : latlng[2] !== undefined
            ? +latlng[2]
            : 1
        const intensity = alt * v

        grid[yCell] = grid[yCell] || []
        const cell = grid[yCell][xCell]

        if (!cell) {
          grid[yCell][xCell] = [point.x, point.y, intensity]
        } else {
          cell[0] = (cell[0] * cell[2] + point.x * intensity) / (cell[2] + intensity)
          cell[1] = (cell[1] * cell[2] + point.y * intensity) / (cell[2] + intensity)
          cell[2] += intensity
        }
      }
    }

    const data: [number, number, number][] = []
    for (let i = 0, len = grid.length; i < len; i++) {
      if (grid[i]) {
        for (let j = 0, len2 = grid[i].length; j < len2; j++) {
          const cell = grid[i][j]
          if (cell) {
            data.push([
              Math.round(cell[0]),
              Math.round(cell[1]),
              Math.min(cell[2], max)
            ])
          }
        }
      }
    }

    this._heat.data(data).draw(this.options.minOpacity)
    this._frame = null
  },

  _animateZoom: function (e: any) {
    const scale = this._map.getZoomScale(e.zoom)
    const offset = this._map
      ._getCenterOffset(e.center)
      ._multiplyBy(-scale)
      .subtract(this._map._getMapPanePos())

    if (L.DomUtil.setTransform) {
      L.DomUtil.setTransform(this._canvas, offset, scale)
    } else {
      this._canvas.style[L.DomUtil.TRANSFORM] =
        L.DomUtil.getTranslateString(offset) + ' scale(' + scale + ')'
    }
  }
})

// ── HeatmapLayer React Component ──────────────────────────────────────────
export interface HeatmapLayerProps {
  points: [number, number, number][] // Array of [lat, lng, intensity]
  radius?: number
  blur?: number
  maxZoom?: number
  max?: number
  minOpacity?: number
  gradient?: Record<number, string>
}

export function HeatmapLayer({
  points,
  radius = 25,
  blur = 15,
  maxZoom = 18,
  max = 1.0,
  minOpacity = 0.05,
  gradient
}: HeatmapLayerProps) {
  const map = useMap()

  useEffect(() => {
    const layer = new (LeafletHeatLayer as any)(points, {
      radius,
      blur,
      maxZoom,
      max,
      minOpacity,
      gradient
    })

    layer.addTo(map)

    return () => {
      map.removeLayer(layer)
    }
  }, [map, points, radius, blur, maxZoom, max, minOpacity, gradient])

  return null
}

export default HeatmapLayer
