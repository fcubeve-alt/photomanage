// GENERATED — do not edit.
// Source: 30_ENGINE/pvm/rules.py, risk.py, classifier.py, verdict.py
// Regenerate: python 40_APP/generate_shared.py
//
// The engine is the reference implementation and the app is what ships. Maintained by
// hand these two diverge silently: the app files a passport somewhere the engine would
// not, and every number measured on the engine stops describing the product. CI
// regenerates this and fails on any diff.

import Foundation

public struct TextRule {
    public let pattern: String
    public let path: String
    public let weight: Double
    public let reason: String
    /// Fires only when the asset already sits under this root, if set.
    public let requiresRoot: String?
}

public enum Rules {

    public static let documentRules: [TextRule] = [
        TextRule(pattern: "\\bpassport\\b", path: "Documents > Identity > Passports", weight: 0.9, reason: "the text “passport” was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\bdriv(er|ing)'?s?\\s+licen[cs]e\\b", path: "Documents > Identity > Driver Licenses", weight: 0.9, reason: "the text “driving licence” was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\b(id\\s*card|national\\s+id|identity\\s+card)\\b", path: "Documents > Identity > ID Cards", weight: 0.9, reason: "the text “ID card” was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\bvisa\\b(?!\\s*(card|debit|credit))", path: "Documents > Identity > Visas", weight: 0.78, reason: "the text “visa” was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\b(tenancy|lease\\s+agreement|assured\\s+shorthold)\\b", path: "Documents > Contracts > Tenancy", weight: 0.85, reason: "tenancy wording was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\b(employment\\s+(contract|agreement)|offer\\s+letter)\\b", path: "Documents > Contracts > Employment", weight: 0.85, reason: "employment-contract wording was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\b(insurance|policy\\s+(number|no\\.?)|underwrit)", path: "Documents > Contracts > Insurance", weight: 0.82, reason: "insurance-policy wording was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\bcontract\\b", path: "Documents > Contracts", weight: 0.7, reason: "the text “contract” was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\b(sort\\s*code|iban\\b|account\\s+number|bank\\s+of\\b)", path: "Documents > Financial > Bank", weight: 0.85, reason: "bank-account details were read on the document", requiresRoot: nil),
        TextRule(pattern: "\\b(hmrc|p60\\b|p45\\b|tax\\s+(return|year|code))", path: "Documents > Financial > Tax", weight: 0.85, reason: "tax wording was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\b(statement|balance\\s+(brought|carried))\\b", path: "Documents > Financial > Statements", weight: 0.72, reason: "statement wording was read on the document", requiresRoot: nil),
        TextRule(pattern: "\\b(prescription\\w*|nhs\\b|test\\s+results?|referral\\s+letter|clinic\\w*|surgery\\s+appointment)\\b", path: "Documents > Medical", weight: 0.8, reason: "this looks like a medical document — filed as a document, and nothing about your health is inferred, stored or shown from it", requiresRoot: nil),
        TextRule(pattern: "\\bdocument\\b", path: "Documents", weight: 0.55, reason: "text on the image reads as a document rather than a scene", requiresRoot: nil),
    ]

    public static let purchaseRules: [TextRule] = [
        TextRule(pattern: "\\b(receipt|invoice)\\b|\\b(vat|subtotal)\\b|\\btotal\\s*[:£$€]", path: "Purchases > Receipts", weight: 0.85, reason: "receipt or invoice wording was read on the image", requiresRoot: nil),
        TextRule(pattern: "\\b(warrant\\w*|guarantee\\w*)\\b", path: "Purchases > Warranty", weight: 0.85, reason: "warranty wording was read on the image", requiresRoot: nil),
        TextRule(pattern: "\\border\\s+(number|no\\.?|confirm\\w*)\\b|\\byour\\s+order\\b|\\border\\s+placed\\b", path: "Purchases > Orders", weight: 0.8, reason: "an order confirmation was read on the image", requiresRoot: nil),
        TextRule(pattern: "\\b(out\\s+for\\s+delivery|tracking\\s+(number|no\\.?)|dispatch\\w*|delivered\\s+on|courier)\\b", path: "Purchases > Delivery", weight: 0.8, reason: "delivery-tracking wording was read on the image", requiresRoot: nil),
        TextRule(pattern: "\\bpurchase\\b", path: "Purchases", weight: 0.55, reason: "the image reads as purchase paperwork, but not which kind", requiresRoot: nil),
    ]

