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

func resetBufferHintText(_ text: String, percent: Double?) -> String? {
    guard percent != nil else { return nil }
    let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
    guard trimmed.contains("重置") else { return nil }
    return "建議預留 1~2 小時緩衝"
}

func stageSummaryText(for status: ProviderStatus) -> String {
    let stages = status.windows.map(\.alertStage)
    if stages.contains("reserve") { return "強制收尾" }
    if stages.contains("handoff") { return "交接準備" }
    if stages.contains("prepare") { return "整理進度" }
    if stages.contains("unavailable") { return "等待資料" }
    return "正常"
}

func stageBadgeColor(_ stage: String) -> NSColor {
    switch stage {
    case "prepare":
        return NSColor.systemYellow.withAlphaComponent(0.18)
    case "handoff":
        return NSColor.systemOrange.withAlphaComponent(0.18)
    case "reserve":
        return NSColor.systemRed.withAlphaComponent(0.16)
    case "unavailable":
        return NSColor.systemGray.withAlphaComponent(0.18)
    default:
        return NSColor.systemGreen.withAlphaComponent(0.16)
    }
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
        wantsLayer = true
        layer?.backgroundColor = NSColor.white.withAlphaComponent(0.55).cgColor
        layer?.cornerRadius = 12
        layer?.borderWidth = 1
        layer?.borderColor = NSColor.separatorColor.withAlphaComponent(0.6).cgColor

        let label = NSTextField(labelWithString: window.title)
        label.font = .systemFont(ofSize: 11, weight: .semibold)
        label.textColor = .secondaryLabelColor
        label.setContentCompressionResistancePriority(.required, for: .horizontal)
        label.widthAnchor.constraint(equalToConstant: 40).isActive = true

        let percent = NSTextField(labelWithString: remainingPercentText(window.remainingPercent))
        percent.font = .systemFont(ofSize: 22, weight: .bold)
        percent.textColor = barColor(for: window.alertStage)
        percent.alignment = .right
        percent.setContentCompressionResistancePriority(.required, for: .horizontal)
        percent.widthAnchor.constraint(equalToConstant: 64).isActive = true

        let resetText = NSTextField(
            labelWithString: unavailableDetailText(window.remainingText, percent: window.remainingPercent)
        )
        resetText.font = .systemFont(ofSize: 12, weight: .medium)
        resetText.textColor = .secondaryLabelColor
        resetText.lineBreakMode = .byWordWrapping
        resetText.maximumNumberOfLines = 2
        resetText.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        resetText.alignment = .right

        let valueColumn = NSStackView(views: [percent, resetText])
        valueColumn.orientation = .vertical
        valueColumn.alignment = .trailing
        valueColumn.spacing = 2

        let row = NSStackView(views: [label, NSView(), valueColumn])
        row.orientation = .horizontal
        row.alignment = .top

        let track = NSView()
        track.wantsLayer = true
        track.layer?.backgroundColor = NSColor.separatorColor.withAlphaComponent(0.22).cgColor
        track.layer?.cornerRadius = 5
        track.translatesAutoresizingMaskIntoConstraints = false
        track.heightAnchor.constraint(equalToConstant: 10).isActive = true

        let fill = NSView()
        fill.wantsLayer = true
        fill.layer?.backgroundColor = barColor(for: window.alertStage).cgColor
        fill.layer?.cornerRadius = 5
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
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 12),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -12),
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 12),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -12)
        ])
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { nil }
}

