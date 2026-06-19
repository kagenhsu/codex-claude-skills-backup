import AppKit
import Foundation

struct UsageWindow {
    let title: String
    let remainingPercent: Double?
    let remainingText: String
    let alertStage: String
}

struct ProviderStatus {
    let name: String
    let windows: [UsageWindow]
}

func commandExists(_ name: String) -> Bool {
    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/which")
    process.arguments = [name]
    do {
        try process.run()
        process.waitUntilExit()
        return process.terminationStatus == 0
    } catch {
        return false
    }
}

func codexInstalledLocally() -> Bool {
    commandExists("codex")
        || FileManager.default.fileExists(atPath: "/Applications/Codex.app")
        || FileManager.default.fileExists(atPath: NSString(string: "~/.codex/quota-status.json").expandingTildeInPath)
}

func claudeInstalledLocally() -> Bool {
    commandExists("claude")
        || FileManager.default.fileExists(atPath: "/Applications/Claude.app")
        || FileManager.default.fileExists(atPath: NSString(string: "~/.claude/settings.json").expandingTildeInPath)
        || FileManager.default.fileExists(atPath: NSString(string: "~/.claude/cctokmon-state.json").expandingTildeInPath)
        || FileManager.default.fileExists(atPath: NSString(string: "~/.claude/cctokmon-cache.json").expandingTildeInPath)
}

func unavailableDetailText(_ text: String, percent: Double?) -> String {
    guard percent == nil else { return text }
    let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
    if trimmed.isEmpty || trimmed == "尚未接上" {
        return "等待下次可用時間"
    }
    if trimmed.hasPrefix("等待 Claude 回傳") {
        return trimmed
    }
    if trimmed == "等待下一次互動" {
        return "等下次互動後更新可用時間"
    }
    if trimmed.hasSuffix("（最近一次有效資料）") {
        let base = String(trimmed.dropLast("（最近一次有效資料）".count))
        return "可於 \(base) 後再次使用（最近一次有效資料）"
    }
    return "可於 \(trimmed) 後再次使用"
}

func runCommand(_ launchPath: String, arguments: [String]) -> String? {
    let process = Process()
    process.executableURL = URL(fileURLWithPath: launchPath)
    process.arguments = arguments

    let stdout = Pipe()
    let stderr = Pipe()
    process.standardOutput = stdout
    process.standardError = stderr

    do {
        try process.run()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else { return nil }
        let data = stdout.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8)
    } catch {
        return nil
    }
}

func loadJSONFile(_ path: String) -> [String: Any]? {
    let realPath = NSString(string: path).expandingTildeInPath
    guard
        let data = FileManager.default.contents(atPath: realPath),
        let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
    else { return nil }
    return object
}

func asDouble(_ value: Any?) -> Double? {
    if let number = value as? Double { return number }
    if let number = value as? Int { return Double(number) }
    if let text = value as? String, let number = Double(text) { return number }
    return nil
}

func remainingTimeText(until date: Date?) -> String {
    guard let date else { return "尚未接上" }
    let interval = max(0, Int(date.timeIntervalSinceNow))
    let days = interval / 86400
    let hours = (interval % 86400) / 3600
    let minutes = (interval % 3600) / 60
    if days > 0 { return "\(days)天 \(hours)小時" }
    if hours > 0 { return "\(hours)小時 \(minutes)分" }
    return "\(minutes)分鐘"
}

func remainingPercentText(_ percent: Double?) -> String {
    guard let percent else { return "限制休息中" }
    return "\(Int(round(percent)))%"
}

func barColor(for stage: String) -> NSColor {
    switch stage {
    case "prepare":
        return NSColor.systemYellow
    case "handoff":
        return NSColor.systemOrange
    case "reserve":
        return NSColor.systemRed
    case "unavailable":
        return NSColor.systemGray
    default:
        return NSColor.systemGreen
    }
}

