import { useLang } from "./LanguageContext";

export default function T({ sk, en }) {
  const { lang } = useLang();

  if (lang === "sk") return sk;
  if (lang === "en") return en;

  return sk || en || "";
}