    public static let screenshotRules: [TextRule] = [
        TextRule(pattern: "\\b(verification|confirmation|security)\\s+code\\b|\\bone[-\\s]?time\\s+(code|password)\\b|\\botp\\b", path: "Screenshots > Temporary > Verification Codes", weight: 0.88, reason: "a one-time verification code was read in the screenshot", requiresRoot: "Screenshots"),
        TextRule(pattern: "\\b(pickup|collection)\\s+code\\b|\\block(er)?\\s*[a-z]?\\d+\\b", path: "Screenshots > Temporary > Pickup Codes", weight: 0.86, reason: "a parcel pickup code was read in the screenshot", requiresRoot: "Screenshots"),
        TextRule(pattern: "\\b(boarding\\s+pass|e[-\\s]?ticket|gate\\s+\\d+|seat\\s+\\d+[a-z]\\b|booking\\s+reference)\\b", path: "Screenshots > Temporary > Tickets", weight: 0.84, reason: "a ticket or boarding pass was read in the screenshot", requiresRoot: "Screenshots"),
        TextRule(pattern: "\\b(directions|route|\\d+\\s*min\\s+(drive|walk)|maps?)\\b", path: "Screenshots > Maps", weight: 0.72, reason: "map or directions wording was read in the screenshot", requiresRoot: "Screenshots"),
        TextRule(pattern: "\\b(add\\s+to\\s+(bag|cart|basket)|checkout|in\\s+stock|free\\s+returns)\\b", path: "Screenshots > Shopping", weight: 0.75, reason: "shop wording was read in the screenshot", requiresRoot: "Screenshots"),
        TextRule(pattern: "\\b(typing|delivered|read\\s+\\d{1,2}:\\d{2}|whatsapp|imessage|telegram)\\b", path: "Screenshots > Chat", weight: 0.72, reason: "chat wording was read in the screenshot", requiresRoot: "Screenshots"),
        TextRule(pattern: "\\b(error\\w*|fail\\w*|unable\\s+to|something\\s+went\\s+wrong|exception|crash\\w*)\\b", path: "Screenshots > Errors", weight: 0.74, reason: "an error message was read in the screenshot", requiresRoot: "Screenshots"),
        TextRule(pattern: "\\b(sprint|stand-?up|jira|confluence|agenda|slide\\s+\\d+|action\\s+items?)\\b", path: "Screenshots > Work", weight: 0.72, reason: "work wording was read in the screenshot", requiresRoot: "Screenshots"),
        TextRule(pattern: "https?://|\\bwww\\.|\\.com\\b", path: "Screenshots > Web", weight: 0.62, reason: "a web address was read in the screenshot", requiresRoot: "Screenshots"),
    ]

    public static let workTextRules: [TextRule] = [
        TextRule(pattern: "\\b(agenda|minutes|action\\s+items?|attendees)\\b", path: "Work > Meetings", weight: 0.7, reason: "meeting wording was read on the image", requiresRoot: nil),
    ]

    public static let sceneMap: [String: String] = [
        "backpack": "Objects > Other",
        "bed": "Objects > Furniture",
        "bicycle": "Objects > Bicycle",
        "bike": "Objects > Bicycle",
        "blackboard": "Work > Whiteboards",
        "blouse": "Clothing > Tops",
        "boot": "Clothing > Shoes",
        "cabinet": "Objects > Furniture",
        "camera": "Objects > Devices",
        "chair": "Objects > Furniture",
        "coat": "Clothing > Outerwear",
        "computer": "Objects > Devices",
        "conference_room": "Work > Meetings",
        "desk": "Objects > Furniture",
        "handbag": "Objects > Other",
        "headphones": "Objects > Devices",
        "jacket": "Clothing > Outerwear",
        "keys": "Objects > Other",
        "laptop": "Objects > Devices",
        "luggage": "Objects > Other",
        "meme": "Downloads > Memes",
        "microwave": "Objects > Appliances",
        "mobile_phone": "Objects > Devices",
        "oven": "Objects > Appliances",
        "presentation": "Work > Meetings",
        "projection_screen": "Work > Meetings",
        "refrigerator": "Objects > Appliances",
        "shirt": "Clothing > Tops",
        "shoe": "Clothing > Shoes",
        "sneaker": "Clothing > Shoes",
        "sofa": "Objects > Furniture",
        "suitcase": "Objects > Other",
        "sunglasses": "Objects > Other",
        "sweater": "Clothing > Tops",
        "t_shirt": "Clothing > Tops",
        "table": "Objects > Furniture",
        "television": "Objects > Devices",
        "umbrella": "Objects > Other",
        "wallpaper": "Downloads > Wallpapers",
        "washing_machine": "Objects > Appliances",
        "whiteboard": "Work > Whiteboards",
        "wristwatch": "Objects > Other",
    ]

    public static let sceneFloor: Double = 0.35

