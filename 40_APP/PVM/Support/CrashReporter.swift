import Foundation
#if canImport(Darwin)
import Darwin
#endif

/// CRASH REPORTING WITHOUT A CRASH-REPORTING SDK.
///
/// Every off-the-shelf option — Crashlytics, Sentry, Bugsnag — works by sending the
/// report to someone else's server. This product's whole claim is that nothing leaves
/// the phone, and the competitor teardown in `COMPETITOR_PRICING_MATRIX.md` records
/// what happens to that claim in this category: privacy labels saying "not linked to
/// me" over payloads carrying user IDs, through six tracking SDKs, *after* the user
/// paid. Shipping one of those and then writing a privacy policy that says "no data is
/// collected" would be the same lie with our name on it.
///
/// So the crash report is written to a file on the device, shown to the user on the
/// next launch, and **sent only if they choose to send it**, by hand, through their own
/// mail app. That is worse for us — we learn about far fewer crashes — and it is the
/// only version consistent with what the permission sheet promises.
///
/// **Async-signal-safety.** A signal handler may only call async-signal-safe functions.
/// It may not allocate, may not take a lock, and may not touch Foundation — the common
/// implementation of this file, which builds a `String` and calls `write(toFile:)`,
/// deadlocks inside `malloc` often enough that the crash it was meant to record is
/// replaced by a hang. Everything the handler needs is therefore prepared at install
/// time: the file descriptor is already open, the preamble is already a C string, and
/// the frame buffer is already allocated. The handler itself calls only `write`,
/// `backtrace`, `backtrace_symbols_fd`, `fsync`, `signal` and `raise`.
enum CrashReporter {

    // MARK: - where it lives

    static var reportURL: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory,
                                            in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSTemporaryDirectory())
        let directory = base.appendingPathComponent("PVM", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        return directory.appendingPathComponent("last-crash.txt")
    }

    /// The report left by the previous run, captured by `install` before it truncates
    /// the file — which is why this is a stored value and not a read.
    ///
    /// Reading lazily would race with the truncation and usually lose: the UI that
    /// wants to show the crash is built after start-up, by which point `install` has
    /// already emptied the file to make room for the next one.
    private(set) static var reportFromLastRun: String?

    static func pendingReport() -> String? {
        guard let text = try? String(contentsOf: reportURL, encoding: .utf8) else { return nil }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }

    /// The user chose not to send it. Only the in-memory copy is dropped: the file on
    /// disk is already empty (`install` truncated it) and deleting it now would unlink
    /// the inode the signal handler's descriptor still points at, quietly discarding
    /// the *next* crash instead of this one.
    static func clearPendingReport() {
        reportFromLastRun = nil
        if !isInstalled { try? FileManager.default.removeItem(at: reportURL) }
    }

    // MARK: - install

    private(set) static var isInstalled = false

    /// `buildSummary` is written into every report. It must contain nothing about the
    /// user's library — version and OS only; `Diagnostics.buildSummary` is the value
    /// this ships with and `LaunchReadinessTests` asserts its shape.
    static func install(buildSummary: String) {
        #if canImport(Darwin)
        guard !isInstalled else { return }
        isInstalled = true

        let path = reportURL.path
        reportFromLastRun = pendingReport()
        crashLogFD = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0o600)
        guard crashLogFD >= 0 else { return }
        // The report can name a crashing symbol in this app; the file it sits in gets
        // the same protection as the catalogue rather than the default.
        try? FileManager.default.setAttributes(
            [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
            ofItemAtPath: path)

        crashPreamble = strdup("PVM crash report\n" + buildSummary + "\nsignal: ")
        crashFrames = UnsafeMutablePointer<UnsafeMutableRawPointer?>.allocate(capacity: 64)

        for sig in [SIGABRT, SIGSEGV, SIGBUS, SIGILL, SIGFPE, SIGTRAP] {
            signal(sig, crashSignalHandler)
        }

        NSSetUncaughtExceptionHandler { exception in
            // Not a signal context — Foundation is legal here. The uncaught-exception
            // handler runs first and `SIGABRT` follows, so this appends rather than
            // replaces, and the file already has the preamble.
            let reason = CrashReporter.redact(exception.reason ?? "")
            let body = "\nexception: \(exception.name.rawValue)\nreason: \(reason)\n"
                + exception.callStackSymbols.joined(separator: "\n") + "\n"
            body.withCString { pointer in
                _ = write(crashLogFD, pointer, strlen(pointer))
            }
            fsync(crashLogFD)
        }
        #endif
    }

    // MARK: - privacy filter

    /// An exception reason is a string this app built, and this app handles passport
    /// numbers and bank statements read out of photographs by OCR. A reason of the
    /// form "no row for 3A1F…/L0/001" is a photo identifier, and one built from OCR
    /// text is worse. Anything that looks like an identifier, a path or a long opaque
    /// token is replaced before it reaches the file the user might mail to us.
    ///
    /// Deliberately over-eager. A redacted report that is harder to debug is a cost we
    /// carry; a report carrying a line of someone's bank statement is not.
    static func redact(_ text: String) -> String {
        var out = text
        for pattern in [
            #"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}(/L0/\d+)?"#,
            #"/[A-Za-z0-9_./-]{12,}"#,                 // absolute paths, container names
            #"\b[A-Za-z0-9+/=]{24,}\b"#,               // base64-ish blobs
            #"\b\d{9,}\b"#,                            // account / document numbers
        ] {
            out = out.replacingOccurrences(of: pattern, with: "<redacted>",
                                           options: .regularExpression)
        }
        return out
    }
}

