// GENERATED — do not edit.
// Source: 30_ENGINE/pvm/importance.py, risk.py
// Regenerate: python 40_APP/generate_shared.py
//
// The engine is the reference implementation and the app is what ships. Maintained by
// hand these two diverge silently: the app files a passport somewhere the engine would
// not, and every number measured on the engine stops describing the product. CI
// regenerates this and fails on any diff.

import Foundation

/// One of §4's 大类. `prefixes` is empty for the two classes that are not
/// branches of the navigational tree — see `Importance.swift`.
public struct AssetClass: Equatable {
    public let key: String
    public let name: String
    public let examples: String
    public let defaultRiskLow: Int
    public let defaultRiskHigh: Int
    public let baselineImportance: Importance
    public let prefixes: [String]
}

public enum AssetClasses {

    public static let treasuredMemory = AssetClass(
        key: "treasured_memory",
        name: "珍贵记忆",
        examples: "老照片、不可替代家庭影像、特殊人生事件",
        defaultRiskLow: 6, defaultRiskHigh: 6,
        baselineImportance: .i4Treasured,
        prefixes: [])

    public static let identityFinancial = AssetClass(
        key: "identity_financial",
        name: "身份/金融证件",
        examples: "身份证、护照、驾照、行驶证、银行卡",
        defaultRiskLow: 5, defaultRiskHigh: 5,
        baselineImportance: .i2Ordinary,
        prefixes: ["Documents > Identity", "Documents > Financial"])

    public static let legalFormal = AssetClass(
        key: "legal_formal",
        name: "法律/正式文件",
        examples: "合同、协议、保险、税务、产权",
        defaultRiskLow: 5, defaultRiskHigh: 5,
        baselineImportance: .i2Ordinary,
        prefixes: ["Documents > Contracts", "Documents > Medical"])

    public static let transaction = AssetClass(
        key: "transaction",
        name: "交易与购买",
        examples: "收据、发票、订单、付款、保修",
        defaultRiskLow: 4, defaultRiskHigh: 4,
        baselineImportance: .i2Ordinary,
        prefixes: ["Documents > Receipts", "Documents > Warranty", "Purchases"])

    public static let workStudy = AssetClass(
        key: "work_study",
        name: "工作/学习",
        examples: "白板、会议、课堂、项目资料",
        defaultRiskLow: 3, defaultRiskHigh: 4,
        baselineImportance: .i2Ordinary,
        prefixes: ["Work"])

    public static let travelEvent = AssetClass(
        key: "travel_event",
        name: "旅行/事件",
        examples: "机票、登机牌、酒店、门票、活动",
        defaultRiskLow: 3, defaultRiskHigh: 4,
        baselineImportance: .i3Meaningful,
        prefixes: ["Travel"])

    public static let peopleFamily = AssetClass(
        key: "people_family",
        name: "人物与家庭",
        examples: "自拍、朋友、家庭、儿童、合照",
        defaultRiskLow: 3, defaultRiskHigh: 4,
        baselineImportance: .i3Meaningful,
        prefixes: ["People"])

    public static let possessionRecord = AssetClass(
        key: "possession_record",
        name: "物品记录",
        examples: "家电、家具、衣服、商品、设备序列号",
        defaultRiskLow: 2, defaultRiskHigh: 2,
        baselineImportance: .i1Low,
        prefixes: ["Objects", "Clothing"])

    public static let burstMoment = AssetClass(
        key: "burst_moment",
        name: "连拍/同一时刻",
        examples: "同人物同场景短时间多张",
        defaultRiskLow: 1, defaultRiskHigh: 2,
        baselineImportance: .i1Low,
        prefixes: [])

    public static let everydayPhoto = AssetClass(
        key: "everyday_photo",
        name: "普通摄影",
        examples: "风景、食物、街景、随手拍",
        defaultRiskLow: 1, defaultRiskHigh: 2,
        baselineImportance: .i2Ordinary,
        prefixes: ["Places"])

    public static let ordinaryScreenshot = AssetClass(
        key: "ordinary_screenshot",
        name: "普通截图",
        examples: "网页、聊天、新闻、商品、工作截图",
        defaultRiskLow: 1, defaultRiskHigh: 2,
        baselineImportance: .i1Low,
        prefixes: ["Screenshots"])

    public static let downloaded = AssetClass(
        key: "downloaded",
        name: "网络/下载内容",
        examples: "Meme、表情包、壁纸、社媒图、宣传图",
        defaultRiskLow: 0, defaultRiskHigh: 1,
        baselineImportance: .i1Low,
        prefixes: ["Downloads"])

    public static let transientInfo = AssetClass(
        key: "transient_info",
        name: "临时信息",
        examples: "验证码、取件码、停车位置、临时导航、一次性报错",
        defaultRiskLow: 1, defaultRiskHigh: 1,
        baselineImportance: .i0None,
        prefixes: ["Screenshots > Temporary", "Screenshots > Errors"])

    public static let undescribed = AssetClass(
        key: "undescribed",
        name: "（§4 未描述）",
        examples: "分类器未能进一步识别的资产",
        defaultRiskLow: 0, defaultRiskHigh: 6,
        baselineImportance: .i2Ordinary,
        prefixes: [])

    /// §4's table, in §4's order. Scanned in order, longest prefix wins.
    public static let all: [AssetClass] = [
        treasuredMemory,
        identityFinancial,
        legalFormal,
        transaction,
        workStudy,
        travelEvent,
        peopleFamily,
        possessionRecord,
        burstMoment,
        everydayPhoto,
        ordinaryScreenshot,
        downloaded,
        transientInfo,
    ]

    /// How many other assets a named person must appear in before they
    /// read as somebody in this user's life rather than a passer-by.
    public static let recurringPerson = 12
    /// Where a considered set of shots becomes a held shutter.
    public static let burstSize = 6
}
