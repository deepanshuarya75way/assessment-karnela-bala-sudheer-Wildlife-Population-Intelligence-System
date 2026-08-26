import AVFoundation
import Foundation

let args = CommandLine.arguments
guard args.count == 4 else { fatalError("usage: replace_audio.swift input replacement output") }
let inputURL = URL(fileURLWithPath: args[1])
let replacementURL = URL(fileURLWithPath: args[2])
let outputURL = URL(fileURLWithPath: args[3])

let asset = AVURLAsset(url: inputURL)
let replacement = AVURLAsset(url: replacementURL)
let composition = AVMutableComposition()

guard let videoTrack = asset.tracks(withMediaType: .video).first,
      let sourceAudio = asset.tracks(withMediaType: .audio).first,
      let replacementAudio = replacement.tracks(withMediaType: .audio).first else {
    fatalError("Missing video or audio track")
}

let videoComp = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
try! videoComp.insertTimeRange(CMTimeRange(start: .zero, duration: asset.duration), of: videoTrack, at: .zero)

let audioComp = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
let start = CMTime(seconds: 2.0, preferredTimescale: 600)
let end = CMTime(seconds: 3.0, preferredTimescale: 600)
try! audioComp.insertTimeRange(CMTimeRange(start: .zero, duration: start), of: sourceAudio, at: .zero)
let replacementDuration = min(replacement.duration, CMTime(seconds: 1.0, preferredTimescale: 600))
try! audioComp.insertTimeRange(CMTimeRange(start: .zero, duration: replacementDuration), of: replacementAudio, at: start)
if asset.duration > end {
    try! audioComp.insertTimeRange(CMTimeRange(start: end, duration: asset.duration - end), of: sourceAudio, at: end)
}

videoComp.preferredTransform = videoTrack.preferredTransform
let exporter = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality)!
exporter.outputURL = outputURL
exporter.outputFileType = .mp4
exporter.shouldOptimizeForNetworkUse = true
let group = DispatchGroup(); group.enter()
exporter.exportAsynchronously { group.leave() }
group.wait()
if let error = exporter.error { fatalError(error.localizedDescription) }