#if canImport(Darwin)

// File-scope globals, not properties: a signal handler cannot safely reach through
// Swift's metadata to a static stored property on first access, and these are written
// once at install time and only read afterwards.
private var crashLogFD: Int32 = -1
private var crashPreamble: UnsafeMutablePointer<CChar>?
private var crashFrames: UnsafeMutablePointer<UnsafeMutableRawPointer?>?

/// Names without `String(describing:)`, because that allocates. A `StaticString`
/// literal's bytes live in the binary, so the pointer is valid forever and no copy is
/// made. The trailing newline is part of the literal rather than a second write: a
/// one-scalar `StaticString` is allowed to use a scalar representation instead of a
/// pointer one, and reading `utf8Start` on it traps.
private func crashLiteral(_ text: StaticString) -> UnsafePointer<CChar> {
    UnsafeRawPointer(text.utf8Start).assumingMemoryBound(to: CChar.self)
}

private func crashSignalName(_ sig: Int32) -> UnsafePointer<CChar> {
    switch sig {
    case SIGABRT: return crashLiteral("SIGABRT\n")
    case SIGSEGV: return crashLiteral("SIGSEGV\n")
    case SIGBUS:  return crashLiteral("SIGBUS\n")
    case SIGILL:  return crashLiteral("SIGILL\n")
    case SIGFPE:  return crashLiteral("SIGFPE\n")
    case SIGTRAP: return crashLiteral("SIGTRAP\n")
    default:      return crashLiteral("UNKNOWN\n")
    }
}

private func crashWrite(_ text: UnsafePointer<CChar>) {
    _ = write(crashLogFD, text, strlen(text))
}

private let crashSignalHandler: @convention(c) (Int32) -> Void = { sig in
    if crashLogFD >= 0 {
        if let preamble = crashPreamble { crashWrite(preamble) }
        crashWrite(crashSignalName(sig))
        if let frames = crashFrames {
            let count = backtrace(frames, 64)
            backtrace_symbols_fd(frames, count, crashLogFD)
        }
        fsync(crashLogFD)
    }
    // Hand the signal back to the system so the OS still records the crash the normal
    // way. Swallowing it would make this file the only record, and a file written by
    // the process that just died is the least trustworthy record there is.
    signal(sig, SIG_DFL)
    raise(sig)
}

#endif