func fallbackStatuses() -> [ProviderStatus] {
    var items: [ProviderStatus] = []
    if claudeInstalledLocally() {
        items.append(
            ProviderStatus(
                name: "Claude Code",
                windows: [
                    UsageWindow(title: "本輪", remainingPercent: nil, remainingText: "尚未接上", alertStage: "unavailable"),
                    UsageWindow(title: "本週", remainingPercent: nil, remainingText: "尚未接上", alertStage: "unavailable")
                ]
            )
        )
    }
    if codexInstalledLocally() {
        items.append(
            ProviderStatus(
                name: "Codex",
                windows: [
                    UsageWindow(title: "本輪", remainingPercent: nil, remainingText: "尚未接上", alertStage: "unavailable"),
                    UsageWindow(title: "本週", remainingPercent: nil, remainingText: "尚未接上", alertStage: "unavailable")
                ]
            )
        )
    }
    return items.isEmpty ? [
        ProviderStatus(
            name: "配額守門員",
            windows: [
                UsageWindow(title: "狀態", remainingPercent: nil, remainingText: "這台電腦尚未偵測到 Codex 或 Claude Code", alertStage: "unavailable")
            ]
        )
    ] : items
}

func loadStatuses() -> [ProviderStatus] {
    let currentFile = URL(fileURLWithPath: #filePath)
    let scriptPath = currentFile.deletingLastPathComponent().appendingPathComponent("quota_guard_snapshot.py").path
    guard
        let output = runCommand("/usr/bin/python3", arguments: [scriptPath]),
        let data = output.data(using: .utf8),
        let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
        let providers = object["providers"] as? [[String: Any]]
    else {
        return fallbackStatuses()
    }

    let items = providers.compactMap { provider -> ProviderStatus? in
        guard let name = provider["name"] as? String else { return nil }
        let windows = (provider["windows"] as? [[String: Any]] ?? []).map { window in
            UsageWindow(
                title: window["title"] as? String ?? "限制",
                remainingPercent: asDouble(window["remaining_percent"]),
                remainingText: window["remaining_text"] as? String ?? "尚未接上",
                alertStage: window["alert_stage"] as? String ?? "unavailable"
            )
        }
        return ProviderStatus(name: name, windows: windows)
    }

    return items.isEmpty ? fallbackStatuses() : items
}

final class UsageRowView: NSView {
    init(window: UsageWindow) {
        super.init(frame: .zero)

        let label = NSTextField(labelWithString: window.title)
        label.font = .systemFont(ofSize: 12, weight: .semibold)

        let value = NSTextField(
            labelWithString: "\(remainingPercentText(window.remainingPercent))  \(unavailableDetailText(window.remainingText, percent: window.remainingPercent))"
        )
        value.font = .systemFont(ofSize: 12, weight: .medium)
        value.textColor = .secondaryLabelColor

        let row = NSStackView(views: [label, NSView(), value])
        row.orientation = .horizontal
        row.alignment = .centerY

        let track = NSView()
        track.wantsLayer = true
        track.layer?.backgroundColor = NSColor.separatorColor.withAlphaComponent(0.3).cgColor
        track.layer?.cornerRadius = 4
        track.translatesAutoresizingMaskIntoConstraints = false
        track.heightAnchor.constraint(equalToConstant: 8).isActive = true

        let fill = NSView()
        fill.wantsLayer = true
        fill.layer?.backgroundColor = barColor(for: window.alertStage).cgColor
        fill.layer?.cornerRadius = 4
        fill.translatesAutoresizingMaskIntoConstraints = false
        track.addSubview(fill)

        let ratio = max(0.08, CGFloat((window.remainingPercent ?? 8) / 100))
        NSLayoutConstraint.activate([
            fill.leadingAnchor.constraint(equalTo: track.leadingAnchor),
            fill.topAnchor.constraint(equalTo: track.topAnchor),
            fill.bottomAnchor.constraint(equalTo: track.bottomAnchor),
            fill.widthAnchor.constraint(equalTo: track.widthAnchor, multiplier: ratio)
        ])

        let stack = NSStackView(views: [row, track])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 6
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor),
            stack.topAnchor.constraint(equalTo: topAnchor),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { nil }
}

final class ProviderCardView: NSView {
    init(status: ProviderStatus) {
        super.init(frame: .zero)
        wantsLayer = true
        layer?.backgroundColor = NSColor.controlBackgroundColor.withAlphaComponent(0.95).cgColor
        layer?.cornerRadius = 14
        layer?.borderWidth = 1
        layer?.borderColor = NSColor.separatorColor.cgColor

        let title = NSTextField(labelWithString: status.name)
        title.font = .systemFont(ofSize: 16, weight: .bold)

        let rows = status.windows.map { UsageRowView(window: $0) }
        let rowsStack = NSStackView(views: rows)
        rowsStack.orientation = .vertical
        rowsStack.alignment = .leading
        rowsStack.spacing = 12

        let stack = NSStackView(views: [title, rowsStack])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16)
        ])
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { nil }
}

