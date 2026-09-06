import Foundation

/// ONE LIBRARY IN, ONE CATALOGUE OUT — resumable at every point.
///
/// Three phases, in this order for a reason:
///  1. **Context** — metadata only, one pass. Home, trips, known people: the facts no
///     single photo contains.
///  2. **Classify** — per asset, escalating from free signals upward, checkpointed
///     every `Catalog.batchSize`. This is the expensive phase and the one that gets
///     killed, so it is the one that resumes.
///  3. **Relate and score** — duplicates, moments and look-alikes are library-level,
///     and risk depends on both classification and duplicate status: an exact duplicate
///     of a passport is still a passport. Scoring last makes that ordering explicit.
///
/// Phase 2 writes `risk = unscored`; phase 3 replaces it. An interrupted run therefore
/// leaves assets classified but not yet scored, and the next run finishes them instead
/// of redoing the expensive part.
public struct RunStats {
    public var seen = 0
    public var classified = 0
    public var skippedUnchanged = 0
    public var forgotten = 0
    public var scored = 0
    public var entities = 0
    public var observations = 0
    public var entityReview = 0
    public var videos = 0
    public var videoFramesSeen = 0
    public var videoFramesProcessed = 0
    public var videoMillisecondsSaved = 0.0
    public var needsReview = 0
    public var unfiled = 0
    public var byTier: [Tier: Int] = [:]
    public var byRisk: [Risk: Int] = [:]
    public var byAction: [Action: Int] = [:]
    public var wallSeconds: Double = 0
    public var context = LibraryContext()

    public var assetsPerSecond: Double { wallSeconds > 0 ? Double(classified) / wallSeconds : 0 }
}

public enum Pipeline {

    private static let unscored: Int32 = -1
    /// §6 R6 — 老照片、特殊家庭影像. How old, relative to now, a capture must be before
    /// it reads as an old photograph rather than a recent one.
    public static let oldPhotoYears = 15.0

    /// PARTIAL, and deliberately conservative: what actually makes an image
    /// irreplaceable is knowledge only the user has, which is §14 Personal Policy and is
    /// not built. What can be derived is the signature of a *scanned* old photograph — a
    /// person in it, a capture date years back, and none of the provenance a phone
    /// camera leaves. A false positive costs one protected photo; a false negative costs
    /// the photo. The asymmetry decides which way to lean.
    public static func looksIrreplaceable(_ a: AssetSignals, _ c: Classification) -> Bool {
        guard c.paths.contains(where: { TaxonomyRuntime.root(of: $0) == "People" }) else { return false }
        guard let when = a.createdAt, a.geo == nil, a.source != "camera" else { return false }
        let years = Date().timeIntervalSince(when) / (365.25 * 86400)
        return years >= oldPhotoYears
    }

