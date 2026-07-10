export interface SurahInfo {
  number: number;
  name: string;
  ayahCount: number;
}

// [name, ayahCount] — index + 1 is the surah number (1..114)
const RAW: ReadonlyArray<readonly [string, number]> = [
  ["الفاتحة", 7], ["البقرة", 286], ["آل عمران", 200], ["النساء", 176],
  ["المائدة", 120], ["الأنعام", 165], ["الأعراف", 206], ["الأنفال", 75],
  ["التوبة", 129], ["يونس", 109], ["هود", 123], ["يوسف", 111],
  ["الرعد", 43], ["إبراهيم", 52], ["الحجر", 99], ["النحل", 128],
  ["الإسراء", 111], ["الكهف", 110], ["مريم", 98], ["طه", 135],
  ["الأنبياء", 112], ["الحج", 78], ["المؤمنون", 118], ["النور", 64],
  ["الفرقان", 77], ["الشعراء", 227], ["النمل", 93], ["القصص", 88],
  ["العنكبوت", 69], ["الروم", 60], ["لقمان", 34], ["السجدة", 30],
  ["الأحزاب", 73], ["سبأ", 54], ["فاطر", 45], ["يس", 83],
  ["الصافات", 182], ["ص", 88], ["الزمر", 75], ["غافر", 85],
  ["فصلت", 54], ["الشورى", 53], ["الزخرف", 89], ["الدخان", 59],
  ["الجاثية", 37], ["الأحقاف", 35], ["محمد", 38], ["الفتح", 29],
  ["الحجرات", 18], ["ق", 45], ["الذاريات", 60], ["الطور", 49],
  ["النجم", 62], ["القمر", 55], ["الرحمن", 78], ["الواقعة", 96],
  ["الحديد", 29], ["المجادلة", 22], ["الحشر", 24], ["الممتحنة", 13],
  ["الصف", 14], ["الجمعة", 11], ["المنافقون", 11], ["التغابن", 18],
  ["الطلاق", 12], ["التحريم", 12], ["الملك", 30], ["القلم", 52],
  ["الحاقة", 52], ["المعارج", 44], ["نوح", 28], ["الجن", 28],
  ["المزمل", 20], ["المدثر", 56], ["القيامة", 40], ["الإنسان", 31],
  ["المرسلات", 50], ["النبأ", 40], ["النازعات", 46], ["عبس", 42],
  ["التكوير", 29], ["الانفطار", 19], ["المطففين", 36], ["الانشقاق", 25],
  ["البروج", 22], ["الطارق", 17], ["الأعلى", 19], ["الغاشية", 26],
  ["الفجر", 30], ["البلد", 20], ["الشمس", 15], ["الليل", 21],
  ["الضحى", 11], ["الشرح", 8], ["التين", 8], ["العلق", 19],
  ["القدر", 5], ["البينة", 8], ["الزلزلة", 8], ["العاديات", 11],
  ["القارعة", 11], ["التكاثر", 8], ["العصر", 3], ["الهمزة", 9],
  ["الفيل", 5], ["قريش", 4], ["الماعون", 7], ["الكوثر", 3],
  ["الكافرون", 6], ["النصر", 3], ["المسد", 5], ["الإخلاص", 4],
  ["الفلق", 5], ["الناس", 6],
];

export const SURAHS: ReadonlyArray<SurahInfo> = RAW.map(([name, ayahCount], i) => ({
  number: i + 1,
  name,
  ayahCount,
}));

/** Strip diacritics, unify hamza/alef/ya/ta-marbuta, drop "سورة" prefix. */
export function normalizeArabic(s: string): string {
  return (s || "")
    .replace(/[ً-ْٰـ]/g, "") // harakat + dagger alef + tatweel
    .replace(/[آأإٱ]/g, "ا") // آ أ إ ٱ → ا
    .replace(/ى/g, "ي") // ى → ي
    .replace(/ة/g, "ه") // ة → ه
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^سوره\s+/, "");
}

// Common alternative names for some surahs.
const ALIASES: Record<string, number> = {
  "براءه": 9,
  "بني اسراييل": 17,
  "الدهر": 76,
  "المومن": 40,
  "حم السجده": 41,
  "لم يكن": 98,
  "الانشراح": 94,
  "الم نشرح": 94,
  "التوحيد": 112,
  "قل هو الله احد": 112,
};

const BY_NAME: Map<string, number> = (() => {
  const m = new Map<string, number>();
  for (const s of SURAHS) m.set(normalizeArabic(s.name), s.number);
  for (const [alias, num] of Object.entries(ALIASES)) m.set(normalizeArabic(alias), num);
  return m;
})();

/** Resolve an Arabic surah name to its number (1..114), or null if unknown. */
export function surahNumberFromName(name: string): number | null {
  return BY_NAME.get(normalizeArabic(name)) ?? null;
}

/** Ayah count of a surah number, or 0 if out of range. */
export function ayahCountOf(surahNumber: number): number {
  return SURAHS[surahNumber - 1]?.ayahCount ?? 0;
}