final class MiniProviderRowView: NSView {
    private let nameLabel: NSTextField
    private let percentLabel = NSTextField(labelWithString: "--%")
    private let fillView = NSView()
    private var fillWidthConstraint: NSLayoutConstraint!

    init(providerName: String) {
        nameLabel = NSTextField(labelWithString: providerName)
        super.init(frame: .zero)

        nameLabel.font = .monospacedSystemFont(ofSize: 11, weight: .semibold)
        percentLabel.font = .monospacedSystemFont(ofSize: 11, weight: .semibold)
        percentLabel.textColor = .secondaryLabelColor

        let labels = NSStackView(views: [nameLabel, NSView(), percentLabel])
        labels.orientation = .horizontal
        labels.alignment = .centerY

        let track = NSView()
        track.wantsLayer = true
        track.layer?.backgroundColor = NSColor.separatorColor.withAlphaComponent(0.25).cgColor
        track.layer?.cornerRadius = 3
        track.translatesAutoresizingMaskIntoConstraints = false
        track.heightAnchor.constraint(equalToConstant: 6).isActive = true

        fillView.wantsLayer = true
        fillView.layer?.cornerRadius = 3
        fillView.translatesAutoresizingMaskIntoConstraints = false
        track.addSubview(fillView)

        fillWidthConstraint = fillView.widthAnchor.constraint(equalTo: track.widthAnchor, multiplier: 0.08)
        fillWidthConstraint.isActive = true

        NSLayoutConstraint.activate([
            fillView.leadingAnchor.constraint(equalTo: track.leadingAnchor),
            fillView.topAnchor.constraint(equalTo: track.topAnchor),
            fillView.bottomAnchor.constraint(equalTo: track.bottomAnchor)
        ])

        let stack = NSStackView(views: [labels, track])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 3
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor),
            stack.topAnchor.constraint(equalTo: topAnchor),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
    }

    func update(with window: UsageWindow?) {
        let percent = window?.remainingPercent
        let ratio = max(0.08, CGFloat((percent ?? 8) / 100))
        fillWidthConstraint.isActive = false
        fillWidthConstraint = fillView.widthAnchor.constraint(equalTo: fillView.superview!.widthAnchor, multiplier: ratio)
        fillWidthConstraint.isActive = true
        fillView.layer?.backgroundColor = barColor(for: window?.alertStage ?? "unavailable").cgColor
        if let percent {
            percentLabel.stringValue = "\(Int(round(percent)))%"
        } else {
            percentLabel.stringValue = "--%"
        }
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { nil }
}

final class MiniContentView: NSView {
    var onExpand: (() -> Void)?

    override func mouseDown(with event: NSEvent) {
        if event.clickCount >= 2 {
            onExpand?()
            return
        }
        window?.performDrag(with: event)
    }
}

