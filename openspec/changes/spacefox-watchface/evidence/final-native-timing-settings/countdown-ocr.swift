import Foundation
import Vision
import ImageIO
for path in CommandLine.arguments.dropFirst() {
    do {
        let url = URL(fileURLWithPath: path)
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil), let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { throw NSError(domain: "input", code: 1) }
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = false
        request.recognitionLanguages = ["en-US"]
        request.regionOfInterest = CGRect(x: 0.16, y: 0.385, width: 0.7, height: 0.11)
        try VNImageRequestHandler(cgImage: image, options: [:]).perform([request])
        let rows = (request.results ?? []).compactMap { item -> [String: Any]? in
            guard let text = item.topCandidates(1).first else { return nil }
            return ["text": text.string, "confidence": text.confidence, "box": [item.boundingBox.minX,item.boundingBox.minY,item.boundingBox.width,item.boundingBox.height]]
        }
        let row: [String: Any] = ["file": path, "width": image.width, "height": image.height, "roi": [0.16,0.385,0.7,0.11], "observations": rows, "backend": "macOS Vision on-device"]
        let raw = try JSONSerialization.data(withJSONObject: row, options: [.sortedKeys])
        print(String(decoding: raw, as: UTF8.self))
    } catch { fputs("OCR input failure: \(path): \(error)\n", stderr); exit(2) }
}
