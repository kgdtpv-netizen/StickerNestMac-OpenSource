import AppKit

let outputDirectory = URL(fileURLWithPath: CommandLine.arguments.dropFirst().first ?? ".")
let iconsetURL = outputDirectory.appendingPathComponent("AppIcon.iconset", isDirectory: true)
try? FileManager.default.removeItem(at: iconsetURL)
try FileManager.default.createDirectory(at: iconsetURL, withIntermediateDirectories: true)

let sizes: [(String, CGFloat)] = [
    ("icon_16x16.png", 16), ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32), ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128), ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256), ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512), ("icon_512x512@2x.png", 1024)
]

func drawIcon(size: CGFloat) -> NSImage {
    let image = NSImage(size: NSSize(width: size, height: size))
    image.lockFocus()
    let bounds = CGRect(x: 0, y: 0, width: size, height: size)
    let base = NSBezierPath(roundedRect: bounds.insetBy(dx: size * 0.06, dy: size * 0.06), xRadius: size * 0.18, yRadius: size * 0.18)
    NSGradient(colors: [
        NSColor(calibratedRed: 0.05, green: 0.38, blue: 0.34, alpha: 1),
        NSColor(calibratedRed: 0.86, green: 0.28, blue: 0.16, alpha: 1)
    ])?.draw(in: base, angle: 135)
    NSColor.white.withAlphaComponent(0.18).setStroke()
    base.lineWidth = size * 0.02
    base.stroke()

    let shapes: [(CGRect, CGFloat)] = [
        (CGRect(x: size * 0.18, y: size * 0.55, width: size * 0.30, height: size * 0.24), -18),
        (CGRect(x: size * 0.48, y: size * 0.48, width: size * 0.32, height: size * 0.27), 16),
        (CGRect(x: size * 0.25, y: size * 0.22, width: size * 0.36, height: size * 0.24), 10),
        (CGRect(x: size * 0.58, y: size * 0.18, width: size * 0.22, height: size * 0.24), -22)
    ]
    for (rect, angle) in shapes {
        NSGraphicsContext.saveGraphicsState()
        let transform = NSAffineTransform()
        transform.translateX(by: rect.midX, yBy: rect.midY)
        transform.rotate(byDegrees: angle)
        transform.translateX(by: -rect.midX, yBy: -rect.midY)
        transform.concat()
        let path = NSBezierPath(roundedRect: rect, xRadius: size * 0.04, yRadius: size * 0.04)
        NSColor.white.setFill()
        path.fill()
        NSColor.black.withAlphaComponent(0.22).setStroke()
        path.lineWidth = max(1, size * 0.011)
        var dash: [CGFloat] = [size * 0.035, size * 0.018]
        path.setLineDash(&dash, count: dash.count, phase: 0)
        path.stroke()
        NSGraphicsContext.restoreGraphicsState()
    }
    image.unlockFocus()
    return image
}

for (filename, size) in sizes {
    let image = drawIcon(size: size)
    guard let tiff = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let data = bitmap.representation(using: .png, properties: [:]) else {
        fatalError("Unable to render \(filename)")
    }
    try data.write(to: iconsetURL.appendingPathComponent(filename))
}