final class FloatingQuotaWindow: NSObject, NSApplicationDelegate {
    private let fullWindowSize = NSSize(width: 500, height: 380)
    private let miniWindowSize = NSSize(width: 260, height: 64)
    private var window: NSPanel!
    private let cardsStack = NSStackView()
    private let updatedLabel = NSTextField(labelWithString: "更新中")
    private let handoffButton = NSButton(title: "複製切換提示詞", target: nil, action: nil)
    private let miniModeButton = NSButton(title: "縮小成 widget", target: nil, action: nil)
    private var contentStack: NSStackView!
    private var miniContentStack: NSStackView!
    private var miniContainerView: NSView!
    private var fullModeConstraints: [NSLayoutConstraint] = []
    private var miniModeConstraints: [NSLayoutConstraint] = []
    private var refreshTimer: Timer?
    private var latestStatuses: [ProviderStatus] = []
    private var autoCopiedFinalPrompt = false
    private var isMini = false
    private var fullModeFrame: NSRect?

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupWindow()
        render()
        startAutoRefresh()
        NSApp.activate(ignoringOtherApps: true)
        window.makeKeyAndOrderFront(nil)
    }

    func applicationWillTerminate(_ notification: Notification) {
        refreshTimer?.invalidate()
    }

    private func buildMiniView() -> NSView {
        let container = MiniContentView()
        container.wantsLayer = true
        container.layer?.cornerRadius = 18
        container.layer?.backgroundColor = NSColor.clear.cgColor

        let title = NSTextField(labelWithString: "☁︎ 配額")
        title.font = .systemFont(ofSize: 12, weight: .bold)

        let expandButton = NSButton(title: "展回", target: self, action: #selector(toggleMini))
        expandButton.bezelStyle = .texturedRounded
        expandButton.font = .systemFont(ofSize: 12, weight: .semibold)
        expandButton.setButtonType(.momentaryPushIn)

        let header = NSStackView(views: [title, NSView(), expandButton])
        header.orientation = .horizontal
        header.alignment = .centerY

        let claudeRow = MiniProviderRowView(providerName: "Claude")
        claudeRow.identifier = NSUserInterfaceItemIdentifier("mini-row-claude")
        let codexRow = MiniProviderRowView(providerName: "Codex")
        codexRow.identifier = NSUserInterfaceItemIdentifier("mini-row-codex")

        let rows = NSStackView(views: [claudeRow, codexRow])
        rows.orientation = .vertical
        rows.alignment = .leading
        rows.spacing = 5

        let right = NSStackView(views: [rows])
        right.orientation = .vertical
        right.alignment = .leading

        let left = NSStackView(views: [header])
        left.orientation = .vertical
        left.alignment = .leading

        let root = NSStackView(views: [left, right])
        root.orientation = .horizontal
        root.alignment = .top
        root.distribution = .fillProportionally
        root.spacing = 12
        root.translatesAutoresizingMaskIntoConstraints = false
        container.addSubview(root)

        container.onExpand = { [weak self] in
            self?.toggleMini()
        }

        NSLayoutConstraint.activate([
            root.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 14),
            root.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -14),
            root.topAnchor.constraint(equalTo: container.topAnchor, constant: 10),
            root.bottomAnchor.constraint(equalTo: container.bottomAnchor, constant: -10),
            left.widthAnchor.constraint(equalToConstant: 72),
            right.widthAnchor.constraint(greaterThanOrEqualToConstant: 148)
        ])

        miniContentStack = rows
        return container
    }

    private func setupWindow() {
        let rect = NSRect(x: 0, y: 0, width: fullWindowSize.width, height: fullWindowSize.height)
        window = NSPanel(
            contentRect: rect,
            styleMask: [.titled, .closable, .miniaturizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.title = "配額守門員"
        window.level = .floating
        window.isFloatingPanel = true
        window.hidesOnDeactivate = false
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        window.titlebarAppearsTransparent = true
        window.center()

        let visual = NSVisualEffectView(frame: rect)
        visual.material = .sidebar
        visual.blendingMode = .behindWindow
        visual.state = .active
        window.contentView = visual

        let title = NSTextField(labelWithString: "Codex Pro × Claude Code")
        title.font = .systemFont(ofSize: 20, weight: .bold)

        updatedLabel.font = .systemFont(ofSize: 11, weight: .medium)
        updatedLabel.textColor = .secondaryLabelColor

        cardsStack.orientation = .vertical
        cardsStack.alignment = .leading
        cardsStack.spacing = 12

        handoffButton.target = self
        handoffButton.action = #selector(copyHandoffPrompt)
        handoffButton.bezelStyle = .rounded

        miniModeButton.target = self
        miniModeButton.action = #selector(toggleMini)
        miniModeButton.bezelStyle = .rounded

        let header = NSStackView(views: [title, NSView(), updatedLabel])
        header.orientation = .horizontal
        header.alignment = .centerY

        let footer = NSStackView(views: [miniModeButton, handoffButton])
        footer.orientation = .horizontal
        footer.alignment = .leading

        contentStack = NSStackView(views: [header, cardsStack, footer])
        contentStack.orientation = .vertical
        contentStack.alignment = .leading
        contentStack.spacing = 14
        contentStack.translatesAutoresizingMaskIntoConstraints = false
        visual.addSubview(contentStack)

        miniContainerView = buildMiniView()
        miniContainerView.translatesAutoresizingMaskIntoConstraints = false
        miniContainerView.isHidden = true
        visual.addSubview(miniContainerView)

        fullModeConstraints = [
            contentStack.leadingAnchor.constraint(equalTo: visual.leadingAnchor, constant: 18),
            contentStack.trailingAnchor.constraint(equalTo: visual.trailingAnchor, constant: -18),
            contentStack.topAnchor.constraint(equalTo: visual.topAnchor, constant: 18),
            contentStack.bottomAnchor.constraint(equalTo: visual.bottomAnchor, constant: -18)
        ]
        miniModeConstraints = [
            miniContainerView.leadingAnchor.constraint(equalTo: visual.leadingAnchor),
            miniContainerView.trailingAnchor.constraint(equalTo: visual.trailingAnchor),
            miniContainerView.topAnchor.constraint(equalTo: visual.topAnchor),
            miniContainerView.bottomAnchor.constraint(equalTo: visual.bottomAnchor)
        ]
        NSLayoutConstraint.activate(fullModeConstraints + miniModeConstraints)
        window.minSize = fullWindowSize
    }

    private func render() {
        let statuses = loadStatuses()
        latestStatuses = statuses
        if !isMini {
            cardsStack.arrangedSubviews.forEach {
                cardsStack.removeArrangedSubview($0)
                $0.removeFromSuperview()
            }
            for item in statuses {
                let card = ProviderCardView(status: item)
                card.translatesAutoresizingMaskIntoConstraints = false
                card.widthAnchor.constraint(equalToConstant: 464).isActive = true
                cardsStack.addArrangedSubview(card)
            }
            resizeWindowToFitContent()
        }
        renderMini()
        handoffButton.title = finalHandoffNeeded() ? "複製最終交接提示詞" : "複製切換提示詞"
        if finalHandoffNeeded(), !autoCopiedFinalPrompt {
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(handoffPrompt(), forType: .string)
            updatedLabel.stringValue = "已自動複製最終交接提示詞"
            autoCopiedFinalPrompt = true
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.6) { [weak self] in
                self?.updatedLabel.stringValue = "更新 \(self?.timeString() ?? "")"
            }
            return
        }
        if !finalHandoffNeeded() {
            autoCopiedFinalPrompt = false
        }
        updatedLabel.stringValue = "更新 \(timeString())"
    }

    @objc private func refreshNow() {
        render()
    }

    @objc private func toggleMini() {
        guard let visual = window.contentView else { return }

        if isMini {
            isMini = false
            miniContainerView.isHidden = true
            contentStack.isHidden = false
            NSLayoutConstraint.activate(fullModeConstraints)
            window.styleMask.insert(.titled)
            window.styleMask.insert(.closable)
            window.styleMask.insert(.miniaturizable)
            window.title = "配額守門員"
            window.minSize = fullWindowSize

            if let storedFrame = fullModeFrame {
                window.setFrame(storedFrame, display: true, animate: false)
            }
            visual.layoutSubtreeIfNeeded()
            render()
            return
        }

        fullModeFrame = window.frame
        isMini = true
        contentStack.isHidden = true
        miniContainerView.isHidden = false
        NSLayoutConstraint.deactivate(fullModeConstraints)
        window.styleMask.remove(.titled)
        window.styleMask.remove(.closable)
        window.styleMask.remove(.miniaturizable)
        window.minSize = miniWindowSize

        var miniFrame = window.frame
        miniFrame.origin.y += miniFrame.height - miniWindowSize.height
        miniFrame.size = miniWindowSize
        window.setFrame(miniFrame, display: true, animate: false)
        visual.layoutSubtreeIfNeeded()
        renderMini()
    }

    @objc private func copyHandoffPrompt() {
        let prompt = handoffPrompt()
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(prompt, forType: .string)
        updatedLabel.stringValue = finalHandoffNeeded() ? "已複製最終交接提示詞" : "已複製切換提示詞"
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.6) { [weak self] in
            self?.updatedLabel.stringValue = "更新 \(self?.timeString() ?? "")"
        }
    }

    private func handoffPrompt() -> String {
        let nextAI = nextAIName()
        let statusLines = latestStatuses.map { status in
            let parts = status.windows.map { window in
                let text = unavailableDetailText(window.remainingText, percent: window.remainingPercent)
                let percent = window.remainingPercent == nil ? "限制休息中" : "\(Int(round(window.remainingPercent ?? 0)))%"
            return "\(window.title) \(percent) / \(text)"
        }.joined(separator: "、")
            return "- \(status.name)：\(parts)"
        }.joined(separator: "\n")

        if finalHandoffNeeded() {
            return """
            ⚠️ 最終交接模式 — 上一棒 AI 即將撞限制，立即切換給\(nextAI)。

            第一件事（這一棒必做，不能跳過）：
            執行 skill `/handoff-now`（Claude Code）或同等動作（Codex 請讀 skills/handoff-now/templates/handoff-now.md 當範本），把當前對話進度寫到專案根目錄 `.handoff-now.md`。寫完之後再做下面的事。

            目前配額狀態：
            \(statusLines)

            然後請直接輸出交接摘要，格式固定：
            - 目前做到哪裡
            - 已完成
            - 未完成
            - 下一步
            - 下次開工提示詞
            - 風險

            要求：
            1. 全程使用繁體中文。
            2. 先寫 `.handoff-now.md`，再回答其他事。
            3. 這一棒以收尾、保存脈絡、交棒為優先，不再開新功能或新大任務。
            4. 若需要修改，只做最小必要收尾。
            """
        }

        return """
        請切換給\(nextAI)繼續動作。先不要重做，先把目前進度整理成可直接接手的交接摘要。

        目前配額狀態：
        \(statusLines)

        交接摘要格式固定：
        - 目前做到哪裡
        - 已完成
        - 未完成
        - 下一步
        - 下次開工提示詞
        - 風險

        要求：
        1. 全程使用繁體中文。
        2. 先讀目前專案相關檔案與最新改動，再填上面 6 項。
        3. 如果上一個 AI 正在限制休息中，這一棒直接接手繼續做。
        4. 下一步只列最小必要動作，不要再開新大任務。
        """
    }

    private func finalHandoffNeeded() -> Bool {
        latestStatuses.contains { status in
            status.windows.contains { $0.alertStage == "reserve" }
        }
    }

    private func nextAIName() -> String {
        let available = latestStatuses.compactMap { status -> (String, Double)? in
            guard let percent = status.windows.first?.remainingPercent else { return nil }
            return (status.name, percent)
        }
        if let best = available.max(by: { $0.1 < $1.1 }) {
            return best.0
        }
        return "下一個可用的 AI"
    }

    private func startAutoRefresh() {
        refreshTimer?.invalidate()
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            self?.render()
        }
        RunLoop.main.add(refreshTimer!, forMode: .common)
    }

    private func timeString() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_TW")
        formatter.dateFormat = "HH:mm:ss"
        return formatter.string(from: Date())
    }

    private func resizeWindowToFitContent() {
        guard let contentView = window.contentView else { return }
        contentView.layoutSubtreeIfNeeded()
        let targetHeight = max(window.minSize.height, contentStack.fittingSize.height + 36)
        var frame = window.frame
        let delta = targetHeight - frame.size.height
        guard abs(delta) > 1 else { return }
        frame.origin.y -= delta
        frame.size.height = targetHeight
        window.setFrame(frame, display: true, animate: false)
    }

    private func renderMini() {
        guard let rows = miniContentStack?.arrangedSubviews as? [MiniProviderRowView] else { return }
        let map = Dictionary(uniqueKeysWithValues: latestStatuses.map { ($0.name, $0) })
        rows.forEach { row in
            switch row.identifier?.rawValue {
            case "mini-row-claude":
                row.update(with: map["Claude Code"]?.windows.first)
            case "mini-row-codex":
                row.update(with: map["Codex"]?.windows.first)
            default:
                row.update(with: nil)
            }
        }
    }
}

let app = NSApplication.shared
let delegate = FloatingQuotaWindow()
app.setActivationPolicy(.regular)
app.delegate = delegate
app.run()