final class ProviderCardView: NSView {
    init(status: ProviderStatus) {
        super.init(frame: .zero)
        wantsLayer = true
        layer?.backgroundColor = NSColor.controlBackgroundColor.withAlphaComponent(0.96).cgColor
        layer?.cornerRadius = 16
        layer?.borderWidth = 1
        layer?.borderColor = NSColor.separatorColor.withAlphaComponent(0.75).cgColor

        let title = NSTextField(labelWithString: status.name)
        title.font = .systemFont(ofSize: 18, weight: .bold)

        let summary = NSTextField(labelWithString: stageSummaryText(for: status))
        summary.font = .systemFont(ofSize: 11, weight: .semibold)
        summary.textColor = .secondaryLabelColor
        summary.alignment = .center
        summary.wantsLayer = true
        summary.drawsBackground = true
        summary.backgroundColor = stageBadgeColor(status.windows.map(\.alertStage).contains("reserve") ? "reserve" : status.windows.map(\.alertStage).contains("handoff") ? "handoff" : status.windows.map(\.alertStage).contains("prepare") ? "prepare" : status.windows.map(\.alertStage).contains("unavailable") ? "unavailable" : "normal")
        summary.isBezeled = false

        let rows = status.windows.map { UsageRowView(window: $0) }
        let rowsStack = NSStackView(views: rows)
        rowsStack.orientation = .vertical
        rowsStack.alignment = .leading
        rowsStack.distribution = .fillEqually
        rowsStack.spacing = 10

        let header = NSStackView(views: [title, NSView(), summary])
        header.orientation = .horizontal
        header.alignment = .centerY

        let hint = NSTextField(labelWithString: "建議預留 1~2 小時緩衝再換手")
        hint.font = .systemFont(ofSize: 11, weight: .regular)
        hint.textColor = .tertiaryLabelColor
        hint.isHidden = !status.windows.contains { resetBufferHintText($0.remainingText, percent: $0.remainingPercent) != nil }

        let stack = NSStackView(views: [header, rowsStack, hint])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16),
            summary.heightAnchor.constraint(equalToConstant: 24),
            summary.widthAnchor.constraint(greaterThanOrEqualToConstant: 72)
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
    private let fullWindowSize = NSSize(width: 560, height: 420)
    private let minimumFullWindowSize = NSSize(width: 420, height: 320)
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