    public static func run(assets: [AssetSignals], catalog: Catalog,
                           budget: Tier = .text,
                           reconcileDeletions: Bool = true,
                           buildMemory: Bool = true,
                           framesFor: ((AssetSignals) -> [Frame])? = nil,
                           progress: ((Int, Int) -> Void)? = nil) -> RunStats {
        let started = Date()
        var stats = RunStats()
        stats.seen = assets.count

        // ---- phase 1: context ------------------------------------------
        let context = LibraryContextBuilder.build(assets)
        stats.context = context
        let classifier = Classifier(context: context, budget: budget)

        if reconcileDeletions {
            let present = Set(assets.map { $0.assetID })
            stats.forgotten = catalog.forget(catalog.knownIDs().subtracting(present))
        }

        // ---- phase 2: classify, checkpointed ---------------------------
        var classifications: [String: Classification] = [:]
        var pending = 0
        catalog.begin()
        for (i, a) in assets.enumerated() {
            guard catalog.needsClassification(a) else {
                stats.skippedUnchanged += 1
                continue
            }
            let c = classifier.classify(a)
            classifications[a.assetID] = c
            catalog.upsert(a, c, risk: .r2Normal, proposal: nil)
            catalog.exec("UPDATE assets SET risk=\(unscored) WHERE asset_id='\(escape(a.assetID))';")
            stats.classified += 1
            stats.byTier[c.tierUsed, default: 0] += 1
            if c.needsReview { stats.needsReview += 1 }
            if c.notes.contains(where: { $0.hasPrefix("unfiled:") }) { stats.unfiled += 1 }

            pending += 1
            if pending >= Catalog.batchSize {
                catalog.checkpoint(a.assetID)
                catalog.begin()
                pending = 0
                progress?(i + 1, assets.count)
            }
        }
        catalog.checkpoint(assets.last?.assetID ?? "")

        // ---- phase 3: relate and score ---------------------------------
        let byID = Dictionary(uniqueKeysWithValues: assets.map { ($0.assetID, $0) })
        let documentIDs = Set(assets.compactMap { a -> String? in
            guard let c = classifications[a.assetID] else { return nil }
            return c.paths.contains(where: { $0.hasPrefix("Documents") }) ? a.assetID : nil
        })
        // The relation between two look-alikes is a question about what they are, so
        // the classifications go in with them: §24 Gate 2 puts that answer in the
        // Category-Specific Entity Resolver rather than in one universal rule ladder.
        let report = Dedup.analyse(assets, documentIDs: documentIDs,
                                   classifications: classifications)
        catalog.writeRelations(report.relations)

        catalog.begin()
        for (assetID, c) in classifications {
            guard let a = byID[assetID] else { continue }
            let isDuplicate = report.exactDuplicateOf[assetID] != nil
            let risk = RiskEngine.classify(
                c,
                isExactDuplicate: isDuplicate,
                hasPerson: c.notes.contains { $0.contains("unnamed person") },
                isIrreplaceable: looksIrreplaceable(a, c))
            var ageDays: Double?
            if let when = a.createdAt {
                ageDays = max(0, Date().timeIntervalSince(when) / 86400)
            }
            let factors = Factors(
                risk: risk,
                lifecycle: RiskEngine.lifecycle(c, ageDays: ageDays),
                confidence: c.primary?.confidence ?? 0,
                recoverability: RiskEngine.recoverability(risk),
                inEquivalenceGroup: report.nearDuplicateInMoment.contains(assetID)
                    && !report.protectedDistinct.contains(assetID),
                isExactDuplicate: isDuplicate)
            let proposal = RiskEngine.propose(c, factors,
                                              duplicateOf: report.exactDuplicateOf[assetID])
            catalog.upsert(a, c, risk: risk, proposal: proposal)
            stats.byRisk[risk, default: 0] += 1
            if let p = proposal { stats.byAction[p.action, default: 0] += 1 }
            stats.scored += 1
        }
        catalog.commit()

        // ---- phase 3b: video --------------------------------------------
        //
        // The engine has no decoder, so frames come from outside — the same shape of
        // contract `AssetSignals` already is with the rest of the world. Without a
        // source a video is still catalogued from its metadata; it is simply never
        // looked inside, and `videos` stays at zero rather than the run implying
        // otherwise.
        //
        // This is L1-B §4's division of labour: decide **which frames deserve deep
        // processing** and record **what the video contributed**. Running a model on
        // those frames is the caller's job, because that is the part needing Vision.
        if let framesFor {
            for asset in assets where asset.isVideo {
                let frames = framesFor(asset)
                // A video whose frames could not be read is not a video with no new
                // information. Saying nothing is honest; an empty record claims the
                // opposite.
                guard !frames.isEmpty else { continue }

                let c = classifications[asset.assetID]
                // Documents get a stricter gate — a page of text that drifts slightly
                // is still a different page, and §9's false merge is expensive there.
                let isDocument = c?.paths.contains { $0.hasPrefix("Documents") } ?? false
                let selection = Deltas.selectKeyframes(frames, isDocument: isDocument)
                let cost = Deltas.estimateCost(selection)

                let record = VideoMemory.record(
                    asset: asset, keyframes: selection.keyframes,
                    frameRate: Pipeline.frameRate(frames, asset),
                    classification: c, context: context,
                    newContentAt: selection.newContentFrames)
                catalog.writeVideoRecord(record, framesSeen: selection.total)

                stats.videos += 1
                stats.videoFramesSeen += selection.total
                stats.videoFramesProcessed += selection.processed
                stats.videoMillisecondsSaved += cost.savedMilliseconds
            }
        }

        // ---- phase 4: remember -----------------------------------------
        // §2 lists Remember among the ten things the product is, and §15 builds every
        // later service on it. No new intelligence is spent: this reads the
        // classifications and signals already computed above.
        if buildMemory, !classifications.isEmpty {
            let graph = MemoryBuilder.build(
                assets: assets, classifications: classifications, context: context,
                momentGroups: report.relations.filter { $0.kind == "same_moment" }
                    .map { $0.members })
            catalog.writeMemory(graph)
            stats.entities = graph.entities.count
            stats.observations = graph.observations.count
        }
        stats.entityReview = report.needsEntityReview.count

        stats.wallSeconds = Date().timeIntervalSince(started)
        return stats
    }

    /// Derived from the frames themselves where they carry timestamps, because the
    /// sampling rate is a property of what the caller handed us and not of the file.
    ///
    /// A caller sampling every tenth frame of a 30 fps video is giving us 3 fps, and
    /// using the file's rate would put every segment boundary in the wrong place — the
    /// record would name the wrong seconds of the user's own video.
    static func frameRate(_ frames: [Frame], _ asset: AssetSignals) -> Double {
        let stamped = frames.filter { $0.timestampSeconds != 0 }
        if let first = stamped.first, let last = stamped.last, stamped.count >= 2 {
            let span = last.timestampSeconds - first.timestampSeconds
            let steps = last.index - first.index
            if span > 0, steps > 0 { return Double(steps) / span }
        }
        if asset.durationSeconds > 0, frames.count > 1 {
            return Double(frames.count - 1) / asset.durationSeconds
        }
        return 1.0
    }

    private static func escape(_ s: String) -> String {
        s.replacingOccurrences(of: "'", with: "''")
    }
}