    // §10 Intent Search vocabulary. Generated for the same reason the
    // scene map is: a search that recognises 身份证 on one side and not
    // the other is two products, and nobody would notice until a user
    // typed it into the wrong one.
    public static let categoryWords: [String: String] = [
        "bank": "Documents > Financial > Bank",
        "clothes": "Clothing",
        "clothing": "Clothing",
        "contract": "Documents > Contracts",
        "delivery": "Purchases > Delivery",
        "documents": "Documents",
        "downloads": "Downloads",
        "drivers license": "Documents > Identity > Driver Licenses",
        "driving licence": "Documents > Identity > Driver Licenses",
        "id card": "Documents > Identity > ID Cards",
        "identity card": "Documents > Identity > ID Cards",
        "insurance": "Documents > Contracts > Insurance",
        "invoice": "Purchases > Receipts",
        "medical": "Documents > Medical",
        "objects": "Objects",
        "order": "Purchases > Orders",
        "passport": "Documents > Identity > Passports",
        "people": "People",
        "places": "Places",
        "receipt": "Purchases > Receipts",
        "screenshot": "Screenshots",
        "screenshots": "Screenshots",
        "statement": "Documents > Financial > Statements",
        "tax": "Documents > Financial > Tax",
        "tenancy": "Documents > Contracts > Tenancy",
        "travel": "Travel",
        "trip": "Travel",
        "visa": "Documents > Identity > Visas",
        "warranty": "Purchases > Warranty",
        "work": "Work",
        "下载": "Downloads",
        "人": "People",
        "人物": "People",
        "保修": "Purchases > Warranty",
        "保险": "Documents > Contracts > Insurance",
        "医疗": "Documents > Medical",
        "发票": "Purchases > Receipts",
        "合同": "Documents > Contracts",
        "地点": "Places",
        "对账单": "Documents > Financial > Statements",
        "工作": "Work",
        "快递": "Purchases > Delivery",
        "截图": "Screenshots",
        "护照": "Documents > Identity > Passports",
        "报税": "Documents > Financial > Tax",
        "收据": "Purchases > Receipts",
        "文件": "Documents",
        "旅行": "Travel",
        "物品": "Objects",
        "租房合同": "Documents > Contracts > Tenancy",
        "签证": "Documents > Identity > Visas",
        "衣服": "Clothing",
        "订单": "Purchases > Orders",
        "证件": "Documents > Identity",
        "身份证": "Documents > Identity > ID Cards",
        "银行": "Documents > Financial > Bank",
        "驾照": "Documents > Identity > Driver Licenses",
    ]

    public static let multiSideWords: [String] = [
        "front and back",
        "both sides",
        "front back",
        "正反面",
        "两面",
        "正反",
    ]

    public static let mediaWords: [String: String] = [
        "photo": "image",
        "photos": "image",
        "video": "video",
        "videos": "video",
        "图片": "image",
        "影片": "video",
        "照片": "image",
        "视频": "video",
    ]

    public static let searchFiller: [String] = [
        "a",
        "all",
        "an",
        "and",
        "any",
        "are",
        "find",
        "for",
        "from",
        "image",
        "images",
        "in",
        "is",
        "me",
        "my",
        "of",
        "or",
        "photo",
        "photos",
        "picture",
        "pictures",
        "please",
        "search",
        "show",
        "some",
        "taken",
        "the",
        "there",
        "to",
        "with",
    ]

    /// Stripped as substrings, longest first: Chinese is not space-separated.
    public static let searchFillerCJK: [String] = [
        "找到",
        "所有",
        "那些",
        "我的",
        "时候",
        "照片",
        "图片",
        "找",
        "查",
        "搜",
        "我",
        "的",
        "有",
        "里",
        "中",
        "和",
        "在",
        "张",
        "个",
        "年",
        "月",
        "日",
        "拍",
        "过",
        "些",
        "了",
    ]


    /// §6 category → risk, in order: the first prefix that matches wins,
    /// and the highest match across all of an asset's paths is taken.
    public static let riskByPathPrefix: [(String, Int)] = [
        ("Documents > Identity", 5),
        ("Documents > Contracts", 5),
        ("Documents > Financial", 5),
        ("Documents > Medical", 5),
        ("Documents > Receipts", 4),
        ("Documents > Warranty", 4),
        ("Documents", 4),
        ("Purchases", 4),
        ("Work", 4),
        ("People", 3),
        ("Travel", 3),
        ("Screenshots > Temporary", 1),
        ("Downloads", 0),
        ("Screenshots", 2),
        ("Objects", 2),
        ("Clothing", 2),
        ("Places", 2),
    ]

    public static let reviewFloor: Double = 0.55
    public static let maxConfidence: Double = 0.99
    public static let settleAt: Double = 0.85
}