    // 任務交接 banner（dual-AI handoff）— 跟既有「配額切換」按鈕是兩件事：
    //   - 既有 handoffButton：Claude/Codex 配額快爆，要切到另一邊繼續打同一份工作
    //   - 這個 banner：NEXT-AI-TASK.md 被更新，下一棒 AI 該接手他自己的活了
    // 資料源：~/Library/Application Support/QuotaGuardian/handoff-state.json，
    // 由 scripts/handoff_watcher.py 寫入。狀態 consumed=true 就隱藏。
    private let handoffBannerContainer = NSView()
    private let handoffBannerLabel = NSTextField(labelWithString: "")
    private let handoffBannerSubLabel = NSTextField(labelWithString: "")
    private let handoffInjectButton = NSButton(title: "▶ 切換並貼上", target: nil, action: nil)
    private let handoffDismissButton = NSButton(title: "忽略", target: nil, action: nil)
    private var lastSeenHandoffWrittenAt: Double = 0

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupWindow()
        // 先把空殼視窗推到前景，確保使用者一定看得到，
        // 之後 render() 再填內容。原本順序「先 render 再 bringWindowToFront」
        // 在第一次跑時，render() 內部 `card.widthAnchor.constraint(equalTo: contentStack.widthAnchor)`
        // 在 card 還沒進 view hierarchy 就 activate，會丟 NSException 被 run loop 吞掉，
        // 導致 bringWindowToFront 跟著被跳過、視窗永遠不出來。
        bringWindowToFront()
        render()
        startAutoRefresh()
        bringWindowToFront()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) { [weak self] in
            self?.bringWindowToFront()
        }
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
            styleMask: [.nonactivatingPanel, .titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.title = "配額守門員"
        window.isFloatingPanel = true
        window.isReleasedWhenClosed = false
        window.hidesOnDeactivate = false
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary]
        window.titlebarAppearsTransparent = true
        // 關鍵：level 一定要在 isFloatingPanel 之後設，不然會被 floating(3) 蓋掉。
        // statusBar level 會浮在全螢幕視窗 / Dock / menu bar 之上，
        // 配 .nonactivatingPanel + canJoinAllSpaces + fullScreenAuxiliary，
        // 才能在任何 Space 都看得到浮動窗。
        window.level = .statusBar
        placeWindowAtTopRight(size: fullWindowSize)

        // 用 .hudWindow + .withinWindow 是為了：
        // 1) 即使 panel 是 .nonactivatingPanel（不會 active），背景仍然會被畫出來，
        //    避免整個視窗看起來變全透明而「以為消失」。
        // 2) .withinWindow 不依賴桌面內容，即使視窗位置背後是空的也能正常顯示。
        let visual = NSVisualEffectView(frame: rect)
        visual.material = .hudWindow
        visual.blendingMode = .withinWindow
        visual.state = .active
        visual.wantsLayer = true
        // 再墊一層底色保險。萬一 VisualEffectView 因為任何原因沒渲染，
        // 這個底色會讓視窗仍然看得到（不會變成完全透明）。
        visual.layer?.backgroundColor = NSColor.windowBackgroundColor.withAlphaComponent(0.92).cgColor
        window.contentView = visual
        window.isOpaque = false
        window.backgroundColor = NSColor.clear

        let title = NSTextField(labelWithString: "Codex Pro × Claude Code")
        title.font = .systemFont(ofSize: 17, weight: .bold)

        updatedLabel.font = .systemFont(ofSize: 11, weight: .medium)
        updatedLabel.textColor = .secondaryLabelColor

        cardsStack.orientation = .vertical
        cardsStack.alignment = .centerX
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
        footer.alignment = .centerY
        footer.distribution = .fillEqually
        footer.spacing = 10
        miniModeButton.setContentHuggingPriority(.defaultLow, for: .horizontal)
        handoffButton.setContentHuggingPriority(.defaultLow, for: .horizontal)
        miniModeButton.heightAnchor.constraint(equalToConstant: 32).isActive = true
        handoffButton.heightAnchor.constraint(equalToConstant: 32).isActive = true

        // ===== 任務交接 banner（預設隱藏，refreshHandoffBanner 控制） =====
        handoffBannerContainer.wantsLayer = true
        handoffBannerContainer.layer?.cornerRadius = 10
        handoffBannerContainer.layer?.backgroundColor = NSColor.systemOrange.withAlphaComponent(0.18).cgColor
        handoffBannerContainer.layer?.borderColor = NSColor.systemOrange.withAlphaComponent(0.55).cgColor
        handoffBannerContainer.layer?.borderWidth = 1
        handoffBannerContainer.translatesAutoresizingMaskIntoConstraints = false
        handoffBannerContainer.isHidden = true

        handoffBannerLabel.font = .systemFont(ofSize: 14, weight: .bold)
        handoffBannerLabel.textColor = .labelColor
        handoffBannerLabel.lineBreakMode = .byTruncatingTail
        handoffBannerSubLabel.font = .systemFont(ofSize: 11, weight: .regular)
        handoffBannerSubLabel.textColor = .secondaryLabelColor
        handoffBannerSubLabel.lineBreakMode = .byTruncatingTail

        let bannerTextStack = NSStackView(views: [handoffBannerLabel, handoffBannerSubLabel])
        bannerTextStack.orientation = .vertical
        bannerTextStack.alignment = .leading
        bannerTextStack.spacing = 2

        handoffInjectButton.target = self
        handoffInjectButton.action = #selector(handoffInject)
        handoffInjectButton.bezelStyle = .rounded
        handoffInjectButton.font = .systemFont(ofSize: 12, weight: .semibold)
        handoffInjectButton.heightAnchor.constraint(equalToConstant: 28).isActive = true

        handoffDismissButton.target = self
        handoffDismissButton.action = #selector(handoffDismiss)
        handoffDismissButton.bezelStyle = .rounded
        handoffDismissButton.font = .systemFont(ofSize: 11, weight: .regular)
        handoffDismissButton.heightAnchor.constraint(equalToConstant: 28).isActive = true

        let bannerButtonStack = NSStackView(views: [handoffDismissButton, handoffInjectButton])
        bannerButtonStack.orientation = .horizontal
        bannerButtonStack.spacing = 6

        let bannerStack = NSStackView(views: [bannerTextStack, NSView(), bannerButtonStack])
        bannerStack.orientation = .horizontal
        bannerStack.alignment = .centerY
        bannerStack.spacing = 8
        bannerStack.translatesAutoresizingMaskIntoConstraints = false
        handoffBannerContainer.addSubview(bannerStack)
        NSLayoutConstraint.activate([
            bannerStack.leadingAnchor.constraint(equalTo: handoffBannerContainer.leadingAnchor, constant: 12),
            bannerStack.trailingAnchor.constraint(equalTo: handoffBannerContainer.trailingAnchor, constant: -10),
            bannerStack.topAnchor.constraint(equalTo: handoffBannerContainer.topAnchor, constant: 8),
            bannerStack.bottomAnchor.constraint(equalTo: handoffBannerContainer.bottomAnchor, constant: -8),
        ])

        contentStack = NSStackView(views: [header, cardsStack, handoffBannerContainer, footer])
        contentStack.orientation = .vertical
        contentStack.alignment = .centerX
        contentStack.spacing = 16
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
        window.minSize = minimumFullWindowSize
    }

    private func placeWindowAtTopRight(size: NSSize) {
        guard let screen = preferredScreen() else { return }
        let visibleFrame = screen.visibleFrame
        let origin = NSPoint(
            x: visibleFrame.maxX - size.width - 20,
            y: visibleFrame.maxY - size.height - 20
        )
        window.setFrame(NSRect(origin: origin, size: size), display: true)
        ensureWindowVisible()
    }

    private func ensureWindowVisible() {
        let current = window.frame
        if NSScreen.screens.contains(where: { $0.visibleFrame.intersects(current) }) {
            return
        }
        guard let fallback = NSScreen.main?.visibleFrame ?? NSScreen.screens.first?.visibleFrame else { return }
        let safeOrigin = NSPoint(
            x: max(fallback.minX + 20, min(current.origin.x, fallback.maxX - current.size.width - 20)),
            y: max(fallback.minY + 20, min(current.origin.y, fallback.maxY - current.size.height - 20))
        )
        window.setFrame(NSRect(origin: safeOrigin, size: current.size), display: true, animate: false)
    }

    private func preferredScreen() -> NSScreen? {
        // 優先放到「使用者目前游標所在的螢幕」，這樣多螢幕情境下
        // 浮動窗一定出現在使用者眼前那塊。
        let cursor = NSEvent.mouseLocation
        if let here = NSScreen.screens.first(where: { NSPointInRect(cursor, $0.frame) }) {
            return here
        }
        // 退而求其次：menu bar 主螢幕（frame.origin == .zero）。
        if let primary = NSScreen.screens.first(where: { $0.frame.origin == .zero }) {
            return primary
        }
        return NSScreen.main ?? NSScreen.screens.first
    }

    private func bringWindowToFront() {
        NSApp.activate(ignoringOtherApps: true)
        NSRunningApplication.current.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
        window.orderFrontRegardless()
        window.makeKeyAndOrderFront(nil)
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
                // 一定要先 addArrangedSubview 再 activate constraint，
                // 不然 card 還沒進 view hierarchy 跟 contentStack 沒有共同祖先，
                // activate 會丟 NSException 被吃掉，整個流程斷在這。
                cardsStack.addArrangedSubview(card)
                card.widthAnchor.constraint(equalTo: contentStack.widthAnchor).isActive = true
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
            window.styleMask.insert(.resizable)
            window.title = "配額守門員"
            window.minSize = minimumFullWindowSize

            if let storedFrame = fullModeFrame {
                window.setFrame(storedFrame, display: true, animate: false)
                ensureWindowVisible()
            } else {
                placeWindowAtTopRight(size: fullWindowSize)
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
        window.styleMask.remove(.resizable)
        window.minSize = miniWindowSize

        var miniFrame = window.frame
        miniFrame.origin.y += miniFrame.height - miniWindowSize.height
        miniFrame.size = miniWindowSize
        window.setFrame(miniFrame, display: true, animate: false)
        ensureWindowVisible()
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

    @objc private func handoffInject() {
        let prompt = handoffPrompt()
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(prompt, forType: .string)
        updatedLabel.stringValue = "已複製交接提示詞"
        handoffBannerContainer.isHidden = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.6) { [weak self] in
            self?.updatedLabel.stringValue = "更新 \(self?.timeString() ?? "")"
        }
    }

    @objc private func handoffDismiss() {
        handoffBannerContainer.isHidden = true
        updatedLabel.stringValue = "已忽略交接提醒"
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
        let targetWidth = max(window.minSize.width, contentStack.fittingSize.width + 36)
        let targetHeight = max(window.minSize.height, contentStack.fittingSize.height + 36)
        var frame = window.frame
        let resizedWidth = max(frame.size.width, targetWidth)
        let resizedHeight = max(frame.size.height, targetHeight)
        let deltaWidth = resizedWidth - frame.size.width
        let deltaHeight = resizedHeight - frame.size.height
        if abs(deltaWidth) <= 1 && abs(deltaHeight) <= 1 { return }
        frame.origin.x -= deltaWidth / 2
        frame.origin.y -= deltaHeight
        frame.size.width = resizedWidth
        frame.size.height = resizedHeight
        window.setFrame(frame, display: true, animate: false)
        ensureWindowVisible()
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